import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from typing import Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

try:
    from croniter import croniter  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    croniter = None

import requests
from base64 import b64encode

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = "frasermolyneux"
REPO = "platform-workloads"
WORKLOADS_PATH = "terraform/workloads"
AZDO_ORG = os.environ.get("AZDO_ORG", "https://dev.azure.com/frasermolyneux")
AZDO_PAT = os.environ.get("AZDO_PAT")

ROOT = Path(__file__).resolve().parents[2]
WORKLOADS_OUT = ROOT / "docs" / "estate" / "workloads.md"
ROUTE_OUT = ROOT / "docs" / "estate" / "route-to-production.md"
PIPELINES_OUT = ROOT / "docs" / "estate" / "pipelines.md"
PIPELINE_SCHED_OUT = ROOT / "docs" / "estate" / "pipeline-scheduling.md"

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"})

ado_session: Optional[requests.Session] = None
if AZDO_PAT:
    ado_session = requests.Session()
    token = b64encode(f":{AZDO_PAT}".encode()).decode()
    ado_session.headers.update({
        "Authorization": f"Basic {token}",
        "Accept": "application/json"
    })


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def github_contents(path: str) -> List[Dict]:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json()


def github_file(repo: str, path: str) -> Optional[str]:
    url = f"https://api.github.com/repos/{OWNER}/{repo}/contents/{path}"
    resp = session.get(url)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    payload = resp.json()
    download_url = payload.get("download_url")
    if not download_url:
        return None
    raw = session.get(download_url)
    raw.raise_for_status()
    return raw.text


def fetch_workflows(repo: str) -> List[Dict]:
    url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/workflows"
    resp = session.get(url)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("workflows", [])


def fetch_ado_pipelines(project: str) -> List[Dict]:
    if not ado_session:
        log("ADO disabled: AZDO_PAT not set")
        return []
    url = f"{AZDO_ORG}/{project}/_apis/pipelines?api-version=7.0"
    resp = ado_session.get(url)
    if resp.status_code == 404:
        log(f"ADO pipelines 404 for project {project}")
        return []
    resp.raise_for_status()
    payload = resp.json()
    pipelines = payload.get("value", [])
    log(f"Fetched {len(pipelines)} ADO pipelines for project {project}")
    return pipelines


def fetch_ado_pipeline_definition(project: str, pipeline_id: int) -> Optional[Dict]:
    if not ado_session:
        return None
    url = f"{AZDO_ORG}/{project}/_apis/build/definitions/{pipeline_id}?api-version=7.0"
    resp = ado_session.get(url)
    if resp.status_code == 404:
        log(f"ADO pipeline definition 404 for pipeline {pipeline_id} in project {project}")
        return None
    resp.raise_for_status()
    return resp.json()


def ado_pipeline_badges(repo: str, project: str, pipelines: Optional[List[Dict]] = None) -> List[str]:
    if pipelines is None:
        pipelines = fetch_ado_pipelines(project)
    badges: List[str] = []
    prefix = f"{repo.lower()}."
    for pipeline in pipelines:
        name = pipeline.get("name", "").lower()
        pipeline_id = pipeline.get("id")
        if not pipeline_id or not name.startswith(prefix):
            continue
        label = pipeline.get("name", repo)
        encoded_name = quote(label, safe="")
        badge_url = (
            f"{AZDO_ORG}/{project}/_apis/build/status/{encoded_name}?branchName=main"
            f"&repoName=frasermolyneux%2F{repo}&label={encoded_name}"
        )
        link_url = f"{AZDO_ORG}/{project}/_build/latest?definitionId={pipeline_id}&branchName=main"
        badges.append(f"[![{label}]({badge_url})]({link_url})")
    log(f"Repo {repo} (project {project}) matched {len(badges)} ADO pipelines")
    return badges


def find_badge(repo: str, workflows: List[Dict], candidates: List[str]) -> Optional[str]:
    for wf in workflows:
        path = wf.get("path", "").lower()
        if any(path.endswith(candidate) for candidate in candidates):
            badge_url = f"https://github.com/{OWNER}/{repo}/actions/workflows/{wf['path']}/badge.svg"
            link_url = f"https://github.com/{OWNER}/{repo}/actions/workflows/{wf['path']}"
            label = wf.get("name") or wf.get("path")
            return f"[![{label}]({badge_url})]({link_url})"
    return None


def workflow_badges(repo: str, workflows: List[Dict]) -> List[str]:
    badges: List[str] = []
    for wf in workflows:
        path = wf.get("path")
        if not path:
            continue
        badge_url = f"https://github.com/{OWNER}/{repo}/actions/workflows/{path}/badge.svg"
        link_url = f"https://github.com/{OWNER}/{repo}/actions/workflows/{path}"
        label = wf.get("name") or path
        badges.append(f"[![{label}]({badge_url})]({link_url})")
    return badges


