# Zemax OpticStudio ZPL 与 ZOS-API 可迁移参考

## 目录

- 证据等级与平台选择
- ZPL 语言核心
- ZPL 函数与关键字能力地图
- 系统、表面、视场、波长与配置
- 顺序光线、非序列光线与偏振
- 分析、文本窗口、向量与图形
- 优化、公差、多重结构与宏求解
- 文件、子宏、外部程序与资源管理
- 可复用 ZPL 模板
- ZPL 工程检查清单
- ZOS-API 架构与连接模式
- ZOS-API 编辑器、分析和工具对象
- ZOS-API 批量光线追迹
- ZOS-API Python 模板与检查清单

## 证据等级与平台选择

Zemax 语法和对象模型按以下证据等级判断：

1. 当前 Ansys Zemax OpticStudio 官方帮助和当前安装自带示例。
2. 用户提供的同版本官方手册和官方示例。
3. 本参考内已核对的通用模式。
4. 用户宏和历史宏只作为线索，不能单独证明当前版本支持。

版本、许可证、分析设置枚举和 ZOS-API 接口会变化。不能确认的函数签名、操作数参数、设置代码或枚举值必须在目标版本的 Programming Help / ZOS-API Syntax Help 中核对。

交付时采用 `SKILL.md` 的 L0-L4 等级。**Check Obsolete Syntax** 用于发现过时语法。ZPL 的 L2 需在目标 OpticStudio 执行到预期检查点。ZOS-API 的 L2 需实际连接并调用任务所用的关键接口。

选择方式：

- ZPL：在 OpticStudio 内运行、操作当前镜头、计算量中小、输出文本或简单图形。
- ZPL Macro Solve：需要把自定义计算作为 LDE 求解参与更新。
- ZPLM Merit Function Operand：需要把 ZPL 计算作为优化操作数。
- ZOS-API Standalone：独立进程打开一个或多个系统，适合批处理。
- ZOS-API Interactive Extension：控制已打开的 OpticStudio 实例。
- ZOS-API User Analysis / User Operand / User Extension：需要深度嵌入界面、分析或优化。
- DLL：需要用户面、对象、散射、衍射、体散射或极高性能回调。

需要大量光线、稳定提取网格结果、多文件并行、复杂 Excel/图像或长时间自动化时，优先 ZOS-API。ZPL 没有完善的调试器和变量遮蔽机制，复杂程序必须自行加入输入检查和诊断输出。

## ZPL 语言核心

ZPL 不区分大小写，每条命令通常独占一行。

```text
! 整行注释
REM 整行注释
x = 5 # 行尾注释
```

### 变量和赋值

- 数值变量无需声明，内部为 64 位双精度。
- 字符串变量名以 `$` 结尾，最长长度受版本限制。
- 变量名不能与关键字或函数重名，不能包含运算符和空格。
- 数值赋值用 `=`，相等比较用 `==`。
- 字符串函数通常以 `$` 开头，结果先赋给字符串变量再 `PRINT`。

```text
x = 5
name$ = $LENSNAME()
line$ = "Lens: " + name$
PRINT line$
```

不要写：

```text
PRINT $LENSNAME()
```

正确写法是先赋值：

```text
name$ = $LENSNAME()
PRINT name$
```

### 数组

数组必须声明，支持 1 至 4 维，默认下标从 1 开始：

```text
DECLARE data, DOUBLE, 2, 20, 10
DECLARE flags, INTEGER, 1, 100

data(1, 1) = 3.5
RELEASE data
RELEASE flags
```

`RELEASE` 在宏结束时不是必须的，但大数组使用完应释放。

### 运算和逻辑

- 数值运算：`+`、`-`、`*`、`/`。
- 逻辑：`&` 与、`|` 或、`^` 异或、`!` 非。
- 比较：`==`、`!=`、`>`、`<`、`>=`、`<=`。
- 字符串比较：`$==`、`$!=`、`$>`、`$<`、`$>=`、`$<=`。
- 用括号明确优先级，不依赖复杂表达式的默认结合顺序。

