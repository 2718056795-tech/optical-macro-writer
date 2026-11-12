#!/usr/bin/env python3
"""对 CODE V Macro-PLUS .seq 文件做保守的静态检查。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


VAR_RE = re.compile(r"\^([A-Za-z_][A-Za-z0-9_]*)")
PARAM_RE = re.compile(r"#(\d+)")
DECL_RE = re.compile(
    r"^\s*(?:LCL|GBL|SHR)?\s*(?:NUM|STR)\s+(.+)$", re.IGNORECASE
)
STRING_RE = re.compile(r''' "[^"]*" | '[^']*' ''', re.VERBOSE)
MODE_START_RE = re.compile(r"^(TOR|MTF|LIB|UGR|UCH)\b", re.IGNORECASE)


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "!" and not in_single and not in_double:
            return line[:index]
    return line


def split_statements(code: str) -> list[str]:
    statements: list[str] = []
    start = 0
    in_single = False
    in_double = False
    for index, char in enumerate(code):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ";" and not in_single and not in_double:
            statement = code[start:index].strip()
            if statement:
                statements.append(statement)
            start = index + 1
    statement = code[start:].strip()
    if statement:
        statements.append(statement)
    return statements


def numbered_statements(lines: list[str]) -> list[tuple[int, str]]:
    statements: list[tuple[int, str]] = []
    fragments: list[str] = []
    start = 0
    for number, line in enumerate(lines, 1):
        code = strip_comment(line).strip()
        if not code:
            continue
        if not fragments:
            start = number
        if code.endswith("&"):
            fragments.append(code[:-1].rstrip())
            continue
        fragments.append(code)
        statements.extend((start, part) for part in split_statements(" ".join(fragments)))
        fragments.clear()
    if fragments:
        raise ValueError(f"第 {start} 行：文件结束前还有未完成的 & 续行")
    return statements


def rfd_count(statements: list[str]) -> int:
    for code in statements:
        if re.match(r"^RFD(?:\s|$)", code, re.IGNORECASE):
            tail = re.sub(r"^RFD\s*", "", code, flags=re.IGNORECASE)
            if not tail:
                return 0
            tokens = re.findall(r"""(?:"[^"]*"|'[^']*'|\S+)""", tail)
            return len(tokens)
    return 0


def declared_variables(lines: list[str]) -> set[str]:
    declared: set[str] = set()
    for line in lines:
        code = strip_comment(line)
        match = DECL_RE.match(code)
        if match:
            declared.update(name.lower() for name in VAR_RE.findall(match.group(1)))
        fct = re.match(r"^\s*FCT\s+@\w+\s*\((.*)\)", code, re.IGNORECASE)
        if fct:
            declared.update(name.lower() for name in VAR_RE.findall(fct.group(1)))
    return declared


def block_issues(commands: list[tuple[int, str]]) -> list[tuple[int, str]]:
    stack: list[tuple[str, int]] = []
    issues: list[tuple[int, str]] = []
    starts = {
        "IF": re.compile(r"^\s*IF\b", re.IGNORECASE),
        "FOR": re.compile(r"^\s*FOR\b", re.IGNORECASE),
        "WHILE": re.compile(r"^\s*(?:WHI|WHILE)\b", re.IGNORECASE),
        "UNTIL": re.compile(r"^\s*(?:UNT|UNTIL)\s*$", re.IGNORECASE),
        "FCT": re.compile(r"^\s*FCT\b", re.IGNORECASE),
    }
    ends = [
        ("IF", re.compile(r"^\s*END\s+IF\b", re.IGNORECASE)),
        ("FOR", re.compile(r"^\s*END\s+FOR\b", re.IGNORECASE)),
        ("WHILE", re.compile(r"^\s*END\s+(?:WHI|WHILE)\b", re.IGNORECASE)),
        ("UNTIL", re.compile(r"^\s*END\s+(?:UNT|UNTIL)\b", re.IGNORECASE)),
        ("FCT", re.compile(r"^\s*END\s+FCT\b", re.IGNORECASE)),
    ]

    for number, statement in commands:
        for kind, pattern in ends:
            if pattern.match(statement):
                if not stack:
                    issues.append((number, f"多余的 END {kind}"))
                elif stack[-1][0] != kind:
                    issues.append(
                        (number, f"END {kind} 与第 {stack[-1][1]} 行的 {stack[-1][0]} 不匹配")
                    )
                else:
                    stack.pop()
                break
        else:
            for kind, pattern in starts.items():
                if pattern.match(statement):
                    stack.append((kind, number))
                    break

    for kind, number in stack:
        issues.append((number, f"{kind} 块没有对应的结束语句"))
    return issues


