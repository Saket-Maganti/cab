from __future__ import annotations

from typing import Any

from causal_agent_bench.tools.base import BaseTool


def _snapshot(state: dict[str, Any]) -> dict[str, Any]:
    site = state.get("knowledge_base", {}).get("web_snapshot")
    if not site:
        raise ValueError("web_snapshot missing from knowledge_base")
    return site


def _pages(state: dict[str, Any]) -> dict[str, Any]:
    return _snapshot(state)["pages"]


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("/"):
        url = f"/{url}"
    return url.rstrip("/") or "/"


def _visited(state: dict[str, Any]) -> set[str]:
    visited = state.setdefault("web_visited_urls", set())
    if isinstance(visited, list):
        visited = set(visited)
        state["web_visited_urls"] = visited
    return visited


def _current_url(state: dict[str, Any]) -> str:
    return _normalize_url(str(state.get("current_url") or _snapshot(state).get("start_url", "/")))


def _page_payload(page: dict[str, Any], *, include_hidden_links: bool = False) -> dict[str, Any]:
    links = list(page.get("links", []))
    sections = page.get("sections", {})
    for section in sections.values():
        parent = section.get("reveal_link_on_parent")
        if parent and include_hidden_links:
            links.append({"href": page["url"], "text": f"Section: {section.get('heading', 'detail')}"})
    visible_sections = [
        key
        for key, section in sections.items()
        if section.get("visible", True) and not section.get("requires_visited")
    ]
    return {
        "url": page["url"],
        "title": page["title"],
        "body": page["body"],
        "links": links,
        "visible_section_ids": visible_sections,
        "frozen_at": page.get("frozen_at"),
    }


def _section_visible(section: dict[str, Any], visited: set[str]) -> bool:
    if section.get("visible", True) and not section.get("requires_visited"):
        return True
    required = section.get("requires_visited") or []
    return all(_normalize_url(url) in visited for url in required)


class WebOpenPageTool(BaseTool):
    name = "web_open_page"
    description = "Open a static frozen HTML page from the local web snapshot (no live network)."
    input_schema = {
        "type": "object",
        "required": ["url"],
        "properties": {"url": {"type": "string"}},
    }
    output_schema = {
        "type": "object",
        "required": ["url", "title", "body", "links"],
        "properties": {
            "url": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string"},
            "links": {"type": "array"},
        },
    }

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        url = _normalize_url(str(arguments["url"]))
        patch = state.get("tool_output_patch", {})
        if state.get("web_intervention") == "web_stale_page" and patch.get("stale_page_url") == url:
            stale = patch.get("stale_content", {})
            state["current_url"] = url
            _visited(state).add(url)
            return {
                "url": url,
                "title": stale.get("title", "Archived copy"),
                "body": stale.get(
                    "body",
                    "ARCHIVED SNAPSHOT (stale): information may be outdated.",
                ),
                "links": stale.get("links", []),
                "stale": True,
            }
        pages = _pages(state)
        if url not in pages:
            raise ValueError(f"unknown snapshot url: {url}")
        page = pages[url]
        state["current_url"] = url
        _visited(state).add(url)
        payload = _page_payload(page, include_hidden_links=state.get("web_intervention") != "web_hidden_evidence")
        if state.get("web_intervention") == "web_conflicting_page" and patch.get("conflict_page_url") == url:
            payload["conflicting_observation"] = patch.get(
                "conflicting_observation",
                {"source_a": "13 months retention", "source_b": "24 months retention"},
            )
        return payload


