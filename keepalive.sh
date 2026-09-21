#!/bin/bash
# MTSCOS AI 仙女座 keepalive — 每分钟巡检关键 daemon
PROJECT_ROOT="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
AUTO_D="$PROJECT_ROOT/_runtime/auto_daemons"
LOG="$PROJECT_ROOT/_runtime/logs/keepalive.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')
mkdir -p "$(dirname "$LOG")"

DAEMONS=(sys_heartbeat_writer sys_patrol_inspector sys_eigenflux_network
         sys_auto_repair sys_local_inference sys_rule_enforcer
         sys_auto_patrol sys_auto_hire sys_deep_inspection
         sys_ramanujan_derive sys_andromeda_auto_evolution
         sys_auto_hire sys_file_organizer sys_copy_inspection)

CHECKED=0; ALIVE=0; LAUNCHED=0
for name in "${DAEMONS[@]}"; do
    CHECKED=$((CHECKED+1))
    pid=$(pgrep -f "_runtime/auto_daemons/${name}\.py" 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        ALIVE=$((ALIVE+1))
    else
        [ -f "$AUTO_D/${name}.py" ] && nohup python3 "$AUTO_D/${name}.py" >> "$LOG" 2>&1 &
        LAUNCHED=$((LAUNCHED+1))
    fi
done
[ $LAUNCHED -gt 0 ] && echo "[$NOW] checked=$CHECKED alive=$ALIVE launched=$LAUNCHED" >> "$LOG"