def analyze(path: Path) -> tuple[list[str], list[str]]:
    raw = path.read_bytes()
    if b"ENCRYPTED" in raw.upper() or b"\x1aORA " in raw:
        return [], ["检测到官方加密序列；只能检查明文头，无法静态分析加密主体"]
    text = None
    encoding = ""
    for candidate in ("utf-8-sig", "gb18030", "cp1252"):
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return ["无法识别文件编码"], []

    lines = text.splitlines()
    try:
        command_lines = numbered_statements(lines)
    except ValueError as exc:
        return [str(exc)], []
    statements = [statement for _, statement in command_lines]
    code_text = "\n".join(statements)
    unquoted_code = STRING_RE.sub("", code_text)
    errors: list[str] = []
    warnings: list[str] = []

    params = {int(value) for value in PARAM_RE.findall(unquoted_code)}
    invalid_params = sorted(params - set(range(1, 10)))
    if invalid_params:
        shown = ", ".join(f"#{n}" for n in invalid_params)
        errors.append(f"Macro-PLUS 替换字段范围是 #1 到 #9，发现 {shown}")
    max_param = max(params.intersection(range(1, 10)), default=0)
    defaults = rfd_count(statements)
    if defaults > 9:
        errors.append(f"RFD 最多允许 9 项默认值，发现 {defaults} 项")
    if defaults < max_param:
        warnings.append(
            f"使用到 #{max_param}，RFD 有 {defaults} 项默认值。无默认值的必填项合法，请核对调用端是否传入"
        )
    gui_defaults = [
        int(value)
        for value in re.findall(
            r"^\s*!\s*ARG(\d+)\s+DEFAULT\b",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
    ]
    if gui_defaults and defaults < max(gui_defaults):
        warnings.append(
            f"存在 ARG{max(gui_defaults)} DEFAULT，但 RFD 只有 {defaults} 个默认项；GUI 注释不提供运行时默认值"
        )

    declared = declared_variables(statements)
    used = {name.lower() for name in VAR_RE.findall(unquoted_code)}
    missing = sorted(used - declared)
    if missing:
        preview = ", ".join(f"^{name}" for name in missing[:20])
        suffix = " ..." if len(missing) > 20 else ""
        warnings.append(f"可能未显式声明的变量：{preview}{suffix}")

    if re.search(r"\bSPLIT\s*\(", code_text, re.IGNORECASE):
        warnings.append(
            "使用了 SPLIT()；其可用性和返回形式需目标版本证据，跨版本输入解析优先使用 LENSTR/LOCSTR/SUBSTR"
        )
    if re.search(r"[A-Za-z]:\\", text):
        warnings.append("发现 Windows 绝对路径；可迁移宏应使用调用参数、相对路径或 CODE V 环境路径")

    for number, issue in block_issues(command_lines):
        errors.append(f"第 {number} 行：{issue}")

    labels: dict[str, int] = {}
    gotos: list[tuple[str, int]] = []
    for number, statement in command_lines:
        label_match = re.match(r"^LBL\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", statement, re.IGNORECASE)
        if label_match:
            name = label_match.group(1).lower()
            if name in labels:
                errors.append(f"第 {number} 行：标签 {label_match.group(1)} 与第 {labels[name]} 行重复")
            else:
                labels[name] = number
        goto_match = re.match(r"^GOTO\s+([A-Za-z_][A-Za-z0-9_]*)\b", statement, re.IGNORECASE)
        if goto_match:
            gotos.append((goto_match.group(1).lower(), number))
    for name, number in gotos:
        if name not in labels:
            errors.append(f"第 {number} 行：GOTO 目标 {name} 未定义")

    if re.search(r"\bRANDF\s*\(\s*\)", code_text, re.IGNORECASE):
        errors.append("RANDF 是无括号函数；使用 RANDF，不要写 RANDF()")

    if re.search(
        r"^\s*(?:CVERROR|CVWARNING)\s*\(",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        errors.append("CVERROR/CVWARNING 是函数，必须将返回值赋给数值变量")

    current_buffer: str | None = None
    for number, code in command_lines:
        if re.match(
            r"^(?:IF|ELS|ELSE|END\s+IF|FOR|END\s+FOR|WHI|WHILE|END\s+(?:WHI|WHILE)|"
            r"UNT|UNTIL|END\s+(?:UNT|UNTIL)|GOTO|LBL|RTN|IN|RUN)\b",
            code,
            re.IGNORECASE,
        ):
            current_buffer = None
        move_match = re.match(
            r"^BUF\s+MOV\s+(B(?:\d+|\^[A-Za-z_]\w*))\b",
            code,
            re.IGNORECASE,
        )
        if move_match:
            current_buffer = move_match.group(1).upper()
        copy_match = re.match(
            r"^BUF\s+COP\b(?:\s+(B(?:\d+|\^[A-Za-z_]\w*))\b)?",
            code,
            re.IGNORECASE,
        )
        if not copy_match:
            if re.match(r"^BUF\b", code, re.IGNORECASE) and not move_match:
                current_buffer = None
            continue
        source_buffer = (copy_match.group(1) or "").upper()
        if current_buffer == "B0":
            errors.append(
                f"第 {number} 行：BUF COP 的目标是当前 buffer；BUF MOV 指向 B0，会尝试写入 B0"
            )
        elif source_buffer == "B0" and current_buffer is None:
            warnings.append(
                f"第 {number} 行：BUF COP B0 前未发现明确的非 B0 目标定位；先 BUF MOV 到本宏拥有的 B1 及以上 buffer"
            )

    for index, (number, code) in enumerate(command_lines):
        command_match = MODE_START_RE.match(code)
        if not command_match:
            continue
        command = command_match.group(1).upper()
        found_terminator = False
        for _, following in command_lines[index + 1 :]:
            if re.match(r"^GO\b", following, re.IGNORECASE):
                found_terminator = True
                break
            if command == "LIB" and re.match(r"^CAN\b", following, re.IGNORECASE):
                found_terminator = True
                break
            if re.match(r"^(?:RTN|TOR|MTF|LIB|UGR|UCH)\b", following, re.IGNORECASE):
                break
        if not found_terminator:
            expected = "GO/CAN" if command == "LIB" else "GO"
            errors.append(f"第 {number} 行：{command} 命令块未发现对应 {expected}")

    if re.search(r"\bBUF\s+(?:Y|YES)\b", code_text, re.IGNORECASE):
        if not re.search(r"\bBUF\s+(?:N|NO)\b", code_text, re.IGNORECASE):
            errors.append("打开了 Buffer 输出捕获，但未发现 BUF N/NO")
        if not re.search(r"\(\s*BUF\.ON\s*\)", code_text, re.IGNORECASE):
            warnings.append("启动了 B0 捕获，请核对接管前的 (BUF.ON) 状态或调用方的捕获约定")
    if re.search(r"^\s*OUT\s+B(?:\^?\w+|\d+)\b", code_text, re.IGNORECASE | re.MULTILINE):
        warnings.append("使用 OUT Bn 捕获输出；便携宏需先在目标 CODE V 版本确认，默认应使用 BUF YES/NO")
    if re.search(r"\bBUF\s+FND\b", code_text, re.IGNORECASE):
        if not re.search(r"\(\s*BUF\.FND\s*\)", code_text, re.IGNORECASE):
            warnings.append("使用了 BUF FND，但未发现 (BUF.FND) 成功检查")
    if re.search(r"\bBUF\s+PUT\s+B0\b", code_text, re.IGNORECASE):
        errors.append("BUF PUT 不能写入输出收集 buffer B0；请使用 B1 及以上")
    if re.search(r"^BUF\s+DEL\s+B0\b", code_text, re.IGNORECASE | re.MULTILINE):
        if not re.search(r"\(\s*BUF\.EMP\s+B0\s*\)", code_text, re.IGNORECASE):
            warnings.append("清理了 B0，请确认原始内容为空、已备份或归本宏所有")
    if re.search(
        r"^\s*\^\w+\s*==\s*IC(?:\s*[+-]\s*\d+)?\s*$",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        errors.append(
            "IC 不能直接赋给普通变量；先用 BUF MOV Bn IC+偏移，再读取 (BUF.I Bn)"
        )
    if re.search(
        r"^\s*DEL\s+TOL\s+SA\s+ALL\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        warnings.append(
            "DEL TOL SA ALL 在部分实机上下文会报告 Extra data；先检查 (NUM TOL)，并优先按 T 编号删除"
        )
    if re.search(
        r"^\s*DEL\s+CMP\s+SO\.\.SI(?:\s+ALL)?\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        errors.append(
            "DEL CMP SO..SI 不是已验证的补偿器清理范围；优先检查 (NUM CMP) 并按 T 编号删除"
        )
    if re.search(
        r"^\s*DEL\s+(?:TOL|CMP)\s+T[^\r\n!]*\^",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        warnings.append(
            "公差/补偿器 T 限定符中拼接变量曾在实机出现 Invalid qualifier；改用固定 T1 循环或动态整条命令并实机验证"
        )
    if re.search(r"\(\s*POS\s+Z\^?\w+\s*\)", code_text, re.IGNORECASE):
        if not re.search(
            r"\(\s*NUM\s+Z\s*\)\s*(?:=|<>|>|<)\s*1",
            code_text,
            re.IGNORECASE,
        ):
            warnings.append(
                "查询了 (POS Z...)，但未发现 (NUM Z) 与 1 的分支保护；官方宏提示单配置时测试 POS Z1 可能致命"
            )

    in_tor = False
    for number, code in command_lines:
        mode = MODE_START_RE.match(code)
        if mode:
            in_tor = mode.group(1).upper() == "TOR"
        elif re.match(r"^(?:GO|CAN|RTN|GOTO|LBL)\b", code, re.IGNORECASE):
            in_tor = False
        if not in_tor:
            continue
        literal_frequency = re.fullmatch(
            r"FRE\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)",
            code,
            re.IGNORECASE,
        )
        if literal_frequency and float(literal_frequency.group(1)) <= 0:
            errors.append(f"第 {number} 行：TOR MTF 的 FRE 必须大于 0，单位为 cycles/mm（lp/mm）")
        variable_frequency = re.match(
            r"^FRE\s+(\^[A-Za-z_]\w*)\b",
            code,
            re.IGNORECASE,
        )
        if variable_frequency:
            variable = re.escape(variable_frequency.group(1))
            has_positive_check = re.search(
                rf"^\s*IF\b[^\r\n]*{variable}[^\r\n]*(?:<=\s*0|<\s*=\s*0|>\s*0|=\s*0)",
                code_text,
                re.IGNORECASE | re.MULTILINE,
            )
            if not has_positive_check:
                warnings.append(
                    f"第 {number} 行：动态 FRE {variable_frequency.group(1)} 未发现正值校验；还需在运行前校验截止频率"
                )

    for number, raw_line in enumerate(lines, 1):
        code = strip_comment(raw_line)
        for match in re.finditer(
            r"\bDPO\s+([\"'])(.*?)\1",
            code,
            re.IGNORECASE,
        ):
            if len(match.group(2)) > 24:
                warnings.append(
                    f"第 {number} 行：DPO 固定标签有 {len(match.group(2))} 个字符，超过官方 24 字符上限"
                )
    dynamic_dpo_names = {
        name.lower()
        for name in re.findall(
            r"^\s*DPO\s+\^([A-Za-z_]\w*)\b",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    }
    for name in sorted(dynamic_dpo_names):
        if not re.search(
            rf"\bLENSTR\s*\(\s*\^{re.escape(name)}\s*\)",
            code_text,
            re.IGNORECASE,
        ):
            warnings.append(
                f"动态 DPO 标签 ^{name} 未发现 24 字符长度检查；截断时应保留曲线唯一标识"
            )

    angular_tolerance = re.search(
        r"^\s*(?:DLA|DLB|BTX|BTY)\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    )
    if angular_tolerance and not (
        re.search(r"\bATANF\s*\(\s*1\s*\)", code_text, re.IGNORECASE)
        or re.search(r"/\s*180(?:\D|$)", code_text)
        or re.search(r"(?:\bRAD\b|弧度|度转弧度)", text, re.IGNORECASE)
    ):
        warnings.append(
            "检测到角度公差，但未发现度转弧度证据；DLA/DLB/BTX/BTY 的输入单位必须明确"
        )

    decenter_tolerance = re.search(
        r"^\s*(?:DLX|DLY|DLA|DLB|BTX|BTY|DSX|DSY)\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    )
    if decenter_tolerance and not re.search(
        r"\(\s*TYP\s+DEC\b",
        code_text,
        re.IGNORECASE,
    ):
        warnings.append(
            "建立了偏心/倾斜公差，但未发现 (TYP DEC S...) 检查；已有非 DAR 偏心面上的公差可能被忽略"
        )

    if re.search(r"\(\s*NUM\s+Z\s*\)", code_text, re.IGNORECASE):
        unqualified_zoom_reads: set[str] = set()
        for match in re.finditer(
            r"\(\s*(RDX|RDY|THI|GLA|IND)\b([^)]*)\)",
            code_text,
            re.IGNORECASE,
        ):
            if not re.search(r"\bZ(?:\^?\w+|\d+)\b", match.group(2), re.IGNORECASE):
                unqualified_zoom_reads.add(match.group(1).upper())
        if unqualified_zoom_reads:
            names = ", ".join(sorted(unqualified_zoom_reads))
            warnings.append(
                f"宏处理多重结构但以下数据库读取未带 Z 限定符：{names}；请确认它们不随结构变化"
            )

    global_names: set[str] = set()
    for line in lines:
        code = strip_comment(line)
        match = re.match(r"^\s*GBL\s+(?:NUM|STR)\s+(.+)$", code, re.IGNORECASE)
        if match:
            global_names.update(name.lower() for name in VAR_RE.findall(match.group(1)))
    if global_names and not re.search(r"^\s*DRO\s+GBL\b", code_text, re.IGNORECASE | re.MULTILINE):
        preview = ", ".join(f"^{name}" for name in sorted(global_names)[:10])
        warnings.append(f"声明了全局变量但未发现 DRO GBL：{preview}；若需跨宏保留请在文件头说明")

    if re.search(r"^\s*RPR\s+[\"']", code_text, re.IGNORECASE | re.MULTILINE):
        if not re.search(r"^\s*RPR\s*$", code_text, re.IGNORECASE | re.MULTILINE):
            warnings.append("设置了交互提示 RPR，但未发现裸 RPR 恢复默认提示")

    fixed_units = {
        int(value)
        for value in re.findall(
            r"^\s*OPE\s+\w+\s+U(\d+)\b",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    }
    if fixed_units:
        shown = ", ".join(f"U{value}" for value in sorted(fixed_units))
        warnings.append(f"使用固定文件单元 {shown}；可迁移宏优先让 OPE 为从 0 开始的 U^unit 分配单元")

    optimization_sequence = (
        re.search(
            r"^\s*@\w+\s*==",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
        and re.search(
            r"^\s*(?:WTC|GO)\b",
            code_text,
            re.IGNORECASE | re.MULTILINE,
        )
    )
    mutating = re.search(
        r"^\s*(?:INS|DEL|DEZ|SAVE|SAV|THI|RDY|GLA|WL|WTW|XAN|YAN|XOB|YOB|XRI|YRI|"
        r"DLT|DLR|DLN|DLV|DLA|DLB|DLX|DLY|DEC|TIL|BTX|BTY|DSX|DSY)\b",
        code_text,
        re.IGNORECASE | re.MULTILINE,
    )
    restores = re.search(r"^\s*RES\b", code_text, re.IGNORECASE | re.MULTILINE)
    if mutating and not restores and not optimization_sequence:
        warnings.append("检测到可能修改镜头的命令，但未发现 RES 恢复临时镜头")

    if re.search(r"^\s*OUT\s+(?:N|NO)\b", code_text, re.IGNORECASE | re.MULTILINE):
        if not re.search(r"\(\s*OUT\s*\)", code_text, re.IGNORECASE):
            warnings.append("关闭了 OUT，但未保存 (OUT)；结束时可能改变用户输出状态")
        if not re.search(r"^\s*OUT\s+(?:Y|YES)\b", code_text, re.IGNORECASE | re.MULTILINE):
            warnings.append("关闭了 OUT，但未发现 OUT Y/YES 恢复；若由调用方负责必须在文件头说明")

    if re.search(r"^\s*VER\s+(?:N|NO)\b", code_text, re.IGNORECASE | re.MULTILINE):
        if not re.search(r"\(\s*VER\s*\)", code_text, re.IGNORECASE):
            warnings.append("关闭了 VER，但未保存 (VER)；结束时可能改变用户验证状态")
        if not re.search(r"^\s*VER\s+(?:Y|YES)\b", code_text, re.IGNORECASE | re.MULTILINE):
            warnings.append("关闭了 VER，但未发现 VER Y/YES 恢复；若由调用方负责必须在文件头说明")

    if encoding != "utf-8-sig" and any(ord(char) > 127 for char in text):
        warnings.append(f"文件按 {encoding} 解码且含非 ASCII 字符；请在目标 CODE V 版本核对编码")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="要检查的 .seq 文件")
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
