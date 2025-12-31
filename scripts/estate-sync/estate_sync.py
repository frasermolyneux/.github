import json
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict
import re
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
REPOS_INDEX_OUT = ROOT / "docs" / "estate" / "repos" / "index.md"
CATEGORIES_DIR = ROOT / "docs" / "estate" / "categories"
REPO_PAGES_DIR = ROOT / "docs" / "estate" / "repos"

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
        log(f"Workflow file not found: {repo}/{path}")
        return None
    resp.raise_for_status()
    payload = resp.json()
    download_url = payload.get("download_url")
    if not download_url:
        log(f"No download_url for workflow: {repo}/{path}")
        return None
    raw = session.get(download_url)
    raw.raise_for_status()
    return raw.text


def list_workflow_files(repo: str) -> List[str]:
    url = f"https://api.github.com/repos/{OWNER}/{repo}/contents/.github/workflows"
    resp = session.get(url)
    if resp.status_code == 404:
        log(f"No workflows directory for repo {repo}")
        return []
    resp.raise_for_status()
    payload = resp.json()
    paths: List[str] = []
    for entry in payload:
        if entry.get("type") == "file" and entry.get("name", "").lower().endswith((".yml", ".yaml")):
            path = entry.get("path")
            if path:
                paths.append(path)
    log(f"Repo {repo} has {len(paths)} workflow files")
    return paths


def list_ado_pipeline_files(repo: str) -> List[str]:
    url = f"https://api.github.com/repos/{OWNER}/{repo}/contents/.azure-pipelines"
    resp = session.get(url)
    if resp.status_code == 404:
        log(f"No .azure-pipelines directory for repo {repo}")
        return []
    resp.raise_for_status()
    payload = resp.json()
    paths: List[str] = []
    for entry in payload:
        if entry.get("type") == "file" and entry.get("name", "").lower().endswith((".yml", ".yaml")):
            path = entry.get("path")
            if path:
                paths.append(path)
    log(f"Repo {repo} has {len(paths)} ADO pipeline files")
    return paths


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
        log("croniter not installed; cannot compute next run")
        return None
    try:
        itr = croniter(cron_expr, now)
        nxt = itr.get_next(datetime)
        return nxt.strftime("%d/%m/%Y %H:%M UTC")
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
            schedules = on_block.get("schedule", []) if isinstance(on_block, dict) else []
            for schedule in schedules or []:
                if isinstance(schedule, dict) and "cron" in schedule:
                    crons.append(str(schedule["cron"]))
        except Exception as exc:  # pragma: no cover - defensive
            log(f"YAML parse failed for {repo}/{path}: {exc}")

    if not crons:
        # Fallback 1: best-effort regex per-line
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("cron:"):
                cron_expr = line.split("cron:", 1)[1].strip().strip('"').strip("'")
                if cron_expr:
                    crons.append(cron_expr)

    if not crons:
        # Fallback 2: regex across file to catch wrapped strings
        matches = re.findall(r"cron:\s*['\"]?([^'\"\n]+)", content, flags=re.IGNORECASE)
        crons.extend([m.strip() for m in matches if m.strip()])

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
    if entries:
        log(f"Repo {repo} workflow {path} has schedules: {', '.join(crons)}")
    else:
        log(f"Repo {repo} workflow {path} has no cron schedule detected")
    return entries


