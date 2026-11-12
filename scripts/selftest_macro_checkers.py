#!/usr/bin/env python3
"""运行光学宏检查器的最小正反测试。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(checker: str, path: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / checker), str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)

        codev_good = folder / "good.seq"
        codev_good.write_text(
            "LCL NUM ^i\nFOR ^i 1 2\nWRI ^i\nEND FOR\nRTN\n",
            encoding="ascii",
        )
        codev_bad = folder / "bad.seq"
        codev_bad.write_text(
            "LCL NUM ^row\n^row == IC+2\nGOTO missing\nUGR\nRTN\n",
            encoding="ascii",
        )
        codev_buffer_good = folder / "buffer_good.seq"
        codev_buffer_good.write_text(
            "LCL NUM ^backup\n"
            "^backup == 1\n"
            "BUF MOV B^backup I1 J1\n"
            "BUF COP B0\n",
            encoding="ascii",
        )
        codev_buffer_bad = folder / "buffer_bad.seq"
        codev_buffer_bad.write_text(
            "BUF MOV B0 I1 J1; BUF COP B1\nBUF COP I2 J1\n",
            encoding="ascii",
        )
        codev_advisory = folder / "advisory.seq"
        codev_advisory.write_text(
            "LCL NUM ^frequency\n"
            "LCL STR ^parts\n"
            '^parts == SPLIT("1-3,5-6", ",")\n'
            "^frequency == #1\n"
            "TOR; FRE ^frequency; GO\n"
            'DPO "THIS LABEL IS LONGER THAN TWENTY FOUR"\n',
            encoding="ascii",
        )
        codev_continued = folder / "continued.seq"
        codev_continued.write_text(
            "! #13 is a comment\n"
            "RFD 1 &\n"
            '    "two"; LCL NUM ^n\n'
            'WRI "#99 ^example ! ; &" #2\n'
            "^n == #1\n"
            "IF ^n > 0 & ! continued condition\n"
            "    AND ^n < 2; WRI ^n; END IF\n",
            encoding="ascii",
        )
        codev_required = folder / "required.seq"
        codev_required.write_text("WRI #1\n", encoding="ascii")
        codev_invalid_fields = folder / "invalid_fields.seq"
        codev_invalid_fields.write_text("RFD 1 2 3 4 5 6 7 8 9 10\nWRI #10\n", encoding="ascii")
        codev_tor = folder / "tor.seq"
        codev_tor.write_text("TOR; FRE 0; GO\n", encoding="ascii")
        codev_other_frequency = folder / "other_frequency.seq"
        codev_other_frequency.write_text("MTF; FRE 0; GO\n", encoding="ascii")

        zpl_good = folder / "good.zpl"
        zpl_good.write_text(
            'FOR i, 1, 2, 1\nPRINT i\nNEXT\n'
            'FOR j=1, 2, 1\nPRINT j\nNEXT\n'
            'temp$ = $TEMPFILENAME()\nGETTEXTFILE temp$, Car\nDELETEFILE temp$\n',
            encoding="ascii",
        )
        zpl_bad = folder / "bad.zpl"
        zpl_bad.write_text(
            'IF a = b\nPRINT "bad"\nENDIF\nGOSUB absent\n'
            'GETTEXTFILE window, temp$\n',
            encoding="ascii",
        )
        zpl_advisory = folder / "advisory.zpl"
        zpl_advisory.write_text(
            'temp$ = $TEMPFILENAME()\nOPENANALYSISWINDOW "FFT MTF"\n',
            encoding="utf-16",
        )

        zos_good = folder / "good.py"
        zos_good.write_text("def value(x):\n    return x + 1\n", encoding="ascii")
        zos_bad = folder / "bad.py"
        zos_bad.write_text(
            "try:\n    value = 1\nexcept:\n    pass\n",
            encoding="ascii",
        )
        zos_advisory = folder / "advisory.py"
        zos_advisory.write_text(
            'source = r"C:\\lens.zmx"\n'
            "system.LoadFile(source, False)\n"
            "system.Save()\n"
            "analysis = system.Analyses.New_Analysis(3)\n"
            "series = results.GetDataSeries(0)\n",
            encoding="ascii",
        )

        rc, out = run("check_codev_macro.py", codev_good)
        require(rc == 0, f"CODE V good failed:\n{out}")
        rc, out = run("check_codev_macro.py", codev_bad)
        require(
            rc == 2 and "IC" in out and "GOTO" in out and "UGR" in out,
            f"CODE V bad missed:\n{out}",
        )
        rc, out = run("check_codev_macro.py", codev_buffer_good)
        require(rc == 0, f"CODE V safe B0 backup failed:\n{out}")
        rc, out = run("check_codev_macro.py", codev_buffer_bad)
        require(
            rc == 2 and out.count("BUF COP 的目标") == 2,
            f"CODE V unsafe B0 copy missed:\n{out}",
        )
        rc, out = run("check_codev_macro.py", codev_advisory)
        require(
            rc == 1
            and "SPLIT" in out
            and "动态 FRE" in out
            and "24" in out,
            f"CODE V advisory checks missed:\n{out}",
        )
        rc, out = run("check_codev_macro.py", codev_continued)
        require(rc == 0, f"CODE V continued statements failed:\n{out}")
        rc, out = run("check_codev_macro.py", codev_required)
        require(rc == 1 and "ERROR:" not in out, f"CODE V required field rejected:\n{out}")
        rc, out = run("check_codev_macro.py", codev_invalid_fields)
        require(rc == 2 and "#10" in out and "RFD" in out, f"CODE V field limit missed:\n{out}")
        rc, out = run("check_codev_macro.py", codev_tor)
        require(rc == 2 and "TOR MTF" in out, f"CODE V zero TOR frequency missed:\n{out}")
        rc, out = run("check_codev_macro.py", codev_other_frequency)
        require(rc == 0, f"CODE V TOR frequency rule applied to another mode:\n{out}")
        rc, out = run("check_codev_macro.py", ROOT.parent / "assets" / "probes" / "codev-smoke.seq")
        require(rc == 0, f"CODE V packaged probe failed static checks:\n{out}")

        rc, out = run("check_zpl_macro.py", zpl_good)
        require(rc == 0, f"ZPL good failed:\n{out}")
        rc, out = run("check_zpl_macro.py", zpl_bad)
        require(rc == 2 and "赋值" in out and "GOSUB" in out and "GETTEXTFILE" in out, f"ZPL bad missed:\n{out}")
        rc, out = run("check_zpl_macro.py", zpl_advisory)
        require(
            rc == 1 and "DELETEFILE" in out and "CLOSEWINDOW" in out,
            f"ZPL advisory checks missed:\n{out}",
        )

        rc, out = run("check_zosapi_python.py", zos_good)
        require(rc == 0, f"ZOS-API good failed:\n{out}")
        rc, out = run("check_zosapi_python.py", zos_bad)
        require(rc == 2 and "bare except" in out, f"ZOS-API bad missed:\n{out}")
        rc, out = run("check_zosapi_python.py", zos_advisory)
        require(
            rc == 1
            and "绝对路径" in out
            and "整数分析编号" in out
            and "SaveAs" in out
            and "NumberOfDataSeries" in out,
            f"ZOS-API advisory checks missed:\n{out}",
        )

    print("OK: all optical macro checker self-tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