### 控制结构

```text
IF condition
    PRINT "true"
ELSEIF other_condition
    PRINT "other"
ELSE
    PRINT "false"
ENDIF

IF condition THEN PRINT "single line"

FOR i, 1, 10, 1
    PRINT i
NEXT

GOSUB calculate
END

SUB calculate
    PRINT "inside subroutine"
RETURN
```

`FOR` 的官方标准语法是 `FOR variable, start, stop, increment`。部分官方页面的示例出现 `FOR i = ...`，新宏统一采用逗号形式，避免混用。起点大于终点时循环会按负方向继续，不会自动跳过；需要“零次循环”语义时必须在 `FOR` 外加条件。

`GOTO` 和 `LABEL` 可用，但只适合统一清理或简单状态机。普通结构优先 `IF`、`FOR` 和 `GOSUB/SUB/RETURN`。

### 输入、输出和格式

```text
FORMAT 12.6
INPUT "Field number?", field

OUTPUT "result.csv"
PRINT "Field,Value"
PRINT field, ",", value
OUTPUT SCREEN
```

输出到文件后必须恢复 `OUTPUT SCREEN`。CSV 中的字符串若可能包含逗号、引号或换行，要做转义或改由 ZOS-API 写 CSV。

## ZPL 函数与关键字能力地图

此处列出官方语言能力范围，用于避免把冷门功能误判为“ZPL 做不到”。精确参数仍需按目标版本核对。

### 常用数值和光学函数

- 系统：`ATYP()`、`AVAL()`、`CONF()`、`FTYP()`、`NFLD()`、`NSUR()`、`NWAV()`、`NCON()`、`PWAV()`、`VERS()`、`UNIT()`。
- 表面：`RADI()`、`CURV()`、`THIC()`、`CONI()`、`PARM()`、`SDIA()`、`STDD()`、`SURP()`、`GETEXTRADATA`。
- 材料和环境：`INDX()`、`GLCM()`、`GRIN()`、`GTEM()`、`GETGLASSDATA`。
- 光线：`RAYTRACE`、`RAYTRACEX`，以及 `RAYX/Y/Z/L/M/N`、`RAGX/Y/Z/L/M/N`、`RAYE()`、`RAYV()`、`LOST()`、`OPDC()`。
- 操作数：`OCOD()`、`OPEV()`、`OPEW()`、`OPER()`、`MFCN()`。
- 编辑器：`MCON()`、`MCOP()`、`TOLV()`、`SOLV()`、`SOLM()`、`SYPR()`、`SPRO()`。
- 图形和窗口：`WINN()`、`WINL()`、`XMIN()`、`XMAX()`、`YMIN()`、`YMAX()`、`PIXX()`、`PIXY()`。
- 文件与时间：`EOFF()`、`ETIM()`、`FICL()`。
- ZPLM 数据：`PVEX()`、`PVEY()`、`PVHX()`、`PVHY()`、`PVPX()`、`PVPY()`。

### 常用字符串函数

`$BUFFER()`、`$CALLSTR()`、`$COAT()`、`$COMMENT()`、`$DATE()`、`$FILENAME()`、`$FILEPATH()`、`$GLASS()`、`$GLASSCATALOG()`、`$LENSNAME()`、`$NOTE()`、`$STR()`、`$TEMPFILENAME()`、`$TOLCOMMENT()`、`$TOLOPERAND()`、`$UNITS()`、`$LEFTSTRING()`、`$RIGHTSTRING()`、`$GETSTRING()`、`$GETSTRINGC()`、`$NEWLINE()`、`$QUOTE()`、`$TAB()`。

路径函数包括数据、程序、宏、玻璃、对象、扩展等目录。它们比写死安装路径可靠，但仍要确认目标文件是否存在。

