"""A fixture whose only defect is one the linter refuses.

An import nothing uses. The formatter has no opinion about it and the type
checker has none either, which is what makes it a fixture for the `lint` check
and not for one of the other two.
"""

import os
