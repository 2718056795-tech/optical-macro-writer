# CODE V Macro-PLUS 可迁移参考

## 目录

- 核心语法
- 官方示例的使用原则
- 版本、错误与兼容处理
- 交互输入与格式化输出
- 变量、数组、并行与函数体系
- 调试、检查与 GUI/SpecBuilder 接口
- 镜头数据库读取
- 表面与镜片扫描
- CODE V buffer 用法
- 捕获并解析分析输出
- 公差宏写法
- 可复用完整模板
- 序列文件分类
- 函数、动态命令与文件输入输出
- 绘图
- 优化序列
- 用户定义接口与高级扩展
- 状态保护与统一清理
- 多重结构和特殊系统
- 分析实现策略
- 常见风险与交付验证
- 调试清单

## 核心语法

CODE V 宏通常保存为 `.seq` 文件，使用 Macro-PLUS 语法。

常用写法：

```codev
! 注释
LCL NUM ^i ^s ^value
LCL STR ^name ^line
LCL NUM ^arr(100)
LCL STR ^names(100)

^value == 0
^name == "TEXT"

IF ^value > 0
    WRI "positive"
ELS
    WRI "not positive"
END IF

FOR ^i 1 10
    WRI ^i
END FOR

WHI ^value < 10
    ^value == ^value + 1
END WHI

GOTO done
LBL done
RTN
```

宏参数使用 `#1` 到 `#9`。`RFD` 为缺省输入定义运行时默认值，但不是引用替换字段的语法前提：必填参数或原样转交给子宏的高位参数可以没有 `RFD` 默认项。只有 `ARG...` 注释不能保证从命令行运行时获得默认值。

```codev
RFD "" 1 1
! #1 输出文件名；为空则只输出到屏幕
! #2 视场编号
! #3 波长编号
```

数值参数可直接读 `#n`。字符串、表面限定符或希望保留原始输入文本时，优先用 `RFSTR(n)`，必要时再 `STR_TO_NUM()`：

```codev
RFD "" 1
LCL STR ^filename
LCL NUM ^field

^filename == RFSTR(1)
^field == ROUNDf(ABSF(#2))
```

推荐规则：

- 在文件头区分必填参数、有 `RFD` 默认值的可选参数，以及只转交给子宏的参数。
- `RFD` 默认项少于实际使用的最高 `#n` 时，不直接判定语法错误；检查调用说明是否明确。
- 局部数值变量用 `LCL NUM`。
- 局部字符串变量用 `LCL STR`。
- 局部数组用 `LCL NUM ^arr(100)` 或 `LCL STR ^arr(100)`。
- 只有跨宏通信或函数库确实需要时才用 `GBL NUM` / `GBL STR`，临时全局量结束后用 `DRO GBL` 清理。
- 赋值通常用 `==`。
- 命令关键字尽量大写，便于阅读。
- 一行可用分号分隔多条语句；长逻辑表达式或命令可在行尾用 `&` 续行。
- 提前退出用 `RTN`。会占用资源或修改状态的宏不要从处理中间直接 `RTN`，应跳到统一清理出口。
- `STR_TO_NUM()` 会搜索并转换字符串内第一个有效数字。例如 `abcd123efg` 返回 `123`，找不到数字时返回 `0`。输入校验先验证整个字段是否符合预定格式，再转换，并单独区分合法零值和非法输入。证据见随包 `Macro-PLUS.pdf` 的 `STR_TO_NUM` 小节（手册第 137 页）。
- `SPLIT()` 在不同 CODE V 版本中的可用性和返回形式需要目标版本证据。需要跨版本解析 `1-3,5-6` 一类输入时，默认使用官方示例广泛采用的 `LENSTR`、`LOCSTR`、`SUBSTR` 和循环；只有目标版本手册或最小探针确认后才使用 `SPLIT()`。

常用逻辑、数学和字符串写法：

- 比较使用 `=`、`<>`、`<`、`<=`、`>`、`>=`；逻辑组合使用 `AND`、`OR`、`NOT`。
- 常见数学函数有 `ABSF`、`ROUNDF`、`SQRTF`、`MINF`、`MAXF`、`MODF`、`ATANF`、`TANF`、`SIGNF`。
- 常见字符串函数有 `CONCAT`、`SUBSTR`、`LOCSTR`、`LENSTR`、`UPCASE`、`LOWCASE`、`TRUNC`、`NUM_TO_STR`、`STR_TO_NUM`、`SPLIT`。
- 函数名和参数形式以目标 CODE V 版本实测为准，尤其是较新的字符串函数和返回数组的工具函数。

## 官方示例的使用原则

官方示例是本参考中 CODE V 语法、命令组合和数据库项用法的首要证据，但不能把每个历史示例的资源管理习惯原样复制到新宏。

使用规则：

1. 官方示例中实际执行的语句可用于证明该版本系列支持相应语法。
2. 同一功能有新旧多种官方写法时，新增宏优先采用显式变量声明、输入校验、`CVERROR`/`CVWARNING`、状态保存和统一清理。
3. 固定覆盖 B0、固定文件单元号、中途 `RTN`、无条件 `OUT Y` 等旧写法只作为兼容性证据，不作为默认工程模板。
4. 分析输出中的表头、列号和相对偏移属于版本相关数据结构，必须在目标版本捕获原始输出后核对。
5. 官方示例可包含依赖可选模块、内部库宏、模板、玻璃目录或许可证的调用；看到语法不等于目标安装必然具备对应资源。
6. 本 skill 只沉淀通用知识，不记录官方示例所在电脑的绝对路径、文件索引或目录依赖。

## 版本、错误与兼容处理

`(CVV)` 返回 CODE V 版本字符串。诊断时原样记录。需要比较版本时，先确认目标版本的格式，再按各数字段比较，并保留可能存在的版本后缀。例如把 `11.10` 转成小数会得到 `11.1`，造成版本排序错误。

```codev
LCL STR ^versionText

^versionText == (CVV)
WRI "CODE V version:" ^versionText
```

推荐兼容策略：

- 只有确实需要某个新命令时才做版本门槛检查。
- 版本字符串解析失败时给出明确错误，不要静默启用未知功能。
- 命令是否可用还可能受许可证和安装组件影响，版本满足不等于功能一定可运行。
- 对 UCH、特定规格函数、分析选项和数据库项做最小实机探针，再运行长宏。

官方宏广泛使用 `CVERROR()` 和 `CVWARNING()` 输出连续消息。第二个参数常以 `0` 表示消息首行、`1` 表示续行：

```codev
LCL STR ^message
LCL NUM ^status

^message == "Field qualifier is out of range."
^status == CVERROR(^message, 0)
^status == CVWARNING("The inactive zoom was skipped.", 0)
^status == CVWARNING("Results contain active zooms only.", 1)
```

不要依赖其返回值表达业务成功；用独立的 `^failed` 或 `^status` 变量控制清理和最终退出。

