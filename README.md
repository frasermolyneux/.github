# Engineering Estate and Community Health

This is the personal-account default community-health repository for
`frasermolyneux`. It owns inherited issue and pull-request templates for
repositories without local overrides, plus the engineering-estate dashboard
and its synchronization.

## Quick Links
- [Route to Production](docs/estate/route-to-production.md) — live badges for the primary release pipelines across the tenant.
- [Workload Catalog](docs/estate/workloads.md) — source-of-truth map from `platform-workloads` JSON to repositories and environments.
- [Pipeline Badges](docs/estate/pipelines.md) — consolidated release and CI badges per workload.
- [Estate Dashboard](docs/index.md) — GitHub Pages entry point and generated-page guidance.

## Maintained and Generated Content

- Maintain community-health templates under `.github/`.
- Maintain synchronization logic in `scripts/estate-sync/estate_sync.py` and
  `.github/workflows/estate-sync.yml`.
- Maintain the Pages entry point in `docs/index.md`.
- Treat `docs/estate/` as generated output. Its files identify the generator
  and must not be edited directly.

## What This Solves

- One place to see pipeline breakage without opening every repository.
- A structured, navigable view of workloads and their dependencies.
- Consistent default issue and pull-request templates where repositories do not
  provide their own.

The scheduled and manually dispatchable estate workflow reads
`platform-workloads` metadata, queries GitHub and Azure DevOps, regenerates
`docs/estate/`, and commits changed generated pages.