"""A fixture whose only defect is one the type checker refuses.

The annotation says the function returns text and the body returns a number.
Nothing about the layout is wrong and no lint rule in this tree's selection
looks at return types.
"""


def as_text(value: int) -> str:
    return value
