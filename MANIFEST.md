# Manifest Files

Manifest files are used to define the testcases that are used in the test suite.
Each manifest file is a JSON file that contains an array of testcases.
Each testcase is an object that contains the following fields:

- `name`: The name of the testcase.
- `description`: A description of the testcase.
- `level`: The level of the testcase.

The following is an example of a manifest file:

```json
{
    "$schema": "../schema.json",
    "name": "My Simple Testcase",
    "description": "This is a simple testcase",
    "level": "1.0",
}
```

This allows for easy validation of the testcases and ensures that the testcases are correctly formatted and contain all the necessary information.
