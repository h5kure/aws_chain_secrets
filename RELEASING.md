# Releasing

Publishing a GitHub Release runs [`.github/workflows/release.yml`](.github/workflows/release.yml),
which builds the package and uploads it to PyPI with trusted publishing. No API token is involved.

A version on PyPI cannot be replaced once uploaded, only yanked, so check everything before the last step.

## Steps

1. In `CHANGELOG.md`, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, add an empty `[Unreleased]` above it,
   and update the links at the bottom:

   ```markdown
   [Unreleased]: https://github.com/h5kure/aws_chain_secrets/compare/vX.Y.Z...HEAD
   [X.Y.Z]: https://github.com/h5kure/aws_chain_secrets/compare/vPREVIOUS...vX.Y.Z
   ```

2. Set `version` in `pyproject.toml` to `X.Y.Z`, then update the lockfile:

   ```bash
   uv lock
   ```

3. Run the checks that CI runs:

   ```bash
   uv run pytest
   uv run ruff check
   uv run ruff format --check
   uv run mypy
   ```

4. Commit as `[behavioral] release: X.Y.Z`, push, and wait for CI to pass on `main`.

5. Create an annotated tag and push it:

   ```bash
   git tag -a vX.Y.Z -m X.Y.Z
   git push origin vX.Y.Z
   ```

6. Publish the GitHub Release from the tag, with the CHANGELOG section as its notes:

   ```bash
   gh release create vX.Y.Z --verify-tag --title X.Y.Z --notes-file <notes.md>
   ```

7. The `build` job checks that the tag matches the project version, runs the tests, builds the package
   and runs `twine check`. The `publish` job then waits for approval in the `pypi` environment.
   Open the workflow run, choose **Review deployments**, and approve it to upload to PyPI.

8. Check the [PyPI page](https://pypi.org/project/aws_chain_secrets/) and install the new version in a clean environment.

## Repository settings

- PyPI trusts this repository's `release.yml` in the `pypi` environment.
  Renaming the workflow file or the environment requires updating the trusted publisher on PyPI.
- The `pypi` environment deploys only from `v*` tags and requires a reviewer to approve.
  Self-review is allowed, since the project has a single maintainer.
- If the project gains collaborators, consider a tag ruleset that restricts who can create,
  update or delete `v*` tags.