### 官方关键字全域地图

系统和镜头数据：

`APMN`、`APMX`、`APTP`、`APXD`、`APYD`、`ATYP`、`AVAL`、`COAT`、`COMMENT`、`CONI`、`CURV`、`EDVA`、`FLDX`、`FLDY`、`FWGT`、`FVDX`、`FVDY`、`FVCX`、`FVCY`、`FVAN`、`FTYP`、`GCRS`、`GLAS`、`GLENSNAME`、`IMA`、`NUMFIELD`、`NUMWAVE`、`PARM`、`PWAV`、`RADI`、`SDIA`、`SETAPODIZATION`、`SETAIM`、`SETAIMDATA`、`SETSTDD`、`SETSURFACEPROPERTY/SURP`、`SETSYSTEMPROPERTY/SYSP`、`SETUNITS`、`SETVIG`、`STOPSURF`、`SURFTYPE`、`TELECENTRIC`、`THIC`、`WAVL`、`WWGT`。

镜头和编辑器结构修改：

`DELETE`、`INSERT`、`DELETECONFIG`、`INSERTCONFIG`、`DELETEMCO`、`INSERTMCO`、`DELETEMFO`、`INSERTMFO`、`DELETEOBJECT`、`INSERTOBJECT`、`DELETETOL`、`INSERTTOL`、`SETCONFIG`、`SETMCOPERAND`、`SETOPERAND`、`SETTOL`、`SETVAR`、`REMOVEVARIABLES`、`SOLVETYPE`、`SOLVEBEFORESTOP`、`SOLVERETURN`。

顺序、非序列和偏振追迹：

`PARAXIAL`、`RAYTRACE`、`RAYTRACEX`、`POLDEFINE`、`POLTRACE`、`NSLT`、`NSTR`、`NSTR2`、`SETNSCPARAMETER`、`SETNSCPOSITION`、`SETNSCPROPERTY`、`SETDETECTOR`、`LOADDETECTOR`、`SAVEDETECTOR`、`RELOADOBJECTS`、`SCATTER`。

分析和数值结果：

`GETDENCUSER1D`、`GETGLASSDATA`、`GETLSF`、`GETMTF`、`GETMTFUSER1D`、`GETNSCMTF`、`GETPSF`、`GETSYSTEMDATA`、`GETTEXTFILE`、`GETVARDATA`、`GETZERNIKE`、`QUICKFOCUS`、`QUICKSENSITIVITY`、`TESTPLATEFIT`、`TOLERANCE`、`OPTIMIZE`、`HAMMER`、`DEFAULTMERIT`、`GLASSTEMPLATE`。

窗口、图形和图像：

`OPENANALYSISWINDOW`、`CLOSEWINDOW`、`LOCKWINDOW`、`UNLOCKWINDOW`、`PRINTWINDOW`、`SAVEWINDOW`、`MODIFYSETTINGS`、`GRAPHICS`、`COLOR`、`LINE`、`PIXEL`、`GTEXT`、`GTEXTCENT`、`GTITLE`、`PLOT`、`PLOT2D`、`EXPORTBMP`、`EXPORTJPG`、`SHOWBITMAP`、`IMASHOW`、`IMAGECOMBINE`、`IMAGEEXTRACT`、`IMASUM`、`CONVERTIMAGETOGRID`、`SETTEXTSIZE`、`SETTITLE`。

文件、目录和系统调用：

`BROWSE`、`OPEN`、`CLOSE`、`READ`、`READNEXT`、`READNEXT_LOCALE`、`READ_LOCALE`、`READSKIP`、`READSTRING`、`REWIND`、`OUTPUT`、`PRINT`、`PRINTFILE`、`SHOWFILE`、`COPYFILE`、`DELETEFILE`、`RENAMEFILE`、`FINDFILE`、`MAKEFOLDER`、`LOADLENS`、`SAVELENS`、`LOADARCHIVE`、`SAVEARCHIVE`、`LOADCATALOG`、`LOADMERIT`、`SAVEMERIT`、`LOADTOLERANCE`、`SAVETOLERANCE`、`CONVERTFILEFORMAT`、`COMMAND`。

