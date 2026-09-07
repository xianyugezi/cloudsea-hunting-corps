# -*- coding: utf-8 -*-
"""批次51 三期收官·全库对账断言脚本（母本落生产日志/三期/，沿批次55/57先例）"""
import re, glob, os, sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
WL = os.path.join(ROOT, '18_装备与素材图鉴', '武器名录')
SEP = re.compile(r'^\|[\s:|-]+\|$')
ok_all = True

def check(name, got, want):
    global ok_all
    ok = got == want
    ok_all = ok_all and ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}: 实测={got!r} 期={want!r}")

def data_rows(path):
    """表格数据行：按连续 | 行块分组（表格间有空行/标题隔开），每块去表头与分隔行；遇『自检』小节停止。"""
    blocks, cur, stopped = [], [], False
    for line in open(path, encoding='utf-8'):
        s = line.strip()
        if s.startswith('#') and '自检' in s:
            stopped = True
        if s.startswith('|'):
            if not stopped:
                cur.append(s)
        else:
            if cur:
                blocks.append(cur)
                cur = []
    if cur:
        blocks.append(cur)
    rows = []
    for b in blocks:
        cells_list = [c for c in b if not SEP.match(c)]
        for c in cells_list[1:]:  # 块首行=表头
            rows.append([x.strip() for x in c.strip('|').split('|')])
    return rows

def rows_upto(path, stop_pat):
    """取 stop_pat 小节之前的表格数据行。"""
    out, cur, stopped = [], [], False
    for line in open(path, encoding='utf-8'):
        s = line.strip()
        if s.startswith('##') and re.search(stop_pat, s):
            stopped = True
        if s.startswith('|'):
            if not stopped:
                cur.append(s)
        else:
            if cur:
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    rows = []
    for b in out:
        cells_list = [c for c in b if not SEP.match(c)]
        rows.extend(cells_list[1:])
    return rows

# ── A. 武器名录 3179 验算 ─────────────────────────────
os.chdir(WL)
n01 = len(rows_upto('01_基础与专械.md', r'自检表'))
n02 = len(data_rows('02_云兽武器.md'))
n03 = len(data_rows('03_商店武器.md'))
n04 = len(data_rows('04_填充武器.md'))
check('01 基础与专械(14+14+5)', n01, 33)
check('02 云兽武器', n02, 24)
check('03 商店武器', n03, 308)
check('04 填充武器', n04, 14)

beast, n_derive = defaultdict(set), 0
for p in glob.glob('巨兽派生/*.md'):
    for cells in data_rows(p):
        if len(cells) >= 5:
            n_derive += 1
            beast[cells[4]].add(cells[1])
king, n_king = defaultdict(set), 0
for p in glob.glob('王骸/*.md'):
    for cells in data_rows(p):
        if len(cells) >= 2:
            n_king += 1
            king[cells[2]].add(cells[1])
check('巨兽派生', n_derive, 2086)
check('王骸', n_king, 714)
check('来源巨兽只数', len(beast), 149)
check('终盘Boss只数', len(king), 51)
bad_b = {k: sorted(v) for k, v in beast.items() if len(v) != 14}
bad_k = {k: sorted(v) for k, v in king.items() if len(v) != 14}
check('巨兽非14类覆盖', bad_b, {})
check('Boss非14类覆盖', bad_k, {})
total = n01 + n02 + n03 + n04 + n_derive + n_king
check('武器名录合计', total, 3179)

# ── B. 铭文列对账（批次53：3179/3179 落末列，3160 句唯一）─────────
inscrip, nonempty = [], 0
def gather_inscription(path):
    global nonempty
    for cells in data_rows(path):
        if cells and cells[-1]:
            inscrip.append(cells[-1])
            if cells[-1] != '—':
                nonempty += 1
for p in ['01_基础与专械.md', '02_云兽武器.md', '03_商店武器.md', '04_填充武器.md']:
    gather_inscription(p)
for p in glob.glob('巨兽派生/*.md') + glob.glob('王骸/*.md'):
    gather_inscription(p)
check('铭文列行数', len(inscrip), 3179)
check('铭文非空句(—以外)', nonempty, 3160)
check('铭文句唯一性', len(set(x for x in inscrip if x != '—')), 3160)

# ── C. 12 号常量对账 ─────────────────────────────
t12 = open(os.path.join(ROOT, '12_全局常量表.md'), encoding='utf-8').read()
check('12号 CONTENT.WEAPON_TOTAL=3179',
      bool(re.search(r'CONTENT\.WEAPON_TOTAL.*?`3179`', t12)), True)
check('12号 CONTENT.CHARM_AFFIX_POOL=26',
      bool(re.search(r'CHARM_AFFIX_POOL.*?`26`', t12)), True)
skill_keys = sorted(set(re.findall(r'SKILL\.[A-Z0-9_]+', t12)))
check('12号 SKILL 域键数(期10)', len(skill_keys), 10)
print('INFO  SKILL 键:', skill_keys)

print('===', 'ALL PASS' if ok_all else 'HAS FAIL', '===')
sys.exit(0 if ok_all else 1)
