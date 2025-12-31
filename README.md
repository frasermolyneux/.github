# Engineering Estate (.github)

This repository is the home for organization-wide visibility: which repositories we manage, their route-to-production pipelines, and how workloads connect.

## Quick Links
- [Route to Production](docs/estate/route-to-production.md) — live badges for the primary release pipelines across the tenant.
- [Workload Catalog](docs/estate/workloads.md) — source-of-truth map from `platform-workloads` JSON to repositories and environments.
- [Pipeline Badges](docs/estate/pipelines.md) — consolidated release and CI badges per workload.

## What This Aims to Solve
- One place to see pipeline breakage without opening every repository.
- A structured, navigable view of workloads and their dependencies.
- A foundation for automation (scheduled sync + issue creation assigned to the Copilot coding agent when drift appears).

## Near-Term Actions
1. Add an `estate-sync` GitHub Action (scheduled + manual trigger) that reads `platform-workloads` metadata, queries GitHub and Azure DevOps statuses, and regenerates the Markdown in `docs/estate/`.
2. Publish the generated content via GitHub Pages (main branch /docs) for a richer dashboard while keeping Markdown as the source.
3. Wire the sync workflow to open/refresh an "Estate sync" issue when changes are detected and assign it to the Copilot coding agent for follow-up updates.