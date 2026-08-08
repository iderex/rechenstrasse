"""Make the package runnable as `python -m rechenstrasse`."""

import sys

from rechenstrasse.cli import main

if __name__ == "__main__":
    sys.exit(main())
