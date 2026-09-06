# -*- coding: utf-8 -*-
"""批次 49 · 完成判据 ①–⑥ 程序化验证"""
import io, re, glob, sys, subprocess

os_root = r"D:\1V1TXTRPG\yunhai\cloudsea-hunting-corps"
FAIL = []
def ok(tag, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + tag + ("  " + detail if detail else ""))
    if not cond:
        FAIL.append(tag)

# ---------- 词表技能名集合（07 §三表格数据行） ----------
t07 = io.open(os_root + r"\18_装备与素材图鉴\07_技能词表.md", encoding="utf-8").read()
skills = set()
for ln in t07.split("\n"):
    m = re.match(r"^\| ([^|]{2,12}) \|", ln)
    if m and "---" not in ln:
        name = m.group(1).strip()
        name = re.sub(r"（.*?）", "", name)
        if name and name not in ("技能",):
            skills.add(name)
print("词表技能名 %d 个: %s" % (len(skills), "、".join(sorted(skills))))
ok("词表24+2技提取", len(skills) >= 24)

# ---------- 判据①：01–03 两字段齐＋技能名可检索 ----------
def extract_skill_refs(text):
    """提取文本中出现的词表技能名（X①/X②/X③ 形式）"""
    found = set()
    for s in skills:
        if re.search(s + r"[①②③]", text):
            found.add(s)
    return found

# 01 分册：165 条目行固有技能非空＋22 总览＋6 基础首列
t01 = io.open(os_root + r"\18_装备与素材图鉴\01_新手商店基础套.md", encoding="utf-8").read()
lines = t01.split("\n")
n_inherent = 0; bad01 = []
shop_ov = 0; base_fx = 0
for ln in lines:
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    # 商店条目：档|套名|槽位|部件|固有|…
    if len(cells) >= 6 and cells[1].isdigit() and cells[3] in ("头", "躯干", "手套", "护腿", "鞋"):
        if cells[5] == "—" or extract_skill_refs(cells[5]):
            n_inherent += 1
        else:
            bad01.append("01商店固有:" + ln[:40])
    # 基础条目：套名（效果）|槽位|部件|固有|…
    elif len(cells) >= 6 and cells[2] in ("头", "躯干", "手套", "护腿", "鞋"):
        if cells[4] == "—" or extract_skill_refs(cells[4]):
            n_inherent += 1
        else:
            bad01.append("01基础固有:" + ln[:40])
    # 商店总览：档|套名|激活|效果|渠道
    elif len(cells) >= 5 and cells[1].isdigit() and re.match(r"^[0-9/]+$", cells[3]):
        if extract_skill_refs(cells[4]) or "无（纯引导" in cells[4]:
            shop_ov += 1
        else:
            bad01.append("01商店总览:" + ln[:40])
    # 基础首列效果
    elif len(cells) >= 6 and cells[2] in ("头", "躯干", "手套", "护腿", "鞋"):
        pass
ok("01·165行固有技能全词表语汇", n_inherent == 165 and not bad01, f"{n_inherent}/165")
ok("01·商店22总览行词表语汇", shop_ov == 22, f"{shop_ov}/22")
ok("01·新手套无套装效果", "套装效果：**无**（纯引导套" in t01)
ok("01·基础6套首列词表语汇＋进阶指引", t01.count("进阶后按方向升档，见 `02_` §二") == 6)
ok("01·激活模板注记 2/4", "激活档位 2／4：2 件①档＋4 件②档" in t01)

# 02 分册：302 行方向列＋12 行进阶
t02 = io.open(os_root + r"\18_装备与素材图鉴\02_进阶套.md", encoding="utf-8").read()
n_dir = 0; bad02 = []
for ln in t02.split("\n"):
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    if len(cells) >= 6 and "套装" in cells[1] and cells[4].startswith(("均衡（", "重装（", "轻装（", "异装（")):
        if extract_skill_refs(cells[4]):
            n_dir += 1
        else:
            bad02.append(ln[:50])
    elif len(cells) >= 6 and "（进阶·" in cells[1]:
        if not extract_skill_refs(cells[5]):
            bad02.append("02进阶:" + ln[:50])
