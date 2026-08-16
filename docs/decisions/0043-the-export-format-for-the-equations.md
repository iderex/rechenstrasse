# 0043. The export format for the equations, and what stays out

Ordered by issue #43.

## Question

The perturbation equations are the output somebody feeds to a numerical code.
What shape do they leave this pipeline in, and what does this board refuse to do
with them?

## Answer

One JSON document per run. Keys sorted, no insignificant whitespace, so that two
runs of the same input produce the same bytes and the replay requirement in
`0007` holds over the export as well as over everything else.

The document carries six things:

The equations, as the expression structure the pipeline works in and not as
a string in some computer algebra dialect. A string obliges the consumer to
carry a parser for whichever dialect was picked and throws away the index
structure on the way out.

The variables, each with its definition, so that a symbol in an equation can be
resolved without reading this repository's source.

The gauge, named explicitly. Never implied, and never carried only in the file
name.

The conventions the equations are written in. The conventions themselves are
fixed elsewhere, and the export names which ones were in force, so a reader
translating into their own does not have to guess.

The background quantities the equations refer to, so the export stands on its
own instead of pointing back at a run the reader does not have.

The provenance block from `0007`: the hash of the input document, the version of
the pipeline, the versions of the libraries that did the algebra, which
canonicalisation implementation was behind the seam, and the command that was
run.

Machine readable first, rendered second. A typeset form may be emitted, and it
is derived from this document every time. It is never the source, never edited
by hand, and never read back in.

Three things stay out of the first version:

Coupling this board to a numerical Boltzmann solver, because that is an
integration against somebody else's interface with its own validation burden,
and it would make this board's correctness depend on a moving target it does not
control.

Integrating anything. The moment this pipeline evolves equations it acquires a
numerical accuracy story, a step size argument and a convergence test, none of
which is what this board is short of.

Comparing against data. That needs a likelihood, a data set with its own
systematics, and a statistics argument, and each of those is a project.

The export format is what keeps all three doors open, and this record says so
instead of leaving the omission to be read as an oversight.

## Reasons

JSON over YAML, because the requirement that two runs agree byte for byte
is easier to hold in a format with fewer ways to write the same value, and
because the consumer is a numerical code, not a person editing the file.
The cost is that the raw document is unpleasant to read, and the rendered form
is what pays it.

The expression structure over a rendered string, because the structure is
what a consumer can act on. Anybody who wants the string can generate it from
the structure, and nobody can go the other way without a parser.

Six required contents instead of the equations alone, because an equation
without its gauge, its conventions and its variable definitions is not wrong so
much as unusable, and the missing parts get filled in by assumption on the
receiving end.

The three exclusions are stated as decisions and not as work not yet done,
because an omission that is not argued reads as a gap somebody should close.

## Ruled out

A typeset form maintained beside the data. An export that names no gauge. An
export whose equations are strings. An export without the provenance block. Any
of the three excluded pieces of work arriving without a record superseding this
one.

## Reopened when

A consumer this board cares about cannot read the format, or the export is found
to need something the six contents cannot carry.
