#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件用途：检测项目文档的新鲜度。
        文档最怕的不是少，而是旧——代码已经改了、规则已经变了，文档还停在上一版，
        下一个接手的 AI 会「非常认真地」按错误信息继续开发（见 references/05）。

创建时间：2026-08-30
维护者：项目组

判定逻辑：
    对每份被监控的文档 D，找出其「关联代码/内容文件」集合中最后修改时间 T_code，
    若 T_code > T_doc，则判定 D 可能过期。
    * 若仓库是 Git 工作区，时间取 Git 最后提交时间（比 mtime 更可靠）；
    * 否则退化为文件系统 mtime。

设计约束：
    * 只读审计，绝不修改任何文件。
    * 退出码：0 = 全部新鲜；1 = 存在可能过期的文档；2 = 运行出错。
    * 无硬编码：根目录、文档清单、代码模式、容忍时长一律走命令行参数。

用法：
    python3 check_docs_freshness.py --root /workspace/云海猎团 \\
        --docs README.md,12_全局常量表.md --code-pattern "*.py"
    python3 check_docs_freshness.py --root . --docs docs/PROJECT.md --grace-hours 24
    python3 check_docs_freshness.py --self-test
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

# ---------------------------------------------------------------- 模块级常量

LOGGER_NAME = "check_docs_freshness"

#: 默认监控的文档（相对 root）。
DEFAULT_DOCS: tuple[str, ...] = (
    "README.md",
    "ARCHITECTURE.md",
    "GAME_RULES.md",
    "DECISIONS.md",
)

#: 默认视为「代码/内容」的 glob 模式（相对 root，递归）。
DEFAULT_CODE_PATTERNS: tuple[str, ...] = ("*.py", "*.cs", "*.json", "*.csv")

#: 默认容忍时长（小时）：文档比代码旧不超过该值不算过期，避免误报。
DEFAULT_GRACE_HOURS = 24.0

#: Git 时间格式（ISO，UTC）。
GIT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


# ---------------------------------------------------------------- 数据结构

@dataclass
class DocReport:
    """单份文档的新鲜度检查结果。"""

    path: str
    doc_mtime: datetime | None = None
    code_mtime: datetime | None = None
    newest_code: str | None = None
    error: str | None = None

    @property
    def stale(self) -> bool:
        """是否判定为可能过期。"""
        if self.error or self.doc_mtime is None or self.code_mtime is None:
            return False
        return self.code_mtime > self.doc_mtime


@dataclass
class FreshnessResult:
    """整体检查结果。"""

    reports: list[DocReport] = field(default_factory=list)
    source: str = "mtime"

    @property
    def stale_docs(self) -> list[DocReport]:
        """返回被判定为可能过期的文档报告列表。"""
        return [r for r in self.reports if r.stale]

    @property
    def ok(self) -> bool:
        """整体是否通过。"""
        return not self.stale_docs


# ---------------------------------------------------------------- 时间获取