## 交互输入与格式化输出

自动化宏优先使用 `RFD` 参数。只有用户明确需要交互式运行时，才使用提示和读取：

```codev
LCL STR ^answer

RPR "Continue? (Y/N)"
READ ^answer
RPR

^answer == UPCASE(SUBSTR(^answer, 1, 1))
IF ^answer <> "Y"
    RTN
END IF
```

- `RPR "..."` 设置读入提示，裸 `RPR` 恢复默认提示。
- `READ` 读取交互输入；文件读取时写明 `U^unit`。
- `REA` 在部分官方宏中作为读取形式或文件打开方式的一部分出现，不能脱离完整命令上下文猜测其含义。
- 交互宏要处理空输入、大小写、取消和非法值；占用资源后取消也必须进入统一清理。

格式化输出使用 `WRI Q...`。格式串可以直接写，也可以放入字符串变量后用 `Q^format`：

```codev
LCL STR ^format

^format == "'CCC'  'DDD.5D'  'DDD.5D'"
WRI Q^format "SUR" 12.345678 -0.125
```

官方示例中的格式标记可见 `C` 字符列和 `D` 数字列，例如 `'CCC'`、`'DD.5D'`、`'DDD.5D'`。列宽和小数位应根据实际最大值设计，并用负数、大数和长材料名验证。`WRITE` 与 `WRI` 均见于官方示例；新增宏统一使用 `WRI`，减少风格分裂。

## 变量、数组、并行与函数体系

变量作用域和生命周期：

- `LCL NUM/STR`：当前宏或函数的局部量。
- `GBL NUM/STR`：跨宏共享；使用前可用 `ISGBL()` 判断，临时量结束后 `DRO GBL`。
- `SHR NUM/STR`：并行区域共享变量。共享写入需要理解锁和线程竞争；结果优先按线程分槽写数组。
- `ISLCL()`、`ISGBL()`、`ISFCT()`：判断局部变量、全局变量或函数是否存在。
- `DRO LCL/GBL/FCT`：删除变量或用户函数。函数库重新载入前可先 `DRO FCT name`。

数组支持一维、多维和显式下标范围：

```codev
LCL NUM ^vector(100)
LCL NUM ^matrix(1..20, 1..10)
LCL NUM ^offsetData(-5..5)
LCL STR ^labels(50)
```

- 下标范围按声明使用，不假设所有数组都从 0 或 1 开始。
- 开启 `BND Y` 进行边界检查；用最小和最大合法下标测试。
- 大数组只在需要期间保留；可用 `REDIMNUM` 调整数值数组。
- 矩阵、FFT 或图像处理优先调用官方数组函数，不手写未经验证的数值算法。

预定义函数按用途分为：

- 数学：`ABSF`、`ACOSF`、`ASINF`、`ATANF`、`ATAN2F`、`COSF`、`SINF`、`TANF`、`EXPF`、`LOGF`、`LOG10F`、`SQRTF`、`MINF`、`MAXF`、`MODF`、`RANDF`、`ROUNDF`、`SIGNF`、`GAUSSWTS`。
- 光学：`ABCD`、`BESTSPH`、`CNVTFIELD`、`GAUSSBEAM`、`INDEX`、`MTF_1FLD`、`PSF_1FLD`、`PSF_DATA_1FLD`、`RAYPOL`、`RAYRSI`、`RAYSIN`、`RAYTRA`、`RMSSPOT`、`RMSWE`、`RMS_1FLD`、`SAGF`、`SASF`、`SDERIVF`、`SPOTDATA`、`TRA_1FLD`、`TRANSFORM`。
- Zernike/拟合：`ZERNIKE`、`ZERNIKEGQ`、`ZFRCOEF`、`ZFRFIT`、`ZRNFIT`、`EVALZERN`、`FITERROR`、`NORMRADIUS`。
- 数组和线性代数：`ARRAY_TO_BUFFER`、`BUFFER_TO_ARRAY`、`ArrayAdd`、`ArraySubtract`、`ArrayScale`、`ArrayElementMultiply`、`ArrayElementDivide`、`ArrayMatrixMultiply`、`ArrayMatrixPseudoInverse`、`ArrayTranspose`、`FFT`、`SVD`、`STDEV`、`SUMF`。
- 图像仿真：`ImageFromArray`、`ImageToArray` 及 `ImageMD...` 系列。
- 字符串：`CONCAT`、`FIND_STR_ARR`、`JOIN`、`LENSTR`、`LOCSTR`、`LOWCASE`、`NUM_TO_STR`、`RFSTR`、`SPLIT`、`STR_TO_NUM`、`SUBSTR`、`TRUNC`、`UPCASE`。
- 文件与消息：`EOFILE`、`CVERROR`、`CVWARNING`、`CVPUTREC`。
- 并行：`THREADNUM`、`INPARALLEL`。

这些名称表示能力范围，不表示所有函数可互换。正式使用前必须核对参数维度、返回数组形状、单位、状态副作用以及目标版本。

## 调试、检查与 GUI/SpecBuilder 接口

开发和回归阶段建议：

```codev
CHK Y
BND Y
VER CTL Y
VER IO Y
LVR LCL
```

- `CHK Y` 强制变量显式声明，可抓出拼写造成的隐式变量。
- `BND Y` 开启数组边界检查。
- `VER COM/CTL/FCT/IO/MAC/SEQ/ALL` 控制不同类别的执行回显；保存原 `(VER)` 状态并恢复。
- `VER LCK Y` 可辅助发现共享变量相关问题。
- `LVR GBL/LCL/FCT` 列出变量或函数。
- `EVA expression` 适合在命令行交互检查表达式和数据库项。

GUI 参数元数据使用 `ARGn NAME/TYPE/DEFAULT/CHOICE/HELP`。类型可包括数值、整数、字符串和 literal；它只描述 Macro Manager 界面，命令行默认值仍由 `RFD` 决定。

SpecBuilder 宏使用 `STV value_one [value_two]` 返回规格值。此类宏必须确认调用环境和返回单位；不能只用 `WRI` 代替 `STV`，也不能残留全局变量、buffer、临时镜头或输出状态。

## 镜头数据库读取

使用括号表达式读取当前镜头数据：

- 表面总数：`(NUM S)`
- 波长数量：`(NUM W)`
- 视场数量：`(NUM F)`
- 光阑面：`(STO)`
- 曲率半径：`(RDY S^s)`
- 表面后的厚度：`(THI S^s)`
- 表面后的材料名：`(GLA S^s)`
- 材料目录名：`(GLA S^s CAT)`
- 表面后的折射率：`(IND S^s)`
- 表面模式：`(RMD S^s)`，普通折射面常为 `"REFR"`。
- 表面类型：`(TYP SUR S^s)`，例如球面、非球面、坐标断点或用户面。
- 当前系统长度单位：`(DIM)`
- 视场类型：`(TYP FLD)`，常见为 `"ANG"`、`"OBJ"`、`"IMG"`、`"RIH"`。
- 变焦位置是否启用：`(POS Z^z)`
- 边缘光线高度：`(HMY S^s W^w Z^z)`
- 边缘光线斜率：`(UMY S^s W^w Z^z)`
- 主光线入射角：`(ICY S^s W^w Z^z)`

