#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
§14 STEP_6_AI_TEAM_COORD 三角治理+全员AI员工协调
================================================
flow_id: flow_intelligent_ai_upgrade_20260817_001
协调人: 田经理(AI项目经理 AI_004)
职责:
  1. 三角治理职责矩阵(ai_core_roles_json): 田统筹/石监理验收/韩队长执行
  2. 全员参与协调机制(ai_team_coord_json): 25关键角色+ai_employees表全员动态调度
  3. 子任务分配: 6大方向→18执行组成员
  4. 协调机制: 每日站会/验收会/总结会+EigenFlux内部通信
  5. 推进 STEP_6 → STEP_7_EXECUTE
"""
import sys, os, json, sqlite3
from datetime import datetime

PROJECT_ROOT = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
ENGINE_DIR = os.path.join(PROJECT_ROOT, "flask-app/ai_engines")
sys.path.insert(0, ENGINE_DIR)

from mt_ir14_dev_flow import transition, get_session, ensure_tables, _get_conn, _LOCK, APP_DB

FLOW_ID = "flow_intelligent_ai_upgrade_20260817_001"
ensure_tables()


def upd(**fields):
    with _LOCK:
        c = _get_conn(); cur = c.cursor()
        sets, params = [], []
        for k, v in fields.items():
            val = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            sets.append(f"{k}=?"); params.append(val)
        sets.append("updated_at=?"); params.append(datetime.now().isoformat()); params.append(FLOW_ID)
        cur.execute(f"UPDATE mt_dev_flow_session SET {', '.join(sets)} WHERE flow_id=?", params)
        c.commit(); c.close()


# 查询 ai_employees 表真实数据(遵循数据库唯一数据源硬约束)
ai_db = APP_DB  # ai_engines/app.db
ai_emp_count = 0
try:
    _c = sqlite3.connect(ai_db); _cur = _c.cursor()
    _cur.execute("SELECT COUNT(*) FROM ai_employees")
    ai_emp_count = _cur.fetchone()[0]
    _c.close()
except Exception as e:
    ai_emp_count = -1
    ai_emp_err = str(e)


# ============================================================
# 一、三角治理职责矩阵 (ai_core_roles_json)
# 田统筹 / 石监理验收 / 韩队长执行 + 张晓峰战略否决权 + 超级管理员终审
# ============================================================
AI_CORE_ROLES = {
    "triangle_governance": {
        "coordination": {
            "role": "统筹",
            "ai_id": "田经理_AI_004",
            "职责": "全局统筹+实施计划+进度跟踪+资源协调+团队对接",
            "STEP_6_duty": "三角治理协调+子任务分配+每日站会主持",
            "决策权": "执行层决策(非战略层)+资源调度",
            "否决权": "无(战略层由张晓峰否决)"
        },
        "acceptance": {
            "role": "验收",
            "ai_id": "石监理_AI_005",
            "职责": "6条量化验收指标+验收硬门槛+质量监理+落库审计",
            "STEP_6_duty": "前置验收指标确认+验收标准同步执行组",
            "决策权": "验收层决策(STEP_8验收否决权)",
            "否决权": "验收不通过可触发STEP_9A loopback"
        },
        "execution": {
            "role": "执行",
            "ai_id": "韩队长_AI_007",
            "职责": "下场实施+技术决策+代码落地+Bug修复+团队执行",
            "STEP_6_duty": "执行小组组建+技术方案拆解+实施排期",
            "决策权": "技术层决策(实现方案选型)+Bug修复优先级",
            "否决权": "无(技术争议报田经理仲裁)"
        }
    },
    "strategic_layer": {
        "战略决策": {
            "ai_id": "张晓峰_AI_002",
            "职责": "战略方向+表决+建设性意见+战略否决权",
            "STEP_6_duty": "方案战略审阅+重大争议战略仲裁",
            "否决权": "战略层否决(可暂停方案推进)"
        }
    },
    "final_approval_layer": {
        "超级管理员终审": {
            "username": "wuchenghao15",
            "认证": "VIKEY+SZU100双硬件密钥",
            "职责": "终审+保密撤回+版本终审",
            "STEP_6_duty": "方案终审(选择立即适配或2工作日后)+无痕日志"
        }
    },
    "support_roles": {
        "孙文档_AI_DEL06": {"role": "文档纪要", "STEP_6_duty": "协调过程全程纪要+文档归档"},
        "钱合规_AI_008": {"role": "合规审计", "STEP_6_duty": "协调过程合规审查+版本委员会成员"},
        "林审计_AI_009": {"role": "审计追溯", "STEP_6_duty": "协调决策落库审计+追溯链路"}
    },
    "decision_flow": "执行层(韩)→统筹层(田)→验收层(石)→战略层(张晓峰否决)→终审层(超级管理员)",
    "escalation_rules": {
        "技术争议": "韩队长→田经理仲裁",
        "资源争议": "田经理→张晓峰战略仲裁",
        "验收争议": "石监理→张晓峰战略仲裁",
        "战略争议": "张晓峰→超级管理员终审"
    }
}


# ============================================================
# 二、全员参与协调机制 (ai_team_coord_json)
# ============================================================
AI_TEAM_COORD = {
    "coordination_lead": "田经理_AI_004",
    "coordination_at": datetime.now().isoformat(),

    # 全员参与现状(数据库唯一数据源)
    "workforce_status": {
        "ai_employees_table": "ai_employees (ai_engines/app.db)",
        "ai_employees_count_db": ai_emp_count,
        "ai_employees_note": f"ai_employees表当前{ai_emp_count}条(数据待导入);§14流程已注册25关键角色;全员参与机制通过方向1调度中枢建立后动态注册",
        "key_roles_registered": 25,
        "key_roles_breakdown": {
            "三角治理核心": 3,
            "固定角色支持": 4,
            "方向执行组": 18
        }
    },

    # 6大方向→18执行组成员子任务分配
    "direction_team_assignment": {
        "方向1_调度中枢": {
            "组长": "刘数据库_AI_104",
            "组员": ["赵网络_AI_105", "李开发_AI_003"],
            "阶段分工": {
                "阶段1_daemon注册": ["刘数据库(注册表/状态机)", "李开发(注册API)"],
                "阶段2_优先级调度": ["赵网络(优先级矩阵/依赖图)", "李开发(调度引擎)"],
                "阶段3_故障切换": ["韩队长(心跳/切换)", "陈逆向(告警/恢复)"]
            },
            "每日站会时间": "09:00"
        },
        "方向2_EigenFlux扩建": {
            "组长": "EF_隔离专家_109",
            "组员": ["EF_分布式安全_108", "EF_威胁情报_110"],
            "阶段分工": {
                "阶段1_专家注册库": ["EF_隔离专家(注册表/安全域)", "孙文档(领域分类)"],
                "阶段2_轮值与权重": ["EF_分布式安全(轮值/权重)", "钱合规(权重落库)"],
                "阶段3_表决机制": ["EF_威胁情报(表决API)", "林审计(共识/落库)"]
            },
            "每日站会时间": "09:30"
        },
        "方向3_AI介入引擎": {
            "组长": "张安全_AI_006",
            "组员": ["AI_对抗专家_106", "AI_行为分析_107"],
            "阶段分工": {
                "阶段1_只读审计(30天)": ["张安全(4类钩子)", "AI_行为分析(基线)"],
                "阶段2_介入表决": ["AI_对抗专家(独立进程)", "EF_分布式安全(表决触发)"],
                "阶段3_全链路追溯": ["AI_行为分析(追溯ID)", "林审计(可视化/异常)"]
            },
            "每日站会时间": "10:00"
        },
        "方向4_巡检闭环": {
            "组长": "陈逆向_AI_101",
            "组员": ["李渗透_AI_102", "王密码学_AI_103"],
            "阶段分工": {
                "阶段1_异常检测": ["陈逆向(检测模型)", "AI_行为分析(分级)"],
                "阶段2_修复策略库": ["李渗透(策略库/匹配)", "韩队长(回滚)"],
                "阶段3_脑库投喂": ["王密码学(加密链路)", "孙文档(结构化)"]
            },
            "每日站会时间": "10:30"
        },
        "方向5_功能拓展": {
            "组长": "张架构师_AI_001",
            "组员": ["EF_性能优化_111", "李开发_AI_003(支援)"],
            "阶段分工": {
                "阶段1_AI建议收集": ["张架构师(建议池)", "孙文档(评估矩阵)"],
                "阶段2_AI方向开发": ["韩队长(Top3功能)", "李开发(API/前端)"],
                "阶段3_移动方向": ["张架构师(适配方案)", "李开发(Top2功能)"]
            },
            "每日站会时间": "11:00"
        },
        "方向6_版本管理": {
            "组长": "田经理_AI_004(委员会主席)",
            "组员": ["石监理_AI_005", "钱合规_AI_008"],
            "阶段分工": {
                "阶段1_5级版本体系": ["钱合规(注册表/5级)", "孙文档(历史)"],
                "阶段2_版本委员会": ["田经理+石监理+钱合规(一致通过)"],
                "阶段3_智能bump引擎": ["韩队长(变更识别)", "钱合规(Git tag)"]
            },
            "每日站会时间": "11:30"
        }
    },

    # 协调机制
    "coordination_mechanism": {
        "communication_channel": "EigenFlux内部通信+mt_dev_flow_events事件流+mt_dev_flow_session状态机",
        "meeting_schedule": {
            "每日站会": "各方向组每日(09:00-11:30滚动)+田经理主持全方向会(12:00)",
            "STEP_8验收会": "6方向全部完成后,石监理主持",
            "STEP_9B总结会": "验收通过后,田经理主持"
        },
        "progress_reporting": {
            "频率": "每日2次(站会+晚汇报)",
            "渠道": "mt_dev_flow_events落库+EigenFlux广播",
            "内容": "完成步骤/进行中步骤/阻塞问题/次日计划"
        },
        "conflict_resolution": {
            "技术冲突": "韩队长→田经理仲裁(1h内响应)",
            "资源冲突": "田经理→张晓峰战略仲裁(4h内响应)",
            "验收冲突": "石监理→张晓峰战略仲裁(4h内响应)",
            "战略冲突": "张晓峰→超级管理员终审(24h内响应)"
        },
        "escalation_to_superadmin": {
            "触发条件": "战略冲突未决/版本L1主bump/超级管理员专属事项",
            "认证要求": "VIKEY+SZU100双硬件密钥在线",
            "响应SLA": "24h内(超级管理员可无痕处理)"
        }
    },

    # 全员参与调度策略(依赖方向1调度中枢)
    "workforce_dispatch_strategy": {
        "phase_1_调度中枢未就绪": "25关键角色手动分配(本STEP_6已完成)",
        "phase_2_调度中枢就绪后": "通过mt_daemon_registry表动态注册全员ai_employees,按优先级矩阵调度",
        "phase_3_全员参与": "11326人(规则文档统计)动态调度,数据导入ai_employees表后激活",
        "data_import_plan": "方向1阶段1完成后,启动ai_employees数据导入(从EigenFlux网络/历史记录恢复)"
    },

    # STEP_7执行前置准备
    "step7_preparation": {
        "执行策略选择": "骨架优先(6方向核心表+API骨架),完整实现分步推进,复杂方向拆子flow",
        "执行顺序": "方向6→方向1→方向2→方向4→方向3→方向5(与实施方案终稿一致)",
        "首批执行": "方向6版本管理(最轻量,无依赖)+方向1阶段1daemon注册(基础设施)",
        "风险预案": "任一方向阻塞超4h,田经理仲裁+必要时拆子flow独立推进"
    }
}


# ============================================================
# 三、落库 + 推进 STEP_6 → STEP_7_EXECUTE
# ============================================================
print("=" * 70)
print("  §14 STEP_6_AI_TEAM_COORD 三角治理+全员AI员工协调")
print("=" * 70)

# 1. 落库三角治理职责矩阵+全员参与协调机制
upd(ai_core_roles_json=AI_CORE_ROLES,
    ai_team_coord_json=AI_TEAM_COORD)
print(f"[OK] 三角治理职责矩阵落库: 田统筹/石监理验收/韩队长执行+张晓峰战略否决+超管终审")
print(f"[OK] 全员参与协调机制落库: 25关键角色+ai_employees表({ai_emp_count}条)动态调度")
print(f"[OK] 6大方向子任务分配: 18执行组成员分工完成")
print(f"[OK] 协调机制: 每日站会(滚动)+验收会+总结会+EigenFlux通信")

# 2. 推进状态转移
transition(FLOW_ID, "STEP_7_EXECUTE",
           event_kind="TEAM_COORDINATED",
           payload={"triangle_governance": 3,
                    "key_roles": 25,
                    "ai_employees_in_db": ai_emp_count,
                    "direction_teams": 6,
                    "coordination_mechanism": "daily_standup+acceptance_meeting+summary_meeting"},
           operator="田经理_AI_004")
print(f"[OK] STEP_6 → STEP_7_EXECUTE (三角治理协调完成, 进入下场实施)")

# ============================================================
# 四、验证
# ============================================================
s = get_session(FLOW_ID)
print(f"\n{'='*70}")
print(f"  STEP_6_AI_TEAM_COORD 落库验证")
print(f"{'='*70}")
print(f"  flow_id:              {s['flow_id']}")
print(f"  current_step:         {s['current_step']}")
print(f"  协调人:               田经理(AI项目经理 AI_004)")
print(f"  三角治理:             田统筹/石监理验收/韩队长执行")
print(f"  战略层:               张晓峰(战略否决权)")
print(f"  终审层:               超级管理员wuchenghao15(VIKEY+SZU100)")
print(f"  关键角色:             25人(三角3+固定4+执行组18)")
print(f"  ai_employees表:       {ai_emp_count}条(全员参与机制已建立)")
print(f"  6大方向执行组:        全部分工")
print(f"  决策流:               执行→统筹→验收→战略→终审")
print(f"  协调机制:             每日站会+验收会+总结会+EigenFlux通信")

conn = sqlite3.connect(APP_DB); cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM mt_dev_flow_events WHERE flow_id=?", (FLOW_ID,))
cnt = cur.fetchone()[0]
conn.close()
print(f"  累计事件:             {cnt}条")
print(f"{'='*70}")
print(f"\n下一步: STEP_7_EXECUTE 下场实施(6大方向真实开发,策略:骨架优先+完整分步+复杂子flow)")
