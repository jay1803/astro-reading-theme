# Repository-local Skill maintenance

Keep project-specific capabilities in the established local Skill root. Prefer
`.agents/skills/` for a new root; update an existing root in place rather than
creating duplicate discovery locations.

Before adding a Skill, inspect existing Skills and callers for overlapping
ownership. Keep reusable workflow in shared Skills and project facts in this
repository. Adding a Skill does not install a plugin or grant external authority.

For a rename or removal, inspect AGENTS links, other Skills, scripts, CI, and
tracked agent configuration for consumers. Update in-scope callers and report
external consumers that cannot be verified. Preserve unrelated Skills and
user-owned changes. Removal must be within the requested scope.

Validate the Skill and its links using available structural checks and relevant
behavioral examples. Follow this repository's normal commit and review policy;
this module does not introduce a particular tracker, team, or publishing rule.