class WebFollowLinkTool(BaseTool):
    name = "web_follow_link"
    description = "Follow a hyperlink from the current static page in the web snapshot."
    input_schema = {
        "type": "object",
        "properties": {
            "href": {"type": ["string", "null"]},
            "link_text": {"type": ["string", "null"]},
        },
    }
    output_schema = {
        "type": "object",
        "required": ["url", "title", "body", "links"],
        "properties": {
            "url": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string"},
            "links": {"type": "array"},
        },
    }

    def _missing_required(self, arguments: dict[str, Any]) -> list[str]:
        if not arguments.get("href") and not arguments.get("link_text"):
            return ["href or link_text"]
        return []

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        current = _current_url(state)
        pages = _pages(state)
        if current not in pages:
            raise ValueError(f"current url not in snapshot: {current}")
        page = pages[current]
        href = arguments.get("href")
        if href:
            target = _normalize_url(str(href))
        else:
            text = str(arguments.get("link_text", "")).lower()
            matches = [link for link in page.get("links", []) if text in str(link.get("text", "")).lower()]
            if not matches:
                raise ValueError(f"no link matching text {arguments.get('link_text')!r} on {current}")
            target = _normalize_url(str(matches[0]["href"]))

        patch = state.get("tool_output_patch", {})
        if state.get("web_intervention") == "web_broken_link" and patch.get("broken_href") == target:
            raise ValueError(f"broken link: {target} returns HTTP 404 in snapshot")

        return WebOpenPageTool()._run({"url": target}, state)


class WebSearchSnapshotTool(BaseTool):
    name = "web_search_snapshot"
    description = "Search the frozen static search index (no live web crawl)."
    input_schema = {
        "type": "object",
        "required": ["query"],
        "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}},
    }
    output_schema = {
        "type": "object",
        "required": ["results"],
        "properties": {"results": {"type": "array"}},
    }

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments["query"]).lower().strip()
        tokens = [token for token in query.split() if token]
        max_results = int(arguments.get("max_results") or 5)
        index = list(_snapshot(state).get("search_index", []))
        patch = state.get("tool_output_patch", {})
        if state.get("web_intervention") == "web_irrelevant_search_result":
            distractor = patch.get(
                "distractor_result",
                {
                    "url": "/",
                    "title": "Widget marketing blog",
                    "snippet": "Widgets are great for everyone!",
                    "score": 999,
                    "distractor": True,
                },
            )
            index = [distractor, *index]

        scored: list[dict[str, Any]] = []
        for entry in index:
            terms = [str(term).lower() for term in entry.get("query_terms", [])]
            haystack = " ".join([*terms, entry.get("title", ""), entry.get("snippet", "")]).lower()
            if not tokens or all(token in haystack for token in tokens) or any(token in haystack for token in tokens):
                scored.append(
                    {
                        "url": entry["url"],
                        "title": entry["title"],
                        "snippet": entry["snippet"],
                        "score": entry.get("score", 0),
                        "distractor": bool(entry.get("distractor")),
                    }
                )
        scored.sort(key=lambda row: row["score"], reverse=True)
        return {"results": scored[:max_results], "query": query}


class WebExtractSectionTool(BaseTool):
    name = "web_extract_section"
    description = "Extract a named section from the current static page in the web snapshot."
    input_schema = {
        "type": "object",
        "required": ["section_id"],
        "properties": {"section_id": {"type": "string"}},
    }
    output_schema = {
        "type": "object",
        "required": ["section_id", "content", "found"],
        "properties": {
            "section_id": {"type": "string"},
            "content": {"type": "string"},
            "found": {"type": "boolean"},
        },
    }

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        section_id = str(arguments["section_id"])
        current = _current_url(state)
        pages = _pages(state)
        if current not in pages:
            raise ValueError(f"current url not in snapshot: {current}")
        page = pages[current]
        section = page.get("sections", {}).get(section_id)
        if not section:
            return {"section_id": section_id, "content": "", "found": False}
        visited = _visited(state)
        if state.get("web_intervention") == "web_hidden_evidence" and patch_section_hidden(
            state, current, section_id
        ):
            return {
                "section_id": section_id,
                "content": "",
                "found": False,
                "hidden": True,
            }
        if not _section_visible(section, visited):
            return {"section_id": section_id, "content": "", "found": False, "hidden": True}
        return {
            "section_id": section_id,
            "content": section.get("content", ""),
            "found": True,
            "heading": section.get("heading"),
        }


def patch_section_hidden(state: dict[str, Any], page_url: str, section_id: str) -> bool:
    patch = state.get("tool_output_patch", {})
    hidden = patch.get("hidden_sections") or []
    return {"page": _normalize_url(page_url), "section_id": section_id} in hidden


def build_web_snapshot_tools() -> list[BaseTool]:
    return [
        WebOpenPageTool(),
        WebFollowLinkTool(),
        WebSearchSnapshotTool(),
        WebExtractSectionTool(),
    ]
