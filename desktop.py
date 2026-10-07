# SPDX-License-Identifier: GPL-3.0-only
import sys
from app import main

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from package_smoke import run

        run(sys.argv[sys.argv.index("--self-test") + 1])
    else:
        for argument in ("--capture", "--overlay"):
            if argument not in sys.argv:
                sys.argv.append(argument)
        main()
