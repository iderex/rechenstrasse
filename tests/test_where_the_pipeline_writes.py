"""Where the pipeline writes, measured on a run rather than read off the source.

Issue #58. An operator who has to delete something needs to know what exists and
where, and the file nobody finds later is the one in a home directory. So the
question is asked of a run: point the interpreter at a home directory of this
suite's own, give it a working directory of its own, drive every stage this tree
has over every theory document in it, and compare both directories with what they
held before.

Reading the source instead would be the cheaper answer and a weaker one. It says
what this tree's own code does and nothing about what the algebra library under
it does, and a cache written by a dependency is a file in a home directory
exactly like one written here.

What the measurement covers today. The stages that exist, which is the reader,
the admissibility gate and the variation of the action with respect to the
metric. There is no command an operator runs, no output file and no cache of
canonical forms, so what is driven here is every stage rather than a run, and the
distinction is why the legs below say "stage" where the issue says "run".

What it does not cover, so that a green result is not read as more than it is.
Nothing here watches the repository tree, the interpreter's own cache
directories inside the environment, or the temporary directory a library may
reach for through a name this file does not redirect. It follows the two
locations issue #58 names and no others. It also cannot see a write a stage makes
and removes again inside one call, because it compares two states and not the
calls between them.

The second leg is a statement about the tree as it stands, and it is the one that
has to change rather than be deleted. The output file an operator asks for is
issue #59 and the run record that carries the provenance is issue #60. When
either lands, a stage writes into the working directory because the operator
asked it to, and that leg becomes a statement about the writes nobody asked for.
The first leg is the promise itself and survives both.

    uv run --frozen pytest -q tests/test_where_the_pipeline_writes.py
"""

import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from rechenstrasse.admissibility import admission
from rechenstrasse.document import reader
from rechenstrasse.variation import metric

ROOT = Path(__file__).resolve().parents[1]
THEORIES = ROOT / "theories"

# The names an interpreter and the libraries under it read to find a home, a
# cache, a configuration directory or a state directory. All of them are
# redirected together, because a guard that redirects the one this platform uses
# passes here and says nothing about the platform whose name it left alone.
HOME_VARIABLES = (
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "APPDATA",
    "LOCALAPPDATA",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
)


def theory_documents() -> list[Path]:
    """Every theory document in the tree, sorted."""
    return sorted(THEORIES.glob("*.json"))


def drive_every_stage() -> None:
    """Put every theory document through every stage this tree has.

    A refusal is a result and not a failure here, so a document the gate places
    outside the covered class is driven as far as it goes and no further. What
    this asserts is that something happened at all, because a loop over an empty
    directory writes no file either and would pass every leg below.
    """
    documents = theory_documents()
    assert documents, f"no theory document below {THEORIES}, which is not a pass"
    for document in documents:
        text = document.read_text(encoding="utf-8")
        admitted = admission.admit(text)
        if isinstance(admitted, admission.NotAdmitted):
            continue
        reader.emit(admitted.action)
        metric.derive(admitted)


def contents(root: Path) -> set[str]:
    """Every path below one directory, relative to it, with forward slashes."""
    return {held.relative_to(root).as_posix() for held in root.rglob("*")}


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home directory of this suite's own, with the interpreter pointed at it.

    The last two lines are the ones that make the legs mean anything. A
    redirection that did not take leaves the legs comparing a directory nothing
    would ever write to against itself, which passes for the wrong reason on
    every machine, so the fixture refuses to hand out a home the interpreter
    does not agree is one.
    """
    made = tmp_path / "home"
    made.mkdir()
    for name in HOME_VARIABLES:
        monkeypatch.setenv(name, str(made))
    assert Path.home() == made
    assert Path(os.path.expanduser("~")) == made
    return made


@pytest.fixture
def working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """A working directory of this suite's own, entered for the length of a test."""
    made = tmp_path / "working"
    made.mkdir()
    monkeypatch.chdir(made)
    assert Path.cwd() == made
    yield made


def test_no_stage_writes_under_a_home_directory(
    home: Path, working_directory: Path
) -> None:
    """The promise itself, and the half of it that survives the pipeline growing.

    A file an operator asked for goes where they asked for it. A file under a
    home directory was asked for by nobody, and it is the one that is still
    there after the working directory has been deleted.
    """
    before = contents(home)
    drive_every_stage()
    assert contents(home) - before == set()


def test_no_stage_writes_into_the_working_directory(
    home: Path, working_directory: Path
) -> None:
    """What the working directory holds after a run, which today is nothing.

    This is a measurement of the tree as it stands rather than the promise. When
    issue #59 gives an operator a command and issue #60 gives its output a
    provenance block, a stage writes here because it was asked to, and this leg
    becomes a statement about the files nobody asked for. It is written so that
    it reds on that day instead of being quietly true forever.
    """
    before = contents(working_directory)
    drive_every_stage()
    assert contents(working_directory) - before == set()


def a_cache_in_the_home_directory() -> None:
    """The one-character version of the mistake, planted where it would go.

    Not a stray temporary file, which nobody writes on purpose. A cache of
    canonical forms under a dot directory in the operator's home is the shape a
    stage would actually take, and record 0005 puts a seam in this pipeline that
    a later implementation could put one behind.
    """
    kept = Path.home() / ".rechenstrasse"
    kept.mkdir(exist_ok=True)
    (kept / "canonical-forms.json").write_text("{}", encoding="utf-8")


def a_dropped_file_in_the_working_directory() -> None:
    """The same mistake at the other allowed location."""
    Path("rechenstrasse-run.json").write_text("{}", encoding="utf-8")


@pytest.mark.parametrize(
    ("planted", "watched"),
    [
        (a_cache_in_the_home_directory, "home"),
        (a_dropped_file_in_the_working_directory, "working"),
    ],
    ids=["under a home directory", "in the working directory"],
)
def test_a_planted_write_is_caught(
    planted: Callable[[], None],
    watched: str,
    home: Path,
    working_directory: Path,
) -> None:
    """The proof that the two legs above bite, at both locations they watch.

    Deleting either leg has to red the suite for the reason it names, and a leg
    comparing two directory listings can fail to bite in a way that reads
    perfectly: a walk that never descends, a redirection the interpreter ignored,
    a comparison against the wrong root. So the write a stage would make is made
    here, through the same fixtures and the same comparison, and what is asserted
    is that it is seen.
    """
    root = home if watched == "home" else working_directory
    before = contents(root)
    drive_every_stage()
    planted()
    appeared = contents(root) - before
    assert appeared, f"the planted write left nothing visible below {root}"