def next_run_from_cron(cron_expr: str, now: datetime) -> Optional[str]:
    if not croniter:
        return None
    try:
        itr = croniter(cron_expr, now)
        nxt = itr.get_next(datetime)
        return nxt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception as exc:  # pragma: no cover - defensive
        log(f"Failed to compute next run for cron '{cron_expr}': {exc}")
        return None


def extract_github_schedule(repo: str, wf: Dict, now: datetime) -> List[Dict]:
    path = wf.get("path")
    if not path:
        return []
    content = github_file(repo, path)
    if not content:
        return []

    crons: List[str] = []
    if yaml:
        try:
            data = yaml.safe_load(content)
            on_block = data.get("on") if isinstance(data, dict) else None
            schedules = []
            if isinstance(on_block, dict):
                schedules = on_block.get("schedule", [])
            elif isinstance(on_block, list):
                # Some workflows use list syntax; schedule would be a dict entry
                schedules = [entry.get("schedule", []) for entry in on_block if isinstance(entry, dict)]
                flattened = []
                for item in schedules:
                    if isinstance(item, list):
                        flattened.extend(item)
                schedules = flattened or schedules
            for schedule in schedules or []:
                if isinstance(schedule, dict) and "cron" in schedule:
                    crons.append(str(schedule["cron"]))
        except Exception as exc:  # pragma: no cover - defensive
            log(f"YAML parse failed for {repo}/{path}: {exc}")

    if not crons:
        # Fallback: best-effort regex style scan
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("cron:"):
                cron_expr = line.split("cron:", 1)[1].strip().strip('"').strip("'")
                if cron_expr:
                    crons.append(cron_expr)

    entries: List[Dict] = []
    for cron_expr in crons:
        next_run = next_run_from_cron(cron_expr, now)
        entries.append({
            "type": "GitHub Actions",
            "repo": repo,
            "name": wf.get("name") or path,
            "cron": cron_expr,
            "next": next_run or "-",
            "link": f"https://github.com/{OWNER}/{repo}/actions/workflows/{path}",
        })
    return entries


def extract_ado_schedule(repo: str, project: str, pipeline: Dict, now: datetime) -> List[Dict]:
    pipeline_id = pipeline.get("id")
    if not pipeline_id:
        return []
    name = pipeline.get("name", "").lower()
    if not name.startswith(f"{repo.lower()}."):
        return []
    definition = fetch_ado_pipeline_definition(project, pipeline_id)
    if not definition:
        return []

    schedules = definition.get("schedules", [])
    cron_entries: List[str] = []
    for sched in schedules:
        cron_expr = sched.get("cron") or sched.get("schedule")
        if cron_expr:
            cron_entries.append(str(cron_expr))

    entries: List[Dict] = []
    for cron_expr in cron_entries:
        next_run = next_run_from_cron(cron_expr, now)
        entries.append({
            "type": "Azure Pipelines",
            "repo": repo,
            "name": pipeline.get("name", str(pipeline_id)),
            "cron": cron_expr,
            "next": next_run or "-",
            "link": f"{AZDO_ORG}/{project}/_build/latest?definitionId={pipeline_id}",
        })
    return entries


def load_workloads() -> Dict[str, List[Dict]]:
    categories: Dict[str, List[Dict]] = {}
    for entry in github_contents(WORKLOADS_PATH):
        if entry["type"] != "dir" or entry["name"] == "examples":
            continue
        category = entry["name"]
        categories[category] = []
        for file_entry in github_contents(f"{WORKLOADS_PATH}/{category}"):
            if file_entry["type"] != "file" or not file_entry["name"].endswith(".json"):
                continue
            raw = session.get(file_entry["download_url"])
            raw.raise_for_status()
            payload = json.loads(raw.text)
            environments = payload.get("environments", [])
            devops_projects = list({env.get("devops_project") for env in environments if env.get("devops_project")})
            categories[category].append({
                "name": payload.get("name", file_entry["name"].replace(".json", "")),
                "repo": payload.get("name", file_entry["name"].replace(".json", "")),
                "environments": [env.get("name") for env in environments if env.get("name")],
                "subscriptions": list({env.get("subscription") for env in environments if env.get("subscription")}),
                "devops_projects": devops_projects,
            })
    return categories


def footer_lines(timestamp: datetime) -> List[str]:
    ts = timestamp.strftime("%Y-%m-%d %H:%M UTC")
    return [
        "",
        "---",
        "Generated by scripts/estate-sync/estate_sync.py",
        "<!-- Auto-generated file; do not edit directly. -->",
        f"Last updated: {ts}",
    ]