解释规则：

- `(GLA S^s)` 表示第 `s` 面之后的介质材料。
- `(THI S^s)` 表示第 `s` 面之后的轴向间隔。
- 一般可用 `ABSF((IND S^s)) > 1.01` 判断第 `s` 面之后是否进入玻璃。
- 普通镜头数据扫描通常从 `S1` 到 `(NUM S)-1`，避免把像面当成镜片前表面。
- 计算曲率时用 `1 / RDY`；平面或无穷半径按 0 处理，阈值需按任务说明。
- 反射、全反射、HLM/HL2、GRIN、NSS、坐标断点和特殊面不能只靠折射率判断；遇到这些系统必须同时检查 `RMD`、`TYP SUR` 和任务定义。
- 不要把“半径绝对值很大”擅自当作应排除的平板或虚拟面。只有用户的物理定义要求时才过滤。

## 表面与镜片扫描

### 每种玻璃区域输出一行

这种方式最适合胶合镜片，因为每个材料区域都会单独输出。

```codev
LCL NUM ^s ^lens ^r1 ^r2 ^ct ^c1 ^c2
LCL STR ^glass ^mode

^lens == 0
WRI "Lens FrontS RearS RadiusFront RadiusRear Thickness Material CurvFront CurvRear"

FOR ^s 1 ((NUM S)-1)
    ^glass == (GLA S^s)
    ^mode == (RMD S^s)

    IF (^mode = "REFR") AND (ABSF((IND S^s)) > 1.01)
        ^lens == ^lens + 1
        ^r1 == (RDY S^s)
        ^r2 == (RDY S^s+1)
        ^ct == (THI S^s)

        ^c1 == 0
        IF ABSF(^r1) > 1E-20
            ^c1 == 1/^r1
        END IF

        ^c2 == 0
        IF ABSF(^r2) > 1E-20
            ^c2 == 1/^r2
        END IF

        WRI ^lens ^s (^s+1) ^r1 ^r2 ^ct ^glass ^c1 ^c2
    END IF
END FOR
```

### 连续玻璃组输出一行

这种方式会把连续玻璃区域合并，可能把胶合双胶合并成一个物理组。只有用户明确想按物理组统计时才使用。

```codev
LCL NUM ^front ^back ^element

^element == 0
^front == 1

WHI ^front < (NUM S)
    WHI ABSF((IND S^front)) = 1
        ^front == ^front + 1
        IF ^front = (NUM S)
            GOTO done
        END IF
    END WHI

    ^back == ^front
    WHI ABSF((IND S^back)) <> 1
        ^back == ^back + 1
    END WHI

    ^element == ^element + 1
    WRI ^element ^front ^back (RDY S^front) (RDY S^back) (GLA S^front)

    ^front == ^back
END WHI

LBL done
```

## CODE V buffer 用法

buffer 适合做三件事：捕获分析输出、读取外部文本表格、生成临时命令文件。

常用命令和函数：

- 清空：`BUF DEL B^b`
- 复制或转置：`BUF COP B^b ... [TRN] [VAL|FMT]`
- 比较差异：`BUF DIF B^b ...`
- 写入：`BUF PUT B^b ...`
- 导入文本：`BUF IMP B^b filename`
- 导出文本：`BUF EXP B^b filename`
- 查找文本：`BUF FND B^b "keyword"`
- 插入行列：`BUF INS B^b ...`
- 移动指针：`BUF MOV B^b I^i J^j`
- 重新解析文本行：`BUF PRS ...`
- 保存和恢复工作表：`BUF SAV`、`BUF RES`
- 排序：`BUF SRT ... ASC|DES`
- 最后一行：`(BUF.LST B^b)`
- 读取字符串：`(BUF.STR B^b I^i J^j)`
- 读取数字：`(BUF.NUM B^b I^i J^j)`
- 单元格类型：`(BUF.TYP B^b I^i J^j)`
- buffer 是否为空：`(BUF.EMP B^b)`
- 指定行的最后一列：`(BUF.COL B^b I^i)`
- 最近一次查找是否成功：`(BUF.FND)`
- 当前 buffer、行、列：`(BUF.B)`、`(BUF.I)`、`(BUF.J)`
- 第一行和最大列：`(BUF.FST B^b)`、`(BUF.MXJ B^b)`
- 输出捕获状态：`(BUF.ON)`
- 整行格式化文本：`(BUF.TXT B^b I^i)`
- 设置显示/导出格式：`BUF FMT B^b ...`
- 设置分隔符：`BUF SEP "..."`，使用后执行 `BUF SEP` 恢复默认值。
- 列出内容：`BUF LIS NOL B^b`

注意两类写法：

- B0 是标准输出收集 buffer；`BUF YES` 捕获的文本追加到 B0。
- 官方手册明确 `BUF PUT` 不允许写 B0。构造表格时使用 B1 及以上的自有 buffer。
- `BUF COP` 的源是命令后面的 buffer，目标是当前 buffer 指针所在位置。备份 B0 时应先把当前指针移到 B1 及以上，再执行 `BUF COP B0`；反向写法会尝试写 B0。
- `(BUF.LEN)` 返回 B0 容量。达到上限时旧行可滚出，按 `(BUF.FST B0)` 到 `(BUF.LST B0)` 访问有效范围。预计输出超过容量时先缩小批次，或在记录并恢复原容量的前提下设置 `BUF LEN`。`VER` 和 `ECH` 会影响实际捕获内容。
- B1 及以上用于自建工作表、导入、排序、矩阵和临时命令数据。
- `B0`、`B1` 这种固定 buffer 名常见于官方示例，但用途不同，不能互换。
- `B^b` 这种变量 buffer 写法适合模板，但如果当前 CODE V 版本或命令不接受变量 buffer 号，应改成固定 `B0` / `B1`。
- `BUF FND` 命中后读取当前 buffer 附近数据时，常见示例写法是 `(BUF.NUM ic+6 jc+4)`，即直接用当前 buffer 的命中行列。
- `IC`、`JC` 是当前单元格行列；`IL`、`JL` 常用于最后一行/列位置。依赖这些隐式位置前必须先执行明确的 `BUF MOV` 或成功的 `BUF FND`。
- 临时 buffer 优先动态寻找空号，并立即写入占位单元格，防止后续再次分配到同一 buffer。

显式写入带类型的单元格。下例仅在 B1 为空时占用它，写入字符串与数字时分别传入参数：

