# Review: 全站防盗链拦截 + /index 路由

- **验收人**: 石监理(shi-003/AI监理) + wuchenghao15(SA)
- **结论**: PASS —— AC-1..AC-8 全满足，MT_IR_D1..D8 零违反，自测 A+B 7/7 PASS（live C 服务重启后复验）

## 过程发现与修复
1. **静态白名单顺序缺陷**（设计评审发现）：初版白名单前缀判定先于外站分支，`/static/*` 外站盗链会被放行。
   → 重构判定顺序：外站 Referer 分支最优先，白名单前缀仅适用本站/无 Referer。
2. **伪造 Referer 端口绕过**（黑客矩阵发现）：`http://127.0.0.1:8888.evil.com/` 经 split(':') 提取后主机名=127.0.0.1 被误判本站。
   → `_mt_hotlink_parse_netloc` hostname+port 双重校验，端口非纯数字一律不信任。
3. **`/index` 404 缺口**：规则文档防盗链重定向目标长期不存在 → 本次与拦截一并落地。

## mandatory_upgrade_flag
True → v22.1.0 → v22.2.0（MINOR：全站新安全面 + 2 处安全缺陷修复 + 路由补齐）
