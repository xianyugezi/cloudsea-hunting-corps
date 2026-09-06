#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_collection.py —— 由模块化分章自动重建单文件合集版

用途
----
`云海猎团_设计稿合集.md` 是 `云海猎团/` 下各分章的**单文件副本**（输出在本脚本同目录，随仓库一同发布）。
手工维护必然漂移（本次即已产生 7 处 H 方向性 bug 残留）。本脚本从分章重新生成，
使「分章版」成为唯一事实来源，合集版成为可随时重建的派生产物。

用法
----
    python3 build_collection.py

约定
----
- 分章文件 `NN_标题.md` 的首行为 H1（`# 《…》· 标题`），紧随其后可能有导航块
  （`> 本文是设计稿…` / `> 总索引：…`）与空行 —— 这些在合集中一律剔除。
- 章节的汉字序号与标题取自 CHAPTERS 表，与分章文件一一对应。
"""

from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
COLLECTION = HERE / "云海猎团_设计稿合集.md"

# (数字文件名, 汉字序号, 合集内标题)
CHAPTERS = [
    ("00_世界观与术语规范.md",          "〇",   "世界观与术语规范"),
    ("01_战斗核心系统.md",              "一",   "战斗核心系统"),
    ("02_职业×流派×武器解耦.md",         "二",   "十四职业 × 流派 × 武器解耦 + 风缆 / 绝技资源"),
    ("03_巨兽与Boss设计.md",            "三",   "巨兽 / Boss 设计"),
    ("04_异常打击体系与共生灵.md",        "四",   "异常打击体系 + 共生灵"),
    ("05_成长与装备循环.md",             "五",   "成长与装备循环"),
    ("06_资源素材日常循环与经济.md",      "六",   "资源 / 素材 / 日常循环 / 经济"),
    ("07_同行兽与云枢浮港.md",           "七",   "同行兽羁绊生态 + 云枢浮港据点中枢"),
    ("08_QQ群异步适配与指令UI战报.md",    "八",   "QQ 群异步适配 + 指令 / UI / 战报表现"),
    ("09_叙事与引导.md",                 "九",   "叙事与引导"),
    ("10_落地优先级与MVP.md",            "十",   "落地优先级 / MVP"),
    ("11_架构与模块化规范.md",           "十一", "架构与模块化规范"),
    ("12_全局常量表.md",                 "十二", "全局常量表"),
    ("14_全局待裁决项与回填记录.md",      "十三", "全局待裁决项与回填记录"),
    ("15_主线章节与难度阶段.md",          "十四", "主线章节与难度阶段（七潮位 × 18 章 ＋ 七·浩劫终局层）"),
]

# 需从分章正文顶部剔除的导航块特征
NAV_PATTERNS = (
    re.compile(r"^>\s*本文是设计稿"),
    re.compile(r"^>\s*总索引："),
)

HEADER = """# 《云海猎团 Cloudsea Hunting Corps》· QQ 群异步回合制 RPG · PvE 设计稿

> **原创 IP 声明**：本稿为原创游戏设计文档，世界观、术语与机制命名**全部原创**，不沿用任何既有商业作品的专有名称，仅借鉴回合制 RPG·PvE 的通用设计思想。
>
> **世界观基调**：「**飞空艇 + 浮岛**」的天空冒险 JRPG 观感（取此类题材的公开基调，不做任何设定照搬），并**弱化日式要素**——整体走**泛奇幻 + 晶石蒸汽**的天空城邦风（不采用和风视觉符号、和风服饰与和风命名）。
>
> **核心定位**：玩家是**巡游者**——**无角色获取（抽卡）系统**，玩家本人即巡游者。乘飞空艇巡弋浮岛、讨伐空兽、剥取素材、锻造装备、挑战更高威胁。可换的是**武器 / 装备 / 符文**。
>
> **三条来源融合**：
> ① **QQ 群异步回合制 RPG·PvE 骨架**（碎片性 + 轻量性为第一性约束）；
> ② **讨伐型战斗循环**（部位硬度 / 部件破坏 / 阶段窗口 / 武器流派 / 战术资源博弈）；
> ③ **长线资源与装备循环**（武器强化 / 符文加工 / 防具套装 / 定向保底 / 超限突破）。

---

> **文件性质**：本文件为 `云海猎团/` 目录下**分章版的自动重建产物**，由 `build_collection.py` 生成。
> **请勿直接编辑本文件** —— 任何改动都应落在对应的分章文件后重新运行脚本，否则会被下一次生成覆盖。
> 分章版是唯一事实来源；本文件仅便于一次性通读或对外交付。
>
> **未收录**（均为「一对象一文件」的独立卡片册，分册查阅更合理，体量也不适合并入单文件）：
> - `13_职业数值卡/` —— 14 张职业数值卡，各职业独立成文，共约 7,200 行；
> - `15_主线章节与任务/` —— 19 张章节任务卡（七潮位 × 18 章 ＋ 七·浩劫终局层），共约 4,000 行，含 **540 条任务**（主线 116 ／ 支线 424）的逐条清单。
> - `16–18 号`（规模规划／世界内容与生态／装备与素材图鉴）以分册查阅为准，`17/00` 总索引可在分片仓库直读。
>
> 上述各册的**总纲仍在本合集中**：职业见「二、十四职业 × 流派 × 武器解耦」，章节任务见「十四、主线章节与难度阶段」。

---

## 目录

"""


def strip_header(text: str) -> str:
    """去掉分章文件的 H1 标题行与紧随其后的导航块 / 空行。"""
    lines = text.splitlines()
    if not lines:
        return ""
    i = 0
    # 跳到第一个 H1 之后
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    i += 1
    # 跳过空行与导航块
    while i < len(lines):
        s = lines[i].strip()
        if s == "":
            i += 1
            continue
        if any(p.match(s) for p in NAV_PATTERNS):
            i += 1
            continue
        break
    return "\n".join(lines[i:]).strip("\n")


def main() -> int:
    missing = [f for f, _, _ in CHAPTERS if not (HERE / f).exists()]
    if missing:
        print("缺少分章文件：", missing, file=sys.stderr)
        return 1

    toc = ["| 章节 | 内容 |", "|---|---|"]
    bodies = []
    for fname, num, title in CHAPTERS:
        raw = (HERE / fname).read_text(encoding="utf-8")
        body = strip_header(raw)
        toc.append(f"| {num} | {title} |")
        bodies.append(f"## {num}、{title}\n\n{body}\n")

    out = HEADER + "\n".join(toc) + "\n\n---\n\n" + "\n\n---\n\n".join(bodies)
    COLLECTION.write_text(out.rstrip() + "\n", encoding="utf-8")
    print(f"已生成：{COLLECTION}")
    print(f"章节数：{len(CHAPTERS)}　行数：{len(out.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
