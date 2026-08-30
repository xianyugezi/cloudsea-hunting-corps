#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件用途：审计模块边界声明完整性。
        检查每个模块文档是否写清了「负责 / 不负责 / 依赖」三要素——
        「不负责」缺失是 AI 把边界写乱的头号原因（见 references/05）。

创建时间：2026-08-30
维护者：项目组

设计约束：
    * 只读审计，绝不修改任何被扫描的文件。
    * 退出码：0 = 全部通过；1 = 发现问题；2 = 运行出错。
    * 无硬编码：扫描范围、判定关键词、输出格式一律走命令行参数。

用法：
    python3 check_boundaries.py --root /workspace/云海猎团 --pattern "*_*.md"
    python3 check_boundaries.py --root . --exclude README.md --format json
    python3 check_boundaries.py --self-test
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

# ---------------------------------------------------------------- 模块级常量

LOGGER_NAME = "check_boundaries"

#: 默认判定关键词。顺序与「三要素」一致：负责 / 不负责 / 依赖。
DEFAULT_SECTIONS: tuple[str, ...] = ("负责", "不负责", "依赖")

#: 默认排除的文件（项目级说明文档不需要模块边界卡）。
DEFAULT_EXCLUDES: tuple[str, ...] = ("README.md", "SKILL.md", "CHANGELOG.md")

#: 视为「声明」的写法：标题行 / 表格表头 / 列表项定义 / 行首定义。
#: ⚠️ 这些字符串会经 str.format(kw=...) 渲染，正则里的量词花括号必须写成双花括号转义，
#: 否则 {0,3} 会被 format 当成占位符而抛 KeyError（曾由 --self-test 捕获）。
_SECTION_PATTERNS: tuple[str, ...] = (
    r"^\s{{0,3}}#{{1,6}}\s*.*{kw}",             # Markdown 标题
    r"^\s*\|?\s*\**\s*{kw}\s*\**\s*\|",         # 表格首列 / 加粗表头
    r"^\s*[-*+]\s*\**\s*{kw}\s*\**\s*[:：]",    # 列表项定义
    r"^\s*\**\s*{kw}\s*\**\s*[:：]",            # 行首定义
)

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


# ---------------------------------------------------------------- 数据结构

@dataclass
class FileReport:
    """单个文件的边界声明审计结果。"""

    path: str
    missing: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        """是否通过审计：无错误且无缺失。"""
        return self.error is None and not self.missing


@dataclass
class AuditResult:
    """整体审计结果。"""

    reports: list[FileReport] = field(default_factory=list)
    scanned: int = 0

    @property
    def failed(self) -> list[FileReport]:
        """返回未通过的文件报告列表。"""
        return [r for r in self.reports if not r.ok]

    @property
    def ok(self) -> bool:
        """整体是否通过。"""
        return not self.failed


# ---------------------------------------------------------------- 核心逻辑

def build_section_regex(keyword: str) -> re.Pattern[str]:
    """
    构造用于识别某个边界声明关键词的正则。

    Args:
        keyword: 边界声明关键词，如「负责」。

    Returns:
        编译后的正则对象（多行模式，忽略大小写）。
    """
    alternation = "|".join(p.format(kw=re.escape(keyword)) for p in _SECTION_PATTERNS)
    return re.compile(alternation, re.MULTILINE | re.IGNORECASE)


def has_section(text: str, keyword: str) -> bool:
    """
    判断文本中是否存在某个边界声明。

    Args:
        text: 文件全文。
        keyword: 边界声明关键词。

    Returns:
        存在返回 True，否则 False。
    """
    try:
        return build_section_regex(keyword).search(text) is not None
    except Exception as exc:  # noqa: BLE001 — 兜底：正则构造/匹配失败时退化为朴素包含判断
        # 宁可放宽判定，也不让审计脚本因为一个奇怪的关键词而崩溃。
        logging.getLogger(LOGGER_NAME).debug(
            "关键词 %r 正则判定失败，退化为包含判断：%s", keyword, exc
        )
        return keyword in text


def iter_target_files(
    root: Path,
    pattern: str,
    excludes: Sequence[str],
    recursive: bool,
) -> list[Path]:
    """
    收集待审计的文件列表。

    Args:
        root: 扫描根目录。
        pattern: 文件名 glob 模式。
        excludes: 需要排除的文件名集合。
        recursive: 是否递归子目录。

    Returns:
        排序后的文件路径列表；出错时返回空列表。
    """
    try:
        walker: Iterable[Path] = root.rglob(pattern) if recursive else root.glob(pattern)
        files = [p for p in walker if p.is_file() and p.name not in set(excludes)]
        return sorted(files)
    except (OSError, ValueError) as exc:
        logging.getLogger(LOGGER_NAME).warning("扫描目录失败，已跳过：%s（%s）", root, exc)
        return []


def audit_file(path: Path, sections: Sequence[str]) -> FileReport:
    """
    审计单个文件的边界声明完整性。

    Args:
        path: 文件路径。
        sections: 必须出现的边界声明关键词列表。

    Returns:
        FileReport。读取失败时记录 error 而非抛出，保证整体流程不中断。
    """
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError) as exc:
        return FileReport(path=str(path), error=f"读取失败：{exc}")

    missing = [kw for kw in sections if not has_section(text, kw)]
    return FileReport(path=str(path), missing=missing)


