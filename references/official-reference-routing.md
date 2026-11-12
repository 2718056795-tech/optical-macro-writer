# 官方资料离线取证与语法冻结

## 目的

完整版 skill 将官方资料放在 `references/official/` 内。它们用于回答“这个完整命令组合是否有官方证据”，不是让宏依赖资料文件运行。生成的宏不得写入这些资料路径。

内置的 `codev-macro-plus.md` 与 `zemax-macros.md` 是能力地图和工程规范，不可能逐字覆盖所有官方命令。遇到陌生、高风险或版本敏感功能时，必须回查本目录中的原始资料。

## 相对目录

```text
references/official/
├── codev/
│   ├── docs/         官方PDF
│   ├── docs-text/    PDF提取文本，供全文检索
│   └── macros/       官方示例宏
└── zemax/
    ├── docs/         已提供的OpticStudio/Zemax资料
    ├── docs-text/    PDF提取文本
    └── examples/     已提供的ZPL补充示例，来源身份见资料清单
```

目录可能因精简安装而缺失。不得把任何电脑上的 `C:\...`、`D:\...` 路径写入 skill、宏或回答；始终从当前 `SKILL.md` 所在文件夹解析相对路径。

先读 `references/official-corpus-manifest.md` 区分 CODE V 官方资料、Zemax 手册和仅作补充的用户示例，不能把所有随包文件笼统称为官方示例。

## 检索命令

从 skill 根目录运行：

```powershell
python scripts/search_official_references.py "BUF COP" --domain codev
python scripts/search_official_references.py "DEL CMP" --domain codev --kind manual
python scripts/search_official_references.py "BTX S" --domain codev --kind example
python scripts/search_official_references.py "QUICKSENSITIVITY" --domain zemax
```

默认进行不区分大小写、连续空白归一化的字面检索，并显示相对文件名、行号和上下文。需要跨行或更复杂的形式时缩短关键词，或增加 `--regex` 使用正则表达式。

如果脚本返回“官方资料目录不存在”，说明当前是精简版。此时只能使用内置参考、用户提供的目标版本资料或官方在线帮助，不得把记忆写法提升为官方证据。

## 取证顺序

对每一个非平凡命令块按以下顺序取证：

1. **目标版本实机成功记录**：相同命令形态、上下文和限定符已经运行成功。
2. **官方同形示例**：示例中完整出现相同命令、限定符顺序和命令模式。
3. **官方手册完整语法**：手册明确列出完整形式，并且当前用法没有自行拼接额外限定符。
4. **内置参考**：用于定位能力和设计结构，不单独证明冷门签名。
5. **推断**：只能作为最小探针候选，不能进入声称稳定的交付宏。

同一个关键字在不同模式中的语义可能不同。例如立即命令、`TOR`块、`LIB`块、数据库项、函数参数和GUI元数据不能互相替代取证。

## CODE V检索方法

先搜索最窄的完整结构，再逐步放宽：

```text
"BUF COP B0"
"DEL CMP T1"
"BTY S2..4"
"FRE" + "SNS" + "CHT"
"TYP DEC"
```

除正向示例外，还要搜索命令附近的以下词：

```text
fatal
invalid
ignored
not supported
avoid
warning
```

官方示例中的注释同样是证据，尤其是单配置、多重结构、特殊面、buffer、公差和文件清理限制。

对输出文本解析，手册只能证明典型布局。仍需在目标版本保存原始B0或分析文本，核对关键词、行列、块数、单位和数值范围。不能把固定偏移当成跨版本API。

## Zemax检索方法

ZPL关键字和操作数先查随包手册文本，再在目标OpticStudio中启用 **Check Obsolete Syntax**。分析向量、操作数参数、Macro Solve和ZPLM必须按当前版本帮助核对。

ZOS-API的连接代码、程序集位置、枚举、分析设置和结果对象以目标电脑当前版本为准：

1. 使用 Application Builder生成连接骨架。
2. 在 Programming/Syntax Help中确认对象和枚举。
3. 一次只打开一个Tool，分析和Tool均在 `finally` 中关闭。
4. Python能解析只达到L1，不证明接口存在。

随包旧版资料可以帮助定位概念，但不能覆盖当前安装版本。

## 语法冻结记录

复杂宏在实现阶段维护一张简短证据表：

```text
功能块 | 完整命令或接口 | 证据等级 | 精确来源 | 目标版本状态
输入   | RFD ...         | B/C      | 包内相对文件:行号或PDF页码 | 未编译
分析   | TOR...GO        | A/B      | 实机日志或示例文件:行号   | 已运行
解析   | B0关键词与列号   | A        | 原始输出文件:行号          | 已核对
```

“官方手册”“官方示例”不是足够精确的来源字段。B/C 级证据必须记录包内相对文件名以及检索返回的行号；同时能取得 PDF 页码时一并记录。A 级证据必须记录目标软件版本、最小调用命令和原始成功输出。这样复制到另一台电脑后才能独立复核，而不依赖原电脑的目录索引或对话记忆。

证据表可保留在工作记录中，不必写进最终宏。宏文件头只标明实际达到的 L0-L4 等级、关键假设和证据表位置。

## 不得做的事

- 不因官方手册分别列出多个限定符，就自行组合手册未展示的复合命令。
- 不把用户宏当作官方语法证据；用户宏只能作为待验证候选或目标版本实机证据。
- 不把检查器“没有报错”表述为软件编译通过。
- 不复制整段官方文档到回答中；只提炼必要规则，保留包内资料供核对。
- 不因资料随包携带就假设目标电脑有相同许可证、玻璃库、模板、内部宏或API版本。
