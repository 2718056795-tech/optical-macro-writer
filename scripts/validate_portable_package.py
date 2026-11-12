#!/usr/bin/env python3
"""验证 optical-macro-writer 便携包的核心文件、官方语料和检查器。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_python(script: Path, *arguments: str) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(script), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-official",
        action="store_true",
        help="要求完整 CODE V/Zemax 随包资料存在",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    required = [
        root / "SKILL.md",
        root / "agents" / "openai.yaml",
        root / "references" / "strict-delivery.md",
        root / "references" / "runtime-verification.md",
        root / "references" / "codev-macro-plus.md",
        root / "references" / "zemax-macros.md",
        root / "references" / "official-reference-routing.md",
        root / "references" / "official-corpus-manifest.md",
        root / "scripts" / "check_codev_macro.py",
        root / "scripts" / "check_zpl_macro.py",
        root / "scripts" / "check_zosapi_python.py",
        root / "scripts" / "search_official_references.py",
        root / "scripts" / "selftest_macro_checkers.py",
        root / "assets" / "probes" / "codev-smoke.seq",
    ]
    missing = [path.relative_to(root) for path in required if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR: 缺少核心文件：{path}")
        return 2

    frontmatter = (root / "SKILL.md").read_text(encoding="utf-8-sig")
    if not frontmatter.startswith("---\n") or "\nname: optical-macro-writer\n" not in frontmatter:
        print("ERROR: SKILL.md frontmatter 不完整或 skill 名称不正确")
        return 2

    local_path_markers = {path.as_posix().casefold() for path in (root, Path.home())}
    core_text_files = [
        root / "SKILL.md",
        *(root / "references").glob("*.md"),
        *(root / "scripts").glob("*.py"),
    ]
    leaked = []
    for path in core_text_files:
        text = path.read_text(encoding="utf-8-sig")
        portable_text = text.replace("\\\\", "\\").replace("\\", "/").casefold()
        if any(marker in portable_text for marker in local_path_markers):
            leaked.append(path.relative_to(root))
    if leaked:
        for path in leaked:
            print(f"ERROR: 核心文件含当前电脑绝对路径：{path}")
        return 2

    rc, output = run_python(root / "scripts" / "selftest_macro_checkers.py")
    if rc:
        print(output.rstrip())
        print("ERROR: 宏检查器回归测试失败")
        return 2
    print("OK: 宏检查器回归测试")

    official = root / "references" / "official"
    if args.require_official:
        counts = {
            "CODE V PDF": len(list((official / "codev" / "docs").rglob("*.pdf"))),
            "CODE V PDF 文字缓存": len(
                list((official / "codev" / "docs-text").rglob("*.pdf.txt"))
            ),
            "CODE V SEQ 示例": len(
                list((official / "codev" / "macros").rglob("*.seq"))
            ),
            "Zemax PDF": len(list((official / "zemax" / "docs").rglob("*.pdf"))),
            "Zemax PDF 文字缓存": len(
                list((official / "zemax" / "docs-text").rglob("*.pdf.txt"))
            ),
            "ZPL 补充示例": len(
                list((official / "zemax" / "examples").rglob("*.zpl"))
            ),
        }
        minimums = {
            "CODE V PDF": 30,
            "CODE V PDF 文字缓存": 30,
            "CODE V SEQ 示例": 450,
            "Zemax PDF": 3,
            "Zemax PDF 文字缓存": 3,
            "ZPL 补充示例": 2,
        }
        failed = False
        for label, count in counts.items():
            print(f"{label}: {count}")
            if count < minimums[label]:
                print(f"ERROR: {label} 少于完整包最低数量 {minimums[label]}")
                failed = True
        if failed:
            return 2

        search_script = root / "scripts" / "search_official_references.py"
        probes = [
            ("CODE V", ("BUF COP", "--domain", "codev", "--max-results", "1")),
            (
                "Zemax",
                ("GETTEXTFILE", "--domain", "zemax", "--kind", "manual", "--max-results", "1"),
            ),
        ]
        for label, arguments in probes:
            rc, output = run_python(search_script, *arguments)
            if rc:
                print(output.rstrip())
                print(f"ERROR: {label} 官方资料检索探针失败")
                return 2
            print(f"OK: {label} 官方资料检索探针")

    print("OK: optical-macro-writer 便携包验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
