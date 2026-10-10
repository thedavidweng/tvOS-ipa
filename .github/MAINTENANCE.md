# Static listing maintenance

Listing generation runs only through workflow_dispatch. Pushes and releases do
not regenerate data. No scheduled lint or Dependabot feeds run in this frozen
repository. Routine workflow lint and its matcher have been retired after a
one-time jactionlint 2.0.2 default audit.

To regenerate manually, run `gh workflow run schedule.yml --ref main`. The job
uses Python 3.11, hash-locked dependencies, and GitHub contents:write permission
for its final commit. Checkout retains the token only because that step pushes.
The commit includes only apps.json, index.html, bundleId.csv and icons. Pushes
are not forced, and generation cannot trigger itself.

For local generation, create a Python 3.11 environment and install with
`python -m pip install --require-hashes -r requirements-generation.txt`.
Run `python generate_json.py --token "$GITHUB_TOKEN"` with a GitHub read token
that can list this public repository's releases. Review generated data before
committing. To update the lock, edit requirements-generation.in and run
`uv pip compile --python-version 3.11 --generate-hashes --output-file requirements-generation.txt requirements-generation.in`.

For a one-time workflow audit use jactionlint 2.0.2 with `--version`,
`--profile default --format summary` and `--diff`. Review proposed fixes.