ok("02·302行方向列词表语汇", n_dir == 302 and not bad02, f"{n_dir}/302")
ok("02·激活断点 2/3·2/4·2/4/5", t02.count("| 2/3 |") == 51 and t02.count("| 2/4 |") == 86 and t02.count("| 2/4/5 |") == 165,
   f"2/3×{t02.count('| 2/3 |')} 2/4×{t02.count('| 2/4 |')} 2/4/5×{t02.count('| 2/4/5 |')}")
ok("02·模板表含固有技能模板列", "固有技能（部件模板）" in t02)
ok("02·进阶12行双方向绑技", t02.count("（进阶·甲）") == 6 and t02.count("（进阶·乙）") == 6)

# 03 分册：153 行
t03 = io.open(os_root + r"\18_装备与素材图鉴\03_王骸套与散件.md", encoding="utf-8").read()
n_king = 0
for ln in t03.split("\n"):
    if not ln.startswith("| ") or "---" in ln:
        continue
    cells = [c.strip() for c in ln.split("|")]
    if len(cells) >= 6 and cells[1].endswith("王骸）") and "王骸" in cells[1]:
        if extract_skill_refs(cells[5]) and cells[6] == "2/4/5":
            n_king += 1
ok("03·153行方向效果词表语汇＋激活2/4/5", n_king == 153, f"{n_king}/153")
ok("03·小套装 7选2/3 口径成文", "7 选 2＝固有①档、选 3＝质变段" in t03)
ok("03·散件注记 v2", "语汇取 `07_技能词表` §三 ① 档" in t03)

# 新造名全库唯一（全库 grep 文件集合核验）
newnames = ["巨兽威压·守", "巨兽威压·疾", "巨兽威压·蚀", "王骸威压·御", "王骸威压·蚀", "磐岩纹章", "轻行纹章", "焰骨纹章", "雾缚纹章"]
for nm in newnames:
    r = subprocess.run(["grep", "-rl", nm, ".", "--include=*.md"], capture_output=True, text=True, cwd=os_root)
    files = [f for f in r.stdout.strip().split("\n") if f and "生产日志" not in f and "生产排期" not in f and "合集" not in f]
    ok(f"新名唯一·{nm}", len(files) <= 5, ",".join(files)[:80])

# ---------- 判据②：2800 行技法态 ----------
cnt_pd = 0; cnt_wg = 0
for f in glob.glob(os_root + r"\18_装备与素材图鉴\武器名录\巨兽派生\*.md"):
    for ln in io.open(f, encoding="utf-8").read().split("\n"):
        if ln.startswith("|") and "---" not in ln and "派生名" not in ln:
            cells = [c.strip() for c in ln.split("|")]
            if cells[4] in ("初形", "成形", "真形"):
                cnt_pd += 1
for f in glob.glob(os_root + r"\18_装备与素材图鉴\武器名录\王骸\*.md"):
    for ln in io.open(f, encoding="utf-8").read().split("\n"):
        if ln.startswith("|") and "---" not in ln and "王骸名" not in ln:
            cells = [c.strip() for c in ln.split("|")]
            if cells[6] in ("初形", "成形", "真形"):
                cnt_wg += 1
ok("②·派生2086＋王骸714技法态100%", cnt_pd == 2086 and cnt_wg == 714, f"{cnt_pd}+{cnt_wg}={cnt_pd+cnt_wg}")
# 无技法/第四态/改流玩法标注
t01w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\01_基础与专械.md", encoding="utf-8").read()
t02w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\02_云兽武器.md", encoding="utf-8").read()
t03w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\03_商店武器.md", encoding="utf-8").read()
t04w = io.open(os_root + r"\18_装备与素材图鉴\武器名录\04_填充武器.md", encoding="utf-8").read()
ok("②·基础14无技法/遗械14第四态/专械5改流",
   t01w.count("| 无技法 |") == 14 and t01w.count("| 绝技即第四态 |") == 14 and t01w.count("| 改流玩法 |") == 5,
   f"无技法{t01w.count('| 无技法 |')}/第四态{t01w.count('| 绝技即第四态 |')}/改流{t01w.count('| 改流玩法 |')}")
ok("②·云兽24/商店308/填充14无技法",
   t02w.count("| 无技法 |") == 24 and t03w.count("| 无技法 |") == 308 and t04w.count("| 无技法 |") == 14,
   f"{t02w.count('| 无技法 |')}/{t03w.count('| 无技法 |')}/{t04w.count('| 无技法 |')}")
