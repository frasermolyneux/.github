# Workload Catalog

This catalog is sourced from `platform-workloads/terraform/workloads/**` (excluding `examples/`). Each workload file defines a set of environments, repositories, and optional integrations (GitHub, Azure DevOps, Terraform state, RBAC).

## Categories (from repository layout)
- dev-platform
- platform
- portal
- geo-location
- xtremeidiots
- molyneux-me
- misc

## What we can extract automatically
- **Repository list**: every workload includes a `github` block that provides the repo name and topics.
- **Environments**: environment names, subscription aliases, OIDC connections (`connect_to_github`, `connect_to_devops`), Terraform state settings, and deploy-script identities.
- **RBAC**: role assignments and optional RBAC administrator scopes.
- **Cross-workload access**: `requires_terraform_state_access` lists state-sharing dependencies.

## Proposed generated output
- A table per category showing workload → environments → linked pipelines (GitHub/Azure DevOps).
- A dependency matrix that shows `requires_terraform_state_access` and any `workload:` or `workload-rg:` scope references.
- A “missing pipeline” list for repos without a `release-to-production` workflow.

## Quick queries (manual for now)
- List workload files: `ls platform-workloads/terraform/workloads/*/*.json`
- Inspect one workload: `cat platform-workloads/terraform/workloads/portal/portal-core.json`

Automation to render these tables is outlined in [automation](automation.md); once implemented, this page becomes generated content.