宏结构和运行控制：

`CALLMACRO`、`CALLSETDBL`、`CALLSETSTR`、`GOSUB`、`SUB`、`RETURN`、`END`、`GOTO`、`LABEL`、`IF/THEN/ELSE/ENDIF`、`FOR/NEXT`、`DECLARE`、`RELEASE`、`INPUT`、`FORMAT`、`PAUSE`、`TIMER`、`RANDOMIZE`、`UPDATE`、`SUSPENDUPDATES`、`RESUMEUPDATES`、`BEEP`、`CLOSEWINDOW`、`OPTRETURN`。

CAD、坐标和复合系统：

`EXPORTCAD`、`GLOBALTOLOCAL`、`LOCALTOGLOBAL`、`COMPOSITEON`、`COMPOSITEOFF`、`COMPOSITEOFFAXISAPERTUREON`、`MAKEFACETLIST`、`IMPORTEXTRADATA`。

物理光学和二进制数据：

`POP`、`ZBF2MAT`、`ZBFCLR`、`ZBFMULT`、`ZBFPROPERTIES`、`ZBFREAD`、`ZBFRESAMPLE`、`ZBFSHOW`、`ZBFSUM`、`ZBFTILT`、`ZBFWRITE`、`ZRD2MAT`、`ZRDAPPEND`、`ZRDFILTER`、`ZRDPLAYBACK`、`ZRDSAVERAYS`、`ZRDSUM`、`XDIFFIA`。

看到关键字名称后仍需检查四件事：输入单位、表面/对象编号基准、结果写入位置（`VEC1..VEC4`、`$BUFFER()`、窗口或文件）以及是否修改当前镜头或打开工具。

## 系统、表面、视场、波长与配置

基础读取：

- 表面数：`NSUR()`。
- 视场数：`NFLD()`，不要把 `MAXF()` 当视场数量。
- 波长数：`NWAV()`。
- 配置数：`NCON()`，当前配置：`CONF()`。
- 表面半径：`RADI(s)`；无限半径通常返回 0。
- 曲率：`CURV(s)`。
- 厚度：`THIC(s)`。
- 材料：`$GLASS(s)`。
- 折射率：`INDX(s)`。
- 系统单位和类型：`UNIT()`、`FTYP()`、`ATYP()`、`AVAL()`。

修改镜头时优先使用专用关键字；通用属性由 `SETSYSTEMPROPERTY/SYSP`、`SETSURFACEPROPERTY/SURP`、`SETCONFIG`、`SETMCOPERAND` 等处理。所有数字代码都必须从当前版本手册取得，不能凭旧宏猜测。

表面 0 是物面，像面通常是 `NSUR()` 对应的最后表面。ZOS-API 的 `NumberOfSurfaces` 与行号关系需按接口确认，常见像面索引为 `NumberOfSurfaces - 1`。

特殊系统必须额外处理：

- 坐标断点和倾斜偏心。
- 反射面、折返、多路径和复合系统。
- dummy 面、pickup、solve 和多重结构。
- GRIN、用户面、衍射面、二元面、自由曲面和相位面。
- 浸没物像空间、无焦系统、远心系统。

## 顺序光线、非序列光线与偏振

顺序单光线：

```text
RAYTRACE hx, hy, px, py, wave

y = RAYY(surface)
m = RAYM(surface)
err = RAYE()
vig = RAYV()
```

参数顺序和可选项按当前帮助核对。局部坐标使用 `RAYX/Y/Z/L/M/N`，全局坐标使用 `RAGX/Y/Z/L/M/N`。每次读取结果前必须检查光线错误和渐晕状态。

