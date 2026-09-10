#!/bin/bash
set -euo pipefail
done_count=$(grep -c '^- \[x\]' tasks.md || true)
wip_count=$(grep -c '^- \[~\]' tasks.md || true)
todo_count=$(grep -c '^- \[ \]' tasks.md || true)
total=$((done_count + wip_count + todo_count))
echo "**Umumiy holat:** ${done_count} / ${total} bajarildi (${wip_count} jarayonda)"
