from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import PurePosixPath
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NOISE_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "form",
    "button",
    "input",
    "iframe",
    "footer",
    "nav",
    "aside",
}
NOISE_TOKENS = {
    "sidebar",
    "breadcrumb",
    "toc",
    "table-of-contents",
    "pagination",
    "newsletter",
    "share",
    "social",
    "cookie",
    "banner",
    "menu",
    "navbar",
    "footer",
    "header",
}
CANDIDATE_SELECTORS = (
    "article",
    "main",
    "[role='main']",
    ".article-content",
    ".post-content",
    ".entry-content",
    ".content",
    ".main-content",
    ".markdown",
    ".docs-content",
    ".theme-doc-markdown",
    "#content",
)
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
CONTAINER_TAGS = {"article", "main", "section", "div", "body"}
BLOCK_TAGS = HEADING_TAGS | {"p", "ul", "ol", "pre", "blockquote"}


@dataclass(slots=True)
class ContentBlock:
    kind: str
    text: str
    level: int = 0


@dataclass(slots=True)
class FetchResult:
    url: str
    title: str
    text_content: str
    markdown_content: str


def fetch_article(url: str, *, timeout_s: int = 20) -> FetchResult:
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=timeout_s,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and "<html" not in response.text[:1000].lower():
        return _build_plain_text_result(url, response.text)

    soup = BeautifulSoup(response.text, "html.parser")
    _remove_noise_nodes(soup)
    root = _select_content_root(soup)
    title = _extract_title(soup, root, url)
    blocks = _extract_blocks(root)

    if not blocks:
        plain_text = _clean_text(root.get_text("\n", strip=True))
        return _build_plain_text_result(url, plain_text, title=title)

    text_content = _render_txt(title=title, url=url, blocks=blocks)
    markdown_content = _render_markdown(title=title, url=url, blocks=blocks)
    return FetchResult(
        url=url,
        title=title,
        text_content=text_content,
        markdown_content=markdown_content,
    )


def guess_stem_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = PurePosixPath(parsed.path)
    candidate = path.stem or path.name
    if candidate in {"", "/", "index", "en", "docs"}:
        candidate = parsed.netloc.replace(".", "-")
    return _slugify(candidate or "fetched-article")


def _build_plain_text_result(url: str, text: str, *, title: str | None = None) -> FetchResult:
    normalized_title = title or guess_stem_from_url(url).replace("-", " ").strip().title()
    body_text = _clean_text(text)
    text_content = f"{normalized_title}\nSource: {url}\n\n{body_text}\n"
    markdown_content = f"# {normalized_title}\n\nSource: <{url}>\n\n{body_text}\n"
    return FetchResult(
        url=url,
        title=normalized_title,
        text_content=text_content,
        markdown_content=markdown_content,
    )


def _remove_noise_nodes(soup: BeautifulSoup) -> None:
    for tag in list(soup.find_all(True)):
        if getattr(tag, "parent", None) is None:
            continue

        name = (tag.name or "").lower()
        if name in NOISE_TAGS:
            tag.decompose()
            continue

        if _has_noise_token(tag):
            tag.decompose()


def _has_noise_token(tag: Tag) -> bool:
    attrs = getattr(tag, "attrs", None) or {}
    tokens: set[str] = set()
    for attr_name in ("class", "id", "aria-label"):
        raw = attrs.get(attr_name)
        if isinstance(raw, str):
            tokens.update(re.split(r"[^a-z0-9_-]+", raw.lower()))
        elif isinstance(raw, Iterable):
            for item in raw:
                tokens.update(re.split(r"[^a-z0-9_-]+", str(item).lower()))
    return any(token in NOISE_TOKENS for token in tokens if token)


def _select_content_root(soup: BeautifulSoup) -> Tag:
    candidates: list[Tag] = []
    seen: set[int] = set()

    for selector in CANDIDATE_SELECTORS:
        for node in soup.select(selector):
            node_id = id(node)
            if node_id in seen:
                continue
            seen.add(node_id)
            candidates.append(node)

    body = soup.body or soup
    candidates.append(body)
    return max(candidates, key=lambda node: len(node.get_text(" ", strip=True)))


