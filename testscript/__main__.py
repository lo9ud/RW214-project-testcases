import os
import pathlib
import sys

import args
import main

if __name__ == "__main__":
    _args, parser = args.get_args(sys.argv[1:])
    if pathlib.Path.cwd().name == "RW214-project-testcases":
        main.main(_args, parser)
    elif pathlib.Path.cwd().name in ["testscript", "testcases"]:
        os.chdir("..")
        main.main(*args.get_args(sys.argv[1:]))
    else:
        print("Please run this script from the 'RW214-project-testcases' root")
        sys.exit(1)