def run_git(root: Path, args: Sequence[str]) -> str | None:
    """
    在指定目录执行 git 命令。

    Args:
        root: 仓库根目录。
        args: git 子命令参数。

    Returns:
        标准输出字符串；失败返回 None。
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        logging.getLogger(LOGGER_NAME).debug("git 命令失败：%s（%s）", " ".join(args), exc)
        return None


def is_git_repo(root: Path) -> bool:
    """判断目录是否位于 Git 工作区内。"""
    return run_git(root, ["rev-parse", "--is-inside-work-tree"]) == "true"


def git_last_commit_time(root: Path, rel_path: str) -> datetime | None:
    """
    获取某文件最后一次提交的时间（Git 视角）。

    Args:
        root: 仓库根目录。
        rel_path: 相对 root 的路径。

    Returns:
        提交时间（转为本地时区 naive datetime）；无提交记录或失败返回 None。
    """
    out = run_git(root, ["log", "-1", "--format=%ci", "--", rel_path])
    if not out:
        return None
    try:
        dt = datetime.strptime(out.splitlines()[0].strip(), GIT_TIME_FORMAT)
        # 统一为本地时区 naive，便于与 mtime 比较
        return dt.astimezone().replace(tzinfo=None)
    except (ValueError, IndexError) as exc:
        logging.getLogger(LOGGER_NAME).debug("解析 git 时间失败：%s（%s）", out, exc)
        return None


def fs_mtime(path: Path) -> datetime | None:
    """
    获取文件系统修改时间。

    Args:
        path: 文件路径。

    Returns:
        本地时间；文件不存在或出错返回 None。
    """
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError as exc:
        logging.getLogger(LOGGER_NAME).debug("获取 mtime 失败：%s（%s）", path, exc)
        return None


def resolve_time(root: Path, path: Path, use_git: bool) -> datetime | None:
    """
    解析文件的「最后变更时间」，优先 Git 提交时间，退化到 mtime。

    Args:
        root: 仓库根目录。
        path: 目标文件绝对路径。
        use_git: 是否优先使用 Git 时间。

    Returns:
        时间；无法获取返回 None。
    """
    if use_git:
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        git_time = git_last_commit_time(root, rel)
        if git_time is not None:
            return git_time
    return fs_mtime(path)


# ---------------------------------------------------------------- 核心逻辑

def is_excluded(path: Path, root: Path, exclude_set: set[str]) -> bool:
    """
    判断文件是否应被排除。

    排除项按「路径段」匹配：既能排除某个文件名（``NOTES.md``），
    也能排除整个目录（``skills``、``build``），避免逐个子文件列举。

    Args:
        path: 待判断文件的绝对路径。
        root: 根目录，用于计算相对路径。
        exclude_set: 排除项集合。

    Returns:
        应排除返回 True，否则 False。
    """
    if path.name in exclude_set or str(path) in exclude_set:
        return True
    try:
        rel_parts = set(path.relative_to(root).parts)
    except ValueError:
        return False
    return bool(rel_parts & exclude_set)


def collect_code_files(root: Path, patterns: Sequence[str], excludes: Sequence[str]) -> list[Path]:
    """
    收集被视为「代码/内容」的文件列表。

    Args:
        root: 根目录。
        patterns: glob 模式列表。
        excludes: 排除项（文件名或目录名，按路径段匹配）。

    Returns:
        排序后的路径列表。
    """
    exclude_set = set(excludes)
    found: list[Path] = []
    for pattern in patterns:
        try:
            for path in root.rglob(pattern):
                if not path.is_file():
                    continue
                if is_excluded(path, root, exclude_set):
                    continue
                found.append(path)
        except (OSError, ValueError) as exc:
            logging.getLogger(LOGGER_NAME).warning("扫描模式 %s 失败：%s", pattern, exc)
    return sorted(set(found))


def check_doc(
    root: Path,
    doc_rel: str,
    code_files: Sequence[Path],
    use_git: bool,
    grace: timedelta,
) -> DocReport:
    """
    检查单份文档的新鲜度。

    Args:
        root: 根目录。
        doc_rel: 文档相对路径。
        code_files: 代码/内容文件列表。
        use_git: 是否优先用 Git 时间。
        grace: 容忍时长。

    Returns:
        DocReport。
    """
    doc_path = root / doc_rel
    if not doc_path.is_file():
        return DocReport(path=doc_rel, error="文档不存在")

    doc_time = resolve_time(root, doc_path, use_git)
    if doc_time is None:
        return DocReport(path=doc_rel, error="无法获取文档最后变更时间")
    doc_time_effective = doc_time + grace

    newest_time: datetime | None = None
    newest_path: str | None = None
    for code_path in code_files:
        if code_path.resolve() == doc_path.resolve():
            continue
        code_time = resolve_time(root, code_path, use_git)
        if code_time is None:
            continue
        if newest_time is None or code_time > newest_time:
            newest_time = code_time
            newest_path = str(code_path.relative_to(root))

    return DocReport(
        path=doc_rel,
        doc_mtime=doc_time_effective,
        code_mtime=newest_time,
        newest_code=newest_path,
    )


def run_check(
    root: Path,
    docs: Sequence[str],
    code_patterns: Sequence[str],
    excludes: Sequence[str],
    grace_hours: float,
) -> FreshnessResult:
    """
    执行一次完整的新鲜度检查。

    Args:
        root: 根目录。
        docs: 被监控文档的相对路径列表。
        code_patterns: 代码/内容文件 glob 模式。
        excludes: 排除项。
        grace_hours: 容忍时长（小时）。

    Returns:
        FreshnessResult。
    """
    log = logging.getLogger(LOGGER_NAME)
    result = FreshnessResult()

    if not root.exists():
        log.error("根目录不存在：%s", root)
        return result

    use_git = is_git_repo(root)
    result.source = "git" if use_git else "mtime"
    log.info("时间来源：%s", result.source)

    code_files = collect_code_files(root, code_patterns, excludes)
    log.info("监控文档 %d 份，代码/内容文件 %d 个", len(docs), len(code_files))

    grace = timedelta(hours=grace_hours)
    for doc_rel in docs:
        report = check_doc(root, doc_rel, code_files, use_git, grace)
        result.reports.append(report)
        if report.error:
            log.warning("%s：%s", doc_rel, report.error)
        elif report.stale:
            log.warning("%s：可能过期（最新变更来自 %s）", doc_rel, report.newest_code)

    return result


# ---------------------------------------------------------------- 输出

def _fmt(dt: datetime | None) -> str:
    """格式化时间用于展示。"""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "-"


def render_text(result: FreshnessResult, grace_hours: float) -> str:
    """渲染人类可读的报告。"""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("项目文档新鲜度检查")
    lines.append("=" * 60)
    lines.append(f"时间来源：{result.source}    容忍时长：{grace_hours:g} 小时")
    lines.append("")

    for report in result.reports:
        if report.error:
            lines.append(f"  [跳过] {report.path}")
            lines.append(f"         {report.error}")
        elif report.stale:
            lines.append(f"  [过期] {report.path}")
            lines.append(f"         文档时间 {_fmt(report.doc_mtime)}")
            lines.append(f"         最新代码 {_fmt(report.code_mtime)}  ← {report.newest_code}")
        else:
            lines.append(f"  [新鲜] {report.path}   （文档 {_fmt(report.doc_mtime)}）")

    lines.append("")
    stale = result.stale_docs
    if stale:
        lines.append(f"❌ {len(stale)} 份文档可能过期")
        lines.append("提示：先更新共享文档，再继续下一轮任务（references/05）。")
    else:
        lines.append("✅ 所有受监控文档均为最新")
    return "\n".join(lines)


def render_json(result: FreshnessResult, grace_hours: float) -> str:
    """渲染 JSON 报告。"""
    payload = {
        "source": result.source,
        "grace_hours": grace_hours,
        "passed": result.ok,
        "docs": [
            {
                "path": r.path,
                "doc_time": _fmt(r.doc_mtime),
                "code_time": _fmt(r.code_mtime),
                "newest_code": r.newest_code,
                "stale": r.stale,
                "error": r.error,
            }
            for r in result.reports
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- 自测

def self_test() -> int:
    """
    内置单元测试：验证时间比较、兜底与过期判定。

    Returns:
        全部通过返回 EXIT_OK，否则 EXIT_ISSUES。
    """
    import tempfile

    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        print(f"  [{'PASS' if condition else 'FAIL'}] {name}")
        if not condition:
            failures.append(name)

    print("== check_docs_freshness 自测 ==")

    check("空报告视为通过", FreshnessResult().ok)
    check("错误项不计入过期", not DocReport(path="x", error="缺失").stale)
    check("缺时间不计入过期", not DocReport(path="x", doc_mtime=None, code_mtime=datetime.now()).stale)

    now = datetime.now()
    older = now - timedelta(days=1)
    check("代码比文档新 → 过期", DocReport(path="x", doc_mtime=older, code_mtime=now).stale)
    check("文档比代码新 → 新鲜", not DocReport(path="x", doc_mtime=now, code_mtime=older).stale)
    check("时间相等 → 不算过期", not DocReport(path="x", doc_mtime=now, code_mtime=now).stale)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "DOC.md").write_text("doc", encoding="utf-8")
        (root / "a.py").write_text("code", encoding="utf-8")
        (root / "b.py").write_text("code", encoding="utf-8")

        files = collect_code_files(root, ["*.py"], [])
        check("可收集代码文件", len(files) == 2)

        # 路径段排除：新增一个嵌套目录再验证
        nested = root / "skills" / "sub"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "c.py").write_text("code", encoding="utf-8")

        check("递归可收集嵌套文件", len(collect_code_files(root, ["*.py"], [])) == 3)
        by_dir = collect_code_files(root, ["*.py"], ["skills"])
        check("目录名排除生效", len(by_dir) == 2 and all("skills" not in str(p) for p in by_dir))
        check("文件名排除生效", len(collect_code_files(root, ["*.py"], ["a.py"])) == 2)

        # 文档刚写、代码更早 → 手动把文档改成更早
        import os
        import time as _time
        past = _time.time() - 3600
        os.utime(root / "DOC.md", (past, past))

        result = run_check(root, ["DOC.md"], ["*.py"], [], grace_hours=0)
        check("真实文件可完成检查", len(result.reports) == 1)
        check("真实场景能检出过期", result.reports[0].stale)

        result_grace = run_check(root, ["DOC.md"], ["*.py"], [], grace_hours=24)
        check("容忍时长内不误报", not result_grace.reports[0].stale)

        missing = run_check(root, ["NOPE.md"], ["*.py"], [], grace_hours=0)
        check("缺失文档被记录为 error 而非崩溃", missing.reports[0].error is not None)
        check("缺失文档不影响整体通过", missing.ok)

    if failures:
        print(f"\n❌ {len(failures)} 项未通过")
        return EXIT_ISSUES
    print("\n✅ 自测全部通过")
    return EXIT_OK


# ---------------------------------------------------------------- 入口

def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="检测项目文档新鲜度（只读审计，不修改任何文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument(
        "--docs",
        default=",".join(DEFAULT_DOCS),
        help="被监控文档，逗号分隔（相对 root）",
    )
    parser.add_argument(
        "--code-pattern",
        action="append",
        default=[],
        help="代码/内容文件 glob 模式，可重复传入（默认 *.py / *.cs / *.json / *.csv）",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除的文件名或目录名，按路径段匹配，可重复传入（如 --exclude skills）",
    )
    parser.add_argument(
        "--grace-hours",
        type=float,
        default=DEFAULT_GRACE_HOURS,
        help=f"容忍时长（小时），文档略旧于代码时不误报（默认 {DEFAULT_GRACE_HOURS:g}）",
    )
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
        docs = [d.strip() for d in args.docs.split(",") if d.strip()]
        patterns = list(args.code_pattern) if args.code_pattern else list(DEFAULT_CODE_PATTERNS)

        result = run_check(
            root=Path(args.root).expanduser().resolve(),
            docs=docs,
            code_patterns=patterns,
            excludes=list(args.exclude),
            grace_hours=args.grace_hours,
        )

        if args.format == "json":
            print(render_json(result, args.grace_hours))
        else:
            print(render_text(result, args.grace_hours))

        return EXIT_OK if result.ok else EXIT_ISSUES

    except Exception as exc:  # noqa: BLE001 — 兜底：任何未预期异常都不应让 CI 崩溃性退出
        logging.getLogger(LOGGER_NAME).error("检查过程发生未预期错误：%s", exc, exc_info=True)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
