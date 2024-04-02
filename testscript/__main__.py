import os
import pathlib
import sys

import args
import main

if __name__ == "__main__":
    match pathlib.Path.cwd().name:
        case "RW214-project-testcases":
            main.main(*args.get_args(sys.argv[1:]))
        case "testscript" | "testcases":
            os.chdir("..")
            main.main(*args.get_args(sys.argv[1:]))
        case _:
            print("Please run this script from the 'RW214-project-testcases' root")
            sys.exit(1)
