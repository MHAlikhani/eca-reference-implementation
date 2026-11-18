# Toolchain currency review

**Checked:** 18 November 2026  
**Local execution:** offline authoring environment; no package-index connectivity during the final review

## Current release information checked

| Component | Local execution baseline | Current upstream release information seen on 18 Nov 2026 | Decision |
|---|---|---|---|
| Python | 3.13.5 | Python 3.15.2 was listed as the latest feature release; 3.14.10 and 3.13.18 were also listed | Keep `requires-python >=3.11`; add a CI matrix for 3.11–3.15. Local run is not a test on 3.15. |
| jsonschema | 4.26.0 | PyPI project page showed 4.26.0 as latest release | Keep 4.26.0 runtime pin. |
| pytest | 9.0.2 | PyPI/doc changelog lists 9.2.0, released 27 Oct 2026 | Set the fresh-install test extra to 9.2.0; local 102-test result remains on 9.0.2. |
| coverage.py | 7.13.3 | Current documentation identifies 7.16.1, released 13 Sep 2026 | Set the fresh-install test extra to 7.16.1; local 82% report remains on 7.13.3. |
| TLA+ Tools | Not installed | v1.8.0 is listed as a pre-release; v1.7.4 is the preceding stable release | Pin stable v1.7.4 by the upstream-published checksum; SANY/TLC pending. |
| Java | OpenJDK 21.0.12 | Official TLA+ usage guide requires Java 11+ | Local Java satisfies the documented minimum. |

## Source records

- Python release index: https://www.python.org/doc/versions/ and https://www.python.org/downloads/
- jsonschema on PyPI: https://pypi.org/project/jsonschema/
- pytest on PyPI: https://pypi.org/project/pytest/ and https://pytest.org/en/stable/changelog.html
- coverage.py documentation: https://coverage.readthedocs.io/en/latest/
- TLA+ releases: https://github.com/tlaplus/tlaplus/releases
- TLA+ CLI guide: https://github.com/tlaplus/tlaplus/blob/master/USE.md

## Reproducibility distinction

`requirements-lock.txt` is retained as the exact environment snapshot used for the local 102-test / 82%-coverage run. `pyproject.toml` and `requirements-current.txt` target the newer test-tool versions identified above for fresh installs. The fresh pins could not be installed or exercised locally because package-index DNS/network access failed. The GitHub Actions workflow is configured to test the current pins across Python 3.11–3.15 and to run the pinned TLA+ tools, but no CI run is claimed until the workflow actually executes in a repository.

Therefore, the local Python result is reproducible against the retained tested lock snapshot; compatibility with current pytest/coverage and Python 3.14/3.15 remains a CI verification gate. Do not report this currency review as proof that those newer environments have already passed.