`RAYTRACEX`、`POLDEFINE`、`POLTRACE` 用于扩展或偏振追迹。偏振结果必须明确 Jones 分量、相位约定、归一化和功率定义。

非序列：

- `NSTR/NSTR2` 运行非序列光线追迹。
- `NSLT`、`NSDC/NSDD/NSDE/NSDP` 等读取对象或探测器数据。
- `SETNSCPARAMETER/POSITION/PROPERTY` 修改对象。
- 探测器需明确清空、追迹、读取、保存和恢复顺序。
- 随机散射分析应 `RANDOMIZE` 或明确固定种子，并记录光线数、分裂、散射、偏振和错误忽略选项。

## 分析、文本窗口、向量与图形

结果提取优先级：

1. 直接函数或稳定操作数。
2. `GET...` 关键字写入 `VEC1..VEC4`。
3. 显示分析窗口时使用 `OPENANALYSISWINDOW`，导出原生分析文本时使用 `GETTEXTFILE` 并指定分析类型与所需设置。
4. 解析分析文本只作为兼容方案。

`VEC1..VEC4` 是共享向量工作区。使用前记录每段数据的起点和长度，不能假设上一次内容已清空。`SETVECSIZE` 只在确实需要时调整，并检查目标版本上限。

典型分析能力：

- MTF/LSF/PSF：`GETMTF`、`GETLSF`、`GETPSF`、`GETMTFUSER1D`。
- 非序列 MTF：`GETNSCMTF`。
- Zernike：`GETZERNIKE`。
- 包围能量/线扩散自定义：`GETDENCUSER1D` 等。
- 通用分析：`OPENANALYSISWINDOW`、`MODIFYSETTINGS`、`GETTEXTFILE`。
- 操作数计算：`OCOD()` + `OPEV()`。

```text
code = OCOD("EFFL")
value = OPEV(code, 0, 1, 0, 0, 0, 0)
PRINT value
```

`OPEV` 总计需要操作数代码加 6 个参数。不同操作数的表面、波长、视场、采样和单位不能通用。

图形分三层：

- `PLOT/PLOT2D`：标准线图和二维图。
- `GRAPHICS` + `LINE/PIXEL/GTEXT/...`：低层绘图。
- `EXPORTBMP/EXPORTJPG/SAVEWINDOW`：输出窗口结果。

## 优化、公差、多重结构与宏求解

优化：

- `SETOPERAND`、`INSERTMFO`、`DELETEMFO`、`DEFAULTMERIT` 管理评价函数。
- `SETVAR`、`REMOVEVARIABLES` 管理变量。
- `OPTIMIZE`、`HAMMER` 执行优化。
- 修改前保存评价函数或镜头副本；限制循环次数和运行时间。

公差：

- `INSERTTOL`、`DELETETOL`、`SETTOL` 管理公差。
- `TOLERANCE`、`QUICKSENSITIVITY` 执行分析。
- `LOADTOLERANCE/SAVETOLERANCE` 管理公差文件。
- 公差操作数的类型代码、最小/最大值、补偿和统计设置必须按当前版本核对。

多重结构：

- `INSERTCONFIG/DELETECONFIG` 管理配置。
- `INSERTMCO/DELETEMCO/SETMCOPERAND` 管理多重结构操作数。
- `MCON()`、`MCOP()` 读取结构数据。
- 所有循环显式遍历配置，不能只读取当前配置后代表全系统。

ZPL Macro Solve：

- 宏可使用全部 ZPL 函数和关键字，但必须通过 `SOLVERETURN` 返回求解值。
- 缺少 `SOLVERETURN` 会使求解失败并令系统处于错误状态。
- 用 `SOLVEBEFORESTOP` 控制求解与光阑的关系时，必须遵循官方约束。
- Macro Solve 可能在系统更新、优化和分析期间反复调用，不能弹出交互框、写大量文件或改变无关系统状态。

ZPLM 操作数：