```codev
IF (BUF.EMP B1)
    BUF PUT B1 I1 J1 "Frequency" "Tangential" "Sagittal"
    BUF PUT B1 I2 J1 100 0.421 0.386
    IF (BUF.TYP B1 I2 J2) = "NUM"
        WRI "Tangential at 100 =" (BUF.NUM B1 I2 J2)
    END IF
    BUF DEL B1
ELS
    WRI "B1 already in use."
END IF
```

## 捕获并解析分析输出

先确认调用方未开启捕获且 B0 为空，再用 `BUF YES` / `BUF NO` 捕获本次分析。若 `(BUF.ON)` 为真，独立宏应在接管前退出，避免关掉调用方的捕获或把诊断输出混进 B0。命令回显也可能进入调用方 B0，需保持原内容时应在执行 `IN` 前先检查会话状态。下例是单结构 MTF 的诊断骨架。关键字、相对偏移和预期块数用目标版本的原始输出确认，`mtfvsfld.seq` 的 `DIFFRACTION LIMIT` 附近可作对照。

```codev
LCL NUM ^i ^numfld ^freq ^first ^last ^row ^previous

IF (BUF.ON)
    RTN
END IF
IF NOT (BUF.EMP B0)
    WRI "B0 already in use."
    RTN
END IF
IF (NUM Z) > 1
    WRI "This example requires one configuration."
    RTN
END IF

^numfld == (NUM F)
^freq == 100
IF ^numfld < 1
    WRI "No field available."
    RTN
END IF

BUF YES
MTF
MFR ^freq
GO
BUF NO

IF (BUF.EMP B0)
    WRI "No output captured."
    RTN
END IF
^first == (BUF.FST B0)
^last == (BUF.LST B0)
^previous == ^first - 1
BUF MOV B0 I^first J1
BUF FND B0 "DIFFRACTION LIMIT"

FOR ^i 1 ^numfld
    IF NOT (BUF.FND)
        WRI "MTF header missing. See B0."
        RTN
    END IF
    ^row == (BUF.I B0)
    IF (^row <= ^previous) OR (^row + 6 > ^last)
        WRI "MTF output incomplete. See B0."
        RTN
    END IF
    ^previous == ^row
    IF (BUF.TYP B0 IC+6 JC+4) <> "NUM"
        WRI "MTF numeric cell missing. See B0."
        RTN
    END IF
    WRI "MTF diagnostic:" ^i (BUF.NUM B0 IC+6 JC+4)
    IF ^i < ^numfld
        BUF FND
    END IF
END FOR

BUF DEL B0
```

关键点：

- `BUF YES` 开始把后续命令输出写入默认输出 buffer。
- `BUF NO` 结束捕获。
- `BUF MOV B0 I^first J1` 可把查找起点移回第一个有效行。
- `BUF FND B0 "keyword"` 查找第一次出现；后续 `BUF FND` 通常继续找下一次。
- `BUF FND` 命中后，`ic` 和 `jc` 可作为当前命中位置的行列坐标。
- 用 `(BUF.NUM ic+行偏移 jc+列偏移)` 或 `(BUF.STR ic+行偏移 jc+列偏移)` 读取当前 buffer 的相对位置。
- 每次首次查找和循环中的下一次查找都检查 `(BUF.FND)`；读取数字前检查 `(BUF.TYP ...) = "NUM"`。
- 正式结果先暂存，校对预期块数、字段标识和频率后统一输出。解析失败保留原始 B0，并给出失败状态。

默认使用经官方手册明确说明的 `BUF YES` / `BUF NO`。若 B0 非空，按调用契约选择退出或经允许备份后继续。`OUT B^b` 只在目标版本已有直接证据时采用。

备份 B0 的方向必须如下：

```codev
! ^backup 是本宏已确认归属的 B1 或更高编号，且目标区可写。
BUF MOV B^backup I1 J1
BUF COP B0
BUF DEL B0
```

不要先执行 `BUF MOV B0 ...` 再 `BUF COP B^backup`，因为 `BUF COP` 会写入当前 buffer，而 B0 不能作为复制目标。分析结束后不能靠单元格复制把内容写回 B0；应保留备份 buffer，并向用户报告其编号或按用户授权导出到文件。

解析 MTF、畸变、光线、CRA、公差输出时：

- 先找稳定表头或关键词，例如频率、视场、波长、指标名。
- 再读取关键词附近的相对行列。
- 在最终宏里保留一个可选诊断参数，用来输出 buffer 原始文本或命中行列。
- 如果用户反馈数值不对，要让用户贴出捕获到的原始 buffer 文本。
- 初版可以保留诊断 `WRI`；最终版再删掉或用参数控制。

## 公差宏写法

只有用户明确要求重新生成公差时，才清空已有公差。官方公差手册列出 `DEL TOL Tk` 和 `DEL CMP Tk`；兼容性较好的做法是持续删除列表首项，让后续项目自动重新编号：

```codev
LCL NUM ^before ^guard

^guard == 0
WHI (NUM TOL) > 0
    ^before == (NUM TOL)
    DEL TOL T1
    ^guard == ^guard + 1
    IF ((NUM TOL) >= ^before) OR (^guard > 10000)
        ! 转入失败清理，避免无限循环
        GOTO cleanup_error
    END IF
END WHI

^guard == 0
WHI (NUM CMP) > 0
    ^before == (NUM CMP)
    DEL CMP T1
    ^guard == ^guard + 1
    IF ((NUM CMP) >= ^before) OR (^guard > 10000)
        GOTO cleanup_error
    END IF
END WHI
```

`DEL TOL SA ALL` 虽可在部分官方示例中找到，但已在目标实机上下文出现 `Extra data 'ALL' ignored`。除非同版本、同命令模式已验证，否则不要把它作为通用清理模板。

常用公差类型按作用对象区分：

- 厚度：`DLT S1..^surf_num V ^val`
- 曲率半径或半径增量：`DLR S1..^surf_num V ^val`
- 面形：`RSE S1..^surf_num C0 V ^val 1E-006`
- 折射率：`DLN S1..^surf_num V ^val`
- 阿贝数：`DLV S1..^surf_num V ^val`
- 单表面 X/Y 偏心：`DLX` / `DLY`
- 单表面 X/Y 倾斜：`DLA` / `DLB`
- 元件或表面组 X/Y 偏心：`DSX` / `DSY`
- 元件或表面组 X/Y 倾斜：`BTX` / `BTY`

不要用自造的通用 `DEC` / `TIL` 代替上述 CODE V 公差类型。完整限定符顺序、`V`、`F` 等选项必须从目标版本公差手册或同上下文官方宏复制。

常用单位换算：

```codev
^mm == ^um / 1000
^deg == ^min / 60
^rad == ^deg / 180 * 3.141592653589793
```