def run_audit(
    root: Path,
    pattern: str,
    excludes: Sequence[str],
    sections: Sequence[str],
    recursive: bool,
) -> AuditResult:
    """
    执行一次完整审计。

    Args:
        root: 扫描根目录。
        pattern: 文件名 glob 模式。
        excludes: 排除的文件名。
        sections: 必须出现的边界声明关键词。
        recursive: 是否递归。

    Returns:
        AuditResult。
    """
    log = logging.getLogger(LOGGER_NAME)
    result = AuditResult()

    if not root.exists():
        log.error("根目录不存在：%s", root)
        return result

    files = iter_target_files(root, pattern, excludes, recursive)
    result.scanned = len(files)
    log.info("扫描到 %d 个文件（root=%s, pattern=%s）", len(files), root, pattern)

    for path in files:
        report = audit_file(path, sections)
        result.reports.append(report)
        if report.error:
            log.warning("%s：%s", report.path, report.error)
        elif report.missing:
            log.warning("%s：缺少边界声明 → %s", report.path, "、".join(report.missing))

    return result


# ---------------------------------------------------------------- 输出

def render_text(result: AuditResult, sections: Sequence[str]) -> str:
    """
    渲染人类可读的文本报告。

    Args:
        result: 审计结果。
        sections: 被检查的关键词，用于提示。

    Returns:
        报告文本。
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("模块边界声明审计")
    lines.append("=" * 60)
    lines.append(f"扫描文件数：{result.scanned}")
    lines.append(f"检查要素　：{'、'.join(sections)}")
    lines.append("")

    failed = result.failed
    if not failed:
        lines.append("✅ 全部文件均包含完整边界声明")
        return "\n".join(lines)

    lines.append(f"❌ {len(failed)} 个文件不完整：")
    lines.append("")
    for report in failed:
        if report.error:
            lines.append(f"  [错误] {report.path}")
            lines.append(f"         {report.error}")
        else:
            lines.append(f"  [缺失] {report.path}")
            lines.append(f"         缺少：{'、'.join(report.missing)}")
    lines.append("")
    lines.append("提示：「不负责」缺失会导致 AI 顺手做完，把模块边界写乱（references/05）。")
    return "\n".join(lines)


def render_json(result: AuditResult, sections: Sequence[str]) -> str:
    """
    渲染 JSON 报告，便于接入 CI。

    Args:
        result: 审计结果。
        sections: 被检查的关键词。

    Returns:
        JSON 字符串。
    """
    payload = {
        "scanned": result.scanned,
        "sections": list(sections),
        "passed": result.ok,
        "issues": [
            {"path": r.path, "missing": r.missing, "error": r.error}
            for r in result.failed
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- 自测

def self_test() -> int:
    """
    内置单元测试：验证核心判定逻辑与兜底行为。

    Returns:
        全部通过返回 EXIT_OK，否则 EXIT_ISSUES。
    """
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")
        if not condition:
            failures.append(name)

    print("== check_boundaries 自测 ==")

    sample = """
# 模块边界卡：示例
## 负责
- 处理伤害
## 不负责
- 不播放动画
| 依赖 | 用途 |
"""
    check("可识别「负责」", has_section(sample, "负责"))
    check("可识别「不负责」", has_section(sample, "不负责"))
    check("可识别「依赖」（表格形式）", has_section(sample, "依赖"))
    check("缺失项能被检出", not has_section(sample, "不存在的字段"))
    check("空文本不误报", not has_section("", "负责"))
    check("关键词含特殊字符不崩溃", not has_section("abc", "["))
    check("行首定义写法可识别", has_section("负责：处理伤害", "负责"))
    check("列表项写法可识别", has_section("- **负责**：处理伤害", "负责"))

    # 「不负责」不能因为文本里有「负责」就算通过（子串陷阱）
    only_positive = "## 负责\n- 处理伤害\n"
    check("仅含「负责」时「不负责」判定为缺失", not has_section(only_positive, "不负责"))

    if failures:
        print(f"\n❌ {len(failures)} 项未通过")
        return EXIT_ISSUES
    print("\n✅ 自测全部通过")
    return EXIT_OK


# ---------------------------------------------------------------- 入口

def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="审计模块边界声明完整性（只读审计，不修改任何文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="扫描根目录（默认当前目录）")
    parser.add_argument("--pattern", default="*.md", help="文件名 glob 模式（默认 *.md）")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除的文件名，可重复传入（默认排除 README.md / SKILL.md / CHANGELOG.md）",
    )
    parser.add_argument(
        "--section",
        action="append",
        default=[],
        help="必须出现的边界声明关键词，可重复传入（默认 负责 / 不负责 / 依赖）",
    )
    parser.add_argument("--no-recursive", action="store_true", help="不递归子目录")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="输出格式")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    parser.add_argument("--self-test", action="store_true", help="运行内置单元测试并退出")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    程序入口。

    Args:
        argv: 命令行参数，None 表示读取 sys.argv。

    Returns:
        退出码：0 通过 / 1 发现问题 / 2 运行出错。
    """
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )

    if args.self_test:
        return self_test()

    try:
        excludes = list(DEFAULT_EXCLUDES) + list(args.exclude)
        sections = list(args.section) if args.section else list(DEFAULT_SECTIONS)

        result = run_audit(
            root=Path(args.root).expanduser().resolve(),
            pattern=args.pattern,
            excludes=excludes,
            sections=sections,
            recursive=not args.no_recursive,
        )

        if args.format == "json":
            print(render_json(result, sections))
        else:
            print(render_text(result, sections))

        return EXIT_OK if result.ok else EXIT_ISSUES

    except Exception as exc:  # noqa: BLE001 — 兜底：任何未预期异常都不应让 CI 崩溃性退出
        logging.getLogger(LOGGER_NAME).error("审计过程发生未预期错误：%s", exc, exc_info=True)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
