"""Where each part of a document sits in the bytes it was read from.

Issue #25 asks that an error carry the location in the file, and the reason it
gives is the one that decides the shape of this module: somebody debugging a
twenty term action against a message with no line number stops using the
pipeline. A path like `lagrangian.terms[7].head` says which part of the document
is wrong and does not say where to put the cursor.

The loader is the one record 0004 fixes and is not replaced here. `json.loads`
reads the bytes into strings, numbers, lists and mappings, and this module then
walks the parsed data and the same text side by side and records where each part
started. Two consequences are worth stating rather than discovering.

The walk is driven by the parsed data, so the paths it produces are exactly the
paths a reader of that data can ask about, and a path this cannot place is a
path nothing could have produced. It is not a second parser with its own opinion
about what the bytes mean.

Walking two things in step is a thing that can go out of step, and a position
index that has drifted is worse than none, because it points confidently at the
wrong line. So every step is taken against the character the data says must be
there, and a character that is not there raises rather than being skipped past.
That arm is reachable only by handing this a text and a value that did not come
from it, which is what its proof does.

What is recorded, per part, and why it is not always the same thing. A member of
a mapping is recorded at its key, because the mistakes at that path are about
the key: a key nobody admits, a key of the wrong kind, a key that should not be
there. A member of a list is recorded at the member itself, since it has no key.
The whole document is recorded at its first character.
"""

import json
from dataclasses import dataclass
from typing import Final

# The four characters JSON counts as whitespace between tokens.
WHITESPACE: Final = " \t\n\r"

# What ends a number or one of the three bare words. Everything else in a
# document is a string, a mapping or a list, and each of those is taken by a
# rule of its own below.
ENDS_A_LITERAL: Final = ",]}" + WHITESPACE


@dataclass(frozen=True)
class Position:
    """One place in the text, counted the way a text editor counts.

    Both are one based, which is what `json.JSONDecodeError` reports for a
    document that did not parse at all, so a refusal from the loader and a
    refusal from the schema point at a line and a column that mean the same
    thing.
    """

    line: int
    column: int

    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}"


class Desynchronised(ValueError):
    """The text and the value did not come from each other.

    Raised rather than recovered from. A wrong position is a worse answer than
    no position, because a reader trusts it and goes to the wrong line.
    """


class _Scan:
    """A cursor over the text that counts lines while it moves."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.at = 0
        self.line = 1
        self.column = 1

    def here(self) -> Position:
        return Position(line=self.line, column=self.column)

    def done(self) -> bool:
        return self.at >= len(self.text)

    def _step(self) -> str:
        character = self.text[self.at]
        self.at += 1
        if character == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return character

    def skip_whitespace(self) -> None:
        while not self.done() and self.text[self.at] in WHITESPACE:
            self._step()

    def take(self, character: str) -> None:
        """Move past one structural character, or refuse to move at all."""
        self.skip_whitespace()
        if self.done() or self.text[self.at] != character:
            found = "the end of the text" if self.done() else repr(self.text[self.at])
            raise Desynchronised(
                f"expected {character!r} at {self.here()} and found {found}, so "
                "the text and the value being walked did not come from each other"
            )
        self._step()

    def skip_string(self) -> None:
        self.take('"')
        while True:
            if self.done():
                raise Desynchronised(
                    f"the string beginning before {self.here()} does not end, so "
                    "the text and the value being walked did not come from each other"
                )
            character = self._step()
            if character == "\\":
                if self.done():
                    raise Desynchronised(
                        f"an escape at {self.here()} ends the text, so the text "
                        "and the value being walked did not come from each other"
                    )
                self._step()
            elif character == '"':
                return

    def skip_literal(self) -> None:
        """Move past a number or one of the three bare words."""
        self.skip_whitespace()
        moved = False
        while not self.done() and self.text[self.at] not in ENDS_A_LITERAL:
            self._step()
            moved = True
        if not moved:
            raise Desynchronised(
                f"expected a number or a bare word at {self.here()} and found "
                "neither, so the text and the value being walked did not come "
                "from each other"
            )


def join(where: str, name: str) -> str:
    """A path the way the schema writes one, so the two can be compared."""
    return name if where == "" else f"{where}.{name}"


def _walk(value: object, path: str, scan: _Scan, found: dict[str, Position]) -> None:
    scan.skip_whitespace()
    if isinstance(value, dict):
        scan.take("{")
        for number, key in enumerate(value):
            if number:
                scan.take(",")
            scan.skip_whitespace()
            under = join(path, str(key))
            found[under] = scan.here()
            scan.skip_string()
            scan.take(":")
            _walk(value[key], under, scan, found)
        scan.take("}")
    elif isinstance(value, list):
        scan.take("[")
        for number, member in enumerate(value):
            if number:
                scan.take(",")
            scan.skip_whitespace()
            under = f"{path}[{number}]"
            found[under] = scan.here()
            _walk(member, under, scan, found)
        scan.take("]")
    elif isinstance(value, str):
        scan.skip_string()
    else:
        scan.skip_literal()


def positions(value: object, text: str) -> dict[str, Position]:
    """Where every part of `value` sits in `text`, by the path that names it.

    `value` is what the loader made of `text`. Both are taken rather than the
    text alone, because the walk follows the parsed data and because handing it
    a mismatched pair is the only way to reach the refusal that proves the two
    are held in step.
    """
    scan = _Scan(text)
    scan.skip_whitespace()
    found: dict[str, Position] = {"": scan.here()}
    _walk(value, "", scan, found)
    scan.skip_whitespace()
    if not scan.done():
        raise Desynchronised(
            f"the value ended at {scan.here()} and the text did not, so the two "
            "did not come from each other"
        )
    return found


def of(text: str) -> dict[str, Position]:
    """The index for text, whether or not the loader could read all of it.

    Where the loader refuses the bytes there is nothing to walk, and the index
    holds one entry: the whole document, at the place the loader stopped. That
    is not a claim that the document is fine. It is what makes a refusal about
    bytes that are not a document point at a line like every other refusal
    does, instead of at the beginning of the file.
    """
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as malformed:
        return {"": Position(line=malformed.lineno, column=malformed.colno)}
    return positions(loaded, text)


def nearest(index: dict[str, Position], path: str) -> Position:
    """The position for a path, or for the closest part of the document above it.

    A refusal about something that is not in the document, a required key it
    does not carry, has no position of its own. Pointing at the mapping that
    should have carried it is the nearest true thing, and it is where the cursor
    belongs anyway.
    """
    at = path
    while at not in index:
        cut = max(at.rfind("."), at.rfind("["))
        if cut < 0:
            return index.get("", Position(line=1, column=1))
        at = at[:cut]
    return index[at]