线性偏心值使用镜头当前长度单位；如果用户固定以 mm 输入，应根据 `(DIM)` 对 mm、cm、inch 做转换。`DLA`、`DLB`、`BTX`、`BTY` 等角度公差以弧度为工程基准，用户以度输入时先乘 `ATANF(1)*4/180`。不要把“度”直接交给角度公差命令。

官方 `PERTURB` 宏和公差手册还提示：若表面已有非 DAR 类型的偏心/倾斜，相关表面或组公差可能被忽略。建立公差前检查 `(TYP DEC S^s)`；常见需特别处理的类型包括 `DDA`、`BEN`、`REV`、`RET`、`ARR`、`EAR`。不能在未检查的情况下把“命令执行成功”解释为“该公差实际生效”。

## 可复用完整模板

### 模板：镜片材料、曲率、厚度表

```codev
! 输出每片镜片的材料、前后表面曲率半径和中心厚度。
LCL NUM ^s ^lens ^r1 ^r2 ^ct
LCL STR ^glass

^lens == 0
WRI "Lens FrontS RearS R1 R2 CT Glass"

FOR ^s 1 ((NUM S)-1)
    IF ABSF((IND S^s)) > 1.01
        ^lens == ^lens + 1
        ^glass == (GLA S^s)
        ^r1 == (RDY S^s)
        ^r2 == (RDY S^s+1)
        ^ct == (THI S^s)
        WRI ^lens ^s (^s+1) ^r1 ^r2 ^ct ^glass
    END IF
END FOR

WRI "Total:" ^lens
```

### 模板：视场和波长循环

```codev
LCL NUM ^w ^f

FOR ^w 1 (NUM W)
    FOR ^f 1 (NUM F)
        WRI "W" ^w "F" ^f
        ! 在这里读取或分析指定视场/波长的数据
    END FOR
END FOR
```

### 模板：参数默认值

```codev
RFD 1 1
LCL NUM ^field ^wave

^field == #1
IF ^field = 0
    ^field == 1
END IF

^wave == #2
IF ^wave = 0
    ^wave == 1
END IF
```

只有当 `0` 不可能是合法输入时，才把 `0` 当默认值标志。

文件头的 `ARG1 NAME`、`ARG1 TYPE`、`ARG1 DEFAULT`、`ARG1 CHOICE`、`ARG1 HELP` 等注释用于 GUI 参数说明；运行时仍以 `RFD` 和宏内校验为准。

## 序列文件分类

`.seq` 是 CODE V 序列文件扩展名，不等于“Macro-PLUS 程序”：

- 以 `RFD`、变量声明、条件和循环为主体：通常是 Macro-PLUS 宏。
- 以 `RDM; LEN`、`TITLE`、`FNO`、`WL`、`S` 等为主体：通常是镜头处方序列。
- 以 `AUTO`、约束、权重和 `GO` 为主体：通常是优化序列。
- 以连续 CODE V 命令为主体：可能是生成后供 `IN` 执行的命令文件。

先分类再修改。不要给镜头处方强加宏参数，也不要把优化约束误当成普通数据库查询。

复杂 Macro-PLUS 宏按以下顺序组织：

1. 文件头写用途、调用语法、输入、输出、单位、修改的状态和使用的 buffer。
2. 用 `ARG...` 注释描述 GUI 参数，用 `RFD` 定义真实运行时默认值。
3. 显式声明全部变量和数组。
4. 保存需要恢复的 CODE V 状态。
5. 在修改镜头前完成参数、版本、系统模式和数组上限检查。
6. 优先从数据库直接读取，必要时才捕获分析输出。
7. 所有错误路径进入统一清理出口。
8. 恢复镜头和环境，再输出结果或错误。

## 函数、动态命令与文件输入输出

### Macro-PLUS 函数

```codev
FCT @OMW_CLAMP(NUM ^x, NUM ^lo, NUM ^hi)
    LCL NUM ^result
    ^result == MAXF(^lo, MINF(^x, ^hi))
END FCT ^result
```

- 函数参数带 `NUM` 或 `STR` 类型，数组参数可写维度。
- 返回值写在 `END FCT` 后。
- 函数名使用任务前缀，避免污染会话中的全局函数命名空间。
- 函数适合纯计算；需要大量修改 CODE V 状态的过程优先写成独立宏并用 `IN` 调用。

调用其他宏：

```codev
IN CV_MACRO:some_macro ^arg1 ^arg2
```

跨宏返回值通常通过约定好的全局变量或 buffer 传递。必须说明由谁创建、删除和恢复。

### 动态命令

`$字符串变量` 会把字符串内容作为 CODE V 命令执行：

```codev
LCL STR ^cmd ^fieldCmd

^cmd == "RSI F1 R1"
$cmd

^fieldCmd == "YRI"
$fieldCmd F1 Z1 10
```

动态命令只用于命令名或参数组合确实动态的场景。执行前限制允许的命令集合，不能直接执行未经验证的外部文本。

### 文件输入输出

```codev
LCL NUM ^unit
LCL STR ^filename ^line

^unit == 0
OPE NEW U^unit ^filename
WRI U^unit "header"
WRI U^unit ^value
CLO U^unit
```

文件处理规则：

- 文件单元变量从 0 开始，让 `OPE ... U^unit` 取得可用单元，不固定写 99 等任意单元号。
- 打开前验证文件名，必要时补扩展名。
- 记录文件是否成功打开，统一清理出口只关闭本宏打开的单元。
- 逐行读取未知结构时用 `READ U^unit` 先读字符串，以 `EOFILE` 判断结束，再解析。
- 矩形表格优先 `BUF IMP`；逐行命令或非矩形文本使用文件单元。
- 外部文本转动态命令前做白名单校验。

## 绘图

官方示例中同时存在 `UGR` 和较新的 `UCH` 绘图流程。新宏在目标版本支持时优先使用 `UCH`；需要兼容旧版本或复用旧模板时使用 `UGR`。

典型数据曲线结构：

```codev
OUT N
UGR
TIT "MTF versus field"
XLA "Field"
YLA "MTF"
XMIN 0
YMIN 0
YMAX 1

DPO "Tangential"
LIN PNT
FOR ^i 1 ^count
    ^x(^i) ^tanMtf(^i)
END FOR
END

DPO "Sagittal"
LIN PNT
FOR ^i 1 ^count
    ^x(^i) ^sagMtf(^i)
END FOR
END

GO
```

绘图规则：

