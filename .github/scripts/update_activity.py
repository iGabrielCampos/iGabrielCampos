import os
import re
import sys
import json
import urllib.request

USERNAME = "iGabrielCampos"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
START_TAG = "<!-- RECENT_ACTIVITY:START -->"
END_TAG = "<!-- RECENT_ACTIVITY:END -->"

def fetch_events():
    url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=30"
    headers = {"User-Agent": "GitHub-Activity-Updater"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching events: {e}", file=sys.stderr)
        return []

def format_event(e):
    etype = e.get("type")
    repo = e.get("repo", {})
    repo_name = repo.get("name")
    if not repo_name:
        return None
    repo_url = f"https://github.com/{repo_name}"
    payload = e.get("payload", {})

    if etype == "PushEvent":
        commits = payload.get("commits", [])
        count = payload.get("size", len(commits))
        ref = payload.get("ref", "").replace("refs/heads/", "")
        branch_str = f" to `{ref}`" if ref else ""
        if count > 0:
            s = "s" if count != 1 else ""
            return f"🔨 Pushed {count} commit{s}{branch_str} in [`{repo_name}`]({repo_url})"
        return f"🔨 Pushed code{branch_str} in [`{repo_name}`]({repo_url})"
    elif etype == "CreateEvent":
        ref_type = payload.get("ref_type", "repository")
        ref = payload.get("ref")
        if ref_type == "repository":
            return f"🚀 Created repository [`{repo_name}`]({repo_url})"
        elif ref:
            return f"🌱 Created {ref_type} `{ref}` in [`{repo_name}`]({repo_url})"
        else:
            return f"🌱 Created {ref_type} in [`{repo_name}`]({repo_url})"
    elif etype == "WatchEvent":
        return f"⭐ Starred [`{repo_name}`]({repo_url})"
    elif etype == "PullRequestEvent":
        action = payload.get("action", "opened")
        num = payload.get("number", "")
        num_str = f" #{num}" if num else ""
        return f"🔀 {action.capitalize()} PR{num_str} in [`{repo_name}`]({repo_url})"
    elif etype == "IssuesEvent":
        action = payload.get("action", "opened")
        num = payload.get("issue", {}).get("number", "")
        num_str = f" #{num}" if num else ""
        return f"📌 {action.capitalize()} issue{num_str} in [`{repo_name}`]({repo_url})"
    elif etype == "ForkEvent":
        return f"🍴 Forked [`{repo_name}`]({repo_url})"
    return None

def main():
    events = fetch_events()
    lines = []
    seen = set()

    for ev in events:
        line = format_event(ev)
        if line and line not in seen:
            seen.add(line)
            lines.append(f"- {line}")
        if len(lines) >= 5:
            break

    if not lines:
        lines = ["*No recent public activity.*"]

    activity_content = "\n" + "\n".join(lines) + "\n"

    readme_full_path = os.path.abspath(README_PATH)
    if not os.path.exists(readme_full_path):
        print(f"README not found at {readme_full_path}", file=sys.stderr)
        sys.exit(1)

    with open(readme_full_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        rf"({re.escape(START_TAG)}).*?({re.escape(END_TAG)})",
        re.DOTALL
    )

    if not pattern.search(content):
        print("Markers not found in README.md", file=sys.stderr)
        return

    new_content = pattern.sub(rf"\1{activity_content}\2", content)

    if new_content != content:
        with open(readme_full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md updated with recent activity.")
    else:
        print("No changes in activity.")

if __name__ == "__main__":
    main()
