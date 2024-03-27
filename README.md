# RW214-project-testcases
![Testcases Valid](https://github.com/lo9ud/RW214-project-testcases/actions/workflows/validate.yml/badge.svg?event=push)

Shared testcases for the 2024 RW214 project.

## Usage

```
% user@machine:~$ python test.py --help

usage: test.py [-h] [-v] [--version] {test,validate} ...

Test script

positional arguments:
  {test,validate}  Action
    test           Run tests
    validate       Validate testcases

options:
  -h, --help       show this help message and exit
  -v, --verbose    Increase output verbosity
  --version        show program's version number and exit

Example: python test.py /path/to/project
```

A testcase is a directory containing three files:

 - `input.[brf|txt]`: The input file.
 - `output.[brf|txt]`: The output file.
 - `manifest.json`: The manifest file.

The input and output files are the Braille and Afrikaans files. The manifest file contains metadata about the testcase. Read more about the manifest file [here](./MANIFEST.md).

To run the tests, run `test.py test`

```
% user@machine:~$ python .\testscript\test.py test path/to/proj/dir/
```

To validate the testcases, run `test.py validate`

```
% user@machine:~$ python .\testscript\test.py validate
```

To create a template for a testcase, run `test.py create`

```
% user@machine:~$ python .\testscript\test.py create 
```

### Example Testcase

```
my-simple-testcase/
├── input.brf
├── output.brf
└── manifest.json
```
mainfest.json:
```json 
{
    "$schema": "../schema.json",
    "name": "My Simple Testcase",
    "description": "This is a simple testcase",
    "level": "1.0",
    "direction": "afrikaans-to-braille",
    "tags": ["text"]
}
```

input.txt:
```
dit is warm
```

output.brf:
```
145-24-2345 24-234 2456-1-1235-134
```

## Contributing

It is strongly recommended to use the main branch for testing. THere are no guaranteees that other branches will be up to date or correct.


Please create a PR with your proposed testcases. The testcases will be reviewed and merged if they meet the requirements. You may also open an issue to discuss the testcase before creating a PR, or upload it there if you do not know how to create a PR.

If an issue is found with a testcase, please create an issue with the testcase name and a description of the issue, using the issue tracker.

Read more about contributing [here](./CONTRIBUTING.md).

# WARNING

DO NOT PUT ANYTHING HERE WHICH COULD BE CONSIDERED PLAGIARISM. YOU WILL BE PERMANENTLY PREVENTED FROM CONTRIBUTING, YOUR CHANGES WILL BE ROLLED BACK, AND YOU WILL BE REPORTED TO THE LECTURER!