- 使用 `PV...()` 函数读取 ZPLM 参数。
- 通过 `OPTRETURN` 返回操作数结果。
- 必须可重复、无交互、无随机漂移，并避免递归触发评价函数更新。

## 文件、子宏、外部程序与资源管理

文件读取：

```text
OPEN filename$
READ value
READSTRING line$
IF EOFF() THEN GOTO finished
REWIND
CLOSE
```

Macro Solve 采用额外限制：

- 必须短小、确定、只读。
- 禁止 `UPDATE`，否则可能重新触发 solve 形成递归。
- 禁止 `INPUT` 和交互窗口。
- 禁止修改 LDE、MFE、MCE、TDE 或系统数据。
- 成功路径调用 `SOLVERETURN`；错误路径不调用，让 OpticStudio 将 solve 标为错误。

ZPLM 的 `OPTRETURN datafield, result` 中 datafield 必须为 `0..50`。Merit Function 中 Data=0 时执行宏；其它 Data 值读取同次执行已经写入的槽位。宏文件名、宏编号和数据槽必须一起核对。

精确 `OPEN` 模式、locale 读取和字符串读取按目标版本核对。每个成功打开的文件都有 `CLOSE`，所有退出路径都执行清理。

临时文件：

```text
temp$ = $TEMPFILENAME()
GETTEXTFILE temp$, Car
! 读取 temp$
DELETEFILE temp$
```

`Car` 是基点分析的三字符代码。完整参数顺序是 `GETTEXTFILE textfilename, type, settingsfilename, flag`，这里使用官方示例的两参数形式。指定设置文件时核对 `flag` 和文件内容。有效的设置文件名可能被写回，先使用本次任务专用的副本。读取前核对输出类型和文件内容，使用 `OPEN` 后先 `CLOSE` 再删除自己的临时文件。[Ansys 官方说明](https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v26101/zh-Hans/OpticStudio_User_Guide/OpticStudio_Help/topics/GETTEXTFILE_keywords.html)

子宏：

- `CALLMACRO` 调用子宏。
- `CALLSETDBL/CALLSETSTR` 和 `CALD()`/`$CALLSTR()` 传递返回值。
- 调用链必须说明输入、返回槽位、是否修改镜头和失败传播。

外部程序：

- `COMMAND` 启动外部命令时通常不会自动等待，也未必返回可靠错误码。
- 不把未经验证的用户文本直接拼成系统命令。
- 需要可靠进程控制、标准输出和退出码时改用 ZOS-API/Python。

资源恢复：

- 文件：`OPEN` / `CLOSE`。
- 输出：`OUTPUT file` / `OUTPUT SCREEN`。
- 窗口：`OPENANALYSISWINDOW` / `CLOSEWINDOW`。
- 锁：`LOCKWINDOW` / `UNLOCKWINDOW`。
- 更新：`SUSPENDUPDATES` / `RESUMEUPDATES` / `UPDATE`。
- 数组：`DECLARE` / `RELEASE`。
- 临时文件：`$TEMPFILENAME()` / `DELETEFILE`。

## 可复用 ZPL 模板

### 镜片材料、前后表面半径与中心厚度

```text
! 输出每个玻璃区域。胶合双胶按材料拆分。
FORMAT 14.7

OUTPUT "lens_data.csv"
PRINT "Lens,FrontS,RearS,R1,R2,CT,Glass"

lens = 0
ns = NSUR()

FOR s, 1, ns-1, 1
    glass$ = $GLASS(s)
    IF INDX(s) > 1.000001
        lens = lens + 1
        PRINT lens, ",", s, ",", s+1, ",", RADI(s), ",", RADI(s+1), ",", THIC(s), ",", glass$
    ENDIF
NEXT

OUTPUT SCREEN
PRINT "Total lenses: ", lens
```

这是普通顺序折射系统模板。坐标断点、反射面、GRIN、dummy、浸没系统和非序列模型必须增加类型判断。