def extract_ado_yaml_schedule(repo: str, project: str, path: str, now: datetime) -> List[Dict]:
    content = github_file(repo, path)
    if not content:
        return []

    crons: List[str] = []
    if yaml:
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                schedules = data.get("schedules") or []
                for sched in schedules or []:
                    if isinstance(sched, dict) and "cron" in sched:
                        crons.append(str(sched["cron"]))
        except Exception as exc:  # pragma: no cover - defensive
            log(f"YAML parse failed for ADO pipeline {repo}/{path}: {exc}")

    if not crons:
        matches = re.findall(r"cron:\s*['\"]?([^'\"\n]+)", content, flags=re.IGNORECASE)
        crons.extend([m.strip() for m in matches if m.strip()])

    entries: List[Dict] = []
    for cron_expr in crons:
        next_run = next_run_from_cron(cron_expr, now)
        entries.append({
            "type": "Azure Pipelines",
            "repo": repo,
            "name": path.split("/")[-1],
            "cron": cron_expr,
            "next": next_run or "-",
            "link": f"https://github.com/{OWNER}/{repo}/blob/main/{path}",
        })
    if entries:
        log(f"Repo {repo} ADO pipeline file {path} schedules: {', '.join(crons)}")
    else:
        log(f"Repo {repo} ADO pipeline file {path} has no cron schedule detected")
    return entries


def extract_ado_schedule(repo: str, project: str, pipeline: Dict, now: datetime) -> List[Dict]:
    # Deprecated: ADO API schedule detection removed in favor of parsing YAML files in repo
    return []


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


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log(f"Wrote {path}")


def _page_link(path: str) -> str:
    # GitHub Pages serves .html; adjust markdown references to avoid 404s
    if path.endswith(".md"):
        return path[:-3] + ".html"
    return path


def nav_line(home: str, workloads: str, pipelines: str, scheduling: str, repos_index: str) -> str:
    return (
        f"🏠 [Home]({_page_link(home)}) | 📦 [Workloads]({_page_link(workloads)}) | 🧪 [Pipelines]({_page_link(pipelines)}) | "
        f"⏰ [Scheduling]({_page_link(scheduling)}) | 📚 [Repos]({_page_link(repos_index)})"
    )


