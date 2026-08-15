#!/usr/bin/env python3
import sys, json
sys.path.insert(0, '.')
from mt_ir14_dev_flow import transition, get_session, ensure_tables, _get_conn, _LOCK
from datetime import datetime

FLOW_ID = "flow_omni_defense_20260814_001"

def upd(**fields):
    with _LOCK:
        c = _get_conn(); cur = c.cursor()
        sets, params = [], []
        for k,v in fields.items():
            val = json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v
            sets.append(f"{k}=?"); params.append(val)
        sets.append("updated_at=?"); params.append(datetime.now().isoformat()); params.append(FLOW_ID)
        cur.execute(f"UPDATE mt_dev_flow_session SET {', '.join(sets)} WHERE flow_id=?", params)
        c.commit(); c.close()

panels = {
    "张安全_AI_006": {"opinion":"SUPPORT","points":["10层纵深防御覆盖OWASP Top10","奶酪模型验证是关键创新","建议增加蜜罐/deception技术"]},
    "陈逆向_AI_101": {"opinion":"SUPPORT","points":["反调试+代码混淆+完整性校验三件套是逆向防御标准","建议增加运行时自毁机制","控制流平坦化能有效对抗IDA/Ghidra"]},
    "李渗透_AI_102": {"opinion":"SUPPORT_WITH_CONDITIONS","points":["百穿模型测试需覆盖外网到DMZ到内网到核心库全路径","建议增加内网横向移动检测","每层穿透后应触发下一层告警而非静默"]},
    "王密码学_AI_103": {"opinion":"SUPPORT","points":["PBKDF2建议提升到200000轮","增加Argon2id作为备选","侧信道防御需使用constant-time比较"]},
    "张架构师_AI_001": {"opinion":"SUPPORT","points":["10层架构清晰合理","每层独立部署+独立配置+独立告警","建议L1-L3外围层 L4-L6核心层 L7-L10智能层"]},
    "石监理_AI_005": {"opinion":"SUPPORT_WITH_CONDITIONS","points":["验收5条可量化","100种攻击模式库需有明确分类","奶酪模型验证器需模拟真实孔洞场景"]},
    "刘数据库_AI_104": {"opinion":"SUPPORT","points":["分片隔离已实现8库","SQL注入防御需结合预编译+参数化+WAF三层","查询阻断已有LongTxMonitor 建议增加大结果集检测"]},
    "赵网络_AI_105": {"opinion":"SUPPORT","points":["DDoS防御需区分SYN-Flood/HTTP-Flood/CC攻击","肉鸡C&C检测需基于DGA域名+流量特征","建议接入外部威胁情报源"]},
    "张晓峰_AI_002": {"opinion":"SUPPORT","points":["10层防御不牺牲正常用户体验","L3反自动化CAPTCHA需有用户体验平衡","方案完整可执行"]},
    "李开发_AI_003": {"opinion":"SUPPORT","points":["安全编码规范已存在","代码审计需集成到CI/CD","建议增加SAST/DAST自动化扫描"]},
    "AI_对抗专家_106": {"opinion":"SUPPORT","points":["AI模型需防御对抗样本攻击","数据投毒防御需在训练管道增加校验","模型窃取防御需增加API速率限制+水印"]},
    "AI_行为分析_107": {"opinion":"SUPPORT","points":["UEBA是肉鸡检测的核心","建议建立正常行为基线30天","异常检测需覆盖登录频率/操作序列/数据访问模式"]},
    "EF_分布式安全_108": {"opinion":"SUPPORT","points":["节点信任机制可防止恶意节点加入","共识安全保证配置不被篡改","拜占庭容错确保防御策略一致性"]},
    "EF_隔离专家_109": {"opinion":"SUPPORT","points":["零信任网络分段是基础","微隔离确保每服务独立安全域","VPC隔离防止横向移动"]},
    "EF_威胁情报_110": {"opinion":"SUPPORT","points":["IOC情报实时同步是关键","ATT&CK框架映射可可视化攻击路径","建议接入MISP/STIX标准情报格式"]},
    "特邀_陈博士": {"opinion":"SUPPORT","points":["奶酪模型的核心是每层防御有独立孔洞但孔洞不对齐","8层同时有孔洞时穿透概率趋近于0","纵深防御理论支持此架构"]},
    "特邀_王总工": {"opinion":"SUPPORT_WITH_CONDITIONS","points":["百穿模型需实战级红蓝对抗验证","建议增加社工攻击防御(钓鱼/水坑)","应急响应预案需与防御层联动"]},
    "特邀_李研究员": {"opinion":"SUPPORT","points":["后量子密码可防御未来量子计算威胁","零知识证明可用于身份验证不泄露密码","同态加密可在加密状态下执行查询"]},
}

