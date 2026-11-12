#!/usr/bin/env python3
"""在 skill 包内按相对路径检索 CODE V 与 Zemax 参考资料。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".bat",
    ".c",
    ".cfl",
    ".cfg",
    ".cpp",
    ".cs",
    ".csv",
    ".dat",
    ".env",
    ".h",
    ".idx",
    ".ini",
    ".json",
    ".len",
    ".md",
    ".pdx",
    ".py",
    ".rec",
    ".seq",
    ".sgt",
    ".stp",
    ".txt",
    ".tmp",
    ".xml",
    ".zpl",
}


def decode_text(path: Path) -> str | None:
    raw = path.read_bytes()
    encodings = ["utf-8-sig", "gb18030", "cp1252"]
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or (
        raw and raw.count(b"\x00") / len(raw) > 0.1
    ):
        encodings.insert(0, "utf-16")
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "\x00" in text and encoding != "utf-16":
            continue
        return text
    return None


def selected_roots(root: Path, domain: str, kind: str) -> list[Path]:
    domains = ("codev", "zemax") if domain == "all" else (domain,)
    paths: list[Path] = []
    for item in domains:
        domain_root = root / item
        if kind in {"all", "manual"}:
            paths.append(domain_root / "docs")
            paths.append(domain_root / "docs-text")
        if kind in {"all", "example"}:
            example_name = "macros" if item == "codev" else "examples"
            paths.append(domain_root / example_name)
    return paths


def build_matcher(query: str, regex: bool):
    if regex:
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"正则表达式无效：{exc}") from exc
        return lambda line: pattern.search(line) is not None
    folded = " ".join(query.casefold().split())
    return lambda line: folded in " ".join(line.casefold().split())


def iter_text_files(roots: list[Path]):
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="关键词或正则表达式")
    parser.add_argument(
        "--domain",
        choices=("all", "codev", "zemax"),
        default="all",
        help="资料域，默认检索全部",
    )
    parser.add_argument(
        "--kind",
        choices=("all", "manual", "example"),
        default="all",
        help="资料类型，默认检索手册文字缓存和示例",
    )
    parser.add_argument("--regex", action="store_true", help="将 query 解释为正则表达式")
    parser.add_argument(
        "--max-results",
        type=int,
        default=30,
        help="最多输出多少个命中，默认 30",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=2,
        help="每个命中前后显示多少行，默认 2",
    )
    args = parser.parse_args()

    if args.max_results < 1 or args.context < 0:
        parser.error("--max-results 必须大于 0，--context 不能小于 0")

    package_root = Path(__file__).resolve().parent.parent
    official_root = package_root / "references" / "official"
    if not official_root.is_dir():
        print(
            "ERROR: 未找到 references/official。当前包可能是轻量版，"
            "请使用包含官方资料的完整便携包。",
            file=sys.stderr,
        )
        return 2

    try:
        matches = build_matcher(args.query, args.regex)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    roots = selected_roots(official_root, args.domain, args.kind)
    result_count = 0
    scanned_count = 0
    unreadable_count = 0
    for path in iter_text_files(roots):
        scanned_count += 1
        text = decode_text(path)
        if text is None:
            unreadable_count += 1
            continue
        lines = text.splitlines()
        current_pdf_page: int | None = None
        for index, line in enumerate(lines):
            page_marker = re.match(r"^===== PAGE (\d+) =====$", line.strip())
            if page_marker:
                current_pdf_page = int(page_marker.group(1))
            if not matches(line):
                continue
            start = max(0, index - args.context)
            end = min(len(lines), index + args.context + 1)
            relative = path.relative_to(package_root)
            page_suffix = (
                f" | PDF页 {current_pdf_page}" if current_pdf_page is not None else ""
            )
            print(f"\n[{relative}:{index + 1}{page_suffix}]")
            for row in range(start, end):
                marker = ">" if row == index else " "
                print(f"{marker} {row + 1:6}: {lines[row]}")
            result_count += 1
            if result_count >= args.max_results:
                print(
                    f"\n已达到 {args.max_results} 条上限；共扫描 {scanned_count} 个文件。"
                )
                return 0

    if result_count:
        print(
            f"\n共找到 {result_count} 条，扫描 {scanned_count} 个文件，"
            f"跳过 {unreadable_count} 个不可解码文件。"
        )
        return 0

    print(
        f"未找到匹配内容；扫描 {scanned_count} 个文件，"
        f"跳过 {unreadable_count} 个不可解码文件。"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
