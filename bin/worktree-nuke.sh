#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-}"

if [[ -z "$NAME" ]]; then
  echo "Usage: $0 <worktree-name>"
  exit 1
fi

if git worktree list | grep -q "/$NAME "; then
  git worktree remove "$NAME"
  echo "Worktree '$NAME' removed"
else
  echo "Worktree '$NAME' not found"
fi

if git branch --list "$NAME" | grep -q .; then
  git branch -D "$NAME"
else
  echo "Branch '$NAME' not found"
fi

git worktree prune -v && echo "worktree prune done"
