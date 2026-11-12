#!/usr/bin/env python3
"""对 ZOS-API Python 脚本做保守的语法和生命周期静态检查。"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


def analyze(path: Path) -> tuple[list[str], list[str]]:
    raw = path.read_bytes()
    text = None
    encoding = ""
    for candidate in ("utf-8-sig", "utf-8", "gb18030", "cp1252"):
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return ["无法识别文件编码"], []

    errors: list[str] = []
    warnings: list[str] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return [f"第 {exc.lineno} 行：Python 语法错误：{exc.msg}"], []

    if re.search(r"[A-Za-z]:\\", text):
        warnings.append(
            "发现 Windows 绝对路径；可迁移 ZOS-API 脚本应从参数、配置或目标版本 Application Builder 取得路径"
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                errors.append(f"第 {node.lineno} 行：禁止 bare except: pass；资源错误会被静默吞掉")

    if re.search(
        r"['\"][^'\"]*(?:Zemax|OpticStudio)[^'\"]*\.dll['\"]",
        text,
        re.IGNORECASE,
    ):
        warnings.append("发现硬编码 OpticStudio/Zemax DLL 路径；连接代码应由目标版本 Application Builder 生成")

    if re.search(
        r"\.(?:New_Analysis|NewAnalysis)\s*\(\s*\d+\s*\)",
        text,
    ):
        warnings.append("New_Analysis 使用了整数分析编号；应使用目标版本 ZOS-API 枚举")

    opens_analysis = re.search(
        r"\.(?:New_Analysis|NewAnalysis|New_[A-Za-z0-9_]+)\s*\(",
        text,
    )
    closes_analysis = re.search(r"\.(?:Close|CloseAnalysis)\s*\(", text)
    if opens_analysis and not closes_analysis:
        warnings.append("创建了分析对象，但未发现 Close/CloseAnalysis")

    opens_tool = re.search(
        r"\.(?:OpenBatchRayTrace|OpenLocalOptimization|OpenGlobalOptimization|"
        r"OpenHammerOptimization|OpenTolerancing|OpenCreateZAR|OpenRestoreZAR|"
        r"OpenExportCAD)\s*\(",
        text,
    )
    if opens_tool and not re.search(r"\.(?:Close|Cancel)\s*\(", text):
        errors.append("打开了 ZOS-API Tool，但未发现 Close/Cancel")

    waits = re.search(r"\.(?:ApplyAndWaitForCompletion|RunAndWaitForCompletion)\s*\(", text)
    if opens_analysis and not waits:
        warnings.append("创建了分析对象，但未发现等待完成调用；请核对同步/异步生命周期")

    modifies = re.search(
        r"\.(?:InsertNewSurfaceAt|RemoveSurfaceAt|InsertNewObjectAt|RemoveObjectAt|"
        r"InsertNewOperandAt|RemoveOperandAt|MakeSolveVariable|SetSurfaceType|"
        r"ChangeType|SetSolveData)\s*\(",
        text,
    ) or re.search(
        r"\.(?:Radius|Thickness|Material|SemiDiameter|Target|Weight|IntegerValue|"
        r"DoubleValue|StringValue)\s*=",
        text,
    )
    if modifies and not re.search(r"\.(?:SaveAs|Save)\s*\(", text):
        warnings.append("检测到系统修改，但未发现 SaveAs/Save；默认应在副本上工作并明确保存策略")

    if (
        re.search(r"\.LoadFile\s*\(", text)
        and re.search(r"\.Save\s*\(", text)
        and not re.search(r"\.SaveAs\s*\(", text)
    ):
        warnings.append("装载了已有镜头后直接调用 Save；批处理默认应 SaveAs 到新路径或保持只读")

    if re.search(r"\.CloseApplication\s*\(", text):
        if re.search(r"InteractiveExtension|ConnectAsExtension", text, re.IGNORECASE):
            errors.append("Interactive Extension 脚本不应关闭用户的 OpticStudio 应用")

    creates_standalone = re.search(
        r"(?:CreateNewApplication|StandaloneApplication|Connection\.CreateNewApplication)",
        text,
        re.IGNORECASE,
    )
    if creates_standalone and not re.search(r"\.CloseApplication\s*\(", text):
        warnings.append("创建了 Standalone OpticStudio 应用，但未发现 CloseApplication")

    if re.search(r"\.ReadNextResult(?:Full)?\s*\(", text):
        if not re.search(r"\berror(?:Code)?\b", text, re.IGNORECASE):
            warnings.append("读取了批量光线结果，但未发现 errorCode/错误状态检查")
        if not re.search(r"\bvignette(?:Code)?\b", text, re.IGNORECASE):
            warnings.append("读取了批量光线结果，但未发现 vignetteCode/渐晕状态检查")

    if re.search(r"\.GetDataSeries\s*\(", text) and not re.search(
        r"\.NumberOfDataSeries\b",
        text,
    ):
        warnings.append("读取 DataSeries 前未发现 NumberOfDataSeries 数量检查")
    if re.search(r"\.GetDataGrid\s*\(", text) and not re.search(
        r"\.NumberOfDataGrids\b",
        text,
    ):
        warnings.append("读取 DataGrid 前未发现 NumberOfDataGrids 数量检查")

    if opens_tool or opens_analysis:
        if not any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(tree)):
            warnings.append("分析或工具对象未放入 try/finally；异常时可能无法释放")

    if encoding not in ("utf-8-sig", "utf-8") and any(ord(char) > 127 for char in text):
        warnings.append(f"文件按 {encoding} 解码且含非 ASCII 字符；请核对目标 Python 环境编码")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="要检查的 ZOS-API Python 文件")
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