### 视场、波长和配置循环

```text
nc = NCON()
nf = NFLD()
nw = NWAV()

FOR c, 1, nc, 1
    SETCONFIG c
    FOR f, 1, nf, 1
        FOR w, 1, nw, 1
            PRINT c, f, w
        NEXT
    NEXT
NEXT
```

### 操作数批量求值

```text
code = OCOD("EFFL")

FOR c, 1, NCON(), 1
    SETCONFIG c
    value = OPEV(code, 0, 1, 0, 0, 0, 0)
    PRINT c, value
NEXT
```

## ZPL 工程检查清单

- ZPL 和 CODE V 赋值/比较符没有混用。
- 数值、字符串和数组变量类型正确。
- 每个 `IF` 有 `ENDIF`，每个 `FOR` 有 `NEXT`，子程序有 `RETURN`，主程序在 `SUB` 前有 `END`。
- `$...()` 字符串函数先赋给字符串变量再打印。
- `OPEV` 参数数量正确，操作数参数和单位已核对。
- `RAYTRACE` 后检查错误和渐晕。
- `VEC1..VEC4` 的数据布局和长度来自当前关键字定义。
- 文件、窗口、锁、更新暂停、输出和临时文件都有清理。
- 修改镜头前保存副本；默认不覆盖原镜头。
- Macro Solve 含 `SOLVERETURN`，ZPLM 含正确的 `OPTRETURN`。
- 随机追迹记录随机种子、光线数和追迹选项。
- 分析文本解析保留原始文本诊断，并标注版本依赖。
- 在 Edit/Run 中实际执行并记录 OpticStudio 版本和结果。使用 `Check Obsolete Syntax` 检查过时语法。
- 明确验证等级 L0-L4；没有软件执行证据时不声称可直接运行。

## ZOS-API 架构与连接模式

ZOS-API 的核心对象路线：

```text
TheApplication
  -> PrimarySystem
     -> SystemData
     -> LDE / NCE / MFE / TDE / MCE
     -> Analyses
     -> Tools
```

连接模式包括 Standalone、Interactive Extension、User Analysis、User Operand 和 User Extension。脚本必须先验证：

- 连接成功。
- 许可证有效。
- 当前模式符合预期。
- `PrimarySystem` 不为空。
- 系统是 Sequential、NonSequential 或混合模式中的预期类型。

Standalone 结束时关闭应用；Interactive Extension 只释放扩展连接，不擅自关闭用户的 OpticStudio。

## ZOS-API 编辑器、分析和工具对象

系统数据 `SystemData`：

- Aperture：孔径类型、数值、渐晕、远心、无焦和半口径策略。
- Fields / Wavelengths：视场和波长集合。
- Environment：温度、压力和环境折射率设置。
- Polarization：偏振状态和 Jones 参数。
- RayAiming：光线瞄准。
- MaterialCatalogs：材料目录。
- Units：镜头、光源、分析、MTF 和无焦单位。
- TitleNotes / Files：标题、备注、镀膜、散射和 GRIN 文件。

编辑器：

- `ILensDataEditor` / `ILDERow`：顺序表面、类型、半径、厚度、材料、半口径、solve、倾斜偏心、镀膜、散射和物理光学。
- `INonSeqEditor` / `INCERow`：对象类型、位置、材料、参数、源、探测器、散射、衍射、体物理和 CAD。
- `IMeritFunctionEditor`：操作数、目标、权重、值和评价函数计算。
- `IToleranceDataEditor`：公差操作数和参数。
- `IMultiConfigEditor`：多重结构操作数和各配置单元格。
- `IEditorCell`：通用单元格值和 solve 接口。

设置表面或对象类型时，先取得类型设置对象，再执行类型变更，随后按该类型专有数据接口填写参数。不要假设所有类型具有相同列。

分析生命周期：

