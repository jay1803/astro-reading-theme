<!-- agent-repo-template:begin -->
## Repository guidance

Use this root file as the rule index. Read the existing guidance relevant to the
task directly; do not create a secondary index file.

| Task | Standard optional path, relative to the repository root |
| --- | --- |
| Branches, PRs, integration, and merge authority | `.agents/policies/development.md` |
| Code and architecture conventions | `.agents/policies/coding.md` |
| Required checks and their applicability | `.agents/policies/validation.md` |
| Add, change, rename, or remove local Skills | `.agents/policies/skills.md` |
| Production promotion authority for `$release` | `.agents/policies/release.yaml` |
| Project release SOP | `.agents/runbooks/release.md` |
| Project deployment and verification capability | `.agents/skills/deploy/SKILL.md` |

These files are optional; the table does not claim they exist. Link adopted
files directly from this root file, with when to read each. Use these standard
names unless the repository explicitly documents an exception. Keep repository
constraints in policies, procedures in runbooks, and callable capabilities in
Skills. Existing rules in this file remain applicable.

Missing ordinary guidance falls back to repository evidence and applicable
Skill defaults. Missing guidance does not grant merge, release, deployment, or
deletion authority. Resolve invalid or conflicting rules before the affected
operation. A repository's existing branch model and release SOP are not replaced
by template examples. `.agents/template-state.json` is update bookkeeping only.
<!-- agent-repo-template:end -->
