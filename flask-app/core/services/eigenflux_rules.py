#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EigenFlux 规则引擎 — 统一规则定义与严格执行  [v1.0.0]
======================================================
**设计目标**：
  将 MTSCOS 项目中 20+ 个 EigenFlux 相关模块的架构规范、命名约定、
  模块职责、API 设计、错误处理、安全约束、数据流、集成模式、性能
  要求和监控规范统一为一份可执行的规则引擎。

**架构**（规则定义 + 验证器 + 执行器）：

  ┌────────────────────────────────────────────────────┐
  │            EigenFluxRulesEngine (本模块)            │
  │   规则定义 · 验证器 · 执行器 · 审计日志 · 报告生成   │
  └───────────────────────┬────────────────────────────┘
                          │ 约束
  ┌───────────────────────▼────────────────────────────┐
  │  eigenflux_*.py / app/services/eigenflux_*.py      │
  │  services/ai/eigenflux_*.py                        │
  │  所有 EigenFlux 相关模块必须遵循本规则               │
  └────────────────────────────────────────────────────┘

**规则分类**：
  R01 — 架构规则（分层架构、模块边界、依赖方向）
  R02 — 命名规则（文件命名、类命名、函数命名、数据库表命名）
  R03 — 模块职责规则（单一职责、职责边界、禁止越界）
  R04 — API 设计规则（统一入口、参数规范、返回格式）
  R05 — 错误处理规则（异常分类、重试策略、降级策略）
  R06 — 安全规则（权限控制、数据加密、审计日志）
  R07 — 数据流规则（数据库规范、状态流转、缓存策略）
  R08 — 集成规则（EigenFlux.al 适配器、广播协议、心跳机制）
  R09 — 性能规则（重试上限、超时控制、资源回收）
  R10 — 监控规则（健康检查、指标采集、告警阈值）

**使用方式**：
  方式 A：规则验证
      from core.services.eigenflux_rules import EigenFluxRulesEngine
      engine = EigenFluxRulesEngine()
      report = engine.validate_project()

  方式 B：规则查询
      rules = engine.get_rules_by_category('R05')
      for r in rules:
          print(f"[{r['id']}] {r['title']}: {r['description']}")

  方式 C：规则执行（在代码中引用规则）
      engine.enforce('R05-01', context={'retry_count': 3})

