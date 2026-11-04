# Console browser dependency security review — November 4, 2026

This review extends [PR #185](https://github.com/wmstipes/The-Foundry-Initiative/pull/185).
The original PR head, `4e1d9dc2ae87a7cd10362605c459bf7081d74dc3`, already
updated Vite to `8.3.5` and `source-map-js` to `1.2.2`. A fresh full npm audit
still reported three affected package entries: two moderate and one high.
Entries include direct packages and affected transitive packages; they are
not a count of distinct advisories.

## Additional fixes and ongoing coverage

| Package | Original PR | Reviewed version | Reason |
| --- | --- | --- | --- |
| Vitest | `5.0.2` | `5.0.5` | Includes the patched `@vitest/mocker` and its required dependency updates. |
| Happy DOM | `20.14.5` | `21.0.4` | Fixes the remaining sandbox, request, and cookie findings. |

Vitest stays on the existing `5.0` release line. Happy DOM's major-version
change is necessary: npm's proposed `20.14.6` update remains affected, and
the maintained ESM advisory lists `21.0.4` as the first patched version.
Direct dependencies remain exactly pinned. Production dependency records and
unchanged optional native-package platform selectors were preserved.

Required Validation now runs plain `npm audit` for the Console browser on
both Ubuntu and Windows. The former `--omit=dev --audit-level=high` command
excluded the build and test dependencies repaired here. The updated command
includes development dependencies and fails on any reported severity; the
README and testing guide use the same command.

Primary advisory references:

- [Vitest mocker traversal fix](https://github.com/vitest-dev/vitest/security/advisories/GHSA-xp26-3454-mjgp)
- [Happy DOM ESM sandbox fix](https://github.com/capricorn86/happy-dom/security/advisories/GHSA-834v-8h66-3h79)
- [Happy DOM request handling](https://github.com/advisories/GHSA-c8p4-j97h-3vg8)
- [Happy DOM cookie scope](https://github.com/advisories/GHSA-5fpq-26gf-qwcr)

## Local validation

Validated on November 4 using Node `24.22.1` and npm `11.9.0`, against the
final lockfile after preserving its unchanged platform metadata:

| Check | Observed result |
| --- | --- |
| `npm ci` | Passed; the lockfile hash was unchanged by installation. |
| Full lockfile audit, explicitly including development dependencies | Zero reported vulnerabilities at every severity. |
| `npm test` | All 21 existing browser tests passed across three files. |
| `npm run build` | TypeScript and Vite production build passed. |
| Console C2 and repository security policy suites | All 25 tests passed. |

No Console application source, Go dependency, test inventory, or release
version changed. Native candidate identity and Windows behavior still require
the full hosted checks on the final committed PR tree.

## PR dependency and release boundary

Required Validation also runs Workbench's full audit on every PR targeting
`main`. PR #185 therefore incorporates the corrected
[Workbench PR #186](https://github.com/wmstipes/The-Foundry-Initiative/pull/186)
as a prerequisite, while both PRs continue to target `main`.
Merge #186 first, then #185. If #186 is squash-merged or rebased onto main,
merge the updated main into #185 and repeat its required checks before merging.

These results establish source dependency and build compatibility. No image,
release, or deployment was published by this review, and no live-cluster
security assessment was performed. Existing deployed artifacts need their
normal reviewed release process to receive these source updates.
