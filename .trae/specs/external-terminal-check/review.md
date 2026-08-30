# Review: flow_external_terminal_check

## 结论：PASS（待 T6 live 复验后最终关闭）

## 变更清单
| 文件 | 类型 | 说明 |
|------|------|------|
| flask-app/app/middlewares/vikey_enforcement_middleware.py | 新增(正本同步) | FIX-1：恢复 SA 双钥强制认证；SHA256 与 _output 正本一致 |
| flask-app/scripts/verify_external_terminal_access.py | 新增 | 四段式验证：A部署/B判定/C live/D外部IP模拟 |
| flask-app/scripts/iron_rule_flow_runner_external_check.py | 新增 | §14 12步骤 flow 执行脚本 |

## 安全审查
- [x] fail-open → fail-closed：中间件加载恢复后，SA 访问需 VIKEY+SZU100+插钥终端+网络四重校验
- [x] 终端绑定不信任 X-Forwarded-For，仅 TCP remote_addr
- [x] 空 IP / 映射地址 / 未知 IP 一律 NOT_BOUND
- [x] 防盗链外站分支优先于白名单前缀（防静态资源盗链绕过）
- [x] 无新增路由、无权限装饰器缺口
- [x] 回滚方案：删除运行位文件即可恢复原状（流程记录保留）

## 已知边界
- verify D 段（外部 IP 模拟）依赖 sudo 免密配置 lo0 alias；不可用时 SKIP，由 B 段矩阵覆盖
- mini 设备 242 离线为独立网络事件，不在本 flow 修复范围
