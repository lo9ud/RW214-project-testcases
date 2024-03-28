from pathlib import Path

import testcase

t = testcase.TestSet(
    [
        testcase.Testcase(
            Path("testcases/diacritic-check"),
        )
    ]
)

p = t.run(
    Path(
        r"C:\Users\adamd\OneDrive\Documents\Stellenbosch University\2024\Computer Science 214\Project\27168182-RW214-project"
    ),
    Path(
        r"C:\Users\adamd\OneDrive\Documents\Stellenbosch University\2024\Computer Science 214\Project\RW214-project-testcases\out"
    ),
)
p.wait()
print(p.returncode)
print(t.err)
print(t.out)
