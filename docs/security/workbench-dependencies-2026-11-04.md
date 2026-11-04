# Workbench dependency security review — November 4, 2026

This review extends [PR #186](https://github.com/wmstipes/The-Foundry-Initiative/pull/186).
The original PR head, `8d31d5745d5a52498a6c18f56df58e99901e93a8`, already
updated Vite to `8.3.5` and `source-map-js` to `1.2.2`. A fresh full npm audit
still reported four affected package entries: three moderate and one high.
Entries include direct packages and affected transitive packages; they are
not a count of distinct advisories.

## Additional fixes

| Package | Original PR | Reviewed version | Reason |
| --- | --- | --- | --- |
| Vitest | `5.0.2` | `5.0.5` | Includes the patched `@vitest/mocker` and its required dependency updates. |
| Happy DOM | `20.14.5` | `21.0.4` | Fixes the remaining sandbox, request, and cookie findings. |
| `fast-uri` | `3.1.8` | `3.1.9` | Patches URI parsing findings within Ajv's existing supported dependency range. |

Vitest stays on the existing `5.0` release line. Happy DOM's major-version
change is necessary: npm's proposed `20.14.6` update remains affected, and
the maintained ESM advisory lists `21.0.4` as the first patched version.
The direct dependencies remain exactly pinned. `fast-uri` remains a transitive
dependency; no override or additional direct dependency was introduced.
Platform selectors on unchanged optional native packages were preserved.

Primary advisory references:

- [Vitest mocker traversal fix](https://github.com/vitest-dev/vitest/security/advisories/GHSA-xp26-3454-mjgp)
- [Happy DOM ESM sandbox fix](https://github.com/capricorn86/happy-dom/security/advisories/GHSA-834v-8h66-3h79)
- [Happy DOM request handling](https://github.com/advisories/GHSA-c8p4-j97h-3vg8)
- [Happy DOM cookie scope](https://github.com/advisories/GHSA-5fpq-26gf-qwcr)
- [fast-uri parsing fix](https://github.com/fastify/fast-uri/security/advisories/GHSA-w74x-v6f9-j3xg)

## Local validation

Validated on November 4 using Node `24.22.1` and npm `11.9.0`, after restoring
the final lockfile's unchanged platform metadata:

| Check | Observed result |
| --- | --- |
| `npm ci` | Passed; the committed lockfile contents were unchanged. |
| `npm audit` including development dependencies | Zero reported vulnerabilities at every severity. |
| `npm test` | All 92 existing tests passed across seven files. |
| `npm run build` | Passed; all 12 precompiled Kubernetes resource validators matched the checked-in output. |
| `npm run csp:check` | Passed; the production JavaScript contains no eval or Function-constructor usage. |

No application source, schema, generated validator, test inventory, or release
version changed. The production build still emits a bundle-size warning;
the build and CSP checks succeed.

Hosted Required Validation, dependency review, and the container workflows
remain merge prerequisites. These local results establish dependency and
build compatibility, not a live-cluster assessment. No image, release, or
deployment was published by this review. Existing deployed artifacts need
their normal reviewed release process to receive these source updates.
