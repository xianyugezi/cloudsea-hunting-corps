# -*- coding: utf-8 -*-
"""批次 55 完成判据独立验证（对 HEAD 原版与盘上终版）"""
import re
import subprocess
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

BASE = r"D:\1V1TXTRPG\yunhai\cloudsea-hunting-corps"
REL = list(ARCHIVES.keys())
PLOT = {  # 剧情生态: 承载线编号
    "阶段一_微澜/04_灰岗旧港.md": "G1",
    "阶段四_怒涛/04_落岛安置营.md": "A4",
    "阶段五_风暴/04_静眼观测台.md": "G7",
    "阶段六_狂岚/04_晖环残泊.md": "G8",
    "阶段六_狂岚/05_打捞场 · 云海浅滩.md": "A7",
    "阶段七_浩劫/05_渊喉回声台.md": "G13",
}
HEAD_RAW = "01c555a"  # 48 收口提交：17_ 尚无档案（=55 开工原版）

ok, fail = [], []


def git_show(tag, rel):
    r = subprocess.run(["git", "-C", BASE, "show", f"{tag}:17_世界内容与生态/{rel}"],
                       capture_output=True)
    return r.stdout.decode("utf-8")


ROW5 = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")
all_texts = []
total = 0
for rel in REL:
    new = open(f"{BASE}\\17_世界内容与生态\\{rel}", encoding="utf-8").read().replace("\r", "").split("\n")
    old = git_show(HEAD_RAW, rel).replace("\r", "").split("\n")

    # 判据③ 命名内容与 ecology.rule 零改动：盘上删档案列 + 删尾注后 ≡ 原版
    strip = []
    for ln in new:
        if ln.startswith("*猎获档案于 2026-09-07"):
            continue
        m = ROW5.match(ln)
        if m and ln.count(" | ") >= 4 and ln.split(" | ")[-1].rstrip(" |").endswith(("。", "！", "？", "」", "）")) or (m and " | " in ln and ln.rstrip().endswith("|") and len(ln.split(" | ")) == 5):
            parts = ln.split(" | ")
            if len(parts) == 5:
                strip.append(" | ".join(parts[:4]) + " |")
                all_texts.append((rel, parts[4].strip()))
                continue
        if ln == "| # | 名字 | 核心机制 | 派生 | 猎获档案 |":
            strip.append("| # | 名字 | 核心机制 | 派生 |")
            continue
        if ln == "|:---:|:---|:---|:---|:---|":
            strip.append("|:---:|:---|:---|:---|")
            continue
        strip.append(ln)
    while strip and strip[-1] == "":
        strip.pop()
    old_cmp = list(old)
    while old_cmp and old_cmp[-1] == "":
        old_cmp.pop()
    if strip == old_cmp:
        ok.append(f"{rel}: 还原一致性 ✓")
    else:
        for a, b in zip(strip, old):
            if a != b:
                fail.append(f"{rel}: 还原不一致 [{a[:60]}] vs [{b[:60]}]")
                break
        else:
            fail.append(f"{rel}: 还原不一致（行数 {len(strip)}/{len(old_cmp)}）")

    # 判据⑤ 行数
    n = len(new)
    (ok if n <= 400 else fail).append(f"{rel}: 行数 {n} {'✓' if n <= 400 else '✗ 超400'}")
    total += len([1 for ln in new if ln.count(" | ") == 4 and ROW5.match(ln) and len(ln.split(" | ")) == 5])

# 判据① 覆盖 409
(ok if total == 409 else fail).append(f"判据① 覆盖 {total}/409 {'✓' if total == 409 else '✗'}")
(ok if len(all_texts) == 409 else fail).append(f"档案句提取 {len(all_texts)}/409 {'✓' if len(all_texts) == 409 else '✗'}")

# 每句 ≤40 字
long_fail = []
for rel, t in all_texts:
    for s in t.split("。"):
        s = s.strip()
        if s and len(s) > 40:
            long_fail.append(f"{rel}: [{len(s)}] {s}")
(ok if not long_fail else fail).append(f"判据③ 每句≤40字 {'✓' if not long_fail else '✗ ' + str(long_fail[:3])}")

# 全库唯一（409 条两两）
uniq = len(set(t for _, t in all_texts)) == 409
(ok if uniq else fail).append(f"档案句全库唯一 ✓/✗ {'✓' if uniq else '✗ 有重复'}")

# 判据② 剧情生态引 G/A 编号
for rel, code in PLOT.items():
    txts = [t for r, t in all_texts if r == rel]
    hit = sum(1 for t in txts if code in t)
    (ok if hit >= 1 else fail).append(f"判据② {rel} 引 {code}：{hit} 处 {'✓' if hit >= 1 else '✗'}")

# 终盘「击破纪念」覆盖：主线终盘 27 只含、剧情终盘 2 只不含
kb, kbn = 0, 0
for rel, cats in ARCHIVES.items():
    path = f"{BASE}\\17_世界内容与生态\\{rel}"
    txt = open(path, encoding="utf-8").read()
    sec = re.search(r"### 终盘巨兽（\d+）(.*?)(?=\n### |\n---)", txt, re.S)
    if not sec:
        continue
    for ln in sec.group(1).split("\n"):
        m = ROW5.match(ln)
        if not m or len(ln.split(" | ")) != 5:
            continue
        last = ln.split(" | ")[-1].strip()
        if rel in PLOT:
            if "击破纪念" not in last:
                kbn += 1
        else:
            if "击破纪念" in last:
                kb += 1
(ok if kb == 27 else fail).append(f"主线终盘击破纪念句 {kb}/27 {'✓' if kb == 27 else '✗'}")
(ok if kbn == 2 else fail).append(f"剧情终盘互文句（无击破纪念）{kbn}/2 {'✓' if kbn == 2 else '✗'}")

# 掉落点名抽查（对照 06 号十四类矩阵与 §二·3 名目，白名单＝创作期已核对项）
WHITELIST = ["鳞革", "骸骨系", "骸骨类", "骸骨正料", "矿石系", "羽丝系", "羽毛", "翎羽", "鸦羽", "绒羽", "鸣羽",
             "零件类", "木材类", "石料", "猎获处理", "王鳞", "盘旋鸢翎", "少息岩衣", "峰隙虚翎", "封印字料"]
named = []
for rel, t in all_texts:
    for w in WHITELIST:
        if w in t:
            named.append((rel, w))
sample = named[:30]
(ok if len(named) >= 20 else fail).append(f"掉落点名可核样本 {len(named)} 处（≥20）{'✓' if len(named) >= 20 else '✗'}；抽查前 30：{sample[:5]}…")

print("=== PASS ===")
print("\n".join(ok))
print("=== FAIL ===")
print("\n".join(fail) if fail else "（无）")
sys.exit(1 if fail else 0)