def _extract_title(soup: BeautifulSoup, root: Tag, url: str) -> str:
    h1 = root.find("h1")
    if h1:
        text = _clean_text(h1.get_text(" ", strip=True))
        if text:
            return text

    og_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find(
        "meta", attrs={"name": "og:title"}
    )
    if og_title and og_title.get("content"):
        text = _clean_text(str(og_title["content"]))
        if text:
            return text

    if soup.title and soup.title.string:
        text = _clean_text(soup.title.string)
        if text:
            return text

    return guess_stem_from_url(url).replace("-", " ").strip().title()


def _extract_blocks(root: Tag) -> list[ContentBlock]:
    blocks = _collect_blocks(root)
    return _dedupe_blocks(blocks)


def _collect_blocks(node: Tag) -> list[ContentBlock]:
    blocks: list[ContentBlock] = []

    for child in node.children:
        if isinstance(child, NavigableString):
            continue
        if not isinstance(child, Tag):
            continue

        name = (child.name or "").lower()
        if name in HEADING_TAGS:
            text = _clean_text(child.get_text(" ", strip=True))
            if text:
                blocks.append(ContentBlock(kind="heading", text=text, level=int(name[1])))
            continue

        if name == "p":
            text = _clean_text(child.get_text(" ", strip=True))
            if text:
                blocks.append(ContentBlock(kind="paragraph", text=text))
            continue

        if name in {"ul", "ol"}:
            for li in child.find_all("li", recursive=False):
                text = _clean_text(li.get_text(" ", strip=True))
                if text:
                    blocks.append(ContentBlock(kind="list_item", text=text))
            continue

        if name == "pre":
            text = child.get_text("\n", strip=False).strip()
            if text:
                blocks.append(ContentBlock(kind="code", text=text))
            continue

        if name == "blockquote":
            text = _clean_text(child.get_text("\n", strip=True))
            if text:
                blocks.append(ContentBlock(kind="blockquote", text=text))
            continue

        if name in CONTAINER_TAGS or child.find(BLOCK_TAGS):
            blocks.extend(_collect_blocks(child))

    return blocks


def _dedupe_blocks(blocks: list[ContentBlock]) -> list[ContentBlock]:
    deduped: list[ContentBlock] = []
    previous_key: tuple[str, str, int] | None = None

    for block in blocks:
        key = (block.kind, block.text, block.level)
        if key == previous_key:
            continue
        deduped.append(block)
        previous_key = key

    return deduped


def _render_txt(*, title: str, url: str, blocks: list[ContentBlock]) -> str:
    lines = [title, f"Source: {url}", ""]

    for block in blocks:
        if block.kind == "heading":
            lines.append(block.text)
            lines.append("")
        elif block.kind == "paragraph":
            lines.append(block.text)
            lines.append("")
        elif block.kind == "list_item":
            lines.append(f"- {block.text}")
        elif block.kind == "code":
            lines.append(block.text)
            lines.append("")
        elif block.kind == "blockquote":
            lines.append(block.text)
            lines.append("")

    return _normalize_output(lines)


def _render_markdown(*, title: str, url: str, blocks: list[ContentBlock]) -> str:
    lines = [f"# {title}", "", f"Source: <{url}>", ""]

    for block in blocks:
        if block.kind == "heading":
            if block.text == title:
                continue
            level = min(max(block.level, 2), 6)
            lines.append(f"{'#' * level} {block.text}")
            lines.append("")
        elif block.kind == "paragraph":
            lines.append(block.text)
            lines.append("")
        elif block.kind == "list_item":
            lines.append(f"- {block.text}")
        elif block.kind == "code":
            lines.append("```")
            lines.append(block.text)
            lines.append("```")
            lines.append("")
        elif block.kind == "blockquote":
            for line in block.text.splitlines():
                lines.append(f"> {line}")
            lines.append("")

    return _normalize_output(lines)


def _normalize_output(lines: list[str]) -> str:
    content = "\n".join(line.rstrip() for line in lines)
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    return content + "\n"


def _clean_text(text: str) -> str:
    normalized = text.replace("\xa0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{2,}", "\n\n", normalized)
    return normalized.strip()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")
    return slug or "fetched-article"
