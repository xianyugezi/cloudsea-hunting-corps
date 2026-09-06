# -*- coding: utf-8 -*-
"""批次 49 · 完成判据 ①–⑥ 程序化验证 v2"""
import io, re, glob, sys, subprocess

os_root = r"D:\1V1TXTRPG\yunhai\cloudsea-hunting-corps"
FAIL = []
def ok(tag, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + tag + ("  " + detail if detail else ""))
    if not cond:
        FAIL.append(tag)

# ---------- 词表技能名集合（仅 §三 六线表区域） ----------
t07 = io.open(os_root + r"\18_装备与素材图鉴\07_技能词表.md", encoding="utf-8").read()
sec3 = t07.split("## §三")[1].split("## §四")[0]
skills = set()
for ln in sec3.split("\n"):
    m = re.match(r"^\| ([^|]{2,12}) \|", ln)
    if m and "---" not in ln:
        name = re.sub(r"（.*?）", "", m.group(1).strip())
        if name and name != "技能":
            skills.add(name)
ok("词表技能名提取", len(skills) == 26, f"{len(skills)}: {'、'.join(sorted(skills))}")

def extract_skill_refs(text):
    found = set()
    for s in skills:
        if re.search(s + r"[①②③]", text):
            found.add(s)
    return found

SLOTS = ("头", "躯干", "手套", "护腿", "鞋")

# ---------- 判据①：01 分册 ----------
t01 = io.open(os_root + r"\18_装备与素材图鉴\01_新手商店基础套.md", encoding="utf-8").read()
n_inh = 0; bad = []
for ln in t01.split("\n"):
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    slot_i = next((i for i in range(1, len(cells)) if cells[i] in SLOTS), None)
    if slot_i is not None and slot_i + 2 < len(cells):
        v = cells[slot_i + 2]
        if v == "—" or extract_skill_refs(v):
            n_inh += 1
        else:
            bad.append(ln[:44])
ok("①·01分册165行固有技能全词表语汇（含新手5/填充20『—』）", n_inh == 165 and not bad, f"{n_inh}/165 {bad[:2]}")
shop_ov = 0
for ln in t01.split("\n"):
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    if len(cells) >= 6 and cells[1].isdigit() and re.fullmatch(r"\**\d/\d\**", cells[3]):
        if extract_skill_refs(cells[4]):
            shop_ov += 1
ok("①·01商店22总览行词表语汇", shop_ov == 22, f"{shop_ov}/22")
ok("①·01新手套无套装效果", "套装效果：**无**（纯引导套" in t01)
ok("①·01基础6套进阶升档指引", t01.count("进阶后按方向升档，见 `02_` §二") == 6)
ok("①·01填充4套保持无效果", t01.count("填充位：效果—，不设激活档位") == 4)

# ---------- 判据①：02 分册 ----------
t02 = io.open(os_root + r"\18_装备与素材图鉴\02_进阶套.md", encoding="utf-8").read()
n_dir = 0; bad2 = []
for ln in t02.split("\n"):
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    # 巨兽系行：星段列以★开头 → 方向=cells[5]
    if len(cells) >= 9 and cells[4].startswith("★"):
        if extract_skill_refs(cells[5]):
            n_dir += 1
        else:
            bad2.append(ln[:44])
    # 进阶云兽行
    elif len(cells) >= 10 and "（进阶·" in cells[1]:
        if not extract_skill_refs(cells[5]):
            bad2.append("02进阶:" + ln[:44])
ok("①·02巨兽系302行方向列词表语汇", n_dir == 302 and not bad2, f"{n_dir}/302")
n_adv = sum(1 for ln in t02.split("\n") if ln.startswith("| ") and "（进阶·甲） |" in ln) + \
        sum(1 for ln in t02.split("\n") if ln.startswith("| ") and "（进阶·乙） |" in ln)
ok("①·02进阶云兽12行双方向绑技词表语汇", n_adv == 12 and not bad2, f"{n_adv}/12")
ok("①·02激活断点（模板表＋302行＝52/88/168）",
   t02.count("| 2/3 |") == 52 and t02.count("| 2/4 |") == 88 and t02.count("| 2/4/5 |") == 168,
   f"{t02.count('| 2/3 |')}/{t02.count('| 2/4 |')}/{t02.count('| 2/4/5 |')}")
ok("①·02模板表固有技能模板列", "固有技能（部件模板）" in t02)

# ---------- 判据①：03 分册 ----------
t03 = io.open(os_root + r"\18_装备与素材图鉴\03_王骸套与散件.md", encoding="utf-8").read()
n_king = 0
for ln in t03.split("\n"):
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    if len(cells) >= 8 and "王骸（" in cells[1]:
        if extract_skill_refs(cells[5]) and cells[6] == "2/4/5":
            n_king += 1
ok("①·03王骸153行效果词表语汇＋激活2/4/5", n_king == 153, f"{n_king}/153")
ok("①·03小套装7选2/3口径", "7 选 2＝固有①档、选 3＝质变段" in t03)
ok("①·03散件注记v2", "语汇取 `07_技能词表` §三 ① 档" in t03)

# 新造名唯一性
for nm in ["巨兽威压·守", "巨兽威压·疾", "巨兽威压·蚀", "王骸威压·御", "王骸威压·蚀",
           "磐岩纹章", "轻行纹章", "焰骨纹章", "雾缚纹章"]:
    r = subprocess.run(["grep", "-rl", nm, ".", "--include=*.md"], capture_output=True, text=True, cwd=os_root)
    files = [f for f in r.stdout.strip().split("\n") if f and "生产日志" not in f and "生产排期" not in f]
    ok(f"①·新名唯一·{nm}", 1 <= len(files) <= 4, ",".join(files)[:70])

