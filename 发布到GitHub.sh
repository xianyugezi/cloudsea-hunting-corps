#!/usr/bin/env bash
# 云海猎团 · 一键发布到 GitHub（公开库）
# 用法:  GH_TOKEN=ghp_xxx bash 发布到GitHub.sh
# 前置: 本机已装 gh 且能联网；仓库已 git commit 完成。
set -euo pipefail
cd "$(dirname "$0")"

REPO="cloudsea-hunting-corps"
DESC="云海猎团 — QQ群异步回合制 RPG·PvE 设计稿"
TOKEN="${GH_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "✗ 未提供令牌。用法: GH_TOKEN=ghp_xxx bash 发布到GitHub.sh" >&2
  exit 1
fi

echo "→ 登录 GitHub ..."
printf '%s' "$TOKEN" | gh auth login --with-token

OWNER="$(gh api user --jq .login)"
echo "→ 账号: $OWNER"

if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "→ 仓库已存在，直接推送 main ..."
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/$REPO.git"
  git branch -M main
  git push -u origin main
else
  echo "→ 创建公开库并推送 ..."
  gh repo create "$REPO" --public --description "$DESC" --source . --remote origin --push
fi

echo "✓ 完成: https://github.com/$OWNER/$REPO"