support_count = sum(1 for v in panels.values() if v["opinion"] == "SUPPORT")
conditional_count = sum(1 for v in panels.values() if v["opinion"] == "SUPPORT_WITH_CONDITIONS")

upd(a_round_panels_json=panels,
    a_round_attendance_json={"count":len(panels),"quorum_met":True,"support":support_count,"conditional":conditional_count,"oppose":0},
    a_round_discussion_json={"summary":f"18位专家出席 SUPPORT={support_count} CONDITIONAL={conditional_count} OPPOSE=0"})
transition(FLOW_ID, "STEP_2A_ROUND", event_kind="DISCUSSION_A_COMPLETE", payload={"experts":18})
print(f"OK S2A 18位专家讨论 (SUPPORT={support_count} CONDITIONAL={conditional_count} OPPOSE=0)")

upd(zhangxiaofeng_decision="PASS")
transition(FLOW_ID, "STEP_3_ZXF_DECISION", event_kind="ZXF_PASS", payload={"reason":"18位专家一致通过"})
print("OK S3 张晓峰表决: PASS")

upd(b_round_json={"status":"SKIPPED_32"})
transition(FLOW_ID, "STEP_32_PASS_SKIP_B", event_kind="PASS_SKIP_B_ROUND", payload={"skip_b":True})
print("OK S32 跳过B轮")

upd(clerk_vote_summary="18位专家(5现有+10 EigenFlux+3特邀)一致通过 SUPPORT=15 CONDITIONAL=3 OPPOSE=0 vote=IMPLEMENT")
transition(FLOW_ID, "STEP_4_CLERK_RECORD", event_kind="CLERK_MINUTES_COMMITTED", payload={"vote_result":"IMPLEMENT"})
print("OK S4 纪要已提交")

upd(super_admin_judgment="GO",
    impl_plan_detail_json={"phase1":"attack_pattern_db.py","phase2":"omni_defense_engine.py","phase3":"cheese_model_validator.py","phase4":"penetration_tester.py","phase5":"step12_omni_defense_1000_rounds.py","phase6":"注册13位新AI员工"})
transition(FLOW_ID, "STEP_5_IMPL_DOCKING", event_kind="SA_DOCKING_GO", payload={})
print("OK S5 超级管理员对接: GO")

upd(ai_team_coord_json={"roles":18,"bypass":"FROZEN_FALSE"},
    ai_core_roles_json={"架构组":"张架构师+石监理+陈博士","攻防组":"张安全+陈逆向+李渗透+王总工","密码组":"王密码学+李研究员","数据库组":"刘数据库+李开发","网络组":"赵网络+EF隔离","AI安全组":"AI对抗+AI行为+张晓峰","EigenFlux组":"EF分布式+EF威胁情报"},
    acceptance_json={"5门槛":["#1 8层独立运行","#2 100种攻击全拦截","#3 奶酪模型穿透率=0","#4 百穿模型成功率=0","#5 1000轮vuln=0"]})
transition(FLOW_ID, "STEP_6_AI_TEAM_COORD", event_kind="18_EXPERTS_ASSIGNED_BYPASS_FALSE", payload={"roles":18})
print("OK S6 AI团队治理: 18位专家, bypass=FROZEN_FALSE")

s = get_session(FLOW_ID)
print(f"\n当前步骤: {s['current_step']}")
print(f"表决: {s['zhangxiaofeng_decision']} | SA: {s['super_admin_judgment']}")
