# 0056. The shape of federation

Ordered by issue #56.

## Question

If installations of this pipeline ever share results with each other, what is
the shape that sharing is allowed to have, and what is it never allowed to do?

## Answer

Nothing federates today. This record fixes the shape anyway, so that whoever
implements it inherits a decision instead of choosing a default while trying to
get a demonstration to work.

Five properties, and all five hold together.

Federation is off unless the operator turns it on for a run. Off is the state
of a fresh install, of a run where nothing was said, and of a run where the
option was mistyped.

It sends only what the operator names. Not everything in the working directory,
not everything from that run, and not whatever the receiving end asked for. The
named thing is the whole of what goes.

It prints exactly what would be sent, and waits for a decision. The print is the
content, not a description of it or a count of it, and the wait is a decision
rather than a countdown that proceeds on silence.

It never sends an input document as a side effect of sending a result. A result
carries the hash of its input under record 0007, and a hash is not the document.
Sending the document is its own act, named by the operator, with its own print
and its own wait.

It carries no telemetry. Not a version ping, not a usage counter, not an error
report, not a first-run beacon. There is no measurement of this pipeline's users
that this pipeline performs.

Turning it on is per run and never a stored setting. A setting somebody enabled
once and forgot is indistinguishable, from the operator's side, from a pipeline
that sends by default, and the promise in issue #54 is about what the machine
does rather than about what somebody remembers agreeing to.

These five are changed by a new record superseding this one, in the way record
0001 fixes for every record here, and not by editing this file. That is worth
saying in this record specifically: the pressure to soften one of these arrives
attached to a feature somebody wants, and a decision that can be adjusted in
place is not a decision anybody can rely on.

## Reasons

The default is being decided while it is free. Every property above costs
nothing today and would cost an argument, a migration and somebody's trust after
the first implementation shipped with the other answer. This is the cheapest
moment there will ever be.

What an operator puts into this pipeline is often unpublished work, and a
document can carry a name, an institution or an address next to the physics.
Issue #54 states that none of it leaves the host. Federation is the one feature
that would make that statement false, so its shape is where that statement is
either kept or quietly lost.

Printing the content rather than describing it, because a description is written
by whoever implemented the send, and the operator is being asked to consent to
the bytes rather than to somebody's summary of them. A count of fields is the
form this usually takes and it is the form that hides the field nobody expected.

Waiting for a decision rather than defaulting after a pause, because a timeout
that proceeds is a send that happened without an answer. Silence is not consent
anywhere else in this tree and it is not consent here.

Separating the result from the document, because the two have entirely different
sensitivity and the convenient implementation ships them together. A result is a
parameter expression. An input document is somebody's unpublished theory with
their name on it.

No telemetry, stated as its own property rather than left as an implication of
the others, because telemetry arrives as an exception to a rule about
federation. It is described as not really sending anything, or as anonymous, or
as necessary for knowing whether anybody uses the tool, and each of those is an
argument this record refuses in advance.

Per run rather than stored, because the alternative shifts the promise from the
machine to somebody's memory. It costs the operator a repeated decision, which
is the price of the decision meaning something.

## Ruled out

Federation on by default. A stored setting that turns it on for later runs. A
send of anything the operator did not name. A summary or a count in place of the
content. A prompt that proceeds on a timeout. An input document sent as a side
effect of sending a result. Telemetry in any form, including a version check, an
update check, a crash report and a usage counter. Adding a sixth property that
weakens one of these five. Editing this record to change any of them.

## Reopened when

A use arrives that these five make impossible rather than inconvenient. The
leading candidate is an unattended run, which cannot answer the wait in the
third property, and the argument there is about how an operator's consent is
expressed ahead of time rather than about whether it is required.
