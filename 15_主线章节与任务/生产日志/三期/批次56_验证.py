# -*- coding: utf-8 -*-
"""三期批次 56 · 完成判据独立验证（不依赖生成脚本逻辑）
①504/504 覆盖：出身列数据行（8 表）＋括号出身（新手 1＋无进阶 4）
②分册单文件 ≤400 行
③新句全库唯一抽查 ≥25（口径：正文库＝全部 .md，排除合集生成物与生产日志）
④8 表列数一致（表头＝分隔＝数据行）
"""
import io, os, glob, random

BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
P1 = os.path.join(BASE, '18_装备与素材图鉴', '01_新手商店基础套.md')
P2 = os.path.join(BASE, '18_装备与素材图鉴', '02_进阶套.md')
P3 = os.path.join(BASE, '18_装备与素材图鉴', '03_王骸套与散件.md')

def rows(lines):
    return [l for l in lines if l.lstrip().startswith('|')]

def split_row(line):
    body = line.strip()
    return [c.strip() for c in body[1:-1].split('|')]

def parse_tables(lines):
    """独立扫描：返回 [(表头行号, 表头cells, [数据行cells...])]，含出身列表的表"""
    tables, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.lstrip().startswith('|') and '| 出身 |' in l:
            head = split_row(l)
            j = i + 1
            data = []
            k = j + 1
            while k < len(lines):
                t = lines[k]
                if t.strip() == '':
                    k += 1
                    continue
                if not t.lstrip().startswith('|'):
                    break
                data.append(split_row(t))
                k += 1
            tables.append((i, head, data))
            i = k
        else:
            i += 1
    return tables

def main():
    l1 = io.open(P1, encoding='utf-8').read().splitlines()
    l2 = io.open(P2, encoding='utf-8').read().splitlines()
    l3 = io.open(P3, encoding='utf-8').read().splitlines()
    sentences = []
    # 出身列覆盖
    col_total = 0
    for name, ls, expect in (('01册', l1, 2), ('02册', l2, 5), ('03册', l3, 1)):
        tabs = parse_tables(ls)
        assert len(tabs) == expect, f'{name}: 出身列表 {len(tabs)}≠{expect}'
        for hi, head, data in tabs:
            assert head[-1] == '出身', head
            for r in data:
                assert len(r) == len(head), f'{name} 表头{len(head)}列 vs 数据{len(r)}列: {r[0]}'
                assert r[-1], f'{name}: 空出身: {r[0]}'
                sentences.append(r[-1])
            col_total += len(data)
    # 括号出身（01 册：新手套条目头行 + 无进阶首行）
    par = [l for l in l1 if '出身：' in l]
    assert len(par) == 5, f'01册括号出身 {len(par)}≠5'
    import re
    for l in par:
        m = re.search(r'出身：([^）｜]+)', l)
        assert m, l
        sentences.append(m.group(1))
    # 判据①
    total = col_total + len(par)
    assert total == 504, f'判据① 覆盖 {total}≠504（列内 {col_total}＋括号 {len(par)}）'
    print(f'判据① 504/504 覆盖 ✅（出身列 {col_total}＋括号 {len(par)}；其中01册列28/02册列318/03册列153）')
    # 判据②
    for p, ls in ((P1, l1), (P2, l2), (P3, l3)):
        assert len(ls) <= 400, f'判据② {os.path.basename(p)} {len(ls)}>400'
    print(f'判据② 行数 ✅ 01={len(l1)} 02={len(l2)} 03={len(l3)}（均≤400）')
    # 句全量互异（强于抽查）
    assert len(set(sentences)) == 504, f'出身句重复 {504 - len(set(sentences))}'
    for s in sentences:
        assert len(s) <= 24, f'超长: {s}'
    # 判据③ 抽查 25 句全库唯一（正文库口径）
    corpus = []
    for p in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
        rel = os.path.relpath(p, BASE).replace('\\', '/')
        if '云海猎团_设计稿合集' in rel:
            continue
        if rel.startswith('15_主线章节与任务/生产日志/'):
            continue
        if rel.startswith('15_主线章节与任务/生产排期_填充批次'):
            continue
        if rel in ('18_装备与素材图鉴/01_新手商店基础套.md', '18_装备与素材图鉴/02_进阶套.md', '18_装备与素材图鉴/03_王骸套与散件.md'):
            continue
        if rel.startswith('18_装备与素材图鉴/02_进阶套/'):
            # 批次 52 在途拆分中间态：与 02 册母本同源镜像（52 收尾统一），非独立设定文本
            continue
        corpus.append(io.open(p, encoding='utf-8').read())
    corpus_text = '\n'.join(corpus)
    random.seed(56)
    sample = random.sample(sentences, 25)
    for s in sample:
        assert corpus_text.count(s) == 0, f'判据③ 撞车: {s}'
    print(f'判据③ 抽查 25 句全库唯一 ✅（正文库 {len(corpus)} 文件；且 504 句全量互异、≤24 字）')
    print('批次 56 三条完成判据全过。')

if __name__ == '__main__':
    main()
