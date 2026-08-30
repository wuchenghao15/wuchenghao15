# Tasks: flow_external_terminal_check

- [x] T1 勘察：3 处 import 失败根因（运行位缺文件）+ 影响面评估（3351 次/日 fail-open）
- [x] T2 FIX-1 部署：正本同步 `flask-app/app/middlewares/vikey_enforcement_middleware.py`（SHA256 一致）
- [x] T3 验证脚本：`flask-app/scripts/verify_external_terminal_access.py`（A/B/C/D 四段式）
- [x] T4 flow 脚本：`flask-app/scripts/iron_rule_flow_runner_external_check.py`（12 步骤 + 1000 轮 1:1 真源）
- [x] T5 执行 flow → FINAL_DONE + v22.2.0→v22.3.0 + git 同步
- [ ] T6 重启 Flask → verify live 复验（C3 401 结构化 / C6 日志零新增报错）
- [ ] T7 溯源三件套（恢复镜像/节点/沙盒/影子节点）