- 绘图前先把结果存入局部数组，避免在图形数据块中混入复杂分析命令。
- `TIT`、`XLA`、`YLA`、`XMIN/XMAX`、`YMIN/YMAX`、`XAX/YAX` 用于标题、标签和坐标范围。
- `DPO` 开始一个数据对象，`LIN`、`PNT`、`SPL` 等设置表现形式，数据点后以 `END` 收束。
- `LIN PNT` 逐点连线，适合离散视场、离散镜片编号和只有一个点也要稳定显示的结果；`SPL PNT` 做样条插值，可能在点间过冲，且少量点时表现依赖版本。灵敏度、合格判定和排名图默认使用 `LIN PNT`，仅在数据本身连续且用户明确需要平滑显示时使用 `SPL PNT`。
- 官方 Macro-PLUS 手册规定 `DPO` 标签最多 24 个字符。动态标签应在生成后用 `LENSTR` 检查并截断，同时保留区分曲线所需的镜片号、正负方向和表面范围。
- `UCH` 可配合图表模板 `CHT`；模板名称和可用性依赖安装环境，不能写成跨电脑的硬依赖。
- 多数据集数量、颜色、线型、注释和输出设备存在版本差异，复杂图必须在目标 CODE V 验证。
- UGR/UCH 可容纳大量数据对象并不代表图例仍可读。曲线很多时同时输出排序表或 CSV；图形负责观察趋势，数值表负责审计。
- 绘图常临时关闭文本输出，但结束时应恢复原 `(OUT)` 状态，而不是固定执行 `OUT Y`。

## 优化序列

以 `AUTO`、变量、约束、权重和 `GO` 为主体的 `.seq` 属于优化序列。它可以夹入 Macro-PLUS 循环或动态生成命令，但其语义不能按普通宏解释。

特别注意两种完全不同的 `@name`：

```codev
FCT @OMW_CLAMP(NUM ^x, NUM ^lo, NUM ^hi)
    LCL NUM ^result
    ^result == MAXF(^lo, MINF(^x, ^hi))
END FCT ^result
```

上面是 Macro-PLUS 函数；而优化序列中的：

```codev
@chiefError == (Y SI R1 F2 W1 Z1) - (Y SI R1 F1 W1 Z1)
@chiefError = 0
WTC 0.5
```

是用户定义优化操作数及其目标和权重。编写优化序列时：

- 先确认哪些曲率、厚度、非球面系数、空气间隔或组位置是变量。
- 把像质目标、结构边界、总长、焦距、畸变、主光线和可制造性约束分开组织。
- `WTC` 与约束的结合方式按当前优化语法核对，不能只复制权重数字。
- Macro-PLUS 的 `==` 赋值和优化操作数定义外形相似，必须结合是否位于 `AUTO` 环境判断。
- 生成或修改优化序列后，先用副本和少量迭代验证；不要默认长时间 `GO` 或覆盖用户当前优化状态。
- 未掌握当前镜头的变量与约束意图时，不自动“补全”优化条件。

## 用户定义接口与高级扩展

Macro-PLUS 还能参与更深层扩展：

- `USR routine_name ...`：调用按 CODE V 约定编译和链接的外部用户子程序。
- 用户定义函数库：通过 `FCT @name` 提供可被镜头、分析或其它宏调用的计算。
- 用户定义面、光栅、HOE、干涉图和表面属性序列：参数、返回数组和错误码必须符合对应接口手册。
- 用户定义公差修改与补偿：区分名义模型、试验模型、补偿变量及每次 trial 的恢复边界。
- SpecBuilder 规格函数：用 `STV` 返回一个或多个规格值。
- 并行宏：只在明确的并行执行环境使用 `SHR`、`THREADNUM` 和 `INPARALLEL`。

涉及 UDS、UDG、USERHOE、USERINT、USERUSP、外部 Fortran/C 子程序或并行回调时，必须先确定接口类型、调用时机、参数表、返回约定、线程安全和目标 CODE V 版本，不能套用普通分析宏模板。

## 状态保护与统一清理

不要无条件以 `OUT Y` / `VER Y` 结束，否则会改变用户原来的工作环境。

```codev
LCL NUM ^savedOut ^savedVer ^failed

^savedOut == (OUT)
^savedVer == (VER)
^failed == 0

OUT N
VER N

! 主体发生错误时：
! ^failed == 1
! GOTO cleanup

LBL cleanup

IF ^savedVer
    VER Y
ELS
    VER N
END IF

IF ^savedOut
    OUT Y
ELS
    OUT N
END IF

RTN
```

会删除或插入面、视场、波长、变焦、孔径、拾取、公差或求解的宏采用事务式结构：

1. 保存 `(FIL)`、`(OUT)`、`(VER)` 和必要模式标志。
2. 参数和系统检查通过后，保存唯一临时镜头。
3. 执行临时修改和分析。
4. 将结果先存入局部数组或自有 buffer。
5. 统一清理出口恢复临时镜头和原文件名。
6. 删除仅由本宏创建的临时文件。
7. 恢复输出和验证状态。

临时文件名避免固定公共名称，可用日期时间生成仅含字母数字的后缀。不要删除未确认由当前宏创建的文件。占用 buffer、打开文件或保存临时镜头后，不要从处理中间直接 `RTN`。

## 多重结构和特殊系统

### 多重结构

- 循环 `Z1..(NUM Z)` 时检查 `(POS Z^z)`，跳过未启用位置。
- 数据库项能带 `Z^z` 时直接查询，不为读取一个值而 `DEZ`。
- 必须临时删除其他变焦位置时，先保存镜头并在清理出口恢复。
- 表面数、光阑、材料、面模式或焦面数可能随变焦变化，不能只在 Z1 建表后套用全部变焦。

### 视场和波长

- 视场类型用 `(TYP FLD)` 分支处理 `ANG`、`OBJ`、`IMG`、`RIH`。
- 波长循环考虑 `(NUM W)`、参考波长 `(REF)`、波长值和权重。
- 焦面分析检查 `NFO`、`FFO`、`IFO`；很多分析要求单焦面或明确的离焦采样。
- 读取光线数据时将 `R/F/W/Z/S` 限定符写清楚，避免依赖当前选择状态。

### 特殊表面和材料

简单顺序透镜可用 `(GLA)`、`(IND)`、`(THI)`、`(RDY)`。复杂系统还要检查：

- `(RMD S^s Z^z)`：`REFR`、`REFL`、`TIRO` 等传播模式。
- `(TYP SUR S^s)`：球面、非球面、坐标断点、HLM/HL2、GRIN、NSS、用户面等。
- `(GLA S^s CAT)`：玻璃目录。
- `(DUM S^s Z^z)`：变焦下的 dummy 状态。
- 物面、光阑、像面、浸没像面和镜面折射率符号变化。
- 胶合面两侧都是玻璃但材料名不同。

按“玻璃材料区域”统计时，玻璃变化应拆分胶合片；按“机械物理组”统计时才合并连续区域。两者必须由用户定义。

### 元件、胶合组和用户组件范围

不要把“镜片编号”“材料区域编号”和“表面编号”混为一套编号：