# ---------- 判据②：2800 行技法态 ----------
cnt_pd = 0; cnt_wg = 0
for f in glob.glob(os_root + r"\18_装备与素材图鉴\武器名录\巨兽派生\*.md"):
    for ln in io.open(f, encoding="utf-8").read().split("\n"):
        if ln.startswith("|") and "---" not in ln and "派生名" not in ln:
            if [c.strip() for c in ln.split("|")][4] in ("初形", "成形", "真形"):
                cnt_pd += 1
for f in glob.glob(os_root + r"\18_装备与素材图鉴\武器名录\王骸\*.md"):
    for ln in io.open(f, encoding="utf-8").read().split("\n"):
        if ln.startswith("|") and "---" not in ln and "王骸名" not in ln:
            if [c.strip() for c in ln.split("|")][6] in ("初形", "成形", "真形"):
                cnt_wg += 1
ok("②·派生2086＋王骸714技法态100%", cnt_pd == 2086 and cnt_wg == 714, f"{cnt_pd}+{cnt_wg}")
t01w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\01_基础与专械.md", encoding="utf-8").read()
t02w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\02_云兽武器.md", encoding="utf-8").read()
t03w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\03_商店武器.md", encoding="utf-8").read()
t04w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\04_填充武器.md", encoding="utf-8").read()
ok("②·基础14/遗械14/专械5技法标注",
   t01w.count("| 无技法 |") == 14 and t01w.count("| 绝技即第四态 |") == 14 and t01w.count("| 改流玩法 |") == 5)
ok("②·云兽24/商店308/填充14无技法",
   t02w.count("| 无技法 |") == 24 and t03w.count("| 无技法 |") == 308 and t04w.count("| 无技法 |") == 14)
t_idx = io.open(os_root + r"\18_装备与素材图鉴\武器名录\00_索引与自检.md", encoding="utf-8").read()
ok("②·14类技法三态总表在案", t_idx.count("| 🗡️巨剑 | 崩 |") == 1 and t_idx.count("§二·补") >= 2)

# ---------- 判据③ ----------
t05 = io.open(os_root + r"\18_装备与素材图鉴\05_符文与护符.md", encoding="utf-8").read()
n_charm = 0; n_emblem = 0
for ln in t05.split("\n"):
    if re.match(r"^\| \d+ \| ", ln):
        for cat in ("| 属性 |", "| 异常 |", "| 生存 |", "| 纹章 |"):
            if cat in ln:
                n_charm += 1
                if cat == "| 纹章 |":
                    n_emblem += 1
                break
ok("③·05护符26条（属性7+异常9+生存6+纹章4）", n_charm == 26 and n_emblem == 4, f"{n_charm}/{n_emblem}")
t12 = io.open(os_root + r"\12_全局常量表.md", encoding="utf-8").read()
ok("③·12号CHARM_AFFIX_POOL=26", re.search(r"CHARM_AFFIX_POOL` \| 护符词条池规模 \| `26`", t12) is not None)
ok("③·12号SKILL域10键", t12.count("| `SKILL.") == 10, str(t12.count("| `SKILL.")))

# ---------- 判据④ ----------
r = subprocess.run(["git", "status", "--porcelain", "--", "06_资源素材日常循环与经济.md"],
                   capture_output=True, text=True, cwd=os_root)
ok("④·06号零改动", r.stdout.strip() == "")
t06 = io.open(os_root + r"\06_资源素材日常循环与经济.md", encoding="utf-8").read()
ok("④·金币账锚定值在案", "≈42,000" in t06 and "≈46,000" in t06)
ok("④·经济闸声明（01/02/12）", "经济线技能过账闸" in t01 and "经济线技能过账闸" in t02 and "经济线技能过账闸" in t12)

# ---------- 判据⑤ ----------
t00 = io.open(os_root + r"\18_装备与素材图鉴\00_总则.md", encoding="utf-8").read()
ok("⑤·总则§五系羁绊与潮汇", "## §五 · 系羁绊与潮汇" in t00 and "潮汇元羁绊" in t00)
ok("⑤·8位/无上限/双层结算成文", "计数口径 8 位" in t00 and "无点亮上限" in t00 and "双层独立结算" in t00)
ok("⑤·分册表07/08翻转", t00.count("✅ 三期批次 49 回填") == 2)

# ---------- 判据⑥ ----------
for f in [r"\18_装备与素材图鉴\01_新手商店基础套.md", r"\18_装备与素材图鉴\02_进阶套.md",
          r"\18_装备与素材图鉴\03_王骸套与散件.md", r"\18_装备与素材图鉴\05_符文与护符.md",
          r"\18_装备与素材图鉴\00_总则.md", r"\18_装备与素材图鉴\武器名录\00_索引与自检.md",
          r"\18_装备与素材图鉴\武器名录\01_基础与专械.md"]:
    n = len(io.open(os_root + f, encoding="utf-8").read().split("\n"))
    ok(f"⑥·行数≤400 {f.split(chr(92))[-1]}", n <= 400, str(n))
ok("⑥·12号豁免（常量唯一出处不拆，批次52任务书豁免清单）", True, f"{len(t12.split(chr(10)))}行·豁免")
ok("⑥·自检表v2行在案", "装备效果 v2 回填（批次 49）" in t01 and "装备效果 v2 回填（批次 49）" in t02
   and "批次 49" in t03 and "批次 49 技法落地" in t_idx)

print()
if FAIL:
    print("未通过 %d 项: %s" % (len(FAIL), "、".join(FAIL)))
    sys.exit(1)
print("=== 全部判据 PASS ===")
