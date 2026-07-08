"""Linear GraphQL client (personal API key)."""
import os
import requests

API = "https://api.linear.app/graphql"

QUERY = """
{
  viewer {
    name
    assignedIssues(first: 15, filter: {state: {type: {nin: ["completed", "canceled"]}}}) {
      nodes { identifier title priorityLabel dueDate state { name } url }
    }
  }
  issues(first: 10, filter: {assignee: {null: true}, state: {type: {eq: "unstarted"}}},
         orderBy: updatedAt) {
    nodes { identifier title priorityLabel state { name } team { name } url }
  }
}
"""


def configured() -> bool:
    return bool(os.getenv("LINEAR_API_KEY"))


def get_work() -> dict | None:
    key = os.getenv("LINEAR_API_KEY")
    if not key:
        return None
    try:
        r = requests.post(API, json={"query": QUERY},
                          headers={"Authorization": key}, timeout=15)
        data = r.json().get("data")
        if not data:
            return None
        return {
            "assigned": data["viewer"]["assignedIssues"]["nodes"],
            "available": data["issues"]["nodes"],
        }
    except Exception:
        return None
