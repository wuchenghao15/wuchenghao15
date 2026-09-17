[规则引擎 + 辅助 AI 组件]
- rules_engine/ : 规则强制执行引擎（8 组件 + Git Hook 模板）
  - rule_meta.py : RULE_META 块解析
  - rule_interceptor.py : Flask 拦截器
  - rule_pre_commit.py : Git Hook 主入口
  - rule_integrity_scanner.py : 覆盖率扫描
  - rule_version.py / rule_db.py / rule_violation_alert.py
- local_ai_unified_gateway.py : 本地 AI 统一网关
- local_ai_mcp_server.py : MCP 工具服务器
