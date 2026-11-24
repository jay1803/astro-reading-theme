# Development policy

This optional module selects the split-branch workflow supported by Develop:
ordinary issue branches start from `develop`, and ordinary PRs target `develop`.
Production promotion from `develop` to `main` belongs to `$release` and its
repository release policy. Enabling this file does not create either branch.

Use a dedicated issue worktree when the shared checkout is dirty. Preserve
existing issue branch names; otherwise use the applicable Skill or repository
naming convention.

Development PRs require the applicable validation, review, and hosting gates.
An Agent may merge into `develop` only when the current request authorizes that
integration and the gates pass. Use squash merge. Enabling platform auto-merge
is not authorized by this module. Do not bypass branch protection.

A merge request targeting another integration branch requires adapting this
policy to the actual repository and checking the installed Skill's capability.
Do not rename or create branches merely to satisfy a template convention.
