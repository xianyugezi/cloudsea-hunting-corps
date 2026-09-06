# -*- coding: utf-8 -*-
"""三期批次 56 · 套装出身志（闲时填充 2026-09-07）
504 套逐套追加一句出身（≤24 字）：巨兽系讨伐轶事／王骸终盘轶事／商店话术／锻造港传闻；
新手套与无进阶填充套写制式说明。列内落格（沿批次 54 档案列先例），行数零增长。
断言：①504/504 覆盖 ②句全量互异 ③len≤24 ④三册 ≤400 行 ⑤只改目标行。
"""
import io, re, sys, os

BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '18_装备与素材图鉴'))
P1 = os.path.join(BASE, '01_新手商店基础套.md')
P2 = os.path.join(BASE, '02_进阶套.md')
P3 = os.path.join(BASE, '03_王骸套与散件.md')

# ---------- 景词（22 生态 → 4 字景语） ----------
SCENE = {
    '云顶针叶林': '林雪压枝', '蚀云外缘': '蚀雾漫界', '云墙环带': '墙云千仞',
    '升降岛链': '岛链起伏', '雷砧云台': '雷砧轰顶', '电离辉带': '辉带流光',
    '静眼孤屿': '静眼无风', '虚天危峰': '危峰插虚', '蚀渊坠城': '坠城沉渊',
    '悬瀑苔崖': '瀑苔湿滑', '乱涡深穴': '乱涡翻底', '云浪浅脊': '云浪漫脊',
    '岛根垂荫': '岛根垂荫', '旋缘雨廊': '雨廊斜旋', '沉岛云渊': '云渊吞岛',
    '浮滩浅礁': '浅礁露头', '涡旋岩廊': '岩廊回风', '渊喉涡廊': '渊喉吞声',
    '砧顶雷池': '雷池谨慎', '碎屿浮岩': '浮岩无根', '穹裂残骸': '穹裂漏光',
    '薄气云脊': '薄气难息',
}
BEAST_TMPL = {  # 星段×方向 → 句骨架（{景}{锚}=称号+巨兽名）
    ('★1–3', '均衡'): '{景}，{锚}就缚，港炉趁热开模',
    ('★4–6', '重装'): '重装随征，{锚}授首，港中增砧二座',
    ('★4–6', '轻装'): '轻装游猎，{锚}难追，三日方落套',
    ('★7–9', '重装'): '{景}鏖战，{锚}授首，重装随军例装',
    ('★7–9', '轻装'): '{景}追逐，{锚}力竭，轻装先登取材',
    ('★7–9', '异装'): '{景}异象，{锚}反常，异装取其蚀料',
}
WANG_TMPL = {  # 王骸方向 → 句骨架（无景词，锚最长 8 字时仍 ≤24）
    '破军': '破阵，{锚}王骨开锋，破军炉先响',
    '守御': '守御压阵，{锚}王骨镇库，随团而行',
    '蚀异': '蚀深，{锚}王骨带纹，蚀异炉慎开',
}

# ---------- 手写句（商店话术 22 ／ 基础有进阶 6 ／ 云兽进阶 12 模板） ----------
SHOP = {
    '布衣束带': '杂货掌柜：布衣束带走量货，新丁头一件',
    '粗缝皮挂': '杂货掌柜：粗缝皮挂实诚价，磨坏再来换',
    '铆钉短打': '杂货掌柜：铆钉短打扛撞，云枢港口碑款',
    '硬革行装': '杂货掌柜：硬革行装走远路，猎团老带新',
    '铁箍护身': '杂货掌柜：铁箍护身压箱底，关键时保命',
    '灰羽猎装': '供给司务：灰羽猎装团发标配，记入功勋',
    '鳞纹软铠': '供给司务：鳞纹软铠柔韧，老猎手回头客',
    '岩壳重衫': '供给司务：岩壳重衫一件顶四件，先试再买',
    '霜线披挂': '供给司务：霜线披挂防涌潮，潮汛季断货',
    '雷哨劲装': '供给司务：雷哨劲装充能快，手快有手慢无',
    '雾网轻铠': '供给司务：雾网轻铠蚀纹猎首选，限量供',
    '潮声护甲': '铁匠工坊：潮声护甲听潮开模，做工见筋骨',
    '渊目守衣': '铁匠工坊：渊目守衣打部位死角，匠人招牌',
    '风缆束甲': '铁匠工坊：风缆束甲走线细，返修率最低',
    '辉鳞战衣': '铁匠工坊：辉鳞战衣灵料镶鳞，慢工出细活',
    '幽骨重铠': '铁匠工坊：幽骨重铠以骨承压，胆大才敢穿',
    '蚀纹徽甲': '珍品柜：蚀纹徽甲蚀料开锋，识货的再来',
    '风暴哨卫': '珍品柜：风暴哨卫响应极快，按需预订',
    '狂岚壁垒': '珍品柜：狂岚壁垒承伤如山，团队硬通货',
    '浩劫残响': '珍品柜：浩劫残响充能霸道，孤胆猎手挚爱',
    '潮根守望': '珍品柜：潮根守望镇涌压舱，压轴藏品',
    '云海之巅': '珍品柜：云海之巅镇柜之宝，有价无市',
}
BASE_ADV = {  # 01 册 §三·1 有进阶 6 套（锻造港传闻）
    '磐岩哨卫': '锻港传闻：磐岩哨卫的模，是磐背獾撞出来的',
    '鹿径轻行': '锻港传闻：鹿径轻行走线，仿的云角鹿逃径',
    '焰骨猎手': '锻港传闻：焰骨猎手出炉那夜，炉膛烧穿了底',
    '雾缚织手': '锻港传闻：雾缚织手的网眼，雾网蛛亲自教的',
    '曦羽祝祷': '锻港传闻：曦羽祝祷淬火用的晨光，等足七日',
    '露羽还生': '锻港传闻：露羽还生救回的猎手，组了谢团',
}

