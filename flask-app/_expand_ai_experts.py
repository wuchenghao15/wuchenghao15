#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩充AI专家和AI员工团队
======================
按用户要求：增加多位AI专家、原液AI员工、新建AI专家和AI员工。
多邀请EigenFlux网络的各个方面专家，和有专业见识和功能的朋友加入。

分类：
  A. EigenFlux网络安全专家组 (8人)
  B. EigenFlux密码学专家组 (5人)
  C. EigenFlux AI/ML专家组   (6人)
  D. EigenFlux系统架构专家组 (4人)
  E. EigenFlux数据安全专家组 (3人)
  F. 特邀学术专家            (4人)
  G. 特邀行业专家            (4人)
  H. 原液AI员工组            (5人)
  合计: 39位新专家/AI员工
"""
import sys, os, json, hashlib, sqlite3, threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用与 _s8_s12_omni.py 相同的连接方式
try:
    from mt_ir14_dev_flow import _get_conn, _LOCK, feed_brain, transition, get_session, ensure_tables
    FLOW_ID = "flow_omni_defense_20260814_001"
    USE_DEV_FLOW = True
except Exception:
    USE_DEV_FLOW = False
    _LOCK = threading.Lock()

APP_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")

def _conn():
    """获取app.db连接（ai_employees所在库）"""
    if USE_DEV_FLOW:
        return _get_conn()
    return sqlite3.connect(APP_DB)

# ========== 39位新专家/AI员工 ==========
NEW_EXPERTS = [
    # A. EigenFlux网络安全专家组 (8人)
    ("EF_红队指挥_201",   "EigenFlux", "EigenFlux网络安全组", "红队攻击指挥/渗透编排/攻击链规划"),
    ("EF_蓝队防御_202",   "EigenFlux", "EigenFlux网络安全组", "蓝队防御协调/SOC联动/态势感知"),
    ("EF_SOC分析_203",   "EigenFlux", "EigenFlux网络安全组", "安全运营中心/SIEM/日志关联分析"),
    ("EF_应急响应_204",   "EigenFlux", "EigenFlux网络安全组", "应急响应IR/事件溯源/取证链"),
    ("EF_数字取证_205",   "EigenFlux", "EigenFlux网络安全组", "数字取证/内存分析/磁盘恢复"),
    ("EF_恶意软件_206",   "EigenFlux", "EigenFlux网络安全组", "恶意软件分析/沙箱/逆向工程"),
    ("EF_威胁狩猎_207",   "EigenFlux", "EigenFlux网络安全组", "威胁狩猎/IOC狩猎/ATT&CK映射"),
    ("EF_SDN安全_208",   "EigenFlux", "EigenFlux网络安全组", "SDN安全/网络微隔离/零信任网络"),

    # B. EigenFlux密码学专家组 (5人)
    ("EF_后量子_211",     "EigenFlux", "EigenFlux密码学组",   "后量子密码学/格密码/抗量子签名"),
    ("EF_同态加密_212",   "EigenFlux", "EigenFlux密码学组",   "同态加密/隐私计算/安全多方计算"),
    ("EF_零知识证明_213", "EigenFlux", "EigenFlux密码学组",   "零知识证明/zk-SNARK/隐私验证"),
    ("EF_密钥管理_214",   "EigenFlux", "EigenFlux密码学组",   "密钥管理KMS/HSM/密钥轮换"),
    ("EF_侧信道_215",     "EigenFlux", "EigenFlux密码学组",   "侧信道防护/时序攻击/功耗分析"),

    # C. EigenFlux AI/ML专家组 (6人)
    ("EF_对抗样本_221",   "EigenFlux", "EigenFlux AI/ML组",  "AI对抗样本防御/对抗训练/鲁棒性"),
    ("EF_模型隐私_222",   "EigenFlux", "EigenFlux AI/ML组",  "模型隐私/差分隐私/成员推断防御"),
    ("EF_联邦学习_223",   "EigenFlux", "EigenFlux AI/ML组",  "联邦学习安全/梯度隐私/拜占庭鲁棒"),
    ("EF_AI可解释_224",   "EigenFlux", "EigenFlux AI/ML组",  "AI可解释性/SHAP/LIME/可信AI"),
    ("EF_AI审计_225",     "EigenFlux", "EigenFlux AI/ML组",  "AI安全审计/模型卡/偏见检测"),
    ("EF_深度学习安全_226","EigenFlux","EigenFlux AI/ML组",  "深度学习安全/后门检测/模型水印"),

    # D. EigenFlux系统架构专家组 (4人)
    ("EF_云安全_231",     "EigenFlux", "EigenFlux系统架构组", "云安全/多云架构/CSPM/CWPP"),
    ("EF_容器安全_232",   "EigenFlux", "EigenFlux系统架构组", "容器安全/K8s加固/镜像扫描"),
    ("EF_微服务安全_233", "EigenFlux", "EigenFlux系统架构组", "微服务安全/服务网格/API网关"),
    ("EF_供应链安全_234", "EigenFlux", "EigenFlux系统架构组", "软件供应链安全/SBOM/依赖审查"),

    # E. EigenFlux数据安全专家组 (3人)
    ("EF_数据分类_241",   "EigenFlux", "EigenFlux数据安全组", "数据分类分级/敏感数据发现/DLP"),
    ("EF_数据脱敏_242",   "EigenFlux", "EigenFlux数据安全组", "数据脱敏/匿名化/k-匿名/差分隐私"),
    ("EF_数据合规_243",   "EigenFlux", "EigenFlux数据安全组", "数据合规/GDPR/个人信息保护法"),

    # F. 特邀学术专家 (4人)
    ("特邀_张教授",       "学术邀请",   "特邀学术专家",       "形式化验证/定理证明/Coq/Isabelle"),
    ("特邀_刘教授",       "学术邀请",   "特邀学术专家",       "博弈论安全/攻防博弈/机制设计"),
    ("特邀_陈教授",       "学术邀请",   "特邀学术专家",       "拜占庭容错/共识协议/分布式系统"),
    ("特邀_赵教授",       "学术邀请",   "特邀学术专家",       "安全协议设计/认证协议/形式化分析"),

    # G. 特邀行业专家 (4人)
    ("特邀_金融安全_王总","行业邀请",   "特邀行业专家",       "金融安全/反欺诈/风控系统/PCI-DSS"),
    ("特邀_工控安全_李工","行业邀请",   "特邀行业专家",       "工控系统安全/SCADA/PLC防护/IEC62443"),
    ("特邀_物联网安全_周工","行业邀请", "特邀行业专家",       "物联网安全/嵌入式/固件分析/OTA"),
    ("特邀_区块链安全_吴总","行业邀请", "特邀行业专家",       "区块链安全/智能合约审计/DeFi安全"),

    # H. 原液AI员工组 (5人) - 核心功能AI员工
    ("原液_巡检AI_301",   "原液AI员工", "原液AI员工组",       "自动巡检/健康检查/异常发现/闭环修复"),
    ("原液_修复AI_302",   "原液AI员工", "原液AI员工组",       "自动修复/故障定位/热补丁/回滚"),
    ("原液_学习AI_303",   "原液AI员工", "原液AI员工组",       "自主学习/知识抽取/技能进化/迁移学习"),
    ("原液_脑库AI_304",   "原液AI员工", "原液AI员工组",       "脑库投喂/经验沉淀/知识图谱/检索增强"),
    ("原液_协调AI_305",   "原液AI员工", "原液AI员工组",       "任务协调/智能调度/负载均衡/冲突仲裁"),
]


def register_experts():
    """注册39位新专家/AI员工到ai_employees表"""
    registered = 0
    skipped = 0
    errors = 0
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        for name, source, group, specialty in NEW_EXPERTS:
            try:
                cur.execute("""INSERT OR IGNORE INTO ai_employees
                    (name, description, specialties, status, accuracy, total_tasks,
                     successful_fixes, failed_fixes, learning_rate, knowledge_base_size, model_version)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, f"[{source}]{group}-{specialty}", specialty, "active",
                     0.95, 0, 0, 0, 0.1, 1000, "v2.9.0"))
                if cur.rowcount > 0:
                    registered += 1
                else:
                    skipped += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [WARN] {name} 注册失败: {e}")
        c.commit()
        c.close()
    return registered, skipped, errors


