import os
import pathlib
import sys

import args
import main

if __name__ == "__main__":
    _args, parser = args.get_args(sys.argv[1:])
    attempts = 0
    cwd = pathlib.Path.cwd()
    while attempts < 5 and not (pathlib.Path.cwd().name == "RW214-project-testcases"):
        if os.path.exists("RW214-project-testcases"):
            os.chdir("RW214-project-testcases")
            break
        os.chdir("..")
        attempts += 1
    if attempts == 5:
        print("Could not find the 'RW214-project-testcases' directory.")
        sys.exit(1)
    elif attempts > 0:
        print("Moved up", attempts, "directories.")
        print("Please ensure you are running this program from the correct directory.")
        print("Initial working directory:", cwd)
        print("Current working directory:", pathlib.Path.cwd())
    try:
        main.main(_args, parser)
    except Exception as e:
        print("An unhandled error occurred:", e)
        if hasattr(_args, "debug") and _args.debug:
            raise
        sys.exit(1)