1. 创建新分析对象。
2. 获取设置对象。
3. 设置波长、视场、采样、极化和其它选项。
4. `ApplyAndWaitForCompletion()` 或对应等待方法。
5. 获取结果。
6. 按结果类型读取 `DataSeries`、`DataGrids`、`DataGridsRgb`、文本或元数据。
7. 关闭分析对象。

不能假设所有分析都返回二维网格。读取前检查结果集合数量、维度、轴、单位、标签和有效状态。

Tools 同一时间通常只允许一个活动工具：

- Local / Global / Hammer Optimization。
- Batch Ray Trace。
- Create/Restore ZAR。
- Export CAD。
- 公差及其它系统工具。

工具无论成功失败都要 `Close()`。

## ZOS-API 批量光线追迹

大量光线不要逐条用操作数调用。官方推荐流程：

1. `OpenBatchRayTrace()`。
2. 创建 `NormUnpol`、`DirectUnpol`、`NormPol`、`DirectPol` 或 `NSC` 数据接口。
3. `ClearData()`。
4. 用 `AddRay()` 填充光线。
5. `RunAndWaitForCompletion()`。
6. `StartReadingResults()`，循环 `ReadNextResult()` 或 Full 版本。
7. 关闭批量追迹工具。

模式差异：

- NormUnpol：归一化视场/瞳坐标，考虑瞳孔渐晕，可返回 OPD，不计算偏振吸收/镀膜 Fresnel。
- DirectUnpol：直接坐标和方向余弦，不自动考虑瞳孔渐晕。
- NormPol：归一化坐标和偏振场，但不提供同样的渐晕检查能力。
- DirectPol：直接坐标偏振追迹。
- NSC：非序列批量追迹。

每条结果检查 `success`、`errorCode`、`vignetteCode`。返回坐标通常是局部坐标；全局坐标需用 LDE 的全局矩阵转换。工具打开时持有系统快照，修改系统后要关闭并重新打开工具才会生效。

## ZOS-API Python 模板与检查清单

推荐结构：

```python
from pathlib import Path


def process_system(system, output_dir: Path) -> None:
    lde = system.LDE
    rows = []
    for surface_number in range(1, lde.NumberOfSurfaces - 1):
        surface = lde.GetSurfaceAt(surface_number)
        rows.append(
            {
                "surface": surface_number,
                "radius": surface.Radius,
                "thickness": surface.Thickness,
                "material": surface.Material,
            }
        )
    # 使用 csv 或 openpyxl 写出 rows。


def main() -> None:
    # 1. 按目标环境连接 TheApplication。
    # 2. 验证许可证、模式和 PrimarySystem。
    # 3. 打开镜头副本或处理当前系统。
    # 4. try/finally 中关闭 analysis/tool/system/application。
    pass
```

实际连接引导代码由 OpticStudio 当前版本的 Application Builder 生成，不从旧电脑复制硬编码 DLL 路径。

检查清单：

- Python/.NET 位数、Python.NET 和 OpticStudio 版本匹配。
- Standalone 与 Interactive Extension 生命周期没有混用。
- 原镜头默认不覆盖。
- 表面/对象编号零基准和像面位置已确认。
- 枚举来自当前 ZOS-API，不用字符串或旧整数猜测。
- 分析设置与结果类型匹配。
- `DataSeries/DataGrids` 的轴、维度和单位已验证。
- 工具、分析、系统和应用均在 `finally` 清理。
- 批量追迹检查成功、错误、渐晕和局部/全局坐标。
- 多配置、温度、波长、视场、偏振和随机种子进入输出元数据。
- 批处理先在一个镜头上验证，再扩展到文件夹。
- 运行 `scripts/check_zosapi_python.py`，消除 Python 语法、空异常处理和明显资源生命周期问题。
- Python 静态通过不证明 ZOS-API 接口存在；所有枚举和设置对象仍以目标版本 Application Builder 与 Syntax Help 为准。
