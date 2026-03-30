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
def get_tab_image(tab_id: str) -> dict:
    """Return the public image URL for a tab screenshot."""
    tab = _find_tab(tab_id)
    return {
        "tab_id": tab_id,
        "image_url": f"/public/guide/{tab['image']}"
    }

@mcp.tool()
def search_ui(query: str) -> list[dict]:
    """Search tabs and sections by text."""
    q = query.lower()
    matches = []
    for tab in DATA["tabs"]:
        hay = f"{tab['title']} {tab['description']}".lower()
        if q in hay:
            matches.append({"type": "tab", "id": tab["id"], "title": tab["title"]})
        for section in tab.get("sections", []):
            shay = f"{section['title']} {section['description']}".lower()
            if q in shay:
                matches.append({
                    "type": "section",
                    "tab_id": tab["id"],
                    "id": section["id"],
                    "title": section["title"],
                })
    return matches

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()