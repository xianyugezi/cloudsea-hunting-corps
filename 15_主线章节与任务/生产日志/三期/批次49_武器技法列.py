# -*- coding: utf-8 -*-
"""批次 49 · 武器名录技法列：基础/云兽/商店/填充标「无技法」、遗械「绝技即第四态」、专械「改流玩法」＋00 索引技法三态总表"""
import io, sys

D = r"D:\1V1TXTRPG\yunhai\cloudsea-hunting-corps\18_装备与素材图鉴\武器名录"

def add_col(path, header_old, header_new, sep_old, sep_new, colval_map, tag):
    """在数据行的指定锚列后插入技法列。colval_map: {首列前缀: 技法文本} 或 全部统一文本"""
    t = io.open(path, encoding="utf-8").read()
    if header_old not in t:
        print(f"[FAIL] {tag} 表头未找到"); sys.exit(1)
    t = t.replace(header_old, header_new, 1)
    t = t.replace(sep_old, sep_new, 1)
    lines = t.split("\n"); cnt = 0
    for i, ln in enumerate(lines):
        if not ln.startswith("| ") or "---" in ln:
            continue
        cells = ln.split("|")
        for prefix, val in colval_map.items():
            if ln.startswith(prefix):
                # 在第 ins_after 列后插值
                cells.insert(ins_after + 1, " " + val + " ")
                lines[i] = "|".join(cells); cnt += 1
                break
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print(f"{tag}: {cnt} 行")
    return cnt

# ---- 01 基础与专械（三表） ----
p = D + r"\01_基础与专械.md"
t = io.open(p, encoding="utf-8").read()
# §一 基础 14：武器列后插「技法」＝无技法
t = t.replace("| 武器 | 模式 | 段/次 |", "| 武器 | 技法 | 模式 | 段/次 |", 1)
t = t.replace("|---|---|:---:|---:|---|---|:---:|---|---|:---:|", "|---|---|---|---|:---:|---:|---|---|:---:|---|---|:---:|", 1)
# 上面分隔行替换有风险，改为按原分隔串精确替换
t = io.open(p, encoding="utf-8").read()
if "| 武器 | 技法 | 模式 |" not in t:
    t = t.replace("| 武器 | 模式 | 段/次 |", "| 武器 | 技法 | 模式 | 段/次 |", 1)
    # §一 分隔行：|---|---|:---:|---:|---|---|:---:|---|:---:|
    t = t.replace("|---|---|:---:|---:|---|:---:|---:|---|:---:|", "|---|---|---|:---:|---:|---|:---:|---:|---|:---:|", 1)
lines = t.split("\n"); c1 = 0
in_sec1 = False
for i, ln in enumerate(lines):
    if ln.startswith("| 🗡️巨剑 | 单段·重"):
        in_sec1 = True
    if ln.startswith("## §二"):
        in_sec1 = False
    if in_sec1 and ln.startswith("| ") and "---" not in ln and "技法" not in ln and ln.count("|") >= 10:
        cells = ln.split("|")
        cells.insert(2, " 无技法 ")
        lines[i] = "|".join(cells); c1 += 1
t = "\n".join(lines)
print(f"01 §一 基础技法列：{c1}（应 14）")

# §二 遗械 14：遗械名列后插「技法」＝绝技即第四态
t = t.replace("| 遗械名 | 原型武器 |", "| 遗械名 | 技法 | 原型武器 |", 1)
t = t.replace("|---|---|---|---|---|---|:---:|---|", "|---|---|---|---|---|---|---|:---:|---|", 1)
lines = t.split("\n"); c2 = 0
in_sec2 = False
for i, ln in enumerate(lines):
    if ln.startswith("## §二"):
        in_sec2 = True
    if ln.startswith("## §三"):
        in_sec2 = False
    if in_sec2 and ln.startswith("| ") and "---" not in ln and "遗械名" not in ln and ln.startswith("| 渊") or (in_sec2 and ln.startswith("| 潮痕长刀")):
        cells = ln.split("|")
        cells.insert(2, " 绝技即第四态 ")
        lines[i] = "|".join(cells); c2 += 1
t = "\n".join(lines)
print(f"01 §二 遗械技法列：{c2}（应 14）")

