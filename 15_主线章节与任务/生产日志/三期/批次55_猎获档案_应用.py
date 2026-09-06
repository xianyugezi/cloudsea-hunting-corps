# -*- coding: utf-8 -*-
"""批次 55 猎获档案·下 —— 应用脚本
逐只在 16 个生态文件的怪物表追加「猎获档案」列，并执行完成判据断言。
"""
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, r"D:\1V1TXTRPG\yunhai\cloudsea-hunting-corps\15_主线章节与任务\生产日志\三期")
from 批次55_猎获档案_数据A import DATA_A
from 批次55_猎获档案_数据B import DATA_B
from 批次55_猎获档案_数据C import DATA_C

ARCHIVES = {}
ARCHIVES.update(DATA_A)
ARCHIVES.update(DATA_B)
ARCHIVES.update(DATA_C)

BASE = r"D:\1V1TXTRPG\yunhai\cloudsea-hunting-corps\17_世界内容与生态"

CAT_RE = re.compile(r"^### (常规巨兽|终盘巨兽|空兽|杂兽)（\d+）")
HEAD_RE = re.compile(r"^\| # \| 名字 \| 核心机制 \| 派生 \|\s*$")
SEP_RE = re.compile(r"^\|:---:\|:---\|:---\|:---\|\s*$")
ROW_RE = re.compile(r"^\| (\d+) \| .+ \|\s*$")

FOOT_NOTE = "*猎获档案于 2026-09-07 由三期填充排期批次 55 逐只落定（风暴/狂岚/浩劫 321＋剧情 88，全库 409/409）。风格沿 54 范式：巨兽＝习性＋弱点，终盘＝击破纪念变体句，剧情生态引 G/A 编号互文；掉落点名对齐 `18_/06_` 十四类矩阵。*"


def sentence_check(text, fname, cat, idx, errors):
    for s in text.split("。"):
        s = s.strip()
        if not s:
            continue
        if len(s) > 40:
            errors.append(f"[句长{len(s)}] {fname}/{cat}#{idx}: {s}")


total = 0
errors = []
report = []
for rel, cats in ARCHIVES.items():
    path = f"{BASE}\\{rel}"
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    out = []
    current = None
    seen = {}  # cat -> {idx: line_no}
    for ln, line in enumerate(lines):
        m = CAT_RE.match(line)
        if m:
            current = m.group(1)
            out.append(line)
            continue
        if HEAD_RE.match(line):
            out.append("| # | 名字 | 核心机制 | 派生 | 猎获档案 |")
            continue
        if SEP_RE.match(line):
            out.append("|:---:|:---|:---|:---|:---|")
            continue
        m = ROW_RE.match(line)
        if m and current:
            idx = int(m.group(1))
            if current not in cats or idx not in cats[current]:
                errors.append(f"{rel}: 缺档案 {current}#{idx}")
                out.append(line)
                continue
            text = cats[current][idx]
            sentence_check(text, rel, current, idx, errors)
            out.append(line.rstrip()[:-1].rstrip() + f" | {text} |")
            seen.setdefault(current, {})[idx] = ln
            total += 1
            continue
        out.append(line)

    # 多余档案检查
    for cat, entries in cats.items():
        got = seen.get(cat, {})
        for idx in entries:
            if idx not in got:
                errors.append(f"{rel}: 未命中数据行 {cat}#{idx}")

    # 还原一致性断言：去掉末列后应与原文完全一致（命名内容与 ecology.rule 零改动）
    restored = []
    cur = None
    for line in out:
        if CAT_RE.match(line):
            cur = None
            restored.append(line)
            continue
        if line == "| # | 名字 | 核心机制 | 派生 | 猎获档案 |":
            restored.append("| # | 名字 | 核心机制 | 派生 |")
            continue
        if line == "|:---:|:---|:---|:---|:---|":
            restored.append("|:---:|:---|:---|:---|")
            continue
        m = ROW_RE.match(line)
        if m and cur:
            pos1 = line.rfind(" | ")
            pos2 = line.rfind(" | ", 0, pos1)
            restored.append(line[:pos2] + " |")
            continue
        restored.append(line)
    if restored != lines:
        errors.append(f"{rel}: 还原一致性断言失败（正文被意外改动）")

    # 尾注追加
    if not any("批次 55" in l for l in out):
        # 找尾注行（最后一个 *...* 行）后插入
        for i in range(len(out) - 1, -1, -1):
            if out[i].startswith("*本文件由回填脚本"):
                out.insert(i + 1, "")
                out.insert(i + 2, FOOT_NOTE)
                break
        else:
            errors.append(f"{rel}: 未找到尾注行")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    report.append(f"{rel}: OK（{sum(len(v) for v in cats.values())} 条）")

print("\n".join(report))
print(f"总覆盖：{total}")
if errors:
    print("!! 断言失败：")
    print("\n".join(errors[:50]))
    sys.exit(1)
print("全部断言通过")
