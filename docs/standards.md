# Lightweight Engineering Standards

These standards describe the common approaches already used across the current
`frasermolyneux` repositories. Apply only the sections relevant to the
repository and change being worked on. Repository-specific guidance and
working implementations remain authoritative.

## Development

- Keep changes focused and follow the repository's existing structure, naming,
  configuration, and dependency-management patterns.
- Prefer shared workflows and composite actions from
  [`frasermolyneux/actions`](https://github.com/frasermolyneux/actions) when an
  existing action covers the required build, test, Terraform, deployment, or
  reporting behavior.
- Pin third-party actions to immutable commit SHAs. Use versioned releases for
  trusted first-party actions so upgrades are deliberate.
- Keep application code, infrastructure code, and environment configuration
  reviewable together when they form one deployable workload.
- Use repository-local Copilot instructions only for context that materially
  improves work in that repository. Do not add agents, prompts, setup
  workflows, or MCP configuration without a demonstrated need.

## Testing and quality

- Run the smallest relevant automated checks before opening or updating a pull
  request. Include the exact commands and outcomes in the pull request.
- Add or update tests for changed behavior. Use the test level that proves the
  change: unit tests for isolated logic, integration tests for boundaries, and
  browser or end-to-end tests for critical user flows.
- Keep pull-request validation read-only unless an explicit, reviewed action
  requests a development deployment.
- Build and test before publishing or deploying an application or package.
- Keep security and reliability findings visible. Suppress analyzer or scanner
  findings only through a reviewed repository mechanism with a specific
  reason.

Current examples include the reusable .NET, CMake, test-reporting, code-quality,
and Terraform actions in
[`frasermolyneux/actions`](https://github.com/frasermolyneux/actions), and the
unit and integration test suites in
[`frasermolyneux/portal-web`](https://github.com/frasermolyneux/portal-web) and
[`frasermolyneux/geo-location`](https://github.com/frasermolyneux/geo-location).

## Deployment and infrastructure

- Define cloud infrastructure as code using the repository's established
  Terraform or Bicep approach. Commit provider or tool version locks where the
  tool supports them.
- Review infrastructure plans before apply. Production changes should come
  from reviewed `main` content or an explicit protected manual workflow.
- Separate development and production configuration, state, credentials, and
  GitHub environments.
- Prefer GitHub OIDC and short-lived cloud credentials over stored deployment
  credentials.
- Give workflows the minimum permissions required for each job and use
  concurrency controls to prevent overlapping environment changes.
- Verify deployments with a health, information, version, or equivalent
  workload-specific check. Keep rollback or destroy paths explicit where the
  workload supports them.

The current estate uses these patterns in application repositories such as
[`frasermolyneux/portal-web`](https://github.com/frasermolyneux/portal-web) and
in infrastructure repositories catalogued by
[`frasermolyneux/platform-workloads`](https://github.com/frasermolyneux/platform-workloads).

## Security

- Never commit secrets, tokens, private keys, connection strings, or sensitive
  external data.
- Store runtime secrets in the platform's secret store and expose only the
  minimum required value to the minimum required environment or job.
- Use least-privilege identities, repository permissions, API permissions, and
  network access.
- Validate untrusted input at system boundaries and avoid logging credentials,
  tokens, or sensitive payloads.
- Keep dependencies and build actions current through reviewed automated
  updates where configured.
- Treat authentication, authorization, secret handling, workflow permissions,
  public exposure, and destructive infrastructure changes as explicit review
  concerns.
- Follow the repository's `SECURITY.md` process where present. Otherwise,
  report vulnerabilities privately to the repository owner rather than
  including exploit details in a public issue.

## Documentation

- Keep the root `README.md` focused on purpose, local development, validation,
  deployment entry points, and links to deeper documentation.
- Document non-obvious architecture, operational prerequisites, manual steps,
  and recovery procedures close to the owning implementation.
- Update documentation in the same change when behavior, configuration,
  interfaces, deployment, or operator actions change.
- Remove obsolete plans after the decision has been implemented or superseded;
  documentation should describe the current system rather than retain stale
  working notes.

## Observability and operations

- Provide a health or readiness signal appropriate to the workload.
- Use structured logs and include stable operational context without recording
  secrets or sensitive payloads.
- Record actionable failure information at external calls, background jobs,
  deployment boundaries, and other operationally significant transitions.
- Use the established Application Insights or OpenTelemetry integration when
  the workload already depends on it. Prefer shared libraries over bespoke
  telemetry plumbing.
- Add availability monitoring and alerts for production services where an
  operator can take a defined action.
- Use audit events for security-sensitive or administrative actions where the
  current implementation supports them.

The shared implementations are maintained in
[`frasermolyneux/observability-opentelemetry`](https://github.com/frasermolyneux/observability-opentelemetry)
and
[`frasermolyneux/observability-appinsights`](https://github.com/frasermolyneux/observability-appinsights).

## Applying these standards

For each change:

1. Read the target repository's instructions and relevant implementation.
2. Select only the standards that apply to the change.
3. Reuse an existing repository or shared-action pattern where practical.
4. Validate the behavior that changed.
5. Record validation, deployment impact, and security-sensitive changes in the
   pull request.

Do not introduce a tool, workflow, abstraction, or governance file solely to
claim compliance with this document.
