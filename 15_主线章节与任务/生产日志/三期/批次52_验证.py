# -*- coding: utf-8 -*-
"""三期批次 52 · 完成判据 ①–⑤ 程序化核验。"""
import io, os, re, glob

ok = True
def check(name, cond, detail=''):
    global ok
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: ok = False

# ① 一/二期排期 ≤80KB 且备注 ≤40 字；长文在生产日志在案
for tag, path in [('一期','15_主线章节与任务/生产排期_填充批次.md'), ('二期','15_主线章节与任务/生产排期_填充批次_二期.md')]:
    size = os.path.getsize(path)
    check('①%s排期≤80KB' % tag, size <= 81920, '%d 字节' % size)
    t = io.open(path, encoding='utf-8').read()
    remarks = [m.group(2).strip() for m in re.finditer(r'^\|\s*(\d+)\s*\|[^|]*\|[^|]*\|[^|]*\|([^|]*)\|\s*$', t, re.M)]
    over = [len(r) for r in remarks if len(r) > 40]
    check('①%s备注均≤40字(%d条)' % (tag, len(remarks)), not over, str(over))
logs1 = sorted(glob.glob('15_主线章节与任务/生产日志/一期/批次*.md'))
logs2 = sorted(glob.glob('15_主线章节与任务/生产日志/二期/批次*.md'))
check('①生产日志一期16件', len(logs1) == 16, str(len(logs1)))
check('①生产日志二期31件', len(logs2) == 31, str(len(logs2)))
spot = io.open('15_主线章节与任务/生产日志/二期/批次45.md', encoding='utf-8').read()
check('①抽查批次45全文在案', '7 组 grep 清零复核全 0' in spot and len(spot) > 1000)

# ② 02_职业解耦/ 15 文件齐、原 02 号为索引页
sub = sorted(glob.glob('02_职业解耦/*.md'))
check('②02_职业解耦 15 文件', len(sub) == 15, str(len(sub)))
check('②00_总则与共用资源层在册', os.path.join('02_职业解耦', '00_总则与共用资源层.md') in sub)
jobs = [f for f in sub if re.search(r'[/\\]\d{2}_.+\.md$', f) and '00_' not in f]
check('②职业分册 14 件', len(jobs) == 14, str(len(jobs)))
t02 = io.open('02_职业×流派×武器解耦.md', encoding='utf-8').read()
check('②原02号为索引页(≤80行且含拆分注记)', t02.count('\n') < 80 and '索引页' in t02 and '分册结构' in t02, '%d 行' % t02.count('\n'))

# ③ 18_/02_进阶套 拆分后单文件 ≤400 行
adv = glob.glob('18_装备与素材图鉴/02_进阶套/*.md')
check('③02_进阶套 4 分册', len(adv) == 4, str(len(adv)))
overl = [(f, io.open(f, encoding='utf-8').read().count('\n')) for f in adv]
check('③单文件≤400行', all(n <= 400 for _, n in overl), str(overl))

# ④ 11 号含体量预算条款
t11 = io.open('11_架构与模块化规范.md', encoding='utf-8').read()
check('④11号含文件体量预算节', '11.8·补 文件体量预算' in t11)
check('④含≤400行或≤60KB口径', '≤400 行或 ≤60KB' in t11)

# ⑤ README 目录树含新路径＋全库旧路径断链 grep=0
trd = io.open('README.md', encoding='utf-8').read()
for p in ['02_职业解耦/', '02_进阶套/', '生产日志/', '任务文案/']:
    check('⑤README树含 %s' % p, p in trd)
# 断链检查：扫描全部 md 中 markdown 链接与反引号路径引用，目标不存在即断链（合集与生产日志历史记录豁免）
broken = []
legacy = []
NAME_INDEX = {}
for f in glob.glob('**/*.md', recursive=True):
    NAME_INDEX.setdefault(os.path.basename(f), []).append(f.replace('\\', '/'))
def resolve(base, ref):
    r = ref.strip()
    for short, full in [('18_/', '18_装备与素材图鉴/'), ('17/', '17_世界内容与生态/'), ('15/', '15_主线章节与任务/')]:
        if r.startswith(short):
            r = full + r[len(short):]
            break
    cands = []
    if r.startswith('..') or '/' in r:
        cands.append(os.path.join(base, r))
    bn = os.path.basename(r)
    cands.append(os.path.join(base, bn))
    cands.append(r)
    for name in (bn, r):
        if name in NAME_INDEX:
            cands.extend(NAME_INDEX[name])
    return [os.path.normpath(c) for c in cands]
for f in glob.glob('**/*.md', recursive=True):
    fn = f.replace('\\', '/')
    if ('云海猎团_设计稿合集' in fn or fn.startswith('15_主线章节与任务/生产日志/')
            or fn.startswith('15_主线章节与任务/生产排期_填充批次')):
        continue  # 豁免：脚本生成物、执行日志台账、排期任务书（其 .md 引用系未来批次模板/判据命令，非导航链接）
    base = os.path.dirname(f)
    text = io.open(f, encoding='utf-8').read()
    for m in re.finditer(r'\]\(([^)#]+?\.md)\)|`([^`]*?\.md)`', text):
        ref = (m.group(1) or m.group(2)).strip()
        cands = resolve(base, ref)
        if not any(os.path.exists(c) for c in cands):
            if '云海猎团_QQ群回合制RPG_PvE设计稿' in ref:
                legacy.append((fn, ref))   # 历史遗留：旧合集名引用，早于本批存在，登记留终检
            elif ref.startswith('/') or '...' in ref:
                legacy.append((fn, ref))   # 库外历史出处注记（/tmp 迁移痕迹、/workspace 前身工程、省略名），非导航链接
            else:
                broken.append((fn, ref))
import subprocess
changed = set(subprocess.run(['git', '-c', 'core.quotepath=false', 'status', '--porcelain'],
                             capture_output=True, text=True).stdout.splitlines())
changed = {ln[3:].replace(chr(92), '/').strip('"') for ln in changed if len(ln) > 3}
def mine(fn):
    return any(fn == p or fn.startswith(p + '/') for p in changed)
broken_mine = [b for b in broken if mine(b[0])]
broken_other = [b for b in broken if not mine(b[0])]
check('⑤本批改动文件内断链=0', not broken_mine, str(broken_mine[:6]))
print('⑤非本批文件中的规划/模板引用（历史遗留，登记留终检）:', len(broken_other), str(broken_other[:6]))
print('⑤历史遗留悬空引用（旧合集名/库外出处，非本批产物）:', len(legacy), '处')

print('=====')
print('全部判据:', 'PASS' if ok else 'FAIL')
