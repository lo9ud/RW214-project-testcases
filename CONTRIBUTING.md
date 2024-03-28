# Contributing

Please create a new branch for your changes and make a pull request to the `main` branch.

## Requirements

The following python packages will be required to push testcases to the repository:

- `black`
- `isort`

To install these packages, run the following command:

```bash
pip install -r requirements.txt
```

This will install the required packages.

## Creating a Testcase

To create a template for a testcase, run `test.py create`

## Creating a Pull Request (PR)

A GitHub account is required to make a PR. If you do not have a GitHub account, you may create an issue using the template provided in the issue tracker.

To create a PR, please follow the steps below:

- On the GitHub page [lo9ud/RW214-project-testcases](https://github.com/lo9ud/RW214-project-testcases).
- Clone the repository to your local machine.
- Create a new branch for your changes from `dev`.
  - The branch name should be descriptive of the changes you are making in the format `dev-<testcase-name>`. i.e.) `dev-my-simple-testcase`.
  - Create a branch using the following command: `git checkout -b dev-<testcase-name> dev`.
- Make your changes.
- Commit your changes to this branch.
- On the GitHub page open you brnach and click on `Contribute` -> `Pull Request` at the top right.
- Fill in the PR template and submit the PR.
- The PR will be reviewed and merged if it meets the requirements.
- If the PR is accepted, the changes will be merged into the main repository, and you may delete your forked repository.
- If the PR is not accepted, you may make the necessary changes and resubmit the PR.

Do not submit too many PR's, as this will make it difficult to review them. If you have multiple testcases to submit, please include them in a single PR.