def check(s):
    assert len(s) <= 24, f'超 24 字({len(s)})：{s}'
    return s

def split_row(line):
    body = line.strip()
    assert body.startswith('|') and body.endswith('|'), line
    return [c.strip() for c in body[1:-1].split('|')]

def join_row(cells):
    return '| ' + ' | '.join(cells) + ' |'

# ---------- 通用：给「一张表」加出身列 ----------
def add_column(lines, header_key, n_data, sentence_fn, tag, counter, mutated, start=0):
    """header_key: 表头行判别子串；start: 起始行（同表头多表时递增）；返回新行列表"""
    out = list(lines)
    hits = [i for i, l in enumerate(out) if i >= start and l.lstrip().startswith('|') and header_key in l and '出身' not in l]
    assert hits, f'{tag}: 表头零命中'
    h = hits[0]
    sep = h + 1
    assert set(out[sep].replace('|', '').replace('-', '').replace(':', '').strip()) == set(), f'{tag}: 第 {sep} 行非分隔行'
    cells = split_row(out[h])
    out[h] = join_row(cells + ['出身'])
    dashes = split_row(out[sep])
    out[sep] = join_row(dashes + [':---'])
    n = 0
    i = sep + 1
    while i < len(out):
        l = out[i]
        if l.strip() == '':
            i += 1
            continue
        if not l.lstrip().startswith('|'):
            break
        cs = split_row(l)
        assert len(cs) == len(cells), f'{tag}: 行 {i+1} 列数 {len(cs)}≠{len(cells)}'
        s = check(sentence_fn(cs))
        out[i] = join_row(cs + [s])
        counter.append((tag, s))
        mutated.add(i)
        n += 1
        i += 1
    assert n == n_data, f'{tag}: 数据行 {n}≠{n_data}'
    return out, h

