#!/usr/bin/env python3
"""对 Zemax OpticStudio ZPL 文件做保守的静态检查。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def strip_comment(line: str) -> str:
    if re.match(r"^\s*REM(?:\s|$)", line, re.IGNORECASE):
        return ""
    if re.match(r"^\s*!", line):
        return ""
    in_quote = False
    for index, char in enumerate(line):
        if char == '"':
            in_quote = not in_quote
        elif char == "#" and not in_quote:
            return line[:index]
    return line


def split_arguments(body: str) -> list[str]:
    args: list[str] = []
    start = 0
    depth = 0
    in_quote = False
    for index, char in enumerate(body):
        if char == '"':
            in_quote = not in_quote
        elif not in_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                args.append(body[start:index].strip())
                start = index + 1
    args.append(body[start:].strip())
    return args


def find_calls(text: str, name: str) -> list[tuple[int, str]]:
    calls: list[tuple[int, str]] = []
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(", re.IGNORECASE)
    for match in pattern.finditer(text):
        depth = 1
        in_quote = False
        index = match.end()
        while index < len(text) and depth:
            char = text[index]
            if char == '"':
                in_quote = not in_quote
            elif not in_quote:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
            index += 1
        if depth == 0:
            line = text.count("\n", 0, match.start()) + 1
            calls.append((line, text[match.end() : index - 1]))
    return calls


def block_issues(lines: list[str]) -> list[tuple[int, str]]:
    stack: list[tuple[str, int]] = []
    issues: list[tuple[int, str]] = []
    for number, raw in enumerate(lines, 1):
        code = strip_comment(raw).strip()
        if not code:
            continue

        if re.match(r"^ENDIF\b", code, re.IGNORECASE):
            if not stack or stack[-1][0] != "IF":
                issues.append((number, "多余或错位的 ENDIF"))
            else:
                stack.pop()
            continue
        if re.match(r"^NEXT(?:\s+\w+)?\b", code, re.IGNORECASE):
            if not stack or stack[-1][0] != "FOR":
                issues.append((number, "多余或错位的 NEXT"))
            else:
                stack.pop()
            continue
        if re.match(r"^(?:ELSEIF|ELSE)\b", code, re.IGNORECASE):
            if not stack or stack[-1][0] != "IF":
                issues.append((number, "ELSE/ELSEIF 没有对应的 IF"))
            continue
        if re.match(r"^IF\b", code, re.IGNORECASE):
            single_line = bool(re.search(r"\bTHEN\s+\S", code, re.IGNORECASE))
            if not single_line:
                stack.append(("IF", number))
            continue
        if re.match(r"^FOR\b", code, re.IGNORECASE):
            stack.append(("FOR", number))

    for kind, number in stack:
        issues.append((number, f"{kind} 块没有对应的结束语句"))
    return issues


def analyze(path: Path) -> tuple[list[str], list[str]]:
    raw = path.read_bytes()
    text = None
    encoding = ""
    candidates = ["utf-8-sig", "gb18030", "cp1252"]
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or (
        raw and raw.count(b"\x00") / len(raw) > 0.1
    ):
        candidates.insert(0, "utf-16")
    for candidate in candidates:
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return ["无法识别文件编码"], []

    lines = text.splitlines()
    code_text = "\n".join(strip_comment(line) for line in lines)
    errors: list[str] = []
    warnings: list[str] = []

    if re.search(r"[A-Za-z]:\\", text):
        warnings.append(
            "发现 Windows 绝对路径；可迁移 ZPL 应使用宏参数、Zemax 路径函数或当前工作目录"
        )

    for number, issue in block_issues(lines):
        errors.append(f"第 {number} 行：{issue}")

    labels: dict[str, int] = {}
    gotos: list[tuple[str, int]] = []
    subs: dict[str, int] = {}
    gosubs: list[tuple[str, int]] = []
    sub_lines: list[int] = []
    return_lines: list[int] = []
    end_lines: list[int] = []

    for number, raw_line in enumerate(lines, 1):
        code = strip_comment(raw_line).strip()
        if not code:
            continue

        textfile_match = re.fullmatch(r"GETTEXTFILE(?:\s+(.*))?", code, re.IGNORECASE)
        if textfile_match:
            arguments = split_arguments(textfile_match.group(1) or "")
            filename = arguments[0]
            if not filename or re.fullmatch(r"\w+|[-+]?\d+(?:\.\d+)?", filename):
                errors.append(
                    f"第 {number} 行：GETTEXTFILE 第一参数是输出文件名，请用带引号的路径或字符串变量"
                )
            if len(arguments) > 4:
                errors.append(f"第 {number} 行：GETTEXTFILE 最多接受四个参数")

        if_match = re.match(r"^IF\b(.*)$", code, re.IGNORECASE)
        if if_match:
            condition = re.split(r"\bTHEN\b", if_match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
            if re.search(r"(?<![<>=!$])=(?!=)", condition):
                errors.append(
                    f"第 {number} 行：IF 条件中疑似使用赋值 =；数值比较应使用 =="
                )

        for_match = re.match(r"^FOR\s+(.+)$", code, re.IGNORECASE)
        if for_match:
            parts = split_arguments(for_match.group(1))
            equals_form = len(parts) == 3 and bool(
                re.match(
                    r"^[A-Za-z_][A-Za-z0-9_]*\s*=\s*.+$",
                    parts[0],
                    re.IGNORECASE,
                )
            )
            if len(parts) != 4 and not equals_form:
                errors.append(
                    f"第 {number} 行：FOR 应为 variable,start,stop,increment 或 variable=start,stop,increment"
                )

        label_match = re.match(r"^LABEL\s+([A-Za-z_][A-Za-z0-9_]*|\d+)\s*$", code, re.IGNORECASE)
        if label_match:
            name = label_match.group(1).lower()
            if name in labels:
                errors.append(f"第 {number} 行：LABEL {name} 与第 {labels[name]} 行重复")
            else:
                labels[name] = number
        goto_match = re.match(r"^GOTO\s+([A-Za-z_][A-Za-z0-9_]*|\d+)\b", code, re.IGNORECASE)
        if goto_match:
            gotos.append((goto_match.group(1).lower(), number))

        sub_match = re.match(r"^SUB\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", code, re.IGNORECASE)
        if sub_match:
            name = sub_match.group(1).lower()
            if name in subs:
                errors.append(f"第 {number} 行：SUB {name} 与第 {subs[name]} 行重复")
            else:
                subs[name] = number
            sub_lines.append(number)
        gosub_match = re.match(r"^GOSUB\s+([A-Za-z_][A-Za-z0-9_]*)\b", code, re.IGNORECASE)
        if gosub_match:
            gosubs.append((gosub_match.group(1).lower(), number))
        if re.match(r"^RETURN\s*$", code, re.IGNORECASE):
            return_lines.append(number)
        if re.match(r"^END\s*$", code, re.IGNORECASE):
            end_lines.append(number)

    for name, number in gotos:
        if name not in labels:
            errors.append(f"第 {number} 行：GOTO 目标 {name} 未定义")
    for name, number in gosubs:
        if name not in subs:
            errors.append(f"第 {number} 行：GOSUB 目标 {name} 未定义")
    if sub_lines:
        first_sub = min(sub_lines)
        if not any(number < first_sub for number in end_lines):
            errors.append("定义了 SUB，但主程序在首个 SUB 前没有 END")
        for name, start in subs.items():
            next_sub = min((line for line in sub_lines if line > start), default=len(lines) + 1)
            if not any(start < line < next_sub for line in return_lines):
                errors.append(f"第 {start} 行：SUB {name} 内未发现 RETURN")

    for number, body in find_calls(code_text, "OPEV"):
        count = len(split_arguments(body))
        if count != 7:
            errors.append(f"第 {number} 行：OPEV 需要 7 个参数，检测到 {count} 个")

    if re.search(
        r"^\s*PRINT\b[^\n]*\$[A-Z_][A-Z0-9_]*\s*\(",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        warnings.append("PRINT 中直接使用了字符串函数；ZPL 通常要求先赋给字符串变量再打印")

    file_output = re.search(
        r"^\s*OUTPUT\s+(?!SCREEN\b)\S+",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    )
    if file_output and not re.search(
        r"^\s*OUTPUT\s+SCREEN\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        errors.append("切换了文件输出，但未发现 OUTPUT SCREEN")

    opened = len(re.findall(r"^\s*OPEN\b", code_text, re.IGNORECASE | re.MULTILINE))
    closed = len(re.findall(r"^\s*CLOSE\s*$", code_text, re.IGNORECASE | re.MULTILINE))
    if opened > closed:
        warnings.append(f"发现 {opened} 次 OPEN，但只有 {closed} 次无参数 CLOSE")

    pairs = (
        ("SUSPENDUPDATES", "RESUMEUPDATES", "暂停了系统更新，但未恢复"),
        ("LOCKWINDOW", "UNLOCKWINDOW", "锁定了窗口，但未解锁"),
    )
    for start, end, message in pairs:
        start_count = len(
            re.findall(rf"^\s*{start}\b", code_text, re.IGNORECASE | re.MULTILINE)
        )
        end_count = len(
            re.findall(rf"^\s*{end}\b", code_text, re.IGNORECASE | re.MULTILINE)
        )
        if start_count != end_count:
            errors.append(f"{message}；{start}={start_count}, {end}={end_count}")

    solve_context = re.search(
        r"\bSOLVEBEFORESTOP\b|MACRO\s+SOLVE",
        text,
        re.IGNORECASE,
    )
    if solve_context and not re.search(r"^\s*SOLVERETURN\b", code_text, re.IGNORECASE | re.MULTILINE):
        errors.append("疑似 ZPL Macro Solve，但未发现 SOLVERETURN")
    if solve_context and re.search(
        r"^\s*(?:UPDATE|INPUT|INSERT|DELETE|GLAS|RADI|CURV|THIC|PARM|CONI|SDIA|"
        r"SET(?:SYSTEMPROPERTY|SURFACEPROPERTY|MCOPERAND|OPERAND|TOL|VAR|NSC)|"
        r"INSERTCONFIG|DELETECONFIG|INSERTMCO|DELETEMCO|INSERTMFO|DELETEMFO|"
        r"INSERTTOL|DELETETOL)\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        errors.append("Macro Solve 中发现 UPDATE、INPUT 或编辑器修改命令；可能递归或破坏求解")

    zplm_context = re.search(r"\bPV(?:EX|EY|HX|HY|PX|PY)\s*\(", code_text, re.IGNORECASE)
    if zplm_context and not re.search(r"^\s*OPTRETURN\b", code_text, re.IGNORECASE | re.MULTILINE):
        errors.append("使用了 ZPLM 参数函数，但未发现 OPTRETURN")

    for match in re.finditer(
        r"^\s*OPTRETURN\s+([+-]?\d+)\s*,",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        datafield = int(match.group(1))
        if not 0 <= datafield <= 50:
            line = code_text.count("\n", 0, match.start()) + 1
            errors.append(f"第 {line} 行：OPTRETURN datafield={datafield}，必须为 0..50")

    declared_arrays = {
        value.lower()
        for value in re.findall(
            r"^\s*DECLARE\s+([A-Za-z_][A-Za-z0-9_]*)\s*,",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    }
    released_arrays = {
        value.lower()
        for value in re.findall(
            r"^\s*RELEASE\s+([A-Za-z_][A-Za-z0-9_]*)\b",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    }
    unreleased = sorted(declared_arrays - released_arrays)
    if unreleased:
        preview = ", ".join(unreleased[:15])
        warnings.append(f"数组未显式 RELEASE：{preview}；小数组可保留，大数组建议释放")

    if re.search(r"^\s*COMMAND\b", code_text, re.IGNORECASE | re.MULTILINE):
        warnings.append("使用 COMMAND 启动外部程序；请核对等待、退出码和输入白名单")

    if re.search(r"\$TEMPFILENAME\s*\(", code_text, re.IGNORECASE) and not re.search(
        r"^\s*DELETEFILE\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        warnings.append("使用了 $TEMPFILENAME()，但未发现 DELETEFILE 清理本宏创建的临时文件")

    opened_analysis = len(
        re.findall(
            r"^\s*OPENANALYSISWINDOW\b",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    )
    closed_windows = len(
        re.findall(
            r"^\s*CLOSEWINDOW\b",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    )
    if opened_analysis > closed_windows:
        warnings.append(
            f"发现 {opened_analysis} 次 OPENANALYSISWINDOW，但只有 {closed_windows} 次 CLOSEWINDOW"
        )

    if re.search(r"^\s*RAYTRACEX?\b", code_text, re.IGNORECASE | re.MULTILINE):
        if not re.search(r"\bRAYE\s*\(", code_text, re.IGNORECASE):
            warnings.append("执行了 RAYTRACE/RAYTRACEX，但未发现 RAYE() 错误检查")
        if not re.search(r"\bRAYV\s*\(", code_text, re.IGNORECASE):
            warnings.append("执行了 RAYTRACE/RAYTRACEX，但未发现 RAYV() 渐晕检查")

    if re.search(r"^\s*SETCONFIG\b", code_text, re.IGNORECASE | re.MULTILINE):
        if not re.search(r"=\s*CONF\s*\(\s*\)", code_text, re.IGNORECASE):
            warnings.append("切换了当前配置但未发现 CONF() 状态保存；结束前应恢复原配置")

    modifying = re.search(
        r"^\s*(?:INSERT|DELETE|GLAS|RADI|CURV|THIC|PARM|CONI|SDIA|SET(?:SYSTEMPROPERTY|"
        r"SURFACEPROPERTY|MCOPERAND|OPERAND|TOL|VAR|NSC)|REMOVEVARIABLES|"
        r"INSERTCONFIG|DELETECONFIG|INSERTMCO|DELETEMCO|INSERTMFO|DELETEMFO|"
        r"INSERTTOL|DELETETOL)\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    )
    if modifying and not re.search(r"^\s*SAVELENS\b", code_text, re.IGNORECASE | re.MULTILINE):
        warnings.append("检测到镜头或编辑器修改，但未发现 SAVELENS；请确认是否有外部副本或明确不保存")

    if encoding != "utf-8-sig" and any(ord(char) > 127 for char in text):
        warnings.append(f"文件按 {encoding} 解码且含非 ASCII 字符；请在目标 OpticStudio 核对编码")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="要检查的 .ZPL 文件")
    args = parser.parse_args()

    exit_code = 0
    for path in args.files:
        print(f"[{path}]")
        if not path.is_file():
            print("ERROR: 文件不存在")
            exit_code = 2
            continue
        errors, warnings = analyze(path)
        for message in errors:
            print(f"ERROR: {message}")
        for message in warnings:
            print(f"WARN: {message}")
        if errors:
            exit_code = 2
        elif warnings and exit_code == 0:
            exit_code = 1
        if not errors and not warnings:
            print("OK: 未发现静态问题")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
