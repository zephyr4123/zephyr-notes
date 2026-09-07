#!/bin/sh
# 把 git 钩子目录指到 tools/hooks（钩子随仓库版本化）。每台机器 clone 后跑一次。
set -e
root="$(git rev-parse --show-toplevel)"
chmod +x "$root"/tools/hooks/*
git -C "$root" config core.hooksPath tools/hooks
echo "✓ core.hooksPath=tools/hooks，commit 时自动跑 tools/lint.py"
