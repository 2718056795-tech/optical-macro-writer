#!/usr/bin/env python3
"""将目录内 PDF 提取为可检索的 UTF-8 文字缓存，保留包内相对路径。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="PDF 源目录")
    parser.add_argument("destination", type=Path, help="文字缓存目标目录")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有缓存")
    args = parser.parse_args()

    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: 缺少 pypdf，无法生成 PDF 文字缓存。", file=sys.stderr)
        return 2

    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_dir():
        print(f"ERROR: PDF 源目录不存在：{source}", file=sys.stderr)
        return 2
    destination.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(source.rglob("*.pdf"))
    converted = 0
    skipped = 0
    failed = 0
    for pdf in pdfs:
        relative = pdf.relative_to(source)
        output = destination / relative.parent / f"{relative.name}.txt"
        if output.exists() and not args.overwrite:
            skipped += 1
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            reader = PdfReader(str(pdf))
            chunks = [f"来源（包内相对路径）：{relative.as_posix()}\n"]
            for page_number, page in enumerate(reader.pages, 1):
                chunks.append(f"\n===== PAGE {page_number} =====\n")
                chunks.append(page.extract_text() or "")
                chunks.append("\n")
            temporary = output.with_suffix(output.suffix + ".tmp")
            with temporary.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write("".join(chunks))
            temporary.replace(output)
            converted += 1
            print(f"OK: {relative.as_posix()} -> {output.relative_to(destination)}")
        except Exception as exc:  # PDF 可能包含损坏对象，逐文件报告后继续。
            failed += 1
            print(f"ERROR: {relative.as_posix()}：{exc}", file=sys.stderr)

    print(
        f"完成：转换 {converted}，跳过 {skipped}，失败 {failed}，"
        f"发现 PDF {len(pdfs)}。"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
