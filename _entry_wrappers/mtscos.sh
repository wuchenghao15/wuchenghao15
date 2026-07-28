#!/usr/bin/env bash
# 薄封装：实际 shell 入口脚本已迁入 entrypoints/mtscos.sh
HERE="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${HERE}/entrypoints/mtscos.sh" "$@"
