# Release procedure

Use the installed global `$release` workflow. Resolve source-control promotion
and merge authority from `.agents/policies/release.yaml` on the live remote
default branch. This runbook does not override that policy.

Determine version sources, changelog requirements, tags, and publication order
from the project's existing release tooling and documentation. Record verified
project-specific steps here when available; no package manager, registry, or
release-trigger mechanism is selected by this module.

If release requires deployment, use the repository's deploy Skill with the exact
immutable revision. When deployment knowledge is missing, use
`$deploy-skill-creator` to capture real targets, commands, migration order,
verification, and rollback boundaries. Do not deploy while those facts remain
unknown. Projects without a deployment surface need no deploy Skill.

Report source integration, tag/publication, deployment, and runtime verification
as distinct outcomes, including any pending human action.
