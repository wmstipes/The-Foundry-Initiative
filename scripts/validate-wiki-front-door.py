#!/usr/bin/env python3
"""Validate the repository-owned source for the curated GitHub Wiki front door."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse


REPOSITORY_URL = "https://github.com/wmstipes/The-Foundry-Initiative"
WIKI_HOME_URL = f"{REPOSITORY_URL}/wiki"
EXPECTED_WIKI_FILES = {"Home.md", "_Sidebar.md"}
SOURCE_NOTICE = (
    "Repository documentation is authoritative. "
    "This Wiki is a curated navigation layer only."
)
REQUIRED_HOME_LABELS = {
    "project overview",
    "current project status",
    "architecture and constraints",
    "roadmap",
    "operator runbooks",
    "milestone records",
    "project vision",
}
AMBIGUOUS_LABELS = {"click here", "here", "link", "more", "read more"}
VOLATILE_PATTERNS = {
    "container digest": re.compile(r"sha256:", re.IGNORECASE),
    "release version": re.compile(r"`v?\d+\.\d+\.\d+(?:[-+][^`]*)?`", re.IGNORECASE),
    "cluster command": re.compile(r"\bkubectl\b", re.IGNORECASE),
    "NodePort": re.compile(r"\bNodePort\b", re.IGNORECASE),
    "live Pod state": re.compile(r"\bReady Pod\b", re.IGNORECASE),
    "private IPv4 address": re.compile(
        r"\b(?:"
        r"10(?:\.\d{1,3}){3}|"
        r"127(?:\.\d{1,3}){3}|"
        r"169\.254(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
        r"192\.168(?:\.\d{1,3}){2}"
        r")\b"
    ),
}
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
RAW_URL = re.compile(r"https?://\S+", re.IGNORECASE)


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _extract_headings(text: str) -> list[tuple[int, str]]:
    return [(len(match.group(1)), match.group(2)) for match in HEADING.finditer(text)]


def _validate_headings(path: Path, text: str, repo_root: Path) -> list[str]:
    display = _relative_path(path, repo_root)
    headings = _extract_headings(text)
    errors: list[str] = []
    if not headings:
        return [f"{display}: must contain headings"]
    if headings[0][0] != 1:
        errors.append(f"{display}: first heading must be H1")
    h1_count = sum(level == 1 for level, _ in headings)
    if h1_count != 1:
        errors.append(f"{display}: expected exactly one H1, found {h1_count}")
    for previous, current in zip(headings, headings[1:]):
        if current[0] > previous[0] + 1:
            errors.append(
                f"{display}: heading level skips from H{previous[0]} to H{current[0]}"
            )
    return errors


def _repository_target(url: str) -> str | None:
    parsed = urlparse(url)
    if f"{parsed.scheme}://{parsed.netloc}" != "https://github.com":
        return None
    prefix = "/wmstipes/The-Foundry-Initiative/"
    if not parsed.path.startswith(prefix):
        return None
    suffix = unquote(parsed.path[len(prefix) :])
    for marker in ("blob/main/", "tree/main/"):
        if suffix.startswith(marker):
            return suffix[len(marker) :]
    return None


def _validate_links(path: Path, text: str, repo_root: Path) -> tuple[list[str], set[str]]:
    display = _relative_path(path, repo_root)
    errors: list[str] = []
    targets: set[str] = set()
    links = list(MARKDOWN_LINK.finditer(text))
    without_links = MARKDOWN_LINK.sub("", text)

    if RAW_URL.search(without_links):
        errors.append(f"{display}: contains a bare URL")

    for match in links:
        label = " ".join(match.group(1).split())
        url = match.group(2).strip()
        normalized_label = label.casefold()
        targets.add(url)

        if normalized_label in AMBIGUOUS_LABELS or RAW_URL.fullmatch(label):
            errors.append(f"{display}: link label is not descriptive: {label!r}")
        if not url.startswith("https://"):
            errors.append(f"{display}: link must use HTTPS: {url}")
            continue
        if "#" in url or "?" in url:
            errors.append(f"{display}: fragments and query strings are out of scope: {url}")
        if url in {REPOSITORY_URL, WIKI_HOME_URL}:
            continue
        if not url.startswith(f"{REPOSITORY_URL}/"):
            errors.append(f"{display}: external link is out of scope: {url}")
            continue
        target = _repository_target(url)
        if target is None:
            errors.append(f"{display}: unsupported repository URL shape: {url}")
            continue
        if not (repo_root / target).exists():
            errors.append(f"{display}: repository target does not exist: {target}")

    return errors, targets


def validate_front_door(repo_root: Path) -> ValidationResult:
    repo_root = repo_root.resolve()
    wiki_dir = repo_root / "docs" / "wiki"
    errors: list[str] = []

    if not wiki_dir.is_dir():
        return ValidationResult(("docs/wiki: directory is missing",))

    actual_files = {
        path.name for path in wiki_dir.iterdir() if path.is_file() and not path.name.startswith(".")
    }
    if actual_files != EXPECTED_WIKI_FILES:
        missing = sorted(EXPECTED_WIKI_FILES - actual_files)
        unexpected = sorted(actual_files - EXPECTED_WIKI_FILES)
        if missing:
            errors.append(f"docs/wiki: missing files: {', '.join(missing)}")
        if unexpected:
            errors.append(f"docs/wiki: unexpected files: {', '.join(unexpected)}")

    page_targets: dict[str, set[str]] = {}
    page_text: dict[str, str] = {}
    for name in sorted(EXPECTED_WIKI_FILES & actual_files):
        path = wiki_dir / name
        text = path.read_text(encoding="utf-8")
        page_text[name] = text
        errors.extend(_validate_headings(path, text, repo_root))
        link_errors, targets = _validate_links(path, text, repo_root)
        errors.extend(link_errors)
        page_targets[name] = targets
        for description, pattern in VOLATILE_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"docs/wiki/{name}: contains volatile {description}")

    home = page_text.get("Home.md", "")
    if SOURCE_NOTICE not in home:
        errors.append("docs/wiki/Home.md: authoritative-source notice is missing")
    home_labels = {
        " ".join(match.group(1).split()).casefold() for match in MARKDOWN_LINK.finditer(home)
    }
    missing_labels = sorted(REQUIRED_HOME_LABELS - home_labels)
    if missing_labels:
        errors.append(
            "docs/wiki/Home.md: missing required navigation labels: "
            + ", ".join(missing_labels)
        )

    home_targets = page_targets.get("Home.md", set())
    sidebar_targets = page_targets.get("_Sidebar.md", set()) - {WIKI_HOME_URL}
    missing_from_home = sorted(sidebar_targets - home_targets)
    if missing_from_home:
        errors.append(
            "docs/wiki/_Sidebar.md: destinations absent from Home.md: "
            + ", ".join(missing_from_home)
        )

    errors.extend(validate_restaurant_workflow(repo_root).errors)
    return ValidationResult(tuple(errors))


def _mapping_block(lines: list[str], key: str, indent: int) -> list[str] | None:
    prefix = " " * indent + key + ":"
    for index, line in enumerate(lines):
        if line == prefix:
            block: list[str] = []
            for candidate in lines[index + 1 :]:
                if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= indent:
                    break
                block.append(candidate)
            return block
    return None


def _list_values(lines: list[str], key: str, indent: int) -> list[str] | None:
    block = _mapping_block(lines, key, indent)
    if block is None:
        return None
    values: list[str] = []
    item_prefix = " " * (indent + 2) + "- "
    for line in block:
        if line.startswith(item_prefix):
            values.append(line[len(item_prefix) :].strip().strip('"\''))
    return values


def validate_restaurant_workflow(repo_root: Path) -> ValidationResult:
    workflow = repo_root / ".github" / "workflows" / "restaurant-api-docker.yml"
    if not workflow.is_file():
        return ValidationResult(("Restaurant API Docker workflow is missing",))
    lines = workflow.read_text(encoding="utf-8-sig").splitlines()
    errors: list[str] = []
    push = _mapping_block(lines, "push", 2)
    if push is None:
        return ValidationResult(("Restaurant API Docker workflow: push trigger is missing",))
    if _list_values(push, "branches", 4) != ["main"]:
        errors.append("Restaurant API Docker workflow: branch trigger must be exactly main")
    if _list_values(push, "tags", 4) != ["v*.*.*"]:
        errors.append("Restaurant API Docker workflow: version-tag trigger changed")
    if _list_values(push, "paths", 4) != ["apps/restaurant-api/**"]:
        errors.append(
            "Restaurant API Docker workflow: branch path filter must be exactly "
            "apps/restaurant-api/**"
        )
    if _mapping_block(lines, "workflow_dispatch", 2) is None:
        errors.append("Restaurant API Docker workflow: manual dispatch trigger is missing")
    return ValidationResult(tuple(errors))


def restaurant_workflow_should_run(
    *, event: str, ref: str = "", changed_paths: tuple[str, ...] = ()
) -> bool:
    """Model the intentionally bounded Restaurant image-publication trigger matrix."""
    if event == "workflow_dispatch":
        return True
    if event != "push":
        return False
    if ref.startswith("refs/tags/v"):
        return True
    if ref != "refs/heads/main":
        return False
    return any(path.startswith("apps/restaurant-api/") for path in changed_paths)


def compare_wiki_copy(repo_root: Path, wiki_dir: Path) -> ValidationResult:
    source_dir = repo_root.resolve() / "docs" / "wiki"
    wiki_dir = wiki_dir.resolve()
    errors: list[str] = []
    if not wiki_dir.is_dir():
        return ValidationResult((f"Wiki checkout is missing: {wiki_dir}",))
    actual = {
        path.name for path in wiki_dir.iterdir() if path.is_file() and not path.name.startswith(".")
    }
    if actual != EXPECTED_WIKI_FILES:
        errors.append(
            "Wiki checkout must contain exactly Home.md and _Sidebar.md; found: "
            + ", ".join(sorted(actual))
        )
    for name in sorted(EXPECTED_WIKI_FILES & actual):
        if (source_dir / name).read_bytes() != (wiki_dir / name).read_bytes():
            errors.append(f"Wiki checkout differs from repository source: {name}")
    return ValidationResult(tuple(errors))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root; defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--wiki-dir",
        type=Path,
        help="Optional cloned Wiki directory to compare byte-for-byte with docs/wiki.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = validate_front_door(args.repo_root)
    errors = list(result.errors)
    if args.wiki_dir is not None:
        errors.extend(compare_wiki_copy(args.repo_root, args.wiki_dir).errors)
    if errors:
        print("Wiki front-door validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Wiki front-door validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
