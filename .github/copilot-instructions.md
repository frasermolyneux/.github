# Copilot instructions

This is the personal-account default community-health repository for
`frasermolyneux`.

- Keep inherited issue forms and the pull-request template concise,
  technology-neutral, and broadly applicable.
- Do not assume a language, framework, cloud, database, package manager,
  deployment model, or repository layout.
- Make only changes relevant to community-health templates and repository
  guidance.
- Never add secrets, credentials, tokens, private connection details, or
  sensitive external data.
- Use [the lightweight engineering standards](../docs/standards.md) when
  changing shared guidance. Apply only the sections supported by the target
  repository and task; repository-specific instructions remain authoritative.

For Markdown or template changes, inspect the rendered structure, verify
changed relative links, and run `git diff --check`.

For issue-form YAML, parse the changed files and confirm each form retains
`name`, `description`, valid body item types, unique `id` values where required,
and required `attributes` or `validations`.
