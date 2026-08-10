"""Varying the action, and the surface terms that get dropped along the way.

The metric variation is issue #30 and is `metric.py`. The scalar field variation
is issue #31 and is not here. Issue #32 requires every dropped surface term to
be named rather than discarded silently: `metric._integrate_by_parts` computes
the two the curvature variation drops, and nothing carries them into an output
yet.
"""