**无 Flask 依赖**：本模块可独立运行，不依赖 Flask。
"""

from __future__ import annotations

import os
import sys
import json
import time
import uuid
import sqlite3
import logging
import threading
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)

# ============================================================
#  0. 路径准备
# ============================================================
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.dirname(_THIS_DIR)
_PROJECT_ROOT = os.path.dirname(_CORE_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

MAX_RETRIES = 3  # 全局重试上限（遵循项目规则 R09-01）


# ============================================================
#  1. 规则定义（R01 ~ R10）
# ============================================================

EIGENFLUX_RULES: Dict[str, Dict[str, Any]] = {

    # ==================== R01 — 架构规则 ====================
    'R01-01': {
        'category': 'R01_架构',
        'title': '三层分层架构',
        'description': 'EigenFlux 模块必须遵循：核心层(core/services) → 服务层(app/services) → 脚本层(根目录) 的分层架构，依赖方向只能从上到下',
        'severity': 'critical',
        'enforceable': True,
        'check': 'layer_dependency',
    },
    'R01-02': {
        'category': 'R01_架构',
        'title': 'Facade 统一入口',
        'description': '每个子系统必须提供 Facade 统一入口（如 vikey_api.py 模式），禁止业务代码直接调用底层驱动',
        'severity': 'high',
        'enforceable': True,
        'check': 'facade_pattern',
    },
    'R01-03': {
        'category': 'R01_架构',
        'title': '模块间通信通过事件总线',
        'description': 'EigenFlux 模块间通信必须通过事件总线(event_bus)或适配器(adapter)，禁止直接 import 其他子系统内部模块',
        'severity': 'high',
        'enforceable': True,
        'check': 'module_communication',
    },
    'R01-04': {
        'category': 'R01_架构',
        'title': '神经元架构对齐',
        'description': '所有 AI 员工必须映射到神经元类型(sensory/motor/inter/memory/inhibitory/excitatory)，遵循 eigenflux_neuron.py 定义',
        'severity': 'medium',
        'enforceable': True,
        'check': 'neuron_alignment',
    },

    # ==================== R02 — 命名规则 ====================
    'R02-01': {
        'category': 'R02_命名',
        'title': '文件命名规范',
        'description': 'EigenFlux 相关文件必须以 eigenflux_ 前缀命名（如 eigenflux_xxx.py），核心服务层以 eigenflux_ 前缀放在 core/services/ 下',
        'severity': 'high',
        'enforceable': True,
        'check': 'file_naming',
    },
    'R02-02': {
        'category': 'R02_命名',
        'title': '类命名规范',
        'description': '服务类必须以 EigenFlux 前缀 + 功能 + Service/Engine/Manager 命名（如 EigenFluxAutoRepairService）',
        'severity': 'medium',
        'enforceable': True,
        'check': 'class_naming',
    },
    'R02-03': {
        'category': 'R02_命名',
        'title': '数据库表命名规范',
        'description': 'EigenFlux 相关数据库表必须以 eigenflux_ 或 auto_ 前缀命名，字段使用 snake_case',
        'severity': 'medium',
        'enforceable': True,
        'check': 'table_naming',
    },
    'R02-04': {
        'category': 'R02_命名',
        'title': 'API 端点命名规范',
        'description': '对外 API 端点必须以 /api/eigenflux/ 前缀命名，使用 kebab-case',
        'severity': 'medium',
        'enforceable': True,
        'check': 'api_naming',
    },

    # ==================== R03 — 模块职责规则 ====================
    'R03-01': {
        'category': 'R03_职责',
        'title': '单一职责原则',
        'description': '每个 EigenFlux 模块只负责一个核心功能域（修复/发现/巡逻/增强/安全/教育等），禁止跨域混用',
        'severity': 'high',
        'enforceable': True,
        'check': 'single_responsibility',
    },
    'R03-02': {
        'category': 'R03_职责',
        'title': '自动修复服务职责边界',
        'description': 'eigenflux_auto_repair_service.py 只负责异常分类、修复策略匹配、修复执行与验证，不负责问题发现',
        'severity': 'high',
        'enforceable': True,
        'check': 'repair_boundary',
    },
    'R03-03': {
        'category': 'R03_职责',
        'title': '自动发现服务职责边界',
        'description': 'eigenflux_auto_discovery.py 只负责问题扫描、发现和记录，不负责修复执行',
        'severity': 'high',
        'enforceable': True,
        'check': 'discovery_boundary',
    },
    'R03-04': {
        'category': 'R03_职责',
        'title': '适配器职责边界',
        'description': 'eigenflux_adapter.py 只负责与 EigenFlux.al 外部网络的通信，不包含业务逻辑',
        'severity': 'high',
        'enforceable': True,
        'check': 'adapter_boundary',
    },
    'R03-05': {
        'category': 'R03_职责',
        'title': '规则引擎职责边界',
        'description': 'eigenflux_rules.py(本模块)只负责规则定义、验证和执行判定，不包含业务实现逻辑',
        'severity': 'high',
        'enforceable': True,
        'check': 'rules_boundary',
    },

    # ==================== R04 — API 设计规则 ====================
    'R04-01': {
        'category': 'R04_API',
        'title': '统一返回格式',
        'description': '所有 EigenFlux API 必须返回统一格式：{"success": bool, "data": ..., "message": str, "rule_id": str}',
        'severity': 'high',
        'enforceable': True,
        'check': 'return_format',
    },
    'R04-02': {
        'category': 'R04_API',
        'title': '模块级单例模式',
        'description': '每个 EigenFlux 服务必须提供模块级单例获取函数（如 get_eigenflux_xxx()），禁止每次 new',
        'severity': 'medium',
        'enforceable': True,
        'check': 'singleton_pattern',
    },
    'R04-03': {
        'category': 'R04_API',
        'title': '便捷函数导出',
        'description': '每个服务模块必须在 __all__ 中导出便捷函数，方便上层调用（如 vikey_api.py 模式）',
        'severity': 'medium',
        'enforceable': True,
        'check': 'convenience_exports',
    },
    'R04-04': {
        'category': 'R04_API',
        'title': '版本信息暴露',
        'description': '每个服务模块必须提供 get_version_info() 方法，返回版本号和依赖信息',
        'severity': 'low',
        'enforceable': True,
        'check': 'version_info',
    },

    # ==================== R05 — 错误处理规则 ====================
    'R05-01': {
        'category': 'R05_错误',
        'title': '重试上限3次',
        'description': '所有自动修复操作最多重试3次（MAX_RETRIES=3），超过后标记为失败并记录',
        'severity': 'critical',
        'enforceable': True,
        'check': 'retry_limit',
    },
    'R05-02': {
        'category': 'R05_错误',
        'title': '异常分类体系',
        'description': '异常必须按 EXCEPTION_CATEGORIES 分类（import_error/syntax_error/attribute_error 等），每类有对应的修复策略',
        'severity': 'high',
        'enforceable': True,
        'check': 'exception_category',
    },
    'R05-03': {
        'category': 'R05_错误',
        'title': '降级策略',
        'description': '当自动修复失败时，必须执行降级策略：记录日志 → 通知管理员 → 保持系统运行（禁止崩溃）',
        'severity': 'critical',
        'enforceable': True,
        'check': 'degradation_strategy',
    },
    'R05-04': {
        'category': 'R05_错误',
        'title': '修复验证机制',
        'description': '每次修复后必须执行验证，验证通过才标记为已修复，失败则触发重试',
        'severity': 'high',
        'enforceable': True,
        'check': 'repair_verification',
    },
    'R05-05': {
        'category': 'R05_错误',
        'title': '知识库积累',
        'description': '每次修复（成功或失败）必须记录到修复知识库，包含异常类型、修复策略、修复结果，供后续复用',
        'severity': 'high',
        'enforceable': True,
        'check': 'knowledge_accumulation',
    },

    # ==================== R06 — 安全规则 ====================
    'R06-01': {
        'category': 'R06_安全',
        'title': '超级管理员操作需VIKEY认证',
        'description': '所有超级管理员级别的 EigenFlux 操作（修复策略变更、规则修改、系统锁定）必须通过 VIKEY 硬件认证',
        'severity': 'critical',
        'enforceable': True,
        'check': 'vikey_auth_required',
    },
    'R06-02': {
        'category': 'R06_安全',
        'title': '操作审计日志',
        'description': '所有 EigenFlux 自动修复、功能拓展、规则变更操作必须记录审计日志，包含操作者、时间、操作内容、结果',
        'severity': 'high',
        'enforceable': True,
        'check': 'audit_log',
    },
    'R06-03': {
        'category': 'R06_安全',
        'title': '敏感数据脱敏',
        'description': '日志和数据库中不得存储明文密码、密钥、Token 等敏感信息，必须脱敏处理',
        'severity': 'critical',
        'enforceable': True,
        'check': 'data_masking',
    },
    'R06-04': {
        'category': 'R06_安全',
        'title': '权限最小化',
        'description': 'EigenFlux 自动修复进程以最小权限运行，禁止 root/admin 权限执行修复操作',
        'severity': 'high',
        'enforceable': True,
        'check': 'least_privilege',
    },
    'R06-05': {
        'category': 'R06_安全',
        'title': '紧急访问Break-Glass',
        'description': '紧急情况下超级管理员可通过 VIKEY 认证临时提升权限，全程审计、24小时内审查、自动降回',
        'severity': 'high',
        'enforceable': True,
        'check': 'break_glass',
    },

    # ==================== R07 — 数据流规则 ====================
    'R07-01': {
        'category': 'R07_数据流',
        'title': '数据库连接规范',
        'description': '所有 EigenFlux 模块必须使用 core.db_path.get_db_path() 解析数据库路径，禁止硬编码路径',
        'severity': 'critical',
        'enforceable': True,
        'check': 'db_path_resolution',
    },
    'R07-02': {
        'category': 'R07_数据流',
        'title': 'WAL模式与忙超时',
        'description': '数据库连接必须启用 WAL 模式和 busy_timeout=30000，防止锁冲突',
        'severity': 'high',
        'enforceable': True,
        'check': 'db_wal_mode',
    },
    'R07-03': {
        'category': 'R07_数据流',
        'title': '状态流转规范',
        'description': '问题/修复状态必须按流转：detected → analyzing → repairing → verifying → fixed/failed，禁止跳过验证',
        'severity': 'high',
        'enforceable': True,
        'check': 'state_transition',
    },
    'R07-04': {
        'category': 'R07_数据流',
        'title': '线程安全',
        'description': '所有共享状态的 EigenFlux 服务必须使用 threading.RLock() 保护并发访问',
        'severity': 'high',
        'enforceable': True,
        'check': 'thread_safety',
    },

    # ==================== R08 — 集成规则 ====================
    'R08-01': {
        'category': 'R08_集成',
        'title': 'EigenFlux.al 适配器统一入口',
        'description': '与 EigenFlux.al 外部网络的所有通信必须通过 eigenflux_adapter.py，禁止其他模块直接调用外部 API',
        'severity': 'critical',
        'enforceable': True,
        'check': 'adapter_singleton',
    },
    'R08-02': {
        'category': 'R08_集成',
        'title': '心跳间隔60秒',
        'description': 'EigenFlux.al 网络心跳间隔固定为60秒，超时3次未响应标记为离线',
        'severity': 'medium',
        'enforceable': True,
        'check': 'heartbeat_interval',
    },
    'R08-03': {
        'category': 'R08_集成',
        'title': '广播协议规范',
        'description': '广播消息必须包含：message_id(uuid)、source、topic、payload、timestamp、signature',
        'severity': 'high',
        'enforceable': True,
        'check': 'broadcast_protocol',
    },
    'R08-04': {
        'category': 'R08_集成',
        'title': '最大重试3次(网络)',
        'description': '与 EigenFlux.al 网络通信失败时最多重试3次，超过后进入离线模式',
        'severity': 'high',
        'enforceable': True,
        'check': 'network_retry',
    },

    # ==================== R09 — 性能规则 ====================
    'R09-01': {
        'category': 'R09_性能',
        'title': '全局重试上限3次',
        'description': '所有重试操作（修复/网络/数据库）全局上限3次，MAX_RETRIES=3',
        'severity': 'critical',
        'enforceable': True,
        'check': 'global_retry_limit',
    },
    'R09-02': {
        'category': 'R09_性能',
        'title': '超时控制',
        'description': '所有外部调用必须设置超时：网络30s、数据库30s、子进程60s，禁止无限等待',
        'severity': 'high',
        'enforceable': True,
        'check': 'timeout_control',
    },
    'R09-03': {
        'category': 'R09_性能',
        'title': '资源回收',
        'description': '所有线程、连接、文件句柄必须在使用后关闭/回收，推荐使用 contextmanager',
        'severity': 'high',
        'enforceable': True,
        'check': 'resource_cleanup',
    },
    'R09-04': {
        'category': 'R09_性能',
        'title': '修复缓存',
        'description': '已修复过的异常必须缓存修复方案，相同异常直接复用，避免重复分析',
        'severity': 'medium',
        'enforceable': True,
        'check': 'repair_cache',
    },

    # ==================== R10 — 监控规则 ====================
    'R10-01': {
        'category': 'R10_监控',
        'title': '健康检查接口',
        'description': '每个 EigenFlux 服务必须提供 health_check() 方法，返回 {status, issues, uptime}',
        'severity': 'high',
        'enforceable': True,
        'check': 'health_check',
    },
    'R10-02': {
        'category': 'R10_监控',
        'title': '指标采集',
        'description': '服务必须采集核心指标：total_detected、total_repaired、total_failed、total_retries、repair_rate',
        'severity': 'medium',
        'enforceable': True,
        'check': 'metrics_collection',
    },
    'R10-03': {
        'category': 'R10_监控',
        'title': '汇总报告',
        'description': '服务必须提供 get_summary() 方法，返回完整运行汇总报告',
        'severity': 'medium',
        'enforceable': True,
        'check': 'summary_report',
    },
    'R10-04': {
        'category': 'R10_监控',
        'title': '定期巡检',
        'description': '系统必须支持定期健康巡检（full/quick两种模式），巡检结果记录到数据库',
        'severity': 'medium',
        'enforceable': True,
        'check': 'periodic_patrol',
    },
}


# ============================================================
#  2. 规则引擎
# ============================================================

class EigenFluxRulesEngine:
    """
    EigenFlux 规则引擎

    职责：
      1. 规则定义（EIGENFLUX_RULES）
      2. 规则验证（validate_project / validate_module）
      3. 规则执行（enforce / enforce_batch）
      4. 审计日志（log_enforcement）
      5. 报告生成（generate_report）

    遵循规则：
      - R03-05: 本模块只负责规则定义和验证，不包含业务逻辑
      - R04-02: 提供模块级单例
      - R07-04: 使用 RLock 保护并发
      - R09-01: 重试上限3次
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._rules = dict(EIGENFLUX_RULES)
        self._enforcement_log: List[Dict[str, Any]] = []
        self._violation_cache: Dict[str, List[Dict]] = {}

    # -------------------- 规则查询 --------------------

    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有规则"""
        with self._lock:
            return dict(self._rules)

    def get_rules_by_category(self, category_prefix: str) -> List[Dict[str, Any]]:
        """按分类前缀获取规则（如 'R05' 返回所有错误处理规则）"""
        with self._lock:
            return [
                {'id': rid, **rule}
                for rid, rule in self._rules.items()
                if rule['category'].startswith(category_prefix)
            ]

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """获取单条规则"""
        with self._lock:
            rule = self._rules.get(rule_id)
            if rule:
                return {'id': rule_id, **rule}
            return None

    def get_categories(self) -> List[str]:
        """获取所有规则分类"""
        with self._lock:
            return sorted(set(r['category'] for r in self._rules.values()))

    # -------------------- 规则执行 --------------------

    def enforce(self, rule_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行单条规则验证

        参数：
          rule_id: 规则ID（如 'R05-01'）
          context: 验证上下文（如 {'retry_count': 3}）

        返回：
          {"success": bool, "rule_id": str, "result": str, "violations": list}

        遵循 R04-01 统一返回格式
        """
        with self._lock:
            rule = self._rules.get(rule_id)
            if not rule:
                return {
                    'success': False,
                    'rule_id': rule_id,
                    'result': 'rule_not_found',
                    'violations': [f'规则 {rule_id} 不存在'],
                }

            context = context or {}
            violations: List[str] = []
            check_type = rule.get('check', '')

            # ---- R05-01: 重试上限3次 ----
            if check_type == 'retry_limit' or check_type == 'global_retry_limit':
                retry_count = context.get('retry_count', 0)
                if retry_count > MAX_RETRIES:
                    violations.append(
                        f"重试次数 {retry_count} 超过上限 {MAX_RETRIES}"
                    )

            # ---- R08-04 / R09-02: 网络重试 / 超时控制 ----
            elif check_type == 'network_retry':
                retry_count = context.get('retry_count', 0)
                if retry_count > MAX_RETRIES:
                    violations.append(
                        f"网络重试 {retry_count} 超过上限 {MAX_RETRIES}，应进入离线模式"
                    )

            elif check_type == 'timeout_control':
                timeout = context.get('timeout', 0)
                call_type = context.get('call_type', 'unknown')
                limits = {'network': 30, 'database': 30, 'subprocess': 60}
                limit = limits.get(call_type, 30)
                if timeout == 0 or timeout > limit:
                    violations.append(
                        f"{call_type} 超时 {timeout}s 不合法，应为 {limit}s"
                    )

            # ---- R07-01: 数据库路径解析 ----
            elif check_type == 'db_path_resolution':
                db_path = context.get('db_path', '')
                if 'app.db' in db_path and 'core' not in db_path and 'db_path' not in str(context.get('resolver', '')):
                    violations.append(
                        f"数据库路径 {db_path} 未通过 core.db_path.get_db_path() 解析"
                    )

            # ---- R07-02: WAL 模式 ----
            elif check_type == 'db_wal_mode':
                conn_attrs = context.get('conn_attrs', {})
                if not conn_attrs.get('journal_mode') == 'WAL':
                    violations.append("数据库连接未启用 WAL 模式")
                if not conn_attrs.get('busy_timeout', 0) >= 30000:
                    violations.append("数据库 busy_timeout 未设置为 30000")

            # ---- R07-03: 状态流转 ----
            elif check_type == 'state_transition':
                valid_flow = ['detected', 'analyzing', 'repairing', 'verifying', 'fixed', 'failed']
                from_state = context.get('from_state', '')
                to_state = context.get('to_state', '')
                if from_state in valid_flow and to_state in valid_flow:
                    from_idx = valid_flow.index(from_state)
                    to_idx = valid_flow.index(to_state)
                    # fixed/failed 是终态，不可流转
                    if from_state in ('fixed', 'failed') and to_state != from_state:
                        violations.append(
                            f"非法状态流转: {from_state} → {to_state}（终态不可流转）"
                        )
                    # 不允许跳过 verifying
                    if from_state == 'repairing' and to_state == 'fixed':
                        violations.append(
                            f"非法状态流转: {from_state} → {to_state}（不可跳过 verifying）"
                        )

            # ---- R07-04: 线程安全 ----
            elif check_type == 'thread_safety':
                has_lock = context.get('has_lock', False)
                shared_state = context.get('shared_state', False)
                if shared_state and not has_lock:
                    violations.append("共享状态未使用锁保护")

            # ---- R06-01: VIKEY 认证 ----
            elif check_type == 'vikey_auth_required':
                has_vikey = context.get('vikey_authenticated', False)
                operation = context.get('operation', '')
                if not has_vikey:
                    violations.append(
                        f"超级管理员操作 '{operation}' 未通过 VIKEY 硬件认证"
                    )

            # ---- R06-02: 审计日志 ----
            elif check_type == 'audit_log':
                has_audit = context.get('audit_logged', False)
                if not has_audit:
                    violations.append("操作未记录审计日志")

            # ---- R06-03: 数据脱敏 ----
            elif check_type == 'data_masking':
                data = str(context.get('data', ''))
                sensitive_patterns = ['password', 'passwd', 'token', 'secret', 'api_key']
                for p in sensitive_patterns:
                    if p in data.lower():
                        violations.append(f"日志/数据中包含敏感字段: {p}")

            # ---- R09-04: 修复缓存 ----
            elif check_type == 'repair_cache':
                has_cache = context.get('has_cache', False)
                exception_type = context.get('exception_type', '')
                if not has_cache and exception_type:
                    violations.append(
                        f"异常类型 {exception_type} 未使用修复缓存"
                    )

            # ---- R10-01: 健康检查 ----
            elif check_type == 'health_check':
                has_health_check = context.get('has_health_check', False)
                if not has_health_check:
                    violations.append("服务未提供 health_check() 方法")

            # ---- R10-02: 指标采集 ----
            elif check_type == 'metrics_collection':
                metrics = context.get('metrics', {})
                required = ['total_detected', 'total_repaired', 'total_failed', 'total_retries']
                for m in required:
                    if m not in metrics:
                        violations.append(f"缺少核心指标: {m}")

            # ---- R08-02: 心跳间隔 ----
            elif check_type == 'heartbeat_interval':
                interval = context.get('interval', 0)
                if interval != 60:
                    violations.append(
                        f"心跳间隔 {interval}s 不符合规则（应为 60s）"
                    )

            # ---- R08-03: 广播协议 ----
            elif check_type == 'broadcast_protocol':
                msg = context.get('message', {})
                required_fields = ['message_id', 'source', 'topic', 'payload', 'timestamp', 'signature']
                for f in required_fields:
                    if f not in msg:
                        violations.append(f"广播消息缺少字段: {f}")

            # ---- R04-01: 统一返回格式 ----
            elif check_type == 'return_format':
                result = context.get('result', {})
                required_fields = ['success', 'data', 'message']
                for f in required_fields:
                    if f not in result:
                        violations.append(f"返回结果缺少字段: {f}")

            # ---- R05-04: 修复验证 ----
            elif check_type == 'repair_verification':
                verified = context.get('verified', False)
                status = context.get('status', '')
                if status == 'fixed' and not verified:
                    violations.append("修复标记为 fixed 但未执行验证")

            result = {
                'success': len(violations) == 0,
                'rule_id': rule_id,
                'rule_title': rule['title'],
                'severity': rule['severity'],
                'result': 'passed' if not violations else 'failed',
                'violations': violations,
                'context': context,
                'timestamp': datetime.now().isoformat(),
            }

            # 记录执行日志
            self._enforcement_log.append(result)
            return result

    def enforce_batch(
        self, rule_ids: List[str], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """批量执行规则验证"""
        results = []
        for rid in rule_ids:
            results.append(self.enforce(rid, context))
        return results

    def enforce_category(
        self, category_prefix: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """按分类批量执行规则验证"""
        rules = self.get_rules_by_category(category_prefix)
        return self.enforce_batch([r['id'] for r in rules], context)

    # -------------------- 项目验证 --------------------

    def validate_project(self) -> Dict[str, Any]:
        """
        验证整个项目的 EigenFlux 规则遵循情况

        扫描所有 eigenflux_*.py 文件，检查命名规范、模块结构等

        返回：
          {"success": bool, "total_rules": int, "passed": int, "failed": int,
           "violations": list, "report": str}
        """
        with self._lock:
            violations: List[Dict[str, Any]] = []
            passed_count = 0
            failed_count = 0

            # 1. 扫描所有 eigenflux_*.py 文件
            eigenflux_files = self._scan_eigenflux_files()

            # 2. 验证 R02-01 文件命名规范
            for fpath in eigenflux_files:
                fname = os.path.basename(fpath)
                if not fname.startswith('eigenflux_'):
                    violations.append({
                        'rule_id': 'R02-01',
                        'file': fpath,
                        'message': f'文件 {fname} 未以 eigenflux_ 前缀命名',
                    })
                    failed_count += 1
                else:
                    passed_count += 1

            # 3. 验证 R07-01 数据库路径解析
            for fpath in eigenflux_files:
                content = self._read_file_safe(fpath)
                if content and 'DB_PATH' in content:
                    if 'get_db_path' not in content and 'db_path' not in content.lower():
                        violations.append({
                            'rule_id': 'R07-01',
                            'file': fpath,
                            'message': '硬编码 DB_PATH，未使用 core.db_path.get_db_path()',
                        })
                        failed_count += 1
                    else:
                        passed_count += 1

            # 4. 验证 R07-02 WAL 模式
            for fpath in eigenflux_files:
                content = self._read_file_safe(fpath)
                if content and 'sqlite3.connect' in content:
                    if 'journal_mode' not in content or 'WAL' not in content:
                        violations.append({
                            'rule_id': 'R07-02',
                            'file': fpath,
                            'message': '数据库连接未启用 WAL 模式',
                        })
                        failed_count += 1
                    else:
                        passed_count += 1

            # 5. 验证 R09-01 重试上限
            for fpath in eigenflux_files:
                content = self._read_file_safe(fpath)
                if content:
                    if 'MAX_RETRIES' in content or 'max_retries' in content:
                        # 检查是否为3
                        import re
                        matches = re.findall(r'MAX_RETRIES\s*=\s*(\d+)', content)
                        for m in matches:
                            if int(m) != 3:
                                violations.append({
                                    'rule_id': 'R09-01',
                                    'file': fpath,
                                    'message': f'MAX_RETRIES={m}，应为 3',
                                })
                                failed_count += 1
                            else:
                                passed_count += 1

            # 6. 验证 R06-03 数据脱敏
            for fpath in eigenflux_files:
                content = self._read_file_safe(fpath)
                if content:
                    lower_content = content.lower()
                    # 检查是否有明文密码（简单的启发式检查）
                    if 'password = ' in lower_content and "'password'" not in lower_content:
                        # 排除变量赋值和配置项
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            stripped = line.strip().lower()
                            if stripped.startswith('password = ') and 'get(' not in stripped and 'input' not in stripped:
                                if not stripped.startswith('#') and not stripped.startswith("'"):
                                    violations.append({
                                        'rule_id': 'R06-03',
                                        'file': fpath,
                                        'line': i + 1,
                                        'message': f'可能的明文密码: {line.strip()[:80]}',
                                    })
                                    failed_count += 1
                                    break

            total = passed_count + failed_count
            success = failed_count == 0

            report = self._generate_report(
                total, passed_count, failed_count, violations, eigenflux_files
            )

            return {
                'success': success,
                'total_rules': total,
                'passed': passed_count,
                'failed': failed_count,
                'violations': violations,
                'files_scanned': len(eigenflux_files),
                'report': report,
            }

    def validate_module(self, module_path: str) -> Dict[str, Any]:
        """
        验证单个模块的规则遵循情况

        参数：
          module_path: 模块文件路径

        返回：
          {"success": bool, "violations": list, "checks": list}
        """
        with self._lock:
            violations: List[Dict[str, Any]] = []
            checks: List[Dict[str, Any]] = []

            content = self._read_file_safe(module_path)
            if not content:
                return {
                    'success': False,
                    'violations': [{'message': f'无法读取文件: {module_path}'}],
                    'checks': [],
                }

            fname = os.path.basename(module_path)

            # R02-01 文件命名
            check_r0201 = {
                'rule_id': 'R02-01',
                'passed': fname.startswith('eigenflux_'),
                'message': f'文件命名: {fname}',
            }
            checks.append(check_r0201)
            if not check_r0201['passed']:
                violations.append({'rule_id': 'R02-01', 'message': f'文件 {fname} 未以 eigenflux_ 前缀命名'})

            # R07-01 数据库路径
            if 'DB_PATH' in content:
                check_r0701 = {
                    'rule_id': 'R07-01',
                    'passed': 'get_db_path' in content or 'db_path' in content.lower(),
                    'message': '数据库路径解析',
                }
                checks.append(check_r0701)
                if not check_r0701['passed']:
                    violations.append({'rule_id': 'R07-01', 'message': '硬编码 DB_PATH'})

            # R07-02 WAL 模式
            if 'sqlite3.connect' in content:
                check_r0702 = {
                    'rule_id': 'R07-02',
                    'passed': 'WAL' in content and 'busy_timeout' in content,
                    'message': 'WAL 模式与忙超时',
                }
                checks.append(check_r0702)
                if not check_r0702['passed']:
                    violations.append({'rule_id': 'R07-02', 'message': '数据库连接未启用 WAL/busy_timeout'})

            # R07-04 线程安全
            if 'threading' in content:
                check_r0704 = {
                    'rule_id': 'R07-04',
                    'passed': 'RLock' in content or 'Lock' in content,
                    'message': '线程安全锁保护',
                }
                checks.append(check_r0704)
                if not check_r0704['passed']:
                    violations.append({'rule_id': 'R07-04', 'message': '使用了 threading 但未见锁保护'})

            # R09-01 重试上限
            if 'MAX_RETRIES' in content or 'max_retries' in content:
                import re
                matches = re.findall(r'(?:MAX_RETRIES|max_retries)\s*=\s*(\d+)', content)
                check_r0901 = {
                    'rule_id': 'R09-01',
                    'passed': all(int(m) == 3 for m in matches) if matches else True,
                    'message': f'重试上限: {matches}',
                }
                checks.append(check_r0901)
                if not check_r0901['passed']:
                    violations.append({'rule_id': 'R09-01', 'message': f'MAX_RETRIES 值不为3: {matches}'})

            # R10-01 健康检查
            check_r1001 = {
                'rule_id': 'R10-01',
                'passed': 'health_check' in content or 'run_health_check' in content,
                'message': '健康检查方法',
            }
            checks.append(check_r1001)
            if not check_r1001['passed']:
                violations.append({'rule_id': 'R10-01', 'message': '缺少 health_check 方法'})

            return {
                'success': len(violations) == 0,
                'module': module_path,
                'violations': violations,
                'checks': checks,
            }

    # -------------------- 审计与报告 --------------------

    def get_enforcement_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取规则执行日志"""
        with self._lock:
            return list(self._enforcement_log[-limit:])

    def clear_enforcement_log(self) -> None:
        """清空执行日志"""
        with self._lock:
            self._enforcement_log.clear()

    def generate_report(self) -> Dict[str, Any]:
        """
        生成完整的规则引擎报告

        遵循 R10-03 汇总报告规则
        """
        with self._lock:
            total_rules = len(self._rules)
            categories = self.get_categories()
            enforcement_count = len(self._enforcement_log)
            passed_enforcements = sum(1 for e in self._enforcement_log if e['success'])
            failed_enforcements = enforcement_count - passed_enforcements

            # 按分类统计规则
            category_stats = {}
            for cat in categories:
                rules = self.get_rules_by_category(cat.split('_')[0])
                category_stats[cat] = {
                    'count': len(rules),
                    'rules': [{'id': r['id'], 'title': r['title'], 'severity': r['severity']} for r in rules],
                }

            return {
                'success': True,
                'data': {
                    'engine_version': '1.0.0',
                    'total_rules': total_rules,
                    'categories': len(categories),
                    'category_stats': category_stats,
                    'enforcement_count': enforcement_count,
                    'passed_enforcements': passed_enforcements,
                    'failed_enforcements': failed_enforcements,
                    'pass_rate': f"{(passed_enforcements / enforcement_count * 100):.1f}%" if enforcement_count else 'N/A',
                    'generated_at': datetime.now().isoformat(),
                },
                'message': 'EigenFlux 规则引擎报告',
                'rule_id': 'R10-03',
            }

    # -------------------- 内部方法 --------------------

    def _scan_eigenflux_files(self) -> List[str]:
        """扫描项目中所有 eigenflux_*.py 文件"""
        results: List[str] = []
        for root, dirs, files in os.walk(_PROJECT_ROOT):
            # 跳过隐藏目录和虚拟环境
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', '.venv', 'venv')]
            for f in files:
                if 'eigenflux' in f.lower() and f.endswith('.py'):
                    results.append(os.path.join(root, f))
        return sorted(results)

    def _read_file_safe(self, fpath: str, max_size: int = 512 * 1024) -> Optional[str]:
        """安全读取文件内容"""
        try:
            if os.path.getsize(fpath) > max_size:
                return None
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None

    def _generate_report(
        self,
        total: int,
        passed: int,
        failed: int,
        violations: List[Dict[str, Any]],
        files: List[str],
    ) -> str:
        """生成验证报告文本"""
        lines = [
            '=' * 60,
            '  EigenFlux 规则验证报告',
            '=' * 60,
            f'  扫描文件数: {len(files)}',
            f'  检查总数:   {total}',
            f'  通过:       {passed}',
            f'  失败:       {failed}',
            f'  通过率:     {(passed / total * 100):.1f}%' if total else '  通过率:     N/A',
            '',
        ]
        if violations:
            lines.append('  违规列表:')
            for v in violations:
                rid = v.get('rule_id', 'N/A')
                fpath = v.get('file', '')
                fname = os.path.basename(fpath) if fpath else ''
                msg = v.get('message', '')
                lines.append(f'    [{rid}] {fname}: {msg}')
        else:
            lines.append('  无违规项')

        lines.extend(['', '=' * 60])
        return '\n'.join(lines)


# ============================================================
#  3. 模块级单例（遵循 R04-02）
# ============================================================

_engine_instance: Optional[EigenFluxRulesEngine] = None
_engine_lock = threading.Lock()


def get_eigenflux_rules_engine() -> EigenFluxRulesEngine:
    """获取规则引擎单例（遵循 R04-02 模块级单例模式）"""
    global _engine_instance
    if _engine_instance is None:
        with _engine_lock:
            if _engine_instance is None:
                _engine_instance = EigenFluxRulesEngine()
    return _engine_instance


# ============================================================
#  4. 便捷函数（遵循 R04-03 便捷函数导出）
# ============================================================

def validate_project() -> Dict[str, Any]:
    """验证整个项目的 EigenFlux 规则遵循情况"""
    return get_eigenflux_rules_engine().validate_project()


def validate_module(module_path: str) -> Dict[str, Any]:
    """验证单个模块"""
    return get_eigenflux_rules_engine().validate_module(module_path)


def enforce_rule(rule_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """执行单条规则验证"""
    return get_eigenflux_rules_engine().enforce(rule_id, context)


def get_rules_by_category(category_prefix: str) -> List[Dict[str, Any]]:
    """按分类获取规则"""
    return get_eigenflux_rules_engine().get_rules_by_category(category_prefix)


def get_all_rules() -> Dict[str, Dict[str, Any]]:
    """获取所有规则"""
    return get_eigenflux_rules_engine().get_all_rules()


def generate_rules_report() -> Dict[str, Any]:
    """生成规则引擎报告"""
    return get_eigenflux_rules_engine().generate_report()


def get_version_info() -> Dict[str, Any]:
    """获取版本信息（遵循 R04-04）"""
    return {
        'module': 'eigenflux_rules',
        'version': '1.0.0',
        'total_rules': len(EIGENFLUX_RULES),
        'categories': len(set(r['category'] for r in EIGENFLUX_RULES.values())),
        'max_retries': MAX_RETRIES,
        'description': 'EigenFlux 统一规则定义与执行引擎',
    }


def health_check() -> Dict[str, Any]:
    """健康检查（遵循 R10-01）"""
    try:
        engine = get_eigenflux_rules_engine()
        return {
            'status': 'healthy',
            'rules_loaded': len(engine.get_all_rules()),
            'enforcement_log_size': len(engine.get_enforcement_log()),
            'issues': [],
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'issues': [str(e)],
        }


__all__ = [
    # 规则定义
    'EIGENFLUX_RULES',
    'MAX_RETRIES',
    # 规则引擎类
    'EigenFluxRulesEngine',
    # 单例
    'get_eigenflux_rules_engine',
    # 便捷函数
    'validate_project',
    'validate_module',
    'enforce_rule',
    'get_rules_by_category',
    'get_all_rules',
    'generate_rules_report',
    'get_version_info',
    'health_check',
]


# ============================================================
#  5. 入口（冒烟测试）
# ============================================================

if __name__ == '__main__':
    print('=' * 60)
    print('  EigenFlux 规则引擎 — 冒烟测试')
    print('=' * 60)

    info = get_version_info()
    print(f"\n[1] 版本信息: {info['module']} v{info['version']}")
    print(f"    规则总数: {info['total_rules']}")
    print(f"    分类数:   {info['categories']}")
    print(f"    重试上限: {info['max_retries']}")

    print('\n[2] 规则分类:')
    engine = get_eigenflux_rules_engine()
    for cat in engine.get_categories():
        rules = engine.get_rules_by_category(cat.split('_')[0])
        print(f"    {cat}: {len(rules)} 条规则")

    print('\n[3] 单条规则验证:')
    r = enforce_rule('R05-01', {'retry_count': 5})
    print(f"    R05-01 (重试5次): success={r['success']}, violations={r['violations']}")

    r = enforce_rule('R05-01', {'retry_count': 3})
    print(f"    R05-01 (重试3次): success={r['success']}, violations={r['violations']}")

    r = enforce_rule('R06-01', {'vikey_authenticated': False, 'operation': '修改修复策略'})
    print(f"    R06-01 (无VIKEY): success={r['success']}, violations={r['violations']}")

    print('\n[4] 项目验证:')
    r = validate_project()
    print(r['report'])

    print('\n[5] 健康检查:')
    r = health_check()
    print(f"    状态: {r['status']}, 规则数: {r['rules_loaded']}")

    print('\n[6] 规则报告:')
    r = generate_rules_report()
    print(f"    总规则: {r['data']['total_rules']}")
    print(f"    分类数: {r['data']['categories']}")
    print(f"    执行次数: {r['data']['enforcement_count']}")

    print('\n' + '=' * 60)
    print('  冒烟测试完成')
    print('=' * 60)