- 独立镜片编号通常按每个玻璃材料区域产生一个 `G` 编号。
- 胶合物理组由连续玻璃区域组成，组内无空气间隔；例如两个材料区域 `G8`、`G9` 可显示为 `G89`，但仍要保留实际表面范围。
- 用户输入的 `1-3,5-6` 如果定义为镜片编号范围，必须先映射到各镜片的前后表面，再建立组件公差；不能把它直接解释成 `S1..S3`。
- 用户组件范围若切入胶合组，应明确选择“扩展到完整胶合组”或报错；不能静默拆开胶合组。
- 只有某物理片的两个外表面在所选变焦位置的 X、Y 半径都近似无穷大时，才可按用户规则识别为平板、保护玻璃或棱镜。只检查一个表面或只检查 `RDY` 都不充分。

多重结构下的平面判断应显式带变焦限定符，并同时检查两个方向：

```codev
IF ABSF((RDX S^front Z^z)) >= 1E18 AND &
   ABSF((RDY S^front Z^z)) >= 1E18 AND &
   ABSF((RDX S^back  Z^z)) >= 1E18 AND &
   ABSF((RDY S^back  Z^z)) >= 1E18
    ! 两个外表面在所选结构中均为平面
END IF
```

阈值应结合数据库对无穷半径的实际返回值确认。单配置镜头是否允许 `Z1` 限定符也要先做最小探针；不能为了统一代码而无条件添加。

## 分析实现策略

按稳定性从高到低选择：

1. 直接数据库项或受支持的宏函数。
2. 官方规格计算模式：明确输入维度，结果写入自有 buffer。
3. 捕获分析文本并按关键词解析。
4. 模拟 GUI 或依赖固定屏幕行列，只作为最后手段。

典型选择：

- 镜头属性、光线高度、入射角、材料、厚度：直接数据库查询。
- 单视场 MTF：目标环境支持时可使用 `MTF_1FLD(...)`；否则运行 MTF 并解析 buffer。
- MTF 文本：以 `"DIFFRACTION LIMIT"` 等表头为锚点，同时校验列类型和块数量。
- 相对照明：运行 `TRA` 后先搜索 `"ERROR"`，再定位 `"RELATIVE ILLUM:"`，并检查活动变焦和视场顺序。
- RMS、PSF、透过率、畸变、AOI、远心度：先找对应数据库项或规格计算路径，再决定是否解析输出。

分析前写清采样、极化、衍射/几何模式、方位角、频率单位、视场类型、波长权重和孔径状态。相同指标在不同分析选项下可能不是同一物理量。

标准分析输出捕获使用 `BUF YES` / `BUF NO` 和 B0。若 B0 非空且用户未授权覆盖，报错退出。不要为了避开 B0 自动改用 `OUT B^b`；它依赖版本和输出模式，只有用户已在目标版本确认有效时才可采用。

## 高风险分析宏的实机经验（以 TOR 灵敏度为例）

### 语法证据分级

编写新宏时给高风险语句做内部证据分级：

- **A：目标版本实机通过**。可作为当前环境的稳定写法。
- **B：官方宏存在相同结构**。命令、限定符顺序和所处命令模式均一致。
- **C：官方手册明确列出完整语法**。允许使用，但仍要验证版本和上下文。
- **D：把多个合法片段自行组合**。不得作为稳定交付，必须简化或先做最小实机试验。

静态检查只负责发现已知模式、变量和结构问题，不提供 A/B/C 级语法证明。交付说明应区分“静态检查未发现问题”和“已在 CODE V 中运行成功”。

交付等级采用 `SKILL.md` 的 L0-L4。目标 CODE V 编译并进入执行时记录检查点。主流程、数值基准和故障恢复按 [实机与数值验收](runtime-verification.md) 留证。

搜索官方宏时同时查看命令附近的注释。`fatal test`、`invalid`、`not supported`、`avoid` 等负面注释往往比另一个成功示例更能揭示上下文限制。

### 先区分可见回显和真正报错行

CODE V 执行：

```codev
OUT N
DEL CMP ...
```

时，`OUT N` 成功后会隐藏下一条命令的回显。如果 `DEL CMP` 报错，日志里最后一条可见命令仍可能是 `OUT N`。因此：

1. 不根据最后一条可见回显直接定位。
2. 调试阶段暂时不关闭 `OUT`/`VER`，或在每个高风险段前输出 `WRI "STEP 3: CLEAR CMP"`。
3. 一次只修改一个候选错误并重新运行。
4. 稳定后再关闭大段分析回显。

在宏开头输出短版本标记，例如 `WRI "MTF93-DSY VERSION 2026-07-29B"`。用户从其它目录或电脑运行同名副本时，先根据版本标记确认执行的是最新文件。

### 清理公差和补偿器

`DEL TOL` 与 `DEL CMP` 的对象是公差/补偿器列表，不要把镜头表面通配思路直接套入。目标版本对复合限定符和变量紧邻限定符的解析可能不同。开发时避免一次写成：

```codev
DEL TOL SA ALL
DEL CMP SO..SI ALL
DEL TOL T1..T^count
```

更保守的清理模式是按列表首项删除，让剩余项目自动重新编号：

```codev
WHI (NUM TOL) > 0
    DEL TOL T1
END WHI

WHI (NUM CMP) > 0
    DEL CMP T1
END WHI
```

`(NUM TOL)` 和 `(NUM CMP)` 分别返回当前公差和补偿器数量，`DEL TOL T1` / `DEL CMP T1` 有官方公差手册完整语法证据。运行时仍要检查删除后数量是否下降；若不下降应立即中止，不能留下无限循环。开发版应增加迭代上限和 `WRI` 计数。

临时模型通常先 `SAV ^tempLens`，再清理和建立分析专用公差。注意：序列因编译外的运行时错误直接中止时，统一清理标签不会执行，当前镜头文件名可能已变成临时名。调试完成前保留原镜头文件，并在每次中止后重新载入原模型。

### 单配置镜头不要查询 `POS Z1`

官方宏存在明确注释：当 `(NUM Z)=1` 时，测试 `(POS Z1)` 可能产生致命错误。应分支处理：

```codev
IF (NUM Z) = 1
    IF (AFC)
        ! 单配置真无焦处理
    END IF
ELS
    FOR ^z 1 (NUM Z)
        IF (POS Z^z)
            ! 仅处理活动变焦位置
        END IF
    END FOR
END IF
```

不要为了统一循环而无条件查询 `POS Z1`。其它只在真正多重结构中有意义的数据库项也要检查类似限制。

### B0 定位和 `IC`/`JC`

`IC`、`JC` 是 buffer 表达式或 buffer 命令中的当前位置标记。下面的普通赋值无效：

```codev
^row == IC + 2
```

使用以下模式：

```codev
BUF MOV B0 I1 J1
BUF FND B0 "PLUS AND MINUS"
IF NOT (BUF.FND)
    ! 转入失败清理
END IF

BUF MOV B0 IC+2
^row == (BUF.I B0) + 1
^plusChange  == (BUF.NUM B0 I^row J3)
^minusChange == (BUF.NUM B0 I^row J4)
```