def render_workloads(categories: Dict[str, List[Dict]], timestamp: datetime) -> str:
    lines = [
        nav_line("../index.md", "./workloads.md", "./pipelines.md", "./pipeline-scheduling.md", "./repos/index.md"),
        "",
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
            detail_link = _page_link(f"./repos/{workload['repo']}.md")
            lines.append(f"| 📁 {repo_link} ([Detail]({detail_link})) | 🌍 {envs} | 🔑 {subs} |")
        lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_route_to_production(repos: List[Tuple[str, Optional[str], Optional[str]]], timestamp: datetime) -> str:
    lines = [
        nav_line("../index.md", "./workloads.md", "./pipelines.md", "./pipeline-scheduling.md", "./repos/index.md"),
        "",
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
        detail_link = _page_link(f"./repos/{name}.md")
        lines.append(f"| 📁 {repo_link} ([Detail]({detail_link})) | 📦 {release} | ✅ {ci} |")
    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_pipelines(categories: Dict[str, List[Dict]], repos: Dict[str, List[str]], timestamp: datetime) -> str:
    lines = [
        nav_line("../index.md", "./workloads.md", "./pipelines.md", "./pipeline-scheduling.md", "./repos/index.md"),
        "",
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
        detail_link = _page_link(f"./repos/{repo_name}.md")
        lines.append(f"| 📁 {repo_link} ([Detail]({detail_link})) | 🏷️ {badge_list} |")

    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_scheduling(schedules: List[Dict], timestamp: datetime) -> str:
    lines = [
        nav_line("../index.md", "./workloads.md", "./pipelines.md", "./pipeline-scheduling.md", "./repos/index.md"),
        "",
        "# Pipeline Scheduling",
        "",
        "Workflows and pipelines with cron-based schedules, grouped by workload category.",
        "",
    ]

    if not schedules:
        lines.append("No schedules detected.")
        lines.append("")
        lines.extend(footer_lines(timestamp))
        return "\n".join(lines)

    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for entry in schedules:
        grouped[entry.get("category", "Uncategorised")].append(entry)

    for category in sorted(grouped.keys(), key=lambda c: c.lower()):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Type | Repository | Name | Cron | Next run (UTC) |")
        lines.append("| --- | --- | --- | --- | --- |")
        for entry in sorted(grouped[category], key=lambda s: (s.get("cron", ""), s.get("name", ""))):
            repo_name = entry.get("repo", "-")
            repo_link = f"[{repo_name}](https://github.com/{OWNER}/{repo_name})" if repo_name != "-" else "-"
            name_val = entry.get("name", "-")
            link = entry.get("link")
            name_cell = f"[🧾 {name_val}]({link})" if link else f"🧾 {name_val}"
            lines.append(
                f"| ⏱️ {entry.get('type', '-')} | 📁 {repo_link} | {name_cell} | "
                f"🕒 {entry.get('cron', '-')} | 📅 {entry.get('next', '-')} |"
            )
        lines.append("")

    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_repo_detail(repo: str, detail: Dict, timestamp: datetime) -> str:
    lines = [
        nav_line("../../index.md", "../workloads.md", "../pipelines.md", "../pipeline-scheduling.md", "./index.md"),
        "",
        f"# {repo}",
        "",
    ]

    repo_link = f"https://github.com/{OWNER}/{repo}"
    ado_project = detail.get("ado_project")
    lines.append("Summary:")
    lines.append(f"- 📁 GitHub: [{repo}]({repo_link})")
    if ado_project:
        lines.append(f"- 🏢 Azure DevOps project: [{ado_project}]({AZDO_ORG}/{ado_project})")
    if detail.get("environments"):
        lines.append(f"- 🌍 Environments: {', '.join(detail['environments'])}")
    if detail.get("subscriptions"):
        lines.append(f"- 🔑 Subscriptions: {', '.join(sorted(detail['subscriptions']))}")
    lines.append(f"- 🗂️ Workflows: https://github.com/{OWNER}/{repo}/tree/main/.github/workflows")
    lines.append(f"- 🗂️ Azure Pipelines YAML: https://github.com/{OWNER}/{repo}/tree/main/.azure-pipelines")

    lines.append("")
    lines.append("## Badges")
    lines.append("")
    badges = detail.get("badges", [])
    lines.append(" ".join(badges) if badges else "No badges found")

    lines.append("")
    lines.append("## Scheduling")
    lines.append("")
    schedules = detail.get("schedules", [])
    lines.append("| Type | Cron | Next run (UTC) | Link |")
    lines.append("| --- | --- | --- | --- |")
    if schedules:
        for entry in sorted(schedules, key=lambda s: (s.get("type", ""), s.get("cron", ""))):
            lines.append(
                f"| {entry.get('type', '-')} | {entry.get('cron', '-')} | {entry.get('next', '-')} | "
                f"[link]({entry.get('link', '#')}) |"
            )
    else:
        lines.append("| - | - | - | - |")

    lines.append("")
    lines.append("## Workflows")
    lines.append("")
    workflows = detail.get("workflows", [])
    lines.append("| Name | Path | Link |")
    lines.append("| --- | --- | --- |")
    if workflows:
        for wf in workflows:
            lines.append(
                f"| {wf.get('name', wf.get('path', '-'))} | {wf.get('path', '-')} | "
                f"[view]({wf.get('link', '#')}) |"
            )
    else:
        lines.append("| - | - | - |")

    lines.append("")
    lines.append("## Azure Pipelines")
    lines.append("")
    ado_pipes = detail.get("ado_pipelines", [])
    lines.append("| Name | Link |")
    lines.append("| --- | --- |")
    if ado_pipes:
        for pipe in ado_pipes:
            lines.append(f"| {pipe.get('name', '-')} | [view]({pipe.get('link', '#')}) |")
    else:
        lines.append("| - | - |")

    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_repos_index(repos: Dict[str, Dict], timestamp: datetime) -> str:
    lines = [
        nav_line("../../index.md", "../workloads.md", "../pipelines.md", "../pipeline-scheduling.md", "./index.md"),
        "",
        "# Repositories",
        "",
        "All repositories with links to their detail pages.",
        "",
        "| Repository | ADO Project | Environments | Subscriptions |",
        "| --- | --- | --- | --- |",
    ]
    for name, detail in sorted(repos.items(), key=lambda i: i[0].lower()):
        envs = ", ".join(detail.get("environments", [])) or "-"
        subs = ", ".join(sorted(detail.get("subscriptions", []))) or "-"
        detail_link = _page_link(f"./{name}.md")
        repo_link = f"[{name}](https://github.com/{OWNER}/{name})"
        ado_project = detail.get("ado_project") or "-"
        ado_link = f"[{ado_project}]({AZDO_ORG}/{ado_project})" if ado_project != "-" else "-"
        lines.append(f"| 📁 {repo_link} ([Detail]({detail_link})) | 🏢 {ado_link} | 🌍 {envs} | 🔑 {subs} |")

    lines.append("")
    lines.extend(footer_lines(timestamp))
    return "\n".join(lines)


def render_category_pages(categories: Dict[str, List[Dict]], repo_details: Dict[str, Dict], timestamp: datetime) -> Dict[str, str]:
    pages: Dict[str, str] = {}
    for category, items in categories.items():
        lines = [
            nav_line("../../index.md", "../workloads.md", "../pipelines.md", "../pipeline-scheduling.md", "../repos/index.md"),
            "",
            f"# {category}",
            "",
            "Workloads in this category.",
            "",
            "| Workload | Environments | Subscriptions |",
            "| --- | --- | --- |",
        ]
        for workload in sorted(items, key=lambda w: w["name"].lower()):
            name = workload["name"]
            envs = ", ".join(workload["environments"]) if workload["environments"] else "-"
            subs = ", ".join(sorted(filter(None, workload["subscriptions"]))) or "-"
            detail_link = _page_link(f"../repos/{workload['repo']}.md")
            repo_link = f"[{name}](https://github.com/{OWNER}/{workload['repo']})"
            lines.append(f"| 📁 {repo_link} ([Detail]({detail_link})) | 🌍 {envs} | 🔑 {subs} |")

        lines.append("")
        lines.extend(footer_lines(timestamp))
        pages[category] = "\n".join(lines)

    return pages


def gather_repo_details(
    repo_meta: Dict[str, Dict],
    workflow_files: Dict[str, List[Dict]],
    schedules: List[Dict],
    badge_sets: Dict[str, List[str]],
    repo_ado_pipelines: Dict[str, List[Dict]],
) -> Dict[str, Dict]:
    details: Dict[str, Dict] = {}
    schedule_by_repo: Dict[str, List[Dict]] = defaultdict(list)
    for sched in schedules:
        schedule_by_repo[sched.get("repo", "")].append(sched)

    for repo, meta in repo_meta.items():
        details[repo] = {
            "ado_project": meta.get("ado_project"),
            "environments": sorted(meta.get("environments", [])),
            "subscriptions": sorted(meta.get("subscriptions", [])),
            "badges": badge_sets.get(repo, []),
            "workflows": workflow_files.get(repo, []),
            "ado_pipelines": repo_ado_pipelines.get(repo, []),
            "schedules": schedule_by_repo.get(repo, []),
        }
    return details


def main() -> None:
    categories = load_workloads()
    now = datetime.now(timezone.utc)

    repo_meta: Dict[str, Dict] = {}
    repo_category: Dict[str, str] = {}
    for category_name, values in categories.items():
        for workload in values:
            repo = workload["repo"]
            repo_category[repo] = category_name
            if repo not in repo_meta:
                repo_meta[repo] = {
                    "environments": set(),
                    "subscriptions": set(),
                    "ado_project": None,
                }
            repo_meta[repo]["environments"].update(workload["environments"])
            repo_meta[repo]["subscriptions"].update(filter(None, workload["subscriptions"]))
            if workload["devops_projects"] and not repo_meta[repo]["ado_project"]:
                repo_meta[repo]["ado_project"] = workload["devops_projects"][0]

    repo_names = sorted(repo_meta.keys())
    repo_badges: List[Tuple[str, Optional[str], Optional[str]]] = []
    repo_workflow_badges: Dict[str, List[str]] = {}
    project_pipeline_cache: Dict[str, List[Dict]] = {}
    schedule_entries: List[Dict] = []
    workflow_file_entries: Dict[str, List[Dict]] = {}
    repo_ado_pipelines: Dict[str, List[Dict]] = {}

    for repo in repo_names:
        workflows = fetch_workflows(repo)
        workflow_paths = list_workflow_files(repo)
        wf_name_lookup = {wf.get("path"): (wf.get("name") or wf.get("path")) for wf in workflows if wf.get("path")}
        log(f"Repo {repo} workflows API returned {len(workflows)} entries; files found {len(workflow_paths)}")

        release_badge = find_badge(repo, workflows, ["release-to-production.yml", "release-to-production.yaml"])
        ci_badge = find_badge(repo, workflows, ["ci.yml", "ci.yaml", "build.yml", "build.yaml", "tests.yml", "tests.yaml"])
        repo_badges.append((repo, release_badge, ci_badge))
        repo_workflow_badges[repo] = workflow_badges(repo, workflows)

        workflow_file_entries[repo] = []
        for path in workflow_paths:
            wf_entry = {"path": path, "name": wf_name_lookup.get(path), "link": f"https://github.com/{OWNER}/{repo}/blob/main/{path}"}
            workflow_file_entries[repo].append(wf_entry)
            schedule_entries.extend(extract_github_schedule(repo, {"path": path, "name": wf_entry["name"]}, now))

        combined_badges = list(repo_workflow_badges[repo])
        project = repo_meta[repo].get("ado_project")
        if project:
            if project not in project_pipeline_cache:
                project_pipeline_cache[project] = fetch_ado_pipelines(project)
            pipelines = project_pipeline_cache[project]
            log(f"Repo {repo} using ADO project {project} with {len(pipelines)} pipelines")
            combined_badges.extend(ado_pipeline_badges(repo, project, pipelines))

            ado_files = list_ado_pipeline_files(repo)
            repo_ado_pipelines[repo] = [
                {"name": p.get("name", "unknown"), "link": f"{AZDO_ORG}/{project}/_build?definitionId={p.get('id')}"}
                for p in pipelines
                if str(p.get("name", "")).lower().startswith(f"{repo.lower()}.")
            ]
            for path in ado_files:
                schedule_entries.extend(extract_ado_yaml_schedule(repo, project, path, now))
        else:
            log(f"Repo {repo} has no ADO project; only GitHub workflows included")
            repo_ado_pipelines[repo] = []
        repo_workflow_badges[repo] = combined_badges

    for entry in schedule_entries:
        entry["category"] = repo_category.get(entry.get("repo"), "Uncategorised")

    repo_details = gather_repo_details(repo_meta, workflow_file_entries, schedule_entries, repo_workflow_badges, repo_ado_pipelines)

    write_markdown(WORKLOADS_OUT, render_workloads(categories, now))
    write_markdown(ROUTE_OUT, render_route_to_production(repo_badges, now))
    write_markdown(PIPELINES_OUT, render_pipelines(categories, repo_workflow_badges, now))
    write_markdown(PIPELINE_SCHED_OUT, render_scheduling(schedule_entries, now))

    write_markdown(REPOS_INDEX_OUT, render_repos_index(repo_details, now))
    category_pages = render_category_pages(categories, repo_details, now)
    for category, content in category_pages.items():
        write_markdown(CATEGORIES_DIR / f"{category}.md", content)
    for name, detail in repo_details.items():
        write_markdown(REPO_PAGES_DIR / f"{name}.md", render_repo_detail(name, detail, now))

    log(f"Generated repo pages: {len(repo_details)}")

    log(f"Total schedule entries: {len(schedule_entries)}")


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    main()
