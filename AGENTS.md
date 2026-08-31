# Repository execution brief

## Purpose

- This is the personal-account default community-health repository for
  `frasermolyneux`.
- It maintains estate documentation and the synchronization that generates the
  estate dashboard.
- Its issue forms and pull-request template are inherited by repositories that
  do not provide local overrides.

## Maintained and generated locations

- Maintain repository guidance in `README.md`, `AGENTS.md`, and
  `.github/copilot-instructions.md`.
- Maintain inherited templates in `.github/ISSUE_TEMPLATE/` and
  `.github/PULL_REQUEST_TEMPLATE.md`.
- Maintain synchronization logic in `scripts/estate-sync/estate_sync.py` and
  its workflow in `.github/workflows/estate-sync.yml`.
- Treat `docs/estate/` as generated output. Change its generator or upstream
  source instead of editing generated pages directly.
- `docs/index.md` and `docs/_config.yml` are maintained GitHub Pages inputs.

## Targeted validation

Run only the checks relevant to the files changed:

```text
python -m py_compile scripts/estate-sync/estate_sync.py
python -c "from pathlib import Path; import yaml; [yaml.safe_load(p.read_text(encoding='utf-8')) for p in Path('.github').rglob('*.yml')]"
git diff --check
```

- For Markdown-only changes, verify changed relative links resolve and run
  `git diff --check`.
- For issue forms and workflows, run the YAML parse command and inspect the
  changed structure against GitHub's schema.
- Do not run the estate synchronization merely to validate documentation or
  template edits; it writes broad generated output and requires external data.

## Constraints

- Distinguish generated estate files from manually maintained sources before
  editing.
- Assume inherited templates affect every repository without a local override.
- Keep shared templates technology-neutral and free of repository-specific
  implementation assumptions.
- Do not add secrets, credentials, tokens, or sensitive values to estate data,
  scripts, templates, or workflows.

## Authoritative references

- [Repository overview](README.md)
- [Estate dashboard overview](docs/index.md)
- [Synchronization workflow](.github/workflows/estate-sync.yml)
- [Synchronization source](scripts/estate-sync/estate_sync.py)
