# optical-macro-writer

用于编写、审查和调试 CODE V Macro-PLUS、Zemax OpticStudio ZPL 和 ZOS-API 光学宏的 Codex Skill。

将仓库目录以 `optical-macro-writer` 为名放入 Codex 用户 skills 目录，再用 `$optical-macro-writer` 调用。

- [Skill 入口](SKILL.md)
- [CODE V 编写参考](references/codev-macro-plus.md)
- [Zemax 编写参考](references/zemax-macros.md)
- [实机与数值验收](references/runtime-verification.md)

有 Python 时，从仓库根目录运行 `python scripts/validate_portable_package.py`，可检查核心文件并执行静态检查器的回归测试。实机验证需要目标版本的光学软件。

本仓库提供 Skill 核心文件。拥有许可的厂商资料可按[相对目录说明](references/official-reference-routing.md)在本地补充。
