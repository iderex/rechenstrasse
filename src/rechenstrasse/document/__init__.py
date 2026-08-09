"""The action as a document, and the reader that turns it into the internal form.

Record 0004 fixes the input as plain data serialised as text, read by a loader
that constructs strings, numbers, lists and mappings and nothing else. The
schema is issue #24 and is in `schema.py`, which also decides that the syntax on
disk is JSON and says why. The reader that turns an accepted document into the
internal representation of record 0005 is issue #25 and is not here yet.
"""
