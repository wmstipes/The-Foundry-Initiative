# Dependency queue review — November 5, 2026

**Source baseline:** `main` at `70209de388a097b12f6140bf1fe577684b767907`,
after the Terraform/Terragrunt pilot and November 4 browser dependency repairs.

This review consolidates the remaining dependency proposals into one maintained
source baseline. The table records the selected changes; the linked pull
requests establish their eventual merge and closure state. Original proposals
are closed as superseded only after the replacement changes reach `main`.

## Queue decisions

| Original PR | Selected change | Reason |
| --- | --- | --- |
| [#165](https://github.com/wmstipes/The-Foundry-Initiative/pull/165) | Refresh the Console builder to Node **24.22.2**, retaining `node:24-alpine`. | Keep the documented Node 24 CI/build baseline. The proposed Node 26.10.0 image is older than current releases; a major baseline change is not needed for this cleanup. Node 26 is supported LTS, not rejected as unsupported. |
| [#177](https://github.com/wmstipes/The-Foundry-Initiative/pull/177) | `actions/upload-artifact` **7.0.2** and `actions/download-artifact` **8.0.2**. | Adopt the reviewed patch releases, retaining full commit-SHA pins. |
| [#178](https://github.com/wmstipes/The-Foundry-Initiative/pull/178) | `actions/setup-node` **7.1.0**. | Update the action while keeping the configured application runtime at Node 24. |
| [#179](https://github.com/wmstipes/The-Foundry-Initiative/pull/179) | Refresh the Console builder to Go **1.27.3**. | Include the additional security patch beyond the proposal's Go 1.27.2 image. |
| [#188](https://github.com/wmstipes/The-Foundry-Initiative/pull/188) | `httpx2` **2.16.0**. | The Python 3.11 minimum is compatible with the supported environments; Restaurant test-client behavior passes. |
| [#189](https://github.com/wmstipes/The-Foundry-Initiative/pull/189) | `setuptools` **84.2.1**. | Update the build declaration and all five explicit CI bootstrap pins together. |
| [#190](https://github.com/wmstipes/The-Foundry-Initiative/pull/190) | Refresh Service Pulse to Python **3.12.16**. | Include the newer security release beyond the proposal's Python 3.12.15 image. |
| [#192](https://github.com/wmstipes/The-Foundry-Initiative/pull/192) | `pytest` **9.2.0**. | Complete discovery passes without changing test source or inventory. |
| [#193](https://github.com/wmstipes/The-Foundry-Initiative/pull/193) | FastAPI **0.162.0**. | Existing tests and targeted JSON/default/validation checks preserve the Restaurant contract. |
| [#194](https://github.com/wmstipes/The-Foundry-Initiative/pull/194) | `k8s.io/api`, `k8s.io/apimachinery`, and `k8s.io/client-go` **0.37.2**, together. | Preserve exact, aligned Kubernetes module versions. The Go language minimum remains `1.27.0`. |
| [#195](https://github.com/wmstipes/The-Foundry-Initiative/pull/195) | Superseded by `setuptools` **84.2.1**. | The selected version includes the security fixes introduced in 84.1.0; the two original PRs change the same declaration. |

The older Required Validation failures for #179, #188, #189, #190, #192, #193,
and #194 came from the Workbench dependency audit and its aggregate gate. Their
relevant application or package checks passed at those historical heads. Those
results explain the old failures; fresh CI on the consolidated changes is the
acceptance gate.

## Pin and compatibility review

The GitHub Actions commits match the official release tags:

| Action | Version | Full commit SHA |
| --- | --- | --- |
| `actions/setup-node` | 7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `actions/upload-artifact` | 7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| `actions/download-artifact` | 8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |

All three replacement Docker Official Images indexes were retrieved and their
response bytes independently matched the pinned SHA-256 digests. Each includes
`linux/amd64` and `linux/arm64/v8`. Immutable upstream Dockerfiles confirm the
selected versions. Both Node child manifests and configuration blobs were also
hashed, and both configurations declare Node 24.22.2. This is content-hash and
source verification, not image signature verification or a vulnerability scan.

The Console builders remain on Alpine 3.24, and Service Pulse remains on Debian
trixie-slim. The final Console image is still `scratch`; Node is a build stage.
The Workbench Dockerfile is outside this change.

The `setuptools` declaration alone does not select the backend used by CI's
`--no-build-isolation` commands. This change therefore aligns the one bootstrap
in Required Validation and the two bootstraps each in ForgeOps CI and ForgeOps
release with `pyproject.toml` at 84.2.1. Wheel remains pinned at 0.48.0.

FastAPI's intermediate compatibility changes were reviewed against the
Restaurant app's JSON routes. Its tested dependency graph includes
`opentelemetry-api`, but no OpenTelemetry SDK or exporter; the dependency update
does not configure telemetry collection.

## Local validation

With Python **3.12.14** and the selected Python dependencies installed together:

- `pip check` passed.
- Complete repository discovery passed **327 tests and 473 subtests**.
- Two real ForgeOps wheels built with `setuptools` 84.2.1 passed the release
  validator and were byte-identical at 58,610 bytes. Both had SHA-256
  `316f778a977582dd30e4bcc870ef610c3002ee0533ffe0aa0a2110e2eafc7c52`.
- Targeted Restaurant checks passed for omitted optional fields, explicit null
  service/body, an absent body, minimum incident length, and the corresponding
  OpenAPI required-field and minimum-length declarations.
- All ten Console policy test functions passed with the three Kubernetes
  modules pinned together at 0.37.2. The `go.mod` and `go.sum` files match the
  reviewed PR #194 files.

Version-specific PyPI metadata reported no listed vulnerabilities for the four
selected Python package versions on November 5. This is a scoped metadata check,
not a complete transitive dependency audit. Hosted dependency review remains
required. No application source or test definitions changed.

Fresh hosted validation must cover Required Validation, CodeQL, ForgeOps
reproducible packaging and supported Python versions, Restaurant tests, and the
Console and Pulse native/multi-architecture container checks. Local Go runtime
or container execution is not claimed by this record. PR checks carry the
results for the final submitted commit.

## Publication and deployment effects

The existing Restaurant workflow automatically publishes
`wmstipes/signalforge-restaurant-api:latest` and a full commit-SHA tag after a
qualifying `main` push and successful required validation. Merging these
Restaurant requirements changes uses that established publication path. It does
not create a semantic-version release tag or deploy to Kubernetes.

A November 5 read-only check found that the `release` environment restricts
allowed refs but has no required-reviewer, wait-timer, or custom-protection rule.
It is therefore not a human approval gate. This resolves the previously
unverified setting in the [October security review](review-2026-10-01.md);
whether to add owner approval remains a separate settings decision. No workflow
triggers, release controls, environment settings, or permissions change here.

Console and Pulse image publication remain manual. Workbench publication
requires its version tag or a manual publishing dispatch. This cleanup does not
request any such dispatch, version-tag creation, or cluster deployment. Source
and build evidence does not establish current cluster health.

## Primary references

- [setup-node 7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0),
  [upload-artifact 7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2),
  [download-artifact 8.0.2](https://github.com/actions/download-artifact/releases/tag/v8.0.2)
- [Node 24.22.2 release](https://nodejs.org/en/blog/release/v24.22.2) and
  [supported release series](https://nodejs.org/en/about/previous-releases)
- [Go 1.27.3 release history](https://go.dev/doc/devel/release#go1.27.3)
- [Python 3.12.16 security release](https://www.python.org/downloads/release/python-31216/)
- Immutable official Dockerfiles:
  [Node](https://github.com/nodejs/docker-node/blob/e994dfe115899a82684caa7533380aa7d439aae1/24/alpine3.24/Dockerfile),
  [Go](https://github.com/docker-library/golang/blob/41d9b4da70324ae7b6461ac2cc401b06719ff57d/1.27/alpine3.24/Dockerfile),
  [Python](https://github.com/docker-library/python/blob/3d7e95597e56a415d9e4abc0f15877e005d2cb2e/3.12/slim-trixie/Dockerfile)
- [setuptools maintained history](https://setuptools.pypa.io/en/latest/history.html)
- [httpx2 2.16.0 changelog](https://github.com/pydantic/httpx2/blob/v2.16.0/src/httpx2/CHANGELOG.md)
- [pytest 9.2.0 release](https://github.com/pytest-dev/pytest/releases/tag/9.2.0)
- [FastAPI 0.162.0 release history](https://github.com/fastapi/fastapi/blob/0.162.0/docs/en/docs/release-notes.md)
- [Release environment settings](https://api.github.com/repos/wmstipes/The-Foundry-Initiative/environments/release)
- [Restaurant build/publication workflow](../../.github/workflows/restaurant-api-docker.yml)