ok("②·14类技法三态总表在案", t_idx.count("| 🗡️巨剑 | 崩 |") == 1 if (t_idx := io.open(os_root + r"\18_装备与素材图鉴\武器名录\00_索引与自检.md", encoding="utf-8").read()) else False)

# ---------- 判据③：05 护符 26＋纹章 4；12 号 POOL=26 ----------
t05 = io.open(os_root + r"\18_装备与素材图鉴\05_符文与护符.md", encoding="utf-8").read()
n_charm = 0; n_emblem = 0
for ln in t05.split("\n"):
    m = re.match(r"^\| (\d+) \| ", ln)
    if m and 1 <= int(m.group(1)) <= 26 and ("混装" in ln or "属性" in ln or "异常" in ln or "生存" in ln):
        n_charm += 1
    if "| 纹章 |" in ln:
        n_emblem += 1
ok("③·护符26条", n_charm == 26, f"{n_charm}")
ok("③·纹章4条", n_emblem == 4, f"{n_emblem}")
t12 = io.open(os_root + r"\12_全局常量表.md", encoding="utf-8").read()
ok("③·12号 POOL=26", re.search(r"CHARM_AFFIX_POOL` \| 护符词条池规模 \| `26`", t12) is not None)
ok("③·12号 SKILL 域 10 键", t12.count("| `SKILL.") == 10, f"{t12.count('| `SKILL.')}")

# ---------- 判据④：06 号金币账不变 ----------
r = subprocess.run(["git", "status", "--porcelain", "--", "06_资源素材日常循环与经济.md"],
                   capture_output=True, text=True, cwd=os_root)
ok("④·06号零改动", r.stdout.strip() == "", r.stdout.strip())
t06 = io.open(os_root + r"\06_资源素材日常循环与经济.md", encoding="utf-8").read()
ok("④·金币账锚定值 42,000/46,000 在案", "≈42,000" in t06 and "≈46,000" in t06)
ok("④·经济闸声明（01/02/12）", "经济线技能过账闸" in t01 and "经济线技能过账闸" in t02 and "经济线技能过账闸" in t12)

# ---------- 判据⑤：00_总则系羁绊/潮汇节 ----------
t00 = io.open(os_root + r"\18_装备与素材图鉴\00_总则.md", encoding="utf-8").read()
ok("⑤·总则§五系羁绊与潮汇", "## §五 · 系羁绊与潮汇" in t00 and "潮汇元羁绊" in t00)
ok("⑤·计数口径8位/无点亮上限/双层独立结算成文", "计数口径 8 位" in t00 and "无点亮上限" in t00 and "双层独立结算" in t00)
ok("⑤·分册表 07/08 翻转已回填", t00.count("✅ 三期批次 49 回填") == 2)

# ---------- 判据⑥：文件行数 ≤400（纪律 10）＋自检表更新 ----------
for f, lim in [(r"\18_装备与素材图鉴\01_新手商店基础套.md", 400), (r"\18_装备与素材图鉴\02_进阶套.md", 400),
               (r"\18_装备与素材图鉴\03_王骸套与散件.md", 400), (r"\18_装备与素材图鉴\05_符文与护符.md", 400),
               (r"\18_装备与素材图鉴\00_总则.md", 400), (r"\18_装备与素材图鉴\武器名录\00_索引与自检.md", 400),
               (r"\18_装备与素材图鉴\武器名录\01_基础与专械.md", 400), (r"\12_全局常量表.md", 400)]:
    n = len(io.open(os_root + f, encoding="utf-8").read().split("\n"))
    ok(f"⑥·行数≤400 {f.split(chr(92))[-1]}", n <= lim, str(n))
ok("⑥·自检表 v2 行（01/02/03/00索引）", "装备效果 v2 回填（批次 49）" in t01 and "批次 49 技法落地" in t_idx
   and "装备效果 v2 回填（批次 49）" in t02 and "批次 49" in t03)

print()
if FAIL:
    print("未通过 %d 项: %s" % (len(FAIL), "、".join(FAIL)))
    sys.exit(1)
print("全部判据 PASS")
