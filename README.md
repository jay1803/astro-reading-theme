# Agent repository template

A minimal repository entrypoint for coding agents, with optional project rules
and safe template updates. Designed to work with the Develop and DevOps Skills in
[jay1803/skills](https://github.com/jay1803/skills).

## Start a new repository

Use GitHub's **Use this template** button, or create a private repository with:

```bash
gh repo create OWNER/PROJECT --private --template jay1803/agent-repo-template
```

Only root `AGENTS.md` is active guidance by default; it is the sole rule index. The
`.template/` directory contains tooling and inactive examples; it does not select
a language, framework, branch model, merge permission, or deployment provider.
Replace this README with the project's own overview after initialization.

Ask an agent with the `repo-initialize` Skill to tailor the repository. That
Skill is delivered by the DevOps plugin (`devops:repo-initialize`). Install a
version containing it through the Skills repository marketplace. The CLI below works without
that Skill. This template is private, so fetching it requires GitHub access.

## Initialize or update an existing repository

Use a separate, reviewed checkout of this template at an immutable commit. The
updater checks its inputs against that commit. Inspect `.template/manage.py`
and the selected modules before running downloaded code. No dependencies beyond
Git and Python 3.9+ are required.

From that template checkout:

```bash
# Preview the core files; TARGET is an existing repository's physical path.
python3 .template/manage.py --target /path/to/project

# Apply after examining the plan and relevant source files.
python3 .template/manage.py --target /path/to/project --apply

# Select optional modules only when their content matches the project decision.
python3 .template/manage.py --target /path/to/project --modules coding validation
python3 .template/manage.py --target /path/to/project --modules coding validation --apply
```

The updater never creates branches, commits, pushes, merges, deploys, installs
Skills, or changes GitHub settings. Follow the target repository's existing
instructions and authorized delivery workflow for those actions. It writes only
the core guidance, selected module destinations, and `.agents/template-state.json`.
It does not copy template tooling or this README into an existing project.

A repository created with GitHub's template button has no update ledger yet.
Run the same initialization command from the reviewed source checkout to adopt
identical files. GitHub template generation does not subscribe the project to
future changes.

## Optional modules

| Module | Destination | Meaning when adopted |
| --- | --- | --- |
| `development` | `.agents/policies/development.md` | Split `develop` / `main` workflow; authorized Agent squash merge into develop; no platform auto-merge |
| `coding` | `.agents/policies/coding.md` | Resolve style and architecture from project evidence |
| `validation` | `.agents/policies/validation.md` | Resolve real checks and report truthful results |
| `skills` | `.agents/policies/skills.md` | Local Skill ownership and caller-aware maintenance |
| `release` | `.agents/policies/release.yaml` | Existing `release-policy/v1`, human-merged develop to main |
| `release-runbook` | `.agents/runbooks/release.md` | Global release handoff and project-specific procedure location |

Examples under `.template/modules/` are inactive until adopted. Do not enable
`development` or `release` merely because files are available. Check real
branches and owner intent first. Customize adopted files to the project; the
updater preserves those customizations. Delete unwanted optional files and
remove any project-authored links that require them. The ledger preserves that
deletion on future updates. Do not delete the ledger to force an upgrade.

Deployment has no generic runnable module. Use DevOps' `deploy-skill-creator`
to build `.agents/skills/deploy/SKILL.md` from actual project/provider facts,
implementing `release-deploy/v1`. Existing deploy Skills and SOPs remain canonical.

## Update behavior

Updates are explicit runs, never automatic background writes. The default
command is read-only. Each file has a source hash and immutable source revision
in the ledger; it records only template-owned content, without local paths or
credentials. `AGENTS.md` tracks only its marked block, preserving everything
outside it, including existing project instructions.

| Situation | Result |
| --- | --- |
| Missing core or newly selected module | Create |
| Existing AGENTS.md without markers | Append a small discovery block |
| File already equals the selected source | Adopt or leave unchanged |
| Untouched managed content, upstream changed | Update, except policies |
| User modified a managed file/block | Preserve; agent compares and integrates deliberately |
| User deleted a managed file/block | Preserve deletion |
| Existing unrelated file at destination | Preserve; agent reconciles without replacement |
| Upstream changed a managed policy | Require policy review; never replace automatically |
| Upstream removed a file | Preserve it and report retirement |
| Invalid state/manifest, symlink, or changed source | Error before writes |

Exit codes: `0` clean plan/apply, `2` preserved content or policy review needs
attention (safe independent writes may have applied), `1` error. Review the
receipt and Git diff; exit `2` is not a complete migration. An interrupted or
I/O-failed apply can leave partial files; inspect the diff and rerun the preview.
There is no destructive force-update or automatic file deletion mode.
`retired-removed` only forgets the already-removed legacy index in the ledger.

For local customizations, compare the old `revision` in the ledger, the current
file, and the new source. Integrate only the relevant improvement. Do not rewrite
the ledger hash to make a customized policy look template-owned. The next run
will continue to preserve it unless it exactly matches the selected source.

## Naming and migration

The module destinations above are the naming convention, with root `AGENTS.md`
as the single index. Files remain optional. Use a different path only for an
explicitly documented repository exception. Policy is `.agents/policies/`, SOP
is `.agents/runbooks/`, and a project capability is `.agents/skills/`.

An update that adopts this layout preserves rule meaning while migrating paths.
For example, move `.agents/release.md` to `.agents/runbooks/release.md`, keep its
content and authority, and update inbound links plus relative links inside the
moved document. Check scripts and CI consumers as well as Markdown. Preserve
historical evidence; distinguish historical path mentions from live consumers.
If the destination exists, compare and reconcile it before any move; do not
replace it blindly. Keep a documented external-path dependency as an exception
until its consumer can migrate.

Version 1.1 removes the redundant index from the template. For a 1.0 adoption:

1. A root block that would change while a recorded legacy index still exists
   returns `index-migration-required`; the helper preserves the old root so
   custom rules remain reachable. Read `.agents/README.md` in full. Transfer unique constraints and useful links
   to root `AGENTS.md` or the applicable canonical policy/SOP, adjusting links
   relative to their new location. Keep customized root instructions intact.
2. Update live references and delete the redundant index only after confirming
   that its content has been preserved and no active consumer needs it. This is
   a deliberate migration by the Agent; the updater does not delete files.
3. Run the new updater preview/apply. A retained old index is `preserve-retired`.
   After the file is removed and the resulting root no longer mentions its old
   path, `retired-removed` removes only its obsolete ledger entry. Other managed
   files retain their real source baselines. Repeating the update must not
   resurrect the index; customized root instructions may report `preserve-local`.

Do not copy the optional release example over an existing release SOP. The
release authority YAML and the release runbook have different ownership. This
migration does not create branches or grant release/deployment authority.

## Develop compatibility and authority

`AGENTS.md` directly links adopted rules and SOPs. General Markdown policies
are read by the agent through this root entrypoint; no new global Develop YAML parser is implied.
`$release` independently reads `.agents/policies/release.yaml` from the live
remote default branch. A candidate policy cannot authorize its own merge.
Permission is constrained by repository policy, the current request, and live
hosting checks/reviews. Missing optional guidance permits ordinary engineering
judgment; it does not grant external mutation authority.

Develop's [branch strategy](https://github.com/jay1803/skills/blob/6ddf750a934fec230b25bf48533f7525c72cb28e/plugins/develop/skills/dev/references/branch-strategy.md)
(SK-78) follows explicit repository policy before fallback defaults. An ordinary
issue PR may target `main` when the repository says so; its name alone does not
make it a production promotion. Human-only review and merge rules still apply.
Without an explicit policy, standalone issue PRs use `develop`; batches use a
temporary integration branch based on `develop`. The optional `development`
module deliberately selects its documented split-branch policy, so leave it
inactive for a main-only project unless adapted to that project's decisions.

Check the installed workflow before relying on this capability: older versions
may still classify every main-targeting PR as a release. Initialization does not
update consumer plugins. Production promotion remains a separate DevOps
`$release` operation governed by live repository policy and current authority;
`release-policy/v1` still describes distinct promotion source and target branches.

When tailoring guidance, keep document-reading triggers and validation specific
to the changed surface. Record the task's actual completion boundary and any
verified disposable local-test scope so an agent can continue authorized work
without repeated approval. Do not describe tests as disposable or production-free
without repository evidence. The template does not grant an unrequested merge,
publication, deployment, or plugin installation.

## Validate template changes

```bash
python3 -m unittest discover -s .template/tests -v
python3 .template/check.py
git diff --check
```

The focused tests cover previews, idempotence, existing instructions, local
changes/deletions, policy updates, bad state, unsafe paths, and stale writes.
The contract checker validates the release-policy example and module inventory.