# §三 专械 5：专械名列后插「技法」＝改流玩法
t = t.replace("| 专械 | 流派 |", "| 专械 | 技法 | 流派 |", 1)
t = t.replace("|---|---|---|:---:|---|---|:---:|", "|---|---|---|---|:---:|---|---|:---:|", 1)
lines = t.split("\n"); c3 = 0
in_sec3 = False
for i, ln in enumerate(lines):
    if ln.startswith("## §三"):
        in_sec3 = True
    if ln.startswith("## §四"):
        in_sec3 = False
    if in_sec3 and ln.startswith("| ") and "---" not in ln and "专械 |" not in ln and ("之" in ln.split("|")[1] if len(ln.split("|")) > 1 else False):
        cells = ln.split("|")
        cells.insert(2, " 改流玩法 ")
        lines[i] = "|".join(cells); c3 += 1
t = "\n".join(lines)
print(f"01 §三 专械技法列：{c3}（应 5）")

# 文头注记补技法声明
t = t.replace(
    "本册由旧 `04_武器名录.md` §一/§三/§四 原样迁入（三期批次 48，派生线另立分册）。",
    "本册由旧 `04_武器名录.md` §一/§三/§四 原样迁入（三期批次 48，派生线另立分册）。\n> **技法列（三期批次 49）**：基础 14 行标「无技法」（白板基型，不参与演化）；遗械 14 行注「绝技即第四态」（`08_羁绊特效设计` §二）；专械 5 行注「改流玩法」（云顶「阵容定义者」型特质）；14 类技法三态总表见 `00_索引与自检.md` §二·补。",
    1)
io.open(p, "w", encoding="utf-8", newline="\n").write(t)

# ---- 02 云兽 24 ----
p = D + r"\02_云兽武器.md"
t = io.open(p, encoding="utf-8").read()
t = t.replace("| 武器名 | 技系 | 武器类型 |", "| 武器名 | 技法 | 技系 | 武器类型 |", 1)
t = t.replace("|---|---|---|---|---|:---:|", "|---|---|---|---|---|---|:---:|", 1)
lines = t.split("\n"); c4 = 0
for i, ln in enumerate(lines):
    if ln.startswith("| ") and "---" not in ln and "武器名" not in ln and "·攻系·" in ln or (ln.startswith("| ") and "·疗系·" in ln) or (ln.startswith("| ") and "·陷系·" in ln) or (ln.startswith("| ") and "·搬系·" in ln):
        cells = ln.split("|")
        cells.insert(2, " 无技法 ")
        lines[i] = "|".join(cells); c4 += 1
t = "\n".join(lines)
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(f"02 云兽技法列：{c4}（应 24）")

# ---- 03 商店 308 ----
p = D + r"\03_商店武器.md"
t = io.open(p, encoding="utf-8").read()
t = t.replace("| 档位 | 武器名 | 武器类型 |", "| 档位 | 武器名 | 技法 | 武器类型 |", 1)
t = t.replace("|---:|---|---|---|---|:---:|", "|---:|---|---|---|---|---|:---:|", 1)
lines = t.split("\n"); c5 = 0
for i, ln in enumerate(lines):
    if ln.startswith("| ") and "---" not in ln and "武器名" not in ln:
        cells = ln.split("|")
        if len(cells) >= 7 and cells[1].strip().isdigit():
            cells.insert(3, " 无技法 ")
            lines[i] = "|".join(cells); c5 += 1
t = "\n".join(lines)
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(f"03 商店技法列：{c5}（应 308）")

# ---- 04 填充 14 ----
p = D + r"\04_填充武器.md"
t = io.open(p, encoding="utf-8").read()
t = t.replace("| 武器名 | 武器类型 | 定位 |", "| 武器名 | 技法 | 武器类型 | 定位 |", 1)
t = t.replace("|---|---|---|---|---|:---:|", "|---|---|---|---|---|---|:---:|", 1)
lines = t.split("\n"); c6 = 0
for i, ln in enumerate(lines):
    if ln.startswith("| 操演·"):
        cells = ln.split("|")
        cells.insert(2, " 无技法 ")
        lines[i] = "|".join(cells); c6 += 1
t = "\n".join(lines)
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(f"04 填充技法列：{c6}（应 14）")

if not (c1 == 14 and c2 == 14 and c3 == 5 and c4 == 24 and c5 == 308 and c6 == 14):
    print("[FAIL] 计数不符"); sys.exit(1)
print("技法列 DONE")
