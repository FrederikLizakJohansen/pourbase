# Publishing pourbase on PyPI

The package version is defined in `src/pourbase/__init__.py`. The current version,
`0.1.0`, is the initial preprint release; the bundled dataset has its own version, `1.0.0`.

For the first release, configure a [pending trusted publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) in the PyPI account:

- PyPI project: `pourbase`
- GitHub owner: `FrederikLizakJohansen`
- Repository: `pourbase`
- Workflow filename: `release.yml`
- Environment: `pypi`

A pending publisher does not reserve the project name. Configure the GitHub `pypi`
environment and its protection settings as appropriate for the repository.

Before releasing, check the version, changelog, citation, CI results and built distributions.
Publish a GitHub release with a tag matching the package version, such as `v0.1.0`.
The release workflow builds the tagged source, checks its distributions and publishes them
using the trusted publisher.
Check the workflow and the resulting PyPI project after publication.

To install this release:

```bash
python -m pip install 'pourbase==0.1.0'
python -m pip install 'pourbase[gui]==0.1.0'
```

For a later release, update the package version and release notes first; use the corresponding
tag. Once a version is published on PyPI its files cannot be replaced with new files of the
same name and version.