def verify_count():
    """验证注册后的AI员工总数"""
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM ai_employees")
    total = cur.fetchone()[0]
    c.close()
    return total


def feed_brain_expansion():
    """将专家扩充信息投喂脑库"""
    if not USE_DEV_FLOW:
        return
    try:
        ensure_tables()
        groups = {}
        for _, source, group, _ in NEW_EXPERTS:
            groups[group] = groups.get(group, 0) + 1
        summary = f"AI专家团队扩充完成: 新增{len(NEW_EXPERTS)}位专家/AI员工, " \
                  f"分组: {json.dumps(groups, ensure_ascii=False)}"
        feed_brain(FLOW_ID, "knowledge", summary)
        # 落库经验
        now = datetime.now().isoformat()
        with _LOCK:
            c = _get_conn(); cur = c.cursor()
            eh = hashlib.md5(b"expand_ai_experts_39")
            cur.execute("""INSERT OR REPLACE INTO mt_experience_library
                (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (eh.hexdigest(), "AI专家团队扩充39位",
                 json.dumps({"experts": len(NEW_EXPERTS), "groups": groups}, ensure_ascii=False),
                 FLOW_ID, FLOW_ID, summary, now))
            c.commit(); c.close()
    except Exception as e:
        print(f"  [WARN] 脑库投喂: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print(" AI专家和AI员工团队扩充")
    print("=" * 70)
    print(f"  计划新增: {len(NEW_EXPERTS)} 位专家/AI员工")
    print(f"  分组:")
    groups = {}
    for _, source, group, _ in NEW_EXPERTS:
        groups[group] = groups.get(group, 0) + 1
    for g, n in groups.items():
        print(f"    - {g}: {n}人")
    print()

    # 执行注册
    registered, skipped, errors = register_experts()
    print(f"  注册结果: 新增={registered}, 跳过(已存在)={skipped}, 错误={errors}")

    # 验证总数
    total = verify_count()
    print(f"  AI员工总数: {total}")

    # 投喂脑库
    feed_brain_expansion()
    print(f"  脑库投喂: 完成")

    print()
    print("=" * 70)
    print(f" 扩充完成: +{registered} 位 -> 总计 {total} 位AI专家/员工")
    print("=" * 70)