也可在数据库读取表达式中直接使用相对地址，例如 `(BUF.NUM B0 IC+3 JC+2)`。无论采用哪种方法，都要先验证关键词、块数、`BUF.TYP` 和表格行数；不能假定不同版本的 TOR 文本布局完全一致。

### TOR 输出和用户结论分层

`BUF YES` 收集 B0 与屏幕 `OUT` 状态相互独立。下列片段仅表示分析命令块，执行前按捕获章节检查 B0 的归属与捕获状态。频率和其他分析设置按任务取证：

```codev
BUF YES
TOR
FRE 93
AZI TAN
SNS YES
ROU NO
SEL NO
CHT NO
GO
BUF NO
```

`SEL NO` 列出全部公差效应。解析完成后先输出：

1. 最敏感镜片或组及其表面范围。
2. 输入偏心量、单位、频率、方位角、视场/变焦聚合规则。
3. 最大绝对 MTF 变化和最坏 MTF 下降。
4. 完整排序表。

对于正负偏心，分别读取 plus/minus 列；按 `MAXF(ABSF(plus),ABSF(minus))` 排敏感度，并另存 `MAXF(0,-plus,-minus)` 表示最坏下降。不要只输出 TOR 原始表，也不要让“最敏感对象”埋在长表末尾。

在 TOR 的 MTF 公差分析中，`FRE` 使用 cycles/mm，即 lp/mm。输入范围为大于 0 至截止频率。其他分析选项的频率命令、单位和限制按该选项手册核对。证据见随包 `Tolerancing.pdf` 的 TOR 选项表。

TOR 表中的 plus/minus 是相对于名义 MTF 的变化量，不是加入公差后的绝对 MTF。三种量必须明确区分：

```text
加入公差后的 MTF = 名义 MTF + TOR 变化量
MTF 百分点变化 = 100 * TOR 变化量
相对原始值百分比 = 100 * TOR 变化量 / 名义 MTF
```

用户要“下降数值”时输出原始变化量或百分点，不要擅自改成相对百分比。分析表的文本解析必须以表头、公差类型和实际块数共同定位；一旦布局验证失败，保留原始 B0 或备份 buffer，不能继续输出看似完整的排名。

排名累加器不能简单初始化为 0 后只用严格大于号更新。若全部结果恰好为 0，会留下镜片号 0 或空方向。使用“尚未写入首值”的标志，或用低于合法范围的哨兵值初始化，并对“全部相同”给出明确结论。

## 常见风险与交付验证

主动修正常见自定义写法：

- 有 `ARG DEFAULT` 但没有 `RFD`。
- 使用未声明变量，依赖隐式全局状态。
- 大数组未限定为局部，或尺寸远超实际需要。
- 固定覆盖 B0，未说明、未检查、未删除。
- 把 `BUF COP` 的源和目标理解反了，先将当前指针移到 B0 后执行复制，导致尝试写 B0。
- `BUF FND` 后直接读取，未检查是否找到和单元格类型。
- 用 `STR_TO_NUM` 的非零结果代替完整字符串校验，使 `12abc` 一类输入被部分接受。
- 未经目标版本确认直接依赖 `SPLIT()`，导致旧版本编译失败。
- 只用 `IND = 1` 判断空气，忽略镜面、特殊面、浸没和材料变化。
- 用 `RDY > 10000` 排除平面，漏掉负大半径并混淆“近似平面”和“应忽略面”。
- 多重结构数据读取未带所选 `Z`，或单配置中无条件查询 `POS Z1`。
- 只检查一个半径方向或一个表面，就把镜片误判为平板、保护玻璃或棱镜。
- 用户组件范围按镜片号输入，却被直接当成表面号；或范围切入胶合组后静默拆组。
- 角度公差把度直接传给以弧度工作的公差类型，或线性公差未按 `(DIM)` 转换。
- 表面已有非 DAR 偏心/倾斜，却未检查公差是否会被忽略。
- `FRE` 非正、超过截止频率，或把 lp/mm 误乘 2。
- 用 `SPL PNT` 平滑离散敏感度数据，图形过冲造成错误直觉。
- 动态 `DPO` 标签超过 24 字符，或截断后丢失正负方向和镜片标识。
- 全零或并列结果时排名变量未初始化，输出不存在的 G0 或空方向。
- 混淆 TOR 变化量、加入公差后的绝对 MTF、百分点变化和相对原始值百分比。
- 删除变焦、视场、孔径、拾取或公差后没有统一恢复。
- 中间 `RTN` 导致输出、验证、文件或临时镜头未恢复。
- 默认值注释与实际 `#n` 单位换算不一致。
- 中文旧编码和 UTF-8 混用导致注释乱码。
- 把无括号函数 `RANDF` 写成 `RANDF()`。
- `GOTO` 指向不存在或重复的 `LBL`。
- `CVERROR/CVWARNING` 未赋给数值变量。
- 进入 TOR、MTF、LIB 等命令模式后漏写 `GO`。
- 关闭 `OUT/VER` 后没有保存并恢复原状态。

静态检查：

- `.seq` 类型分类正确。
- 所有 `#n` 都在调用说明中定义；可选参数有对应 `RFD` 默认项，必填或转交参数明确标注。
- 所有 `^变量` 均显式声明，必要全局量有清理责任。
- `ARGn DEFAULT` 与 `RFD` 的参数数量一致，交互 `RPR` 在退出前恢复。
- `IF/FOR/WHILE/UNTIL/FCT` 块成对。
- 数组上限覆盖数据规模，且不过度分配。
- 每个 buffer、文件单元和临时文件都有明确所有权与清理。
- 每次分析输出查找都检查成功与类型。
- 所有修改型路径最终进入恢复逻辑。
- 单位、符号、视场、波长、变焦和胶合片定义写入注释与输出。

实机验证至少分三步：

1. 用最小普通顺序镜头验证语法和输出列。
2. 用包含胶合片、平面、反射面或多重结构的镜头验证边界条件。
3. 制造一个错误输入，确认报错后镜头、输出、验证、buffer 和临时文件均恢复。

## 调试清单

CODE V 报错时依次检查：

- 是否漏了 `LCL NUM` 或 `LCL STR`。
- 使用 `#n` 时是否有足够数量的 `RFD` 默认值。
- 字符串比较是否加了引号，大小写是否一致。
- 表面范围是否误包含物面或像面。
- 数组长度是否不够。
- 数组是否远大于实际需要，造成不必要的内存占用。
- buffer 解析是否因为输出格式变化而错列。
- `BUF FND` 后是否检查了 `(BUF.FND)`，读取前是否检查单元格类型。
- 单位是否和用户期望一致。
- 胶合镜片到底是按材料拆分，还是按物理组合并。
- 宏是否改动了镜头、视场、波长、变焦、孔径、输出或验证状态，以及所有退出路径是否恢复。