def render_workloads(categories: Dict[str, List[Dict]], timestamp: datetime) -> str:
    lines = [
        "# Workload Catalog",
        "",
        "Generated from platform-workloads/terraform/workloads (excluding examples).",
        "",
    ]
    for category in sorted(categories.keys()):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Workload | Environments | Subscriptions |")
        lines.append("| --- | --- | --- |")
        for workload in sorted(categories[category], key=lambda w: w["name"]):
            envs = ", ".join(workload["environments"]) if workload["environments"] else "-"
            subs = ", ".join(sorted(filter(None, workload["subscriptions"]))) or "-"
            repo_link = f"[{workload['repo']}](https://github.com/{OWNER}/{workload['repo']})"
            lines.append(f"| {repo_link} | {envs} | {subs} |")
        lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_route_to_production(repos: List[Tuple[str, Optional[str], Optional[str]]], timestamp: datetime) -> str:
    lines = [
        "# Route to Production",
        "",
        "This page is generated from repository workflows. Badges link to the owning workflow so you can jump straight to failing runs.",
        "",
        "## Release pipelines",
        "",
        "| Repository | Release Pipeline | CI/Main |",
        "| --- | --- | --- |",
    ]
    for name, release_badge, ci_badge in sorted(repos, key=lambda r: r[0].lower()):
        release = release_badge or "Not configured"
        ci = ci_badge or "Not found"
        repo_link = f"[{name}](https://github.com/{OWNER}/{name})"
        lines.append(f"| {repo_link} | {release} | {ci} |")
    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_scheduling(schedules: List[Dict], timestamp: datetime) -> str:
    lines = [
        "# Pipeline Scheduling",
        "",
        "Workflows and pipelines with cron-based schedules.",
        "",
        "| Type | Repository | Name | Cron | Next run (UTC) | Link |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if schedules:
        for entry in sorted(schedules, key=lambda s: (s.get("repo", ""), s.get("name", ""))):
            lines.append(
                f"| {entry.get('type', '-')} | {entry.get('repo', '-')} | {entry.get('name', '-')} | "
                f"{entry.get('cron', '-')} | {entry.get('next', '-')} | "
                f"[link]({entry.get('link', '#')}) |"
            )
    else:
        lines.append("| - | - | - | - | - | - |")

    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_pipelines(categories: Dict[str, List[Dict]], repos: Dict[str, List[str]], timestamp: datetime) -> str:
    lines = [
        "# Pipeline Badges",
        "",
        "All workflow badges per workload. Badges link to the workflow definitions.",
        "",
        "| Workload | Workflows |",
        "| --- | --- |",
    ]

    workloads = []
    for category in categories.values():
        workloads.extend(category)

    for workload in sorted(workloads, key=lambda w: w["name"].lower()):
        repo_name = workload["repo"]
        badges = repos.get(repo_name, [])
        repo_link = f"[{workload['name']}](https://github.com/{OWNER}/{repo_name})"
        badge_list = " ".join(badges) if badges else "No workflows found"
        lines.append(f"| {repo_link} | {badge_list} |")

    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def main() -> None:
    categories = load_workloads()
    now = datetime.now(timezone.utc)

    repo_names = sorted({w["repo"] for values in categories.values() for w in values})
    repo_badges: List[Tuple[str, Optional[str], Optional[str]]] = []
    repo_workflow_badges: Dict[str, List[str]] = {}
    repo_ado_projects: Dict[str, str] = {}
    project_pipeline_cache: Dict[str, List[Dict]] = {}
    schedule_entries: List[Dict] = []
    for values in categories.values():
        for workload in values:
            if workload["devops_projects"]:
                repo_ado_projects[workload["repo"]] = workload["devops_projects"][0]
            else:
                log(f"Repo {workload['repo']} has no devops_project; skipping ADO")
    for repo in repo_names:
        workflows = fetch_workflows(repo)
        release_badge = find_badge(repo, workflows, ["release-to-production.yml", "release-to-production.yaml"])
        ci_badge = find_badge(repo, workflows, ["ci.yml", "ci.yaml", "build.yml", "build.yaml", "tests.yml", "tests.yaml"])
        repo_badges.append((repo, release_badge, ci_badge))
        repo_workflow_badges[repo] = workflow_badges(repo, workflows)
        for wf in workflows:
            schedule_entries.extend(extract_github_schedule(repo, wf, now))

    repo_all_badges: Dict[str, List[str]] = {}
    for repo, badges in repo_workflow_badges.items():
        combined = list(badges)
        project = repo_ado_projects.get(repo)
        if project:
            if project not in project_pipeline_cache:
                project_pipeline_cache[project] = fetch_ado_pipelines(project)
            pipelines = project_pipeline_cache[project]
            combined.extend(ado_pipeline_badges(repo, project, pipelines))
            for pipeline in pipelines:
                schedule_entries.extend(extract_ado_schedule(repo, project, pipeline, now))
        else:
            log(f"Repo {repo} has no ADO project; only GitHub workflows included")
        repo_all_badges[repo] = combined

    WORKLOADS_OUT.parent.mkdir(parents=True, exist_ok=True)
    WORKLOADS_OUT.write_text(render_workloads(categories, now), encoding="utf-8")
    ROUTE_OUT.write_text(render_route_to_production(repo_badges, now), encoding="utf-8")
    PIPELINES_OUT.write_text(render_pipelines(categories, repo_all_badges, now), encoding="utf-8")
    PIPELINE_SCHED_OUT.write_text(render_scheduling(schedule_entries, now), encoding="utf-8")


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    main()
