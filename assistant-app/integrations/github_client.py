"""GitHub REST client (personal access token)."""
import os
import requests


def configured() -> bool:
    return bool(os.getenv("GITHUB_TOKEN"))


def _get(url: str, **params):
    return requests.get(
        f"https://api.github.com{url}",
        headers={"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
                 "Accept": "application/vnd.github+json"},
        params=params, timeout=15,
    ).json()


def get_work() -> dict | None:
    if not configured():
        return None
    try:
        me = _get("/user").get("login")
        review = _get("/search/issues", q=f"is:pr is:open review-requested:{me}").get("items", [])
        out = {"review_requested": [
            {"title": p["title"], "url": p["html_url"], "repo": p["repository_url"].split("/repos/")[-1]}
            for p in review[:10]
        ], "repos": []}
        for repo in [r.strip() for r in os.getenv("GITHUB_REPOS", "").split(",") if r.strip()]:
            issues = _get(f"/repos/{repo}/issues", state="open", per_page=10)
            if isinstance(issues, list):
                out["repos"].append({"repo": repo, "open_issues": [
                    {"title": i["title"], "url": i["html_url"],
                     "labels": [l["name"] for l in i.get("labels", [])]}
                    for i in issues if "pull_request" not in i
                ]})
        return out
    except Exception:
        return None
