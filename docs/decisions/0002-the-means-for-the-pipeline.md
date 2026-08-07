# 0002. The means for the pipeline

Ordered by issue #2.

## Question

What is this pipeline made of, and why does that fit the rules this repository
holds itself to rather than the habits of whatever was built last?

## Answer

Python for the pipeline layer, with SymPy as the computer algebra system in the
same process, and one versioned boundary at canonicalisation so the operation
that is expected to be hot can be replaced by a compiled core without changing
anything above it. That boundary is the seam decided in record 0005, and this
record adds nothing to its shape.

The four questions the choice was checked against, answered here rather than
left implied.

Can the means carry a property a machine refuses, a proof that runs, and a claim
that cites the command behind it. It can. A refusal is a value returned by a
named function and an exit status distinct from an internal error, which is
issue #28. A proof is a test the runner executes, and the harness in issue #14
is where the first one lands. A claim carries a command because the commands are
`python -m rechenstrasse` and the test runner, both of which a reader can run on
a clone. None of the three needs anything the language does not already have.

Is anything outside this repository forcing a different means, and is that force
real and held to its smallest surface. One force is real. Canonicalisation under
index symmetry is the operation the indexwerk core exists to do fast, and that
core is not Python. The force is held to the single operation on the seam in
record 0005, so it reaches one function signature and no stage above it. No
other force was found. The published corpus is numbers and prose, the theory
sources are papers, and neither of those constrains what reads them.

Does the means add a language, a runtime or a dependency the tree does not
already carry, and is that cost paid knowingly. The tree carries no language at
all today, so the whole cost is new and is paid once here. It is one runtime and
one large dependency. SymPy is a substantial body of code to trust, it is slower
than the alternatives at the tensor work this pipeline does most of, and its
version is a thing a result depends on, which is why record 0007 already
requires the algebra library versions in the provenance of a run rather than
only the pipeline version.

Would the work be testable by the harness that already exists, or does it need a
parallel apparatus nobody maintains. There is no harness in the tree yet, so the
honest form of the question is whether the means lets one harness cover
everything. It does. The default suite and the `native-or-long` suite of record
0009 are the same runner with different markers, rather than two tools, and the
second harness exists because of what the work needs from the machine rather
than because the means could not reach it.

Speed is a property of the seam and not of the tree, and the number that decides
whether that was true is the benchmark in issue #66.

## Reasons

The audience writes Python. A pipeline whose output goes into a paper is checked
by somebody reading the code that produced it, and a means the reader has to
learn first is a means that does not get checked. That argument is weak on its
own and is not the whole of this one, but it is not nothing on a board whose
stated purpose is to replace private notebooks with something other people can
inspect.

SymPy in the same process rather than a subprocess to a general system, because
the internal representation of record 0005 crosses stage boundaries dozens of
times per run and a serialisation boundary at each one is both slow and a place
where a term can be lost in translation. The cost is that the algebra library
and the pipeline share a runtime and a failure mode.

Julia with Symbolics.jl was rejected on the tensor parts rather than on speed.
It is faster on paper, and the ready pieces for abstract index work are thinner,
which means writing the parts that already exist elsewhere before writing the
pipeline. It also adds a runtime the audience mostly does not have, against a
speed argument that record 0005 has already localised to one operation.

A compiled language with no general computer algebra system underneath was
rejected because it means building one first. That is a larger project than this
one and it is the project indexwerk already is for the part that matters.

A proprietary system was rejected because it is the thing this board was opened
to replace. A result that can only be reproduced by somebody holding a license
is not reproducible in the sense record 0007 requires.

The interpreter lock is accepted rather than argued away. Nothing in the covered
class needs threads to be correct, and the parallelism worth having is over
documents, which is separate processes.

## Ruled out

A second computer algebra system alongside SymPy. A stage above the seam
importing from whatever implements canonicalisation, which record 0005 already
forbids and which is the shape this means makes easiest to do by accident.
Reaching for a compiled core anywhere except behind that seam. A dependency on a
system nobody can install without a license. Adding a second language to the
tree without a record superseding this one, which is separate from the forced
surfaces this record names, since those are held to an interface rather than
being a language the tree carries.

## Reopened when

The benchmark in issue #66 reports that the time is spread across the Python
layer rather than concentrated in canonicalisation, which would mean the seam
cannot buy back what the means costs, or SymPy stops being able to express
something in the covered class of record 0003 at a version this repository can
still pin.