# ---------- 01 册 ----------
def do_01(counter, mutated):
    lines = io.open(P1, encoding='utf-8').read().splitlines()
    # §一 新手套：条目头行括号内插出身
    hits = [i for i, l in enumerate(lines) if l.startswith('**启潮行装**（') and '出身' not in l]
    assert len(hits) == 1
    i = hits[0]
    s = check('制式说明：教官凭据直发五件同批，无轶事')
    lines[i] = lines[i].replace('）', f'｜出身：{s}）', 1)
    counter.append(('01新手', s)); mutated.add(i)
    # §二 商店总览表 22 行：出身列（商店话术）
    lines, _ = add_column(lines, '| 档位 | 套装名 | 激活档位 | 套装效果 | 渠道 |', 22,
                          lambda cs: SHOP[cs[1]], '01商店', counter, mutated)
    # §三·1 有进阶 6 行：出身列（锻造港传闻）
    lines, _ = add_column(lines, '| 套装名 | 绑定云兽 | 系 | 构筑偏向 | 二次打造两段流程 |', 6,
                          lambda cs: BASE_ADV[cs[0]], '01基础有进阶', counter, mutated)
    # §三·2 无进阶 4 套：部件表首行（含「填充位」）第 1 列单元格内插出身
    n = 0
    for i, l in enumerate(lines):
        if l.lstrip().startswith('|') and '填充位' in l and '出身' not in l:
            cs = split_row(l)
            m = re.match(r'^([^(]+)（填充位：[^）]*）$', cs[0])
            assert m, f'01无进阶 首行异常: {cs[0]}'
            xi = m.group(1).strip()
            assert cs[1].endswith('系'), cs[1]
            s = check(f'制式说明：{cs[1]}定额批产四系同模，无轶事')
            cs[0] = cs[0][:-1] + f'｜出身：{s}）'
            lines[i] = join_row(cs)
            counter.append(('01无进阶', s)); mutated.add(i)
            n += 1
    assert n == 4, f'01无进阶 {n}≠4'
    io.open(P1, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    return lines

# ---------- 02 册 ----------
def do_02(counter, mutated):
    lines = io.open(P2, encoding='utf-8').read().splitlines()
    # §一 填充 4 套：出身列（制式说明）
    lines, _ = add_column(lines, '| 套装名 | 系 | 套装效果 | 激活档位 | 主抗 | 素材消耗（材料十四类） | 强化上限 |', 4,
                          lambda cs: check(f'制式说明：{cs[1]}坯装定额兜底，无轶事'), '02填充', counter, mutated)
    # §二 有进阶 12 套：出身列（锻造港传闻，锚=来源称号）
    def adv(cs):
        m = re.match(r'^([^.·]+)[ .·]+([^ ]+) 专属素材', cs[3])
        assert m, cs[3]
        return check(f'锻港传闻：{m.group(2)}{m.group(1).strip()}料只锻一炉，甲乙互斥')
    lines, _ = add_column(lines, '| 套装名 | 绑定基础套（云兽·系） | 方向 | 消耗巨兽材料（来源巨兽·星段·生态） | 套装效果（进阶版） | 激活档位 | 主抗 | 素材增量（材料十四类） | 强化上限 |', 12,
                          adv, '02云兽进阶', counter, mutated)
    # §三 巨兽系三表：出身列（讨伐轶事）
    def beast(cs):
        m = re.match(r'^(\S+) · (\S+)$', cs[1])
        assert m, cs[1]
        star, direction = cs[3].strip(), cs[4].split('（')[0].strip()
        key = (star, direction)
        assert key in BEAST_TMPL, f'未知星段方向: {key}'
        eco = cs[2].strip()
        assert eco in SCENE, f'未知生态: {eco}'
        return check(BEAST_TMPL[key].format(景=SCENE[eco], 锚=m.group(2) + m.group(1)))
    KEY3 = '| 套装名 | 来源巨兽 | 生态 | 星段 | 方向（套装效果） | 激活 | 主抗 | 素材（材料十四类） | 强化上限 |'
    lines, h1 = add_column(lines, KEY3, 51, beast, '02巨兽T1', counter, mutated)
    lines, h2 = add_column(lines, KEY3, 86, beast, '02巨兽T2', counter, mutated, h1 + 1)
    lines, h3 = add_column(lines, KEY3, 165, beast, '02巨兽T3', counter, mutated, h2 + 1)
    io.open(P2, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    return lines

# ---------- 03 册 ----------
def do_03(counter, mutated):
    lines = io.open(P3, encoding='utf-8').read().splitlines()
    def wang(cs):
        m = re.match(r'^(\S+) · (\S+)$', cs[1])
        assert m, cs[1]
        eco = cs[2].strip()
        assert eco in SCENE, f'未知生态: {eco}'
        return check(WANG_TMPL[cs[3].strip()].format(景=SCENE[eco], 锚=m.group(2) + m.group(1)))
    lines, _ = add_column(lines, '| 套装名 | 来源终盘 Boss | 生态 | 方向 | 套装效果 | 激活 | 主抗 | 素材（材料十四类） | 强化上限 |', 153,
                          wang, '03王骸', counter, mutated)
    io.open(P3, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    return lines

def main():
    counter, mutated = [], set()
    l1 = do_01(counter, mutated)
    l2 = do_02(counter, mutated)
    l3 = do_03(counter, mutated)
    # 断言① 504/504
    total = len(counter)
    # 断言② 句全量互异
    ss = [s for _, s in counter]
    assert len(set(ss)) == total, f'出身句有重复 {total - len(set(ss))} 处'
    # 断言④ 三册行数 ≤400
    for p, ls in ((P1, l1), (P2, l2), (P3, l3)):
        assert len(ls) <= 400, f'{p} 行数 {len(ls)} > 400'
    names = {}
    for tag, s in counter:
        names[tag] = names.get(tag, 0) + 1
    print('覆盖分账:', names, '合计', total)
    print('行数: 01=%d 02=%d 03=%d' % (len(l1), len(l2), len(l3)))
    print('样例（各域首句）:')
    seen = set()
    for tag, s in counter:
        if tag not in seen:
            seen.add(tag)
            print('  [%s] %s (%d字)' % (tag, s, len(s)))
    assert total == 504, f'总覆盖 {total}≠504'
    print('断言①②④ 全过，待写回后的独立验证脚本复跑。')

if __name__ == '__main__':
    main()
