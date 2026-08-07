# 0004. An action is read as a document and never executed

Ordered by issue #4.

## Question

In what form does a proposed action reach this pipeline, may that form contain
anything the pipeline runs, and by what route does it grow when somebody needs a
term it cannot express?

## Answer

An action reaches the pipeline as a document, and no part of that document is
ever executed.

The format family is plain data serialised as text. A loader reads it into
strings, numbers, lists and mappings and constructs nothing else, so no tag, no
directive and no field in an input document can name a type, call a function or
import a module. Whether the bytes on disk are one plain data syntax or another
is a smaller question and belongs to the schema in issue #24. What this record
fixes is that the family has no execution semantics at all, rather than having
them and being asked not to use them.

The pipeline does not evaluate a string from the document as an expression. A
Lagrangian term is a structure in the document with a named head and named
arguments, which the parser maps onto the internal representation of record
0005, and a term the schema has no head for is refused with that head named. It
is not passed to an expression parser to see what happens.

The schema grows by a change to the schema, never by a document. A term nobody
can express today is added by opening an issue that names the term and the
theory it comes from, landing a schema version that carries it with a fixture
document that uses it, and giving the admissibility gate of issue #26 its
matching case, so a widened input surface and a widened refusal surface move in
the same change. A document declares the schema version it is written against,
which is what makes an old document readable after the schema has moved.

## Reasons

A gate can decide a document and cannot decide a program. Admissibility is the
whole of milestone 3, and the moment the input is executable the question of
which class an input falls into stops having an answer that can be computed
before running it. Record 0003 draws a boundary between covered and refused
families, and that boundary is only checkable because what is being classified
sits still while it is read.

A document hashes. Record 0007 requires a run to record the hash of its input,
and that requirement means something only if the input is a fixed sequence of
bytes whose meaning does not depend on what the machine did while reading it. A
program that generates its own action produces a different thing to hash than
the thing that determined the answer.

A document from a stranger is data. Running a stranger's file on an operator's
machine is a different security posture, with a different threat model and
different obligations, and this board has no reason to take it on to save a
schema extension. The document parser is already the surface that eats a file
somebody else wrote, which is why issue #18 puts static analysis on it, and that
is a much smaller surface than an interpreter.

Refusing a term the schema has no head for, rather than handing the text to an
expression parser, is the same argument one level down. An expression parser is
a small interpreter, and a term it silently accepts as something other than what
the author meant is the exact failure this board exists to remove: the operator
writes a term, the pipeline reads a different one, and the answer looks
reasonable.

The cost is expressiveness, and it is deliberate. Somebody who wants a term the
schema cannot express writes an issue instead of a function, and waits. That is
slower for them and it is what makes the covered class of record 0003 mean
something, because a class anybody can widen from an input file is not a class.

## Ruled out

Executing any part of an input document. A format whose loader can construct
objects, call constructors or import modules, including the tagged forms of
otherwise plain data syntaxes. A field whose value is source code in any
language. An expression string evaluated at load. A plugin path, an import hook
or any other route by which a document names code to run. Ignoring an
unrecognised key or an unrecognised term head, which is issue #24's refusal and
is named here because a silent drop is how an executable input would be
smuggled back in. Widening the schema in a change that does not also say what
the widened surface refuses.

## Reopened when

A theory inside the covered class of record 0003 is found to need a term that
cannot be expressed as data at any schema version. The argument then is about
whether that theory belongs in the covered class, and not about whether to run
the input.
