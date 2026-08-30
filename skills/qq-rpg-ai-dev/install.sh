#!/usr/bin/env bash
#
# 文件用途：把 qq-rpg-ai-dev skill 组安装到 CodeBuddy 的 skills 目录。
# 创建时间：2026-08-30
# 维护者：项目组
#
# 用法：
#   bash install.sh              软链安装（默认，推荐：改一处两边生效，无漂移）
#   bash install.sh --copy       复制安装（项目目录可能被清理时用）
#   bash install.sh --uninstall  卸载
#
# 退出码：0 成功 / 1 失败

set -euo pipefail

SKILL_NAME="qq-rpg-ai-dev"

# ---- 日志函数：统一输出到 stderr，便于与正常输出分离 ----
log()  { printf '[install] %s\n' "$*" >&2; }
warn() { printf '[install][WARN] %s\n' "$*" >&2; }
die()  { printf '[install][ERROR] %s\n' "$*" >&2; exit 1; }

# ---- 解析参数 ----
resolve_source_dir() {
    # 优先用脚本自身所在目录，避免依赖调用者的 cwd
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    printf '%s' "$script_dir"
}

resolve_target_dir() {
    # CodeBuddy 用户级 skills 目录；允许用环境变量覆盖，便于测试
    local base="${CODEBUDDY_HOME:-$HOME/.codebuddy}"
    printf '%s/skills' "$base"
}

do_uninstall() {
    local target="$1/$SKILL_NAME"
    if [ -L "$target" ] || [ -d "$target" ]; then
        rm -rf "$target"
        log "已卸载：$target"
    else
        warn "未找到安装记录，无需卸载：$target"
    fi
}

do_install() {
    local mode="$1" src="$2" dst_parent="$3"
    local target="$dst_parent/$SKILL_NAME"

    [ -f "$src/SKILL.md" ] || die "源目录缺少 SKILL.md，不是合法的 skill：$src"

    if [ -L "$target" ] || [ -d "$target" ]; then
        log "已存在安装，先移除：$target"
        rm -rf "$target"
    fi

    mkdir -p "$dst_parent" || die "无法创建目录：$dst_parent"

    if [ "$mode" = "copy" ]; then
        cp -R "$src" "$target" || die "复制失败：$src -> $target"
        log "✅ 复制安装完成"
    else
        ln -s "$src" "$target" || die "软链创建失败：$src -> $target"
        log "✅ 软链安装完成"
    fi

    log "源：$src"
    log "目标：$target"

    # 安装后自检：目标必须能读到 SKILL.md
    if [ -f "$target/SKILL.md" ]; then
        log "自检通过：目标可读到 SKILL.md"
    else
        die "自检失败：目标读不到 SKILL.md，安装可能不完整"
    fi
}

main() {
    local mode="link"
    case "${1:-}" in
        --copy)      mode="copy" ;;
        --link)      mode="link" ;;
        --uninstall) do_uninstall "$(resolve_target_dir)"; exit 0 ;;
        "")          : ;;
        *)           die "未知参数：$1（可用：--copy / --link / --uninstall）" ;;
    esac

    local src dst_parent
    src="$(resolve_source_dir)"
    dst_parent="$(resolve_target_dir)"

    log "skill 名称：$SKILL_NAME"
    log "安装模式：$mode"
    do_install "$mode" "$src" "$dst_parent"
}

main "$@"
