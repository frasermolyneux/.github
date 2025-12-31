# Automation Plan

Goal: keep the estate overview in this repository current without manual edits.

## Data Sources
- **GitHub GraphQL API**: list repositories under `frasermolyneux`, fetch workflows and latest conclusions, emit status badges.
- **Azure DevOps REST API**: query build definitions and latest runs for pipelines that still live in DevOps.
- **platform-workloads Terraform**: parse `terraform/workloads/**` to understand workloads, environments, and cross-scope dependencies.

## Workflow Outline
1. **Scheduled GitHub Action** (e.g., daily):
   - Fetch repo list + workflow statuses (GraphQL).
   - Query Azure DevOps builds for known pipelines (use env secrets for PAT).
   - Parse platform-workloads JSON to map workloads → repos → environments → dependencies.
   - Generate Markdown (route-to-production, workload tables, dependency diagrams) into `estate/*.md`.
2. **Drift Detection**:
   - If generated files change, open/append to an issue titled "Estate sync" and assign to the Copilot coding agent for implementation.
   - Attach a diff snippet so the agent can update the static docs or fix missing pipelines.
3. **Manual trigger**:
   - Provide a workflow_dispatch input to refresh on demand.

## Implementation Notes
- Use a small TypeScript or Python script committed under `scripts/estate-sync` to produce Markdown and optional mermaid graphs.
- Store API tokens as environment-scoped secrets in this repo; restrict Azure DevOps PAT scope to Build.Read.
- Keep generation deterministic (stable ordering) so PR noise stays low.
- Consider publishing to GitHub Pages for a richer dashboard view while keeping the Markdown as the source of truth.
