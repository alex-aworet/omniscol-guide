from pathlib import Path
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("omniscol-guide")

DATA = json.loads(Path("guide/site_map.json").read_text(encoding="utf-8"))

def _find_tab(tab_id: str) -> dict:
    for tab in DATA["tabs"]:
        if tab["id"] == tab_id:
            return tab
    raise ValueError(f"Unknown tab: {tab_id}")

@mcp.tool()
def list_tabs() -> list[dict]:
    """List the tabs available in the Omniscol onboarding guide."""
    return [{"id": t["id"], "title": t["title"], "route": t["route"]} for t in DATA["tabs"]]

@mcp.tool()
def get_tab_by_route(route: str) -> dict:
    """Find and return a tab by its route path."""
    for tab in DATA["tabs"]:
        if tab["route"] == route:
            return {
                "id": tab["id"],
                "title": tab["title"],
                "description": tab["description"],
                "route": tab["route"],
                "sections": tab.get("sections", []),
            }
    raise ValueError(f"No tab found for route: {route}")

@mcp.tool()
def get_tab_context(tab_id: str) -> dict:
    """Return the explanation and sections for a tab."""
    tab = _find_tab(tab_id)
    return {
        "id": tab["id"],
        "title": tab["title"],
        "description": tab["description"],
        "route": tab["route"],
        "sections": tab.get("sections", []),
    }

@mcp.tool()
def search_ui(query: str) -> list[dict]:
    """Search tabs and sections by text. Returns route, title, description, and location."""
    q = query.lower()
    matches = []
    for tab in DATA["tabs"]:
        hay = f"{tab['title']} {tab['description']}".lower()
        if q in hay:
            matches.append({
                "type": "tab",
                "id": tab["id"],
                "title": tab["title"],
                "description": tab["description"],
                "route": tab["route"],
            })
        for section in tab.get("sections", []):
            shay = f"{section['title']} {section['description']}".lower()
            if q in shay:
                matches.append({
                    "type": "section",
                    "tab_id": tab["id"],
                    "tab_title": tab["title"],
                    "tab_route": tab["route"],
                    "id": section["id"],
                    "title": section["title"],
                    "description": section["description"],
                })
    return matches

@mcp.tool()
def check_route_match(route1: str, route2: str) -> dict:
    """Compare two routes and return whether they match. Use this to determine if user is already on the target page."""
    match = route1 == route2
    return {
        "route1": route1,
        "route2": route2,
        "match": match,
        "message": f"Routes {'MATCH' if match else 'DO NOT MATCH'}"
    }

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()