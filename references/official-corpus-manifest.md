# 随包参考资料范围与证据身份

## CODE V

`references/official/codev/docs/` 收录用户提供的 CODE V 官方说明文档，`docs-text/` 是由这些 PDF 生成的包内全文检索缓存，`macros/` 收录用户提供的 CODE V 官方示例宏。

这三部分可用于确认 Macro-PLUS、命令模式、数据库项、分析、公差、优化、buffer、文件和绘图等完整语法及上下文。官方示例证明的是其对应版本系列中的写法；目标电脑的版本、许可证、模板、目录和内部库仍需实机确认。

随包 `Macro-PLUS.pdf` 封面标明 Version 11.5（2021 年 3 月）。遇到版本差异时，对照目标 CODE V 自带帮助，实机记录保留完整的 `(CVV)` 字符串。[Keysight CODE V](https://www.keysight.com/gb/en/products/software/optical-solutions-software/optical-design-solutions/codev.html)

## Zemax OpticStudio

`references/official/zemax/docs/` 收录用户提供的 OpticStudio/Zemax 手册，`docs-text/` 是全文检索缓存。

英文主手册为 OpticStudio 2024 R2，中文主手册为 OpticStudio 19.4。引用时记录对应版本。

`references/official/zemax/examples/` 收录用户提供的 ZPL 示例作为补充案例。除非文件自身明确标明官方来源，否则这些示例不得单独提升为“官方同形示例”证据；必须再由随包手册或目标版本帮助确认。

ZOS-API 的 Application Builder、Programming Help、Syntax Help 和目标版本程序集未随包固化。连接骨架、枚举、分析设置对象、结果接口和 DLL 位置必须以目标电脑安装的 OpticStudio 为最终依据。

## 使用边界

- 参考资料仅供生成和核对宏，不是宏运行时依赖。
- 随包官方原文、全文缓存及示例依原厂许可使用。向外部仓库同步前按适用授权确定可上传范围。
- 所有检索从当前 skill 根目录解析包内相对路径。
- 不能把旧版官方示例中的固定路径、模板名、玻璃库、许可证能力或内部宏当作目标电脑必然存在的资源。
- 内置静态检查器用于拦截已知错误模式，不替代 CODE V 编译或 OpticStudio 的过时语法检查。
