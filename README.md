# RW214-project-testcases

Shared testcases for the 2024 RW214 project.

## Usage

A testcase is a directory containing three files:

 - `input.[brf|txt]`: The input file.
 - `output.[brf|txt]`: The output file.
 - `manifest.json`: The manifest file.

The input and output files are the Braille and Afrikaans files respectively. The manifest file contains metadata about the testcase. The manifest file is a simple json file with the following keys:

 - `name`: The name of the testcase.
 - `description`: A description of the testcase.
 - `direction`: The direction of the translation. Either `braille-to-afrikaans` or `afrikaans-to-braille`.
 - `level`: The level of contractions for the testcase
 - `tags`: A list of tags for the testcase.

### Currently allowed tags:
 
 - `text`: The testcase is a simple text translation.
 - `numbers`: The testcase contains numbers.
 - `punctuation`: The testcase contains punctuation.
 - `contractions`: The testcase contains contractions.
 - `long`: The testcase is long. (> 100 characters words)

Please ensure that testcases are correctly tagged

### Example

```
my-simple-testcase/
├── input.brf
├── output.brf
└── manifest.json
```
mainfest.json:
```json 
{
  "name": "My Simple Testcase",
  "description": "A simple testcase to test the translation.",
  "direction": "braille-to-afrikaans",
  "level": "1.1",
  "tags": ["text"]
}
```

input.txt:
```
Dit is warm
```

output.brf:
```
6-145-24-2345 24-234 2456-1-1235-134
```

## Contributing

Please create a PR with your proposed testcases. The testcases will be reviewed and merged if they meet the requirements. You may also open an issue to discuss the testcase before creating a PR, or upload it there if you do not know how to create a PR.

If an issue is found with a testcase, please create an issue with the testcase name and a description of the issue, using the 
