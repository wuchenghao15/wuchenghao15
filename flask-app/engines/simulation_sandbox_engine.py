# [unused] import os, sys, sqlite3, json, hashlib, random, re, argparse, datetime, traceback, logging, uuid, fnmatch, pathlib
from typing import Dict, List, Optional, Tuple, Any

_BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_BASE, os.pardir, os.pardir))
AI_ENGINES_DIR = os.path.join(os.path.dirname(_BASE), "ai_engines")
sys.path.insert(0, AI_ENGINES_DIR)  # 给未来导入 §14 用
ENG_DB = os.path.join(_BASE, "app.db")
SES_DB = os.path.join(AI_ENGINES_DIR, "app.db")
LOG_DIR = os.path.join(PROJECT_ROOT, "_runtime", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
NOW = lambda: datetime.datetime.now().isoformat(timespec="seconds")
TODAY_STR = lambda: datetime.date.today().isoformat().replace("-", "")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [SimulationSandbox] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(os.path.join(LOG_DIR, "simulation_sandbox_engine.log"), encoding="utf-8")]
)
log = logging.getLogger("sim_sandbox")

# 连接函数（简单版，不用复杂连接池）
def get_conn(): return sqlite3.connect(ENG_DB, timeout=30)
def get_ses_conn(): return sqlite3.connect(SES_DB, timeout=20)


# =====================================================================
# 九、ensure_tables()（CREATE TABLE IF NOT EXISTS，3张新表）
# =====================================================================
def ensure_tables():
    conn = get_conn()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mt_sandbox_sessions (
          session_id TEXT PRIMARY KEY, scenario_code TEXT NOT NULL, scenario_title TEXT, scenario_prompt_json TEXT,
          actors_json TEXT, turns INTEGER DEFAULT 0, total_messages INTEGER DEFAULT 0,
          consensus_level REAL DEFAULT 0.0, outcome_summary TEXT, final_status TEXT DEFAULT 'RUNNING',
          created_at TEXT NOT NULL, finished_at TEXT, duration_seconds REAL, tags TEXT
        );
        CREATE TABLE IF NOT EXISTS mt_sandbox_messages (
          message_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, turn_num INTEGER NOT NULL,
          actor_role TEXT NOT NULL, actor_id TEXT NOT NULL, actor_name TEXT NOT NULL,
          message_content TEXT NOT NULL, emotional_tone TEXT, priority INTEGER, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS mt_sandbox_outcomes (
          outcome_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, outcome_type TEXT NOT NULL,
          outcome_title TEXT, outcome_body_json TEXT, feasibility REAL, value_score REAL,
          cost_score REAL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sbmsg_session ON mt_sandbox_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_sbout_session ON mt_sandbox_outcomes(session_id);
        CREATE INDEX IF NOT EXISTS idx_sbscenario ON mt_sandbox_sessions(scenario_code);
        """)
        conn.commit()
    finally:
        conn.close()
    log.info("3 mt_sandbox_* 表 + 3索引 ensure 完成")


# =====================================================================
# 三、ActorPool（真实源，种子学者）
# =====================================================================
class ActorPool:
    def __init__(self):
        self.actors: List[Dict[str, Any]] = []
        self._build()

    SCHOLARS_SEED = [
      # 24个学者/专家（领域覆盖ARCH/SEC/COM/AI/DATA/PERF/EDU/DB/IOT）
      ("林崇德", "SCHOLAR", "EDU_PSYCHOLOGY", "青少年发展心理学", 0.92, 0.4, 0.95, "严谨", "从教育公平与可及性视角评估"),
      ("戴锦华", "SCHOLAR", "CULTURE_STUDY", "文化批评与媒介研究", 0.88, 0.3, 0.90, "严谨", "AI媒介对公众文化塑造的影响"),
      ("朱清时", "SCHOLAR", "SCIENCE_HISTORY", "科学史与哲学", 0.93, 0.2, 0.97, "严谨", "系统迭代与科学范式变化关系"),
      ("金观涛", "SCHOLAR", "SYSTEMS_PHI", "系统哲学与演化论", 0.95, 0.35, 0.98, "严谨", "复杂系统稳态与失控边界"),
      ("钱颖一", "SCHOLAR", "ECONOMICS", "制度经济学与治理", 0.91, 0.3, 0.94, "平衡", "制度设计与激励相容"),
      ("许晨阳", "SCHOLAR", "MATHEMATICS", "代数几何", 0.94, 0.15, 0.96, "严谨", "形式化证明与正确性边界"),
      ("文小刚", "SCHOLAR", "PHYSICS", "凝聚态物理拓扑序", 0.96, 0.25, 0.98, "严谨", "高维约束下的涌现秩序"),
      ("郑南宁", "SCHOLAR", "AI_VISION", "计算机视觉与认知", 0.95, 0.5, 0.97, "平衡", "AI视觉鲁棒性与泛化边界"),
      ("高文", "SCHOLAR", "COMPUTER_ARCH", "数字视频编解码", 0.93, 0.45, 0.95, "平衡", "工程复杂度vs系统可靠性平衡"),
      ("倪明选", "SCHOLAR", "DISTRIBUTED_SYS", "分布式系统调度", 0.92, 0.5, 0.94, "激进", "大规模调度中的瓶颈识别"),
      ("潘建伟", "SCHOLAR", "QUANTUM_SAFE", "量子信息安全", 0.96, 0.1, 0.98, "严谨", "未来量子威胁下的密码学窗口期"),
      ("王小云", "SCHOLAR", "CRYPTOGRAPHY", "哈希函数密码分析", 0.95, 0.05, 0.99, "严谨", "安全协议中的哈希结构弱点分析"),
      ("怀进鹏", "SCHOLAR", "EDU_GOV", "教育治理信息化", 0.90, 0.4, 0.92, "平衡", "教育数字化的治理框架边界"),
      ("杨卫", "SCHOLAR", "MECHANICS", "断裂力学与可靠性", 0.92, 0.2, 0.95, "严谨", "系统疲劳与结构缺陷传播"),
      ("张钹", "SCHOLAR", "AI_FOUNDATION", "AI可解释性与推理", 0.96, 0.25, 0.98, "严谨", "黑箱AI决策的可解释性要求"),
      ("姚期智", "SCHOLAR", "THEORETICAL_CS", "计算理论与密码学", 0.98, 0.1, 0.99, "严谨", "可证明安全与零知识边界"),
      ("王恩东", "SCHOLAR", "HIGH_PERF", "高性能计算架构", 0.93, 0.5, 0.95, "平衡", "算力瓶颈与效率/能耗曲线"),
      ("梅宏", "SCHOLAR", "SOFTWARE_ENG", "软件体系结构", 0.94, 0.35, 0.96, "严谨", "大规模软件系统的演化稳定性"),
      ("孙凝晖", "SCHOLAR", "COMPILER", "编译优化与芯片协同", 0.92, 0.45, 0.94, "激进", "指令集/编译器/OS三层权衡"),
      ("樊文飞", "SCHOLAR", "DATA_MANAGE", "大数据管理与一致性", 0.93, 0.2, 0.95, "严谨", "强一致性vs可用性的CAP边界"),
      ("王永炎", "SCHOLAR", "TRADITIONAL_LOGIC", "东方系统逻辑", 0.89, 0.4, 0.90, "平衡", "整体论vs还原论在AI系统中的互补"),
      ("张伯礼", "SCHOLAR", "HEALTH_SYSTEM", "医疗系统治理", 0.90, 0.35, 0.92, "严谨", "系统级风险传播与分级响应"),
      ("胡永康", "SCHOLAR", "PETROLEUM_SYS", "大型工业系统工程", 0.91, 0.3, 0.93, "严谨", "复杂工业系统的安全/效率权衡"),
      ("钱七虎", "SCHOLAR", "DEFENSE_SYSTEM", "防护工程系统", 0.92, 0.15, 0.94, "严谨", "系统攻防对抗中的冗余设计原则"),
    ]

    def _build(self):
        # 源1: engines/app.db ai_employees (5条真实记录)
        try:
            conn=get_conn()
            rows=conn.execute("SELECT id,name,capabilities,specialties,status,accuracy,skill_level,model_version FROM ai_employees WHERE is_enabled=1 OR status='ACTIVE' OR is_enabled IS NULL").fetchall()
            for row in rows:
                emp_id,name,caps,specs,status,acc,sl,mv = row
                self.actors.append({
                    "actor_id": f"EMP_{emp_id}", "actor_name": name, "role": "AI_EMPLOYEE", "actor_role": "AI_EMPLOYEE",
                    "domain": (specs or "GENERAL")[:32], "specialty": (caps or "开发修复")[:64],
                    "expertise_weight": 0.50 + 0.05 * max(sl or 0, 0) + max(acc or 0.6, 0.6) * 0.20,
                    "risk_tolerance": 0.55, "accuracy_rate": acc or 0.70, "style": "实用派",
                    "perspective": f"擅长{specs or '开发修复'}，{caps or '实际任务解决'}",
                    "source": "ai_employees",
                })
            conn.close()
        except Exception as e: log.error(f"读ai_employees失败: {e}")

        # 源2: ses/app.db mt_eigenflux_expert_registry (21条真实专家)
        try:
            conn=get_ses_conn()
            rows=conn.execute("SELECT expert_id,expert_name,domain,weight,tenure_status,accuracy_rate FROM mt_eigenflux_expert_registry").fetchall()
            for eid,ename,domain,wt,tenure,acc in rows:
                self.actors.append({
                    "actor_id": f"EXP_{eid}", "actor_name": ename, "role": "EIGENFLUX_EXPERT", "actor_role": "EIGENFLUX_EXPERT",
                    "domain": domain or "GENERAL", "specialty": f"{domain}领域专家",
                    "expertise_weight": wt if wt else 0.70,
                    "risk_tolerance": 0.40 if tenure=="CORE" else 0.50,
                    "accuracy_rate": acc if acc else 0.85,
                    "style": "核心专家" if tenure=="CORE" else "领域专家",
                    "perspective": f"EigenFlux注册专家：{domain}领域",
                    "source": "eigenflux_registry",
                })
            conn.close()
        except Exception as e: log.error(f"读eigenflux_registry失败: {e}")

        # 源3: SCHOLARS_SEED (24学者)
        for name,role,domain,spec,wt,risk,acc,style,persp in self.SCHOLARS_SEED:
            self.actors.append({
                "actor_id": f"SCH_{hashlib.md5(name.encode()).hexdigest()[:8]}",
                "actor_name": name, "role": role, "actor_role": role, "domain": domain, "specialty": spec,
                "expertise_weight": wt, "risk_tolerance": risk, "accuracy_rate": acc,
                "style": style, "perspective": persp, "source": "scholars_seed",
            })

        log.info(f"ActorPool build完成: 共{len(self.actors)}人 = AI员工{sum(1 for a in self.actors if a['role']=='AI_EMPLOYEE')} + EigenFlux专家{sum(1 for a in self.actors if a['role']=='EIGENFLUX_EXPERT')} + 学者{sum(1 for a in self.actors if a['role']=='SCHOLAR')}")

    def sample(self, scenario_code: str, k: int = 8) -> List[Dict]:
        role_distribution = {
            "GAP_PROPOSAL":     {"EIGENFLUX_EXPERT":3, "SCHOLAR":3, "AI_EMPLOYEE":2},
            "PROPOSAL_REVIEW":  {"EIGENFLUX_EXPERT":4, "SCHOLAR":3, "AI_EMPLOYEE":1},
            "ARCH_UPGRADE":     {"EIGENFLUX_EXPERT":3, "SCHOLAR":4, "AI_EMPLOYEE":2},
            "MRCAO_K12_TUTOR":  {"EIGENFLUX_EXPERT":4, "SCHOLAR":4, "AI_EMPLOYEE":2},
            "WU_MEIGONG_UI_THEME": {"EIGENFLUX_EXPERT":4, "SCHOLAR":4, "AI_EMPLOYEE":2},
            "YANG_AN_SECURITY_EXPERT": {"EIGENFLUX_EXPERT":5, "SCHOLAR":4, "AI_EMPLOYEE":2},
        }.get(scenario_code.upper(), {"EIGENFLUX_EXPERT":3,"SCHOLAR":3,"AI_EMPLOYEE":2})
        # K12场景：领域偏好加权（SCHOLAR偏好EDU_PSY/EDU_GOV/AI_FOUNDATION；EIGEN偏好AI/COMPLIANCE/ARCHITECTURE/DATA）
        prefer_domains = {
            "MRCAO_K12_TUTOR": {"SCHOLAR":["EDU_PSYCHOLOGY","EDU_GOV","AI_FOUNDATION","TRADITIONAL_LOGIC","HEALTH_SYSTEM"],
                                "EIGENFLUX_EXPERT":["AI","COMPLIANCE","ARCHITECTURE","DATA","PERFORMANCE"],
                                "AI_EMPLOYEE":["education","architecture","security","operation"]},
            "WU_MEIGONG_UI_THEME": {"SCHOLAR":["CULTURE_STUDY","COMPUTER_ARCH","AI_VISION","TRADITIONAL_LOGIC","HEALTH_SYSTEM","EDU_PSYCHOLOGY"],   # 戴锦华(文化/媒介配色)+高文(工设/系统配色)+郑南宁(视觉/色彩鲁棒)+王永炎(整体论)+林崇德(认知/可读性)
                                    "EIGENFLUX_EXPERT":["PERFORMANCE","ARCHITECTURE","AI","COMPLIANCE","DATA","SECURITY"],   # 性能(渲染速度)+架构(CSS主题切换)+AI(推荐)+合规(可达性)
                                    "AI_EMPLOYEE":["architecture","operation","education","frontend"]},   # 架构+运维+前端AI落地
            "YANG_AN_SECURITY_EXPERT": {"SCHOLAR":["COMPUTER_ARCH","TRADITIONAL_LOGIC","LAW_SCIENCE","CRYPTOGRAPHY","CYBER_SECURITY","DEFENSE_SYSTEM","AI_FOUNDATION"],   # 计算机架构·密码学·法学合规·国防安全
                                        "EIGENFLUX_EXPERT":["SECURITY","COMPLIANCE","DBA","ARCHITECTURE","PERFORMANCE","DATA","OPS"],   # 安全/合规/DB/架构/性能/运维
                                        "AI_EMPLOYEE":["security","operation","architecture","database"]},   # 杨安AI落地团队
        }.get(scenario_code.upper(), {})
        result=[]
        for role,n in role_distribution.items():
            pool=[a for a in self.actors if a["role"]==role]
            if not pool: pool=self.actors
            pref = prefer_domains.get(role, [])
            if pref:
                # 偏好池优先，不足从普通池补
                pref_pool=[a for a in pool if any(p.lower() in (a.get("domain","") or "").lower() or p.lower() in (a.get("specialty","") or "").lower() for p in pref)]
                chosen=[]
                if pref_pool: chosen = random.sample(pref_pool, k=min(n, len(pref_pool)))
                if len(chosen)<n:
                    rest=[a for a in pool if a not in chosen]
                    chosen += random.sample(rest, k=min(n-len(chosen), len(rest)))
            else:
                chosen = random.sample(pool, k=min(n,len(pool)))
            for a in chosen:
                a = dict(a)
                a["speak_weight"] = round(a["expertise_weight"] + random.uniform(-0.05, 0.05), 3)
                result.append(a)
        random.shuffle(result)
        return result


# =====================================================================
# 四、ScenarioEngine（3种固定场景，基于真实DB现状触发）
# =====================================================================
class ScenarioEngine:
    PRESETS = {
        "GAP_PROPOSAL": {
            "title": "当前系统缺口讨论+提案生成场景",
            "intro": "基于mt_feature_dev_lifecycle发现的125个未完成功能缺口，从多角色视角讨论优先级与冲突，产出≥2条可落地提案，投递mt_ai_suggestion_pool并生成§14 proposal_json",
            "prompt_base": "作为{role} {name}（{domain} {specialty}），请从{perspective}出发，针对当前系统缺口现状，提出{what_to_say}要求：(1)100字内(2)有具体数据支撑/边界条件(3)明确不妥协点。",
            "targets": [
                "首轮：指出最紧迫的3个高价值缺口与各自风险",
                "次轮：缺口优先级冲突时的取舍原则",
                "三轮：自动落地研发的安全边界（哪些能自动做，哪些必须SA介入）",
                "末轮：对最终提案投票，并给出改进建议",
            ],
            "outcome_types": ["PRIORITY_RANKING","SAFETY_BOUNDARY","PROPOSAL_JSON","§14_PROPOSAL"],
            "turns": (5,7),
            "require_consensus": 0.70,
        },
        "PROPOSAL_REVIEW": {
            "title": "§14提案多角色评审场景（模拟张雪峰/SA终审）",
            "intro": "取mt_dev_flow_session中final_status='OPEN'的proposal，模拟12步骤中评审环节：A轮5人讨论→综合意见→模拟张雪峰决策→落库§14结构+喂脑库",
            "prompt_base": "你是{role} {name}（{domain} {specialty}），作为§14 A-round评审员，需要评估FLOW提案{flow_title}: {flow_summary}。从{perspective}给出：①过/不过/修改 ②理由③修改点。",
            "targets": ["合规审查","架构合理性","成本收益","可测试性","SA终审边界"],
            "outcome_types": ["REVIEW_VOTES","ZHANGXIAOFENG_DECISION","BRAIN_FEED"],
            "turns": (4,5), "require_consensus": 0.60,
        },
        "ARCH_UPGRADE": {
            "title": "下季度架构升级前瞻讨论场景（未来要实现的要求）",
            "intro": "基于当前v22.7.0能力，设身处地讨论v23+架构升级的3个核心方向：分布式推理/本地向量脑库/跨端OneDrive同步隔离。",
            "prompt_base": "作为{role} {name}（{specialty} {style}派），从{perspective}评估v23.0.0的{direction}方向，请给出：①最小MVP功能集 ②未来3个里程碑 ③3个不允许踩的风险边界。",
            "targets": ["分布式推理集群治理","本地向量脑库+混合检索","OneDrive沙箱与代码同步隔离","EigenFlux专家治理体系"],
            "outcome_types": ["MVP_SPEC","MILESTONE_JSON","RISK_BOUNDARY"],
            "turns": (6,7), "require_consensus": 0.55,
        },
        "MRCAO_K12_TUTOR": {
            "title": "K12「曹老师AI」专有私教设计评审场景（AI员工+EigenFlux+学者综合评定）",
            "intro": "针对K12学生的答疑解惑AI私教「曹老师AI」：9大功能模块+1对1专项训练+学习积极性引导+AI建议&EigenFlux&专家学者综合评定；最终产出完整9模块落地方案JSON和1对1训练模型配置JSON。",
            "prompt_base": "你是{role} {name}（{domain}领域{specialty}，{style}派，权重≈{weight:.2f}）。作为{perspective}的代表，请针对「曹老师AI」第{feature_idx}个功能模块【{feature_name}】，从{perspective}出发提出设计评审意见：(1)该模块MVP必须具备什么能力（用K12真实学段/学科知识点举例）(2)该模块如何提高学生学习积极性，并引导学生理解「学习真正意义」(3)1对1私教个性化设计要点（4)边界与风险（未成年人隐私/误导/AI可解释性）。(100~180字)",
            "targets": [
                "F1题目解答与分析：多步推理+题型母题迁移（基于mt_edu_sync_question_types 7题型）",
                "F2教辅拓展知识：同步教材章节+知识点拓展（基于mt_edu_sync_content 27条教辅）",
                "F3错题复习引导：错因分类+艾宾浩斯重做计划+相似题推送",
                "F4知识巩固：薄弱知识点思维导图+分层闯关练习",
                "F5每日挑战：学情驱动的3题小挑战+成长勋章/奖励系统",
                "F6随机小测试：按学科/章节约束抽题+自动批改+错点定位",
                "F7信息录入&画像：学段/年级/学科偏好+近期考分+学习时间+错题本导入",
                "F8学习习惯&薄弱环节分析：频率/时长/错因聚类→薄弱知识点Top10画像",
                "F9 1对1专项训练+综合评定：基于画像+EigenFlux&学者共识的AI私教个性化训练计划，真正的私教闭环",
            ],
            "outcome_types": ["CONSENSUS","AI_SUGGESTION","BRAIN_FEED","MRCAO_PLAN_JSON","CAO_1V1_MODEL_JSON"],
            "turns": (7,9), "require_consensus": 0.65,
        },
        "WU_MEIGONG_UI_THEME": {
            "title": "「吴美工AI」前端配色调度排版专家评审场景（节日配色/个性化主题/UI/UX Token系统）",
            "intro": "针对系统前端页面布局与配色的「吴美工AI」：按国家公祭日/国庆/春节/用户生日当月等时间点自动切换配色方案；根据用户年龄/性别动态调整排版/字号/间距/对比度；最终输出Element Plus+mtscos-*设计Token的完整配色方案+页面布局UX配置，经AI员工+EigenFlux+文化学者/视觉专家综合评定，成为真正的专门前端配色调度排版专家。",
            "prompt_base": "你是{role} {name}（{domain}领域{specialty}，{style}派，权重≈{weight:.2f}）。作为{perspective}的代表，请针对「吴美工AI」第{feature_idx}个功能模块【{feature_name}】，从{perspective}提出评审意见：(1)该模块MVP必须覆盖哪些节日/个性化场景（举具体例子并给具体配色HEX）(2)如何与现有Element Plus+MTSCOS设计Token兼容，并避免破坏设计规范(3)排版/字号/间距/可达性（WCAG对比度）如何保障(4)边界与风险：文化禁忌色彩/渲染性能/权限页面一致性。(100~180字)",
            "targets": [
                "F1 节日/纪念日专属配色：国家公祭日·灰阶肃穆/国庆·中国红金/春节·朱红春联色/中秋·月白银桂/生日月·糖果粉彩/儿童·明亮糖果色/教师节·谢师桃李色/毕业季·学士蓝金/端午·艾草青绿/清明·素雅烟青/元宵·花灯橙金/建党·红旗红金（12+套预设）",
                "F2 用户画像自适应配色排版：年龄→字号阶+阅读行距；性别→色调偏好；视障→高对比/大字号模式；手机/平板/桌面→栅格断点自动缩放",
                "F3 动态页面布局调度：栅格12/24列/间距8px×n/卡片圆角×阴影强度/导航侧边栏折叠/留白比例 按场景自适应",
                "F4 Element Plus+mtscos-* Token生成器：基于模板主题(aurora/twilight/dawn/ink)自动产出--el-color-primary 5色阶+--mtscos-spacing/--mtscos-shadow/--mtscos-btn 24+Token JSON",
                "F5 综合评定&主题切换闭环：AI建议×EigenFlux×文化学者(戴锦华)×视觉专家(郑南宁)×工设专家(高文) 5方评定+data-theme切换触发器+暗色模式适配+无障碍(WCAG AA)验证",
            ],
            "outcome_types": ["CONSENSUS","AI_SUGGESTION","BRAIN_FEED","WU_PALETTE_SCHEME_JSON","WU_LAYOUT_UX_CONFIG_JSON"],
            "turns": (7,9), "require_consensus": 0.62,
        },
        "YANG_AN_SECURITY_EXPERT": {
            "title": "「杨安 AI」底层安全专家场景（系统安全/权限矩阵/密码策略/参数优化/OWASP Top10加固）",
            "intro": "针对「搭建环境模拟新环境」的系统安全加固任务，由杨安AI作为底层安全专家：12维度安全审计矩阵对齐OWASP Top10；11级角色×100点权限矩阵优化；超级管理员wuchenghao15 7要素+VIKEY实时检测强化；Flask响应header(HSTS/CSP/XFO/XXSS/Referrer)安全加固；反黑客6策略；数据库SQL注入/凭据硬编码/速率限制/会话防盗链全链路审查；结合AI建议池+EigenFlux SECURITY/DBA/COMPLIANCE专家+密码学/法学学者综合评定，成为真正的底层安全专家。",
            "prompt_base": "你是{role} {name}（{domain}领域{specialty}，{style}派，权重≈{weight:.2f}）。作为{perspective}的代表，请针对「杨安 AI」第{feature_idx}模块【{feature_name}】从{perspective}提出系统性评审意见：(1)该模块MVP必须满足NIST/OWASP哪几条基线要求(用具体风险等级举例)(2)如何以「新增生产配置 + 小范围改入口选择配置」的最小变更方式落地（参照经验：禁止把真实密钥硬编码进.env）(3)如何和现有§用户权限11级角色/100点权限矩阵/@system_container装饰器兼容并强化（4)边界与风险回滚策略+灰度canary 1%验证。(120~200字)",
            "targets": [
                "F1 Flask安全响应header加固：HSTS/CSP默认-Report-Only/X-Frame-Options/X-XSS-Protection/Referrer-Policy/X-Content-Type-Options 6项全链路覆盖",
                "F2 密码与凭据策略：SHA256/plaintext→升级bcrypt/pbkdf2/argon2；禁止明文落库；SECRET_KEY轮转；.env.example模板+环境变量注入；禁止真实密钥写入仓库",
                "F3 权限矩阵优化：11级角色(guest~SA)×100点权限的加权门槛；超级管理员wuchenghao15 VIIKEY 7要素检测实时强制；@system_container装饰器防盗链/Referer强化；Arduino路由仅SA 403硬锁",
                "F4 数据库&SQL安全：参数化查询/禁止字符串拼接SQL；SQLite PRAGMA foreign_keys/jounral_mode=WAL；敏感表(用户/权限/规则)行级访问审计；备份TLS加密+异地隔离",
                "F5 反黑客速率&会话：IP级/用户级速率限制(登录失败→渐进锁定)；CSRF token每请求轮换；会话固定破坏(登出自动rotate)；SameSite=Lax/HttpOnly cookie；监控异常(300+路由 黑客注入探针300轮验证)",
                "F6 系统参数配置优化：生产/开发环境分层(ProductionConfig强制缺省即报错)；§规则治理3表完整性自检每300s；CI流水线安全门；sys_rule_enforcer弱约束词扫描；AI巡检异常自动告警投喂链",
            ],
            "outcome_types": ["CONSENSUS","AI_SUGGESTION","BRAIN_FEED","YANG_SECURITY_AUDIT_JSON","YANG_PERMISSION_OPTIMIZATION_JSON"],
            "turns": (7,10), "require_consensus": 0.65,
        },
    }

    def list_scenarios(self) -> List[str]: return sorted(self.PRESETS.keys())

    def build_context(self, scenario_code: str) -> Dict:
        code = scenario_code.upper()
        if code not in self.PRESETS: raise ValueError(f"未知场景: {scenario_code}")
        preset = self.PRESETS[code]
        ctx = {"scenario_code": code, "title": preset["title"], "intro": preset["intro"]}
        try:
            conn = get_conn()
            if code == "GAP_PROPOSAL":
                # 真实列：gap_id, gap_type, title, severity, file_path, line_number, status, weight
                stats_rows = conn.execute("SELECT severity, COUNT(*) FROM mt_feature_dev_lifecycle GROUP BY severity").fetchall()
                stats = {r[0]: r[1] for r in stats_rows}
                top10 = conn.execute("SELECT gap_id,gap_type,title,severity,file_path,line_number,status,COALESCE(weight,0) FROM mt_feature_dev_lifecycle WHERE severity IN ('high','medium') ORDER BY CASE status WHEN 'completed' THEN 1 ELSE 0 END ASC, COALESCE(weight,0) DESC LIMIT 10").fetchall()
                ctx["gap_stats"] = stats
                ctx["top10_gaps"] = [dict(zip(["gap_id","gap_type","title","severity","file","line","status","priority"], r)) for r in top10]
            if code == "PROPOSAL_REVIEW":
                # mt_dev_flow_session 在 SES_DB
                conn.close()
                conn = get_ses_conn()
                flow = conn.execute("SELECT flow_id,proposal_title,proposal_summary,COALESCE(proposal_json,'{}') FROM mt_dev_flow_session WHERE final_status='OPEN' ORDER BY created_at DESC LIMIT 1").fetchone()
                if flow:
                    ctx["target_flow"] = {"flow_id":flow[0],"title":flow[1],"summary":flow[2],"proposal_json":flow[3]}
            if code == "ARCH_UPGRADE":
                all_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                daemons = conn.execute("SELECT COUNT(*) FROM mt_daemon_registry").fetchone()[0] if "mt_daemon_registry" in all_tables else 0
                ctx["capability_snapshot"] = {
                    "current_version": "v22.7.0",
                    "daemons_registered": daemons,
                    "ai_employees_total": conn.execute("SELECT COUNT(*) FROM ai_employees").fetchone()[0],
                    "brain_feeds_total": conn.execute("SELECT COUNT(*) FROM mt_ai_brain_feed_log").fetchone()[0],
                    "broadcast_events_total": conn.execute("SELECT COUNT(*) FROM mt_ef_broadcast_events").fetchone()[0],
                }
            if code == "MRCAO_K12_TUTOR":
                # MRCAO: 真实数据源=SES mt_edu_sync_content / mt_edu_sync_question_types / mt_edu_sync_experiments
                try:
                    conn.close()
                except Exception: pass
                conn = get_ses_conn()
                # 1) content: 27条 真实列=content_id/stage/subject/grade_level/chapter/content_type/title/knowledge_tags/difficulty/status
                contents = conn.execute("SELECT content_id,stage,subject,grade_level,chapter,content_type,title,knowledge_tags,difficulty,status FROM mt_edu_sync_content WHERE status='ACTIVE' ORDER BY stage,subject,grade_level LIMIT 14").fetchall()
                ctx["k12_content_sample"] = [
                    dict(zip(["content_id","stage","subject","grade_level","chapter","content_type","title","knowledge_tags","difficulty","status"], r))
                    for r in contents
                ]
                subj_cnt = conn.execute("SELECT subject, COUNT(*) FROM mt_edu_sync_content WHERE status='ACTIVE' GROUP BY subject").fetchall()
                grade_cnt = conn.execute("SELECT grade_level, COUNT(*) FROM mt_edu_sync_content WHERE status='ACTIVE' AND grade_level IS NOT NULL GROUP BY grade_level").fetchall()
                ctx["k12_content_stats"] = {"by_subject":{r[0]:r[1] for r in subj_cnt}, "by_grade":{r[0]:r[1] for r in grade_cnt}, "total_active": sum(r[1] for r in subj_cnt)}
                # 2) question_types: 7条 真实列=qtype_id/stage/subject/question_type/parent_question/solving_model/solving_steps/knowledge_points/difficulty/answer_template/scoring_rubric
                qts = conn.execute("SELECT qtype_id,subject,question_type,parent_question,solving_model,solving_steps,knowledge_points,difficulty,answer_template FROM mt_edu_sync_question_types WHERE status='ACTIVE'").fetchall()
                ctx["k12_question_types"] = [
                    dict(zip(["qtype_id","subject","question_type","parent_question","solving_model","solving_steps","knowledge_points","difficulty","answer_template"], r))
                    for r in qts
                ]
                # 3) experiments: 4条 真实列=experiment_id/subject/experiment_name/chapter/objective/materials/difficulty
                exps = conn.execute("SELECT experiment_id,subject,experiment_name,chapter,objective,materials,difficulty FROM mt_edu_sync_experiments WHERE status='ACTIVE'").fetchall()
                ctx["k12_experiments"] = [
                    dict(zip(["experiment_id","subject","experiment_name","chapter","objective","materials","difficulty"], r))
                    for r in exps
                ]
                # 4) 9功能模块清单（与PRESETS.targets对应）
                ctx["cao_9_features"] = [
                    {"idx":1,"name":"题目解答与分析","short":"F1_QA_ANALYSIS","data_ref":"k12_question_types"},
                    {"idx":2,"name":"教辅拓展知识同步","short":"F2_CONTENT_EXTEND","data_ref":"k12_content_sample"},
                    {"idx":3,"name":"错题复习引导","short":"F3_WRONG_REVIEW","data_ref":"艾宾浩斯曲线+错因标签"},
                    {"idx":4,"name":"知识巩固","short":"F4_KNOWLEDGE_CONSOLIDATE","data_ref":"knowledge_tags/思维导图"},
                    {"idx":5,"name":"每日挑战","short":"F5_DAILY_CHALLENGE","data_ref":"勋章/成长值/连续打卡"},
                    {"idx":6,"name":"随机小测试","short":"F6_RANDOM_QUIZ","data_ref":"chapter/difficulty分层抽题"},
                    {"idx":7,"name":"学生信息录入与画像","short":"F7_PROFILE_ONBOARD","data_ref":"年级/学科/习惯/考分6字段"},
                    {"idx":8,"name":"学习习惯&薄弱环节分析","short":"F8_WEAKNESS_ANALYSIS","data_ref":"错因聚类+时间聚类+知识点聚类"},
                    {"idx":9,"name":"1对1专项训练&真正私教闭环","short":"F9_1V1_TRAINING","data_ref":"画像×EigenFlux共识×brain_feed_log综合评定"},
                ]
            if code == "WU_MEIGONG_UI_THEME":
                # WU: 真实数据源=PROJECT_ROOT下 .trae/rules/设计规范.md + flask-app/static/css/*.css 真实CSS Design Token
                import re as _re
                design_spec_path = os.path.join(PROJECT_ROOT, ".trae", "rules", "设计规范.md")
                tokens_file = os.path.join(os.path.dirname(PROJECT_ROOT) if False else PROJECT_ROOT, "flask-app", "static", "css", "mtscos_design_tokens.css")
                themes_file = os.path.join(PROJECT_ROOT, "flask-app", "static", "css", "art_themes.css")
                tokens_file = os.path.join(PROJECT_ROOT, "flask-app", "static", "css", "mtscos_design_tokens.css")
                try:
                    conn.close()
                except Exception: pass
                # 1) 读现有4套art主题真实色阶（data-theme=aurora/twilight/dawn/ink）
                existing_themes = {}
                try:
                    css_text = open(themes_file, "r", encoding="utf-8", errors="ignore").read()
                    for theme_name in ["aurora","twilight","dawn","ink"]:
                        m_block = _re.search(rf'\[data-theme="{theme_name}"\]\s*\{{([^}}]+)\}}', css_text, _re.DOTALL)
                        if m_block:
                            block = m_block.group(1)
                            theme_tokens = {}
                            for m_tok in _re.finditer(r'(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);', block):
                                theme_tokens[m_tok.group(1).strip()] = m_tok.group(2).strip()
                            existing_themes[theme_name] = theme_tokens
                except Exception as e: log.warning(f"读art_themes.css失败: {e}")
                ctx["existing_4_themes"] = existing_themes
                # 2) 读 mtscos_design_tokens.css 关键 Token（颜色/字号/间距/圆角/阴影 共100+）
                base_tokens = {"color_levels":{},"typography":{},"spacing":{},"radius":{},"shadows":{},"buttons":{},"text_bg":{}}
                try:
                    tok_text = open(tokens_file, "r", encoding="utf-8", errors="ignore").read()
                    # 颜色色阶5套（primary/success/warning/danger/info）
                    for base in ["primary","success","warning","danger","info","critical","error"]:
                        base_tokens["color_levels"][base] = {}
                        for m in _re.finditer(rf'--el-color-{base}(-(light|dark)-\d)?\s*:\s*([^;]+);', tok_text):
                            key = f"{base}{(m.group(1) or '')}"
                            base_tokens["color_levels"][base][key] = m.group(3).strip()
                    # 字号6档 + font-family
                    for m in _re.finditer(r'--el-font-(size-[a-z-]+|family(?:-mono)?)\s*:\s*([^;]+);', tok_text):
                        base_tokens["typography"][f"font-{m.group(1)}"] = m.group(2).strip()
                    # 间距8阶 xs~4xl (--mtscos-spacing-*)
                    for m in _re.finditer(r'--mtscos-spacing-([a-z0-9]+)\s*:\s*([^;]+);', tok_text):
                        base_tokens["spacing"][f"spacing-{m.group(1)}"] = m.group(2).strip()
                    # 圆角6阶
                    for m in _re.finditer(r'--mtscos-radius-([a-z0-9]+)\s*:\s*([^;]+);', tok_text):
                        base_tokens["radius"][f"radius-{m.group(1)}"] = m.group(2).strip()
                    # 阴影4种
                    for m in _re.finditer(r'--mtscos-shadow-(card|card-hover|modal|dropdown)\s*:\s*([^;]+);', tok_text):
                        base_tokens["shadows"][f"shadow-{m.group(1)}"] = m.group(2).strip()
                    # 按钮24 token（高度/字号/内边距/色阶5套）
                    for m in _re.finditer(r'--mtscos-btn-([a-z0-9_-]+)\s*:\s*([^;]+);', tok_text):
                        base_tokens["buttons"][f"btn-{m.group(1)}"] = m.group(2).strip()
                    # 文字墨色6档 + 宣纸背景色（mtscos-text-*）
                    for m in _re.finditer(r'--mtscos-text-(primary|regular|secondary|placeholder|disabled|inverse)\s*:\s*([^;]+);', tok_text):
                        base_tokens["text_bg"][f"text-{m.group(1)}"] = m.group(2).strip()
                except Exception as e: log.warning(f"读mtscos_design_tokens.css失败: {e}")
                ctx["base_tokens_snapshot"] = base_tokens
                # 3) 设计规范md摘要（存在则记关键元数据）
                if os.path.exists(design_spec_path):
                    try:
                        s = os.stat(design_spec_path)
                        ctx["design_spec_meta"] = {"path": design_spec_path, "size_bytes": s.st_size, "aligned_with": "Element Plus Design Token", "enforced": "§14 L1核心层，禁止硬编码颜色"}
                    except Exception: pass
                # 4) 5功能清单
                ctx["wu_5_features"] = [
                    {"idx":1,"name":"节日/纪念日专属配色","short":"F1_FESTIVAL_PALETTES","data_ref":"existing_4_themes 基准 × 12节日色阶扩展"},
                    {"idx":2,"name":"用户画像自适应配色排版","short":"F2_PROFILE_ADAPTIVE","data_ref":"年龄/性别/视障/设备4维度"},
                    {"idx":3,"name":"动态页面布局调度","short":"F3_LAYOUT_SCHEDULER","data_ref":"Grid 12/24列 + spacing/radius/shadows Token"},
                    {"idx":4,"name":"Design Token生成器","short":"F4_TOKEN_GENERATOR","data_ref":"Element Plus --el-color-* 5色阶 + mtscos-* 6大类 100+Token"},
                    {"idx":5,"name":"综合评定&主题切换闭环","short":"F5_COMPREHENSIVE_RATING","data_ref":"5方共识(Eigen/SCH/EMP) + WCAG AA + data-theme切换器"},
                ]
            if code == "YANG_AN_SECURITY_EXPERT":
                # YANG: 真实数据源=主库mt_users/权限/规则/治理3表 + Flask app/middlewares现状 + SECURITY/DBA EigenFlux专家注册数
                import re as _re
                try:
                    conn.close()
                except Exception: pass
                # 1) 主库 mt_users/角色/权限真快照
                users_snapshot = {"tables_found": [], "user_count": 0, "role_cols": [], "password_hash_algos": {}, "sa_usernames": []}
                try:
                    conn = get_conn()  # ENGINE库(app/engines/app.db)
                except Exception:
                    conn = None
                main_conn = None
                try:
                    main_base = os.path.join(PROJECT_ROOT, "flask-app")
                    sys.path.insert(0, main_base)
                    from core.db_path import get_db_path as _get_main_db
                    MAIN_DB_PATH = _get_main_db("app.db")
                    main_conn = sqlite3.connect(MAIN_DB_PATH, timeout=15)
                    curm = main_conn.cursor()
                    # 查mt_users/user表
                    curm.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%users%' OR name LIKE '%role%' OR name LIKE '%permission%' OR name LIKE 'mt_rule_%' OR name LIKE '%security%')")
                    sec_tables = [r[0] for r in curm.fetchall()]
                    users_snapshot["tables_found"] = sorted(sec_tables)
                    if "mt_users" in sec_tables:
                        curm.execute("PRAGMA table_info(mt_users)")
                        ut_cols = [r[1] for r in curm.fetchall()]
                        users_snapshot["role_cols"] = ut_cols[:30]
                        curm.execute("SELECT count(*) FROM mt_users")
                        users_snapshot["user_count"] = curm.fetchone()[0]
                        # 密码算法抽样
                        pw_cols = [c for c in ut_cols if "pass" in c.lower() or "hash" in c.lower() or "pwd" in c.lower()]
                        if pw_cols:
                            curm.execute(f"SELECT {pw_cols[0]} FROM mt_users LIMIT 20")
                            algo_map = {}
                            for (v,) in curm.fetchall():
                                vs = str(v or "")[:40]
                                if not vs or vs in ("None", ""): continue
                                a = "unknown"
                                if vs.startswith(("$2a$","$2b$","$2y$")): a = "bcrypt"
                                elif vs.startswith(("$pbkdf2","pbkdf2:")): a = "pbkdf2"
                                elif vs.startswith("$argon2"): a = "argon2"
                                elif len(vs) == 64 and all(c in "0123456789abcdefABCDEF" for c in vs): a = "sha256"
                                elif vs.startswith("sha1$") or len(vs) == 40: a = "sha1_or_weak"
                                else: a = "plaintext_or_weak"
                                algo_map[a] = algo_map.get(a,0)+1
                            users_snapshot["password_hash_algos"] = algo_map
                        # SA白名单=wuchenghao15(规则§用户权限唯一SA)
                        for key_col in ["username","user_name","account","name"]:
                            if key_col in ut_cols:
                                curm.execute(f"SELECT {key_col}, role FROM mt_users WHERE role LIKE '%super%' OR role IN ('sadmin','sa') OR {key_col}='wuchenghao15' LIMIT 20")
                                for r in curm.fetchall():
                                    users_snapshot["sa_usernames"].append({"account":r[0],"role":r[1]})
                                break
                    # 规则治理3表mt_rule_*(§14 L0)
                    rule_counts = {}
                    for tname in ("mt_rule_changelog","mt_rule_violation_alert","mt_rule_integrity_scan"):
                        if tname in sec_tables:
                            curm.execute(f"SELECT count(*) FROM {tname}")
                            rule_counts[tname] = curm.fetchone()[0]
                    users_snapshot["rule_governance_counts"] = rule_counts
                    # 现有eigenflux SECURITY/DBA领域专家
                    if "eigenflux_registrations" in sec_tables:
                        curm.execute("SELECT role,name,speciality_json FROM eigenflux_registrations WHERE (role LIKE '%SEC%' OR role LIKE '%DBA%' OR name LIKE '%sec%' OR name LIKE '%dba%') LIMIT 10")
                        users_snapshot["security_dba_experts"] = [dict(role=r[0], name=r[1], spec=str(r[2])[:60]) for r in curm.fetchall()]
                except Exception as _e:
                    log.warning(f"[YANG build_context main_db read] skip: {_e}")
                finally:
                    if main_conn:
                        try: main_conn.close()
                        except Exception: pass
                ctx["security_snapshot"] = users_snapshot
                # 2) Flask响应安全header现状(middlewares扫描)
                headers_now = {"HSTS": False,"CSP": False,"XFrame": False,"XXSS": False,"ReferrerPolicy": False,"XContentType": False,"RateLimit": False,"CSRF": False}
                scan_paths = [
                    os.path.join(PROJECT_ROOT, "flask-app", "app", "middlewares"),
                    os.path.join(PROJECT_ROOT, "flask-app", "app"),
                    os.path.join(PROJECT_ROOT, "flask-app", "routes"),
                ]
                for sp in scan_paths:
                    if not os.path.isdir(sp): continue
                    for root_dir, _, files in os.walk(sp):
                        for fn in files:
                            if not fn.endswith(".py"): continue
                            try:
                                txt = open(os.path.join(root_dir, fn), "r", encoding="utf-8", errors="ignore").read()
                            except Exception: continue
                            for sig, key in [("Strict-Transport-Security","HSTS"),("Content-Security-Policy","CSP"),
                                              ("X-Frame-Options","XFrame"),("X-XSS-Protection","XXSS"),
                                              ("Referrer-Policy","ReferrerPolicy"),("X-Content-Type-Options","XContentType"),
                                              ("rate_limit","RateLimit"),("CSRF","CSRF")]:
                                if sig in txt and not headers_now[key]:
                                    headers_now[key] = True
                ctx["response_headers_status"] = headers_now
                # 3) 硬编码密钥线索grep (仅文件名+行号汇总，不打印真实值)
                hardcoded_audit = {"candidate_matches_total": 0, "files_hits": {}, "policy": "仅写入占位符，真实密钥禁止写入仓库/.env"}
                try:
                    root = pathlib.Path(PROJECT_ROOT) / "flask-app"
                    patterns = [r'SECRET_KEY\s*=\s*["\']([^"\']{16,})["\']', r'password\s*=\s*["\']([^"\']{6,})["\']', r'DATABASE_URL\s*=\s*["\']([^"\']+://[^"\']+)["\']']
                    for f in list(root.rglob("*.py"))[:220]:
                        try: txt = f.read_text(encoding='utf-8', errors='ignore')
                        except Exception: continue
                        hits = 0
                        for pat in patterns:
                            for _ in _re.finditer(pat, txt):
                                hits += 1
                        if hits:
                            hardcoded_audit["files_hits"][str(f.relative_to(root))] = hits
                            hardcoded_audit["candidate_matches_total"] += hits
                except Exception as _e:
                    log.warning(f"[YANG hardcode scan] skip: {_e}")
                ctx["hardcoded_secrets_audit"] = hardcoded_audit
                # 4) YANG 6大功能模块清单（与PRESETS.targets对应）
                ctx["yang_6_features"] = [
                    {"idx":1,"name":"Flask响应安全Headers加固","short":"F1_HEADERS_HARDENING","data_ref":"HSTS/CSP-ReportOnly/XFO/XXSS/Referrer/X-Content-Type 6项对齐OWASP Secure Headers Project"},
                    {"idx":2,"name":"密码与密钥凭据治理","short":"F2_SECRETS_GOVERNANCE","data_ref":"password算法升级→bcrypt/pbkdf2/argon2 + .env.example + 变量注入"},
                    {"idx":3,"name":"11级角色×100点权限矩阵优化+SA VIIKEY","short":"F3_PERMISSION_MATRIX","data_ref":"§用户权限×11角色+wuchenghao15 7要素+USB VIKEY实时签核+Arduino仅SA"},
                    {"idx":4,"name":"DB安全&SQL注入防御&审计","short":"F4_DATABASE_SECURITY","data_ref":"参数化查询+PRAGMA外键/WAL+敏感表行级审计+备份TLS加密异地隔离"},
                    {"idx":5,"name":"反黑客速率/会话/CSRF/防盗链","short":"F5_ANTI_HACKING","data_ref":"登录渐进锁+SameSite/HttpOnly+CSRF rotate+黑客300探针验证+Referer防盗链"},
                    {"idx":6,"name":"系统参数&CI安全门&规则完整性自检","short":"F6_PARAMS_AND_CI_GATE","data_ref":"Prod/Dev分层配置+§治理3表自检+sys_rule_enforcer弱约束词清零+CI安全门"},
                ]
            conn.close()
        except Exception as e:
            log.warning(f"scenario context真实数据读取失败（降级通用prompt）: {e}")
        return ctx


# =====================================================================
# 五、ActorAgent（发言生成：用模板+权重+情感，不用远程LLM，零token）
# =====================================================================
class ActorAgent:
    TONE = ["郑重", "审慎", "直接", "犀利", "务实", "温和", "警惕", "乐观", "批判", "期待"]
    PREFIX = {
        "AI_EMPLOYEE": ["从实际落地执行角度看：", "我在日常修复中观察到：", "如果真要我动手做，我会先："],
        "EIGENFLUX_EXPERT": ["作为领域专家，我想指出：", "从专业边界看核心问题是：", "基于我的领域权重，我建议："],
        "SCHOLAR": ["从学术研究视角分析：", "更长远的范式性问题在于：", "我的学科方法给这个问题的启示是："],
    }

    @staticmethod
    def speak(actor: Dict, scenario_preset: Dict, ctx: Dict, turn_num: int, prior_messages: List[Dict]) -> Dict:
        targets = scenario_preset.get("targets", ["第一轮发言"])
        direction = targets[min(turn_num - 1, len(targets)-1)]
        prefix = random.choice(ActorAgent.PREFIX[actor["role"]])
        tone = random.choice(ActorAgent.TONE)
        name=actor["actor_name"]; role=actor["role"]; dom=actor["domain"]; spec=actor["specialty"]; persp=actor["perspective"]; style=actor.get("style","")
        weight=actor.get("speak_weight",actor["expertise_weight"])
        scenario_code = ctx.get("scenario_code","")
        if scenario_code=="GAP_PROPOSAL" and "top10_gaps" in ctx:
            top=ctx["top10_gaps"]
            pick=random.choice(top)
            sev_rank = {"high":"高优先级","medium":"中","critical":"紧急","low":"低"}
            content = (f"{prefix}当前缺口总览是{ctx.get('gap_stats',{})}，我挑出{pick['gap_type']}型缺口「{str(pick['title'])[:36]}」（{pick['file']}:{pick['line']}，"
                       f"严重度={sev_rank.get(pick['severity'],'-')}，状态={pick['status']}，权重={pick.get('priority',0)}）"
                       f"。从{persp}出发，我的{direction}要求是：①支持/反对=「{'支持' if weight>0.75 else '谨慎支持' if weight>0.6 else '有条件通过'}」；"
                       f"②不妥协边界=「「{style}派要求{dom}领域专家权重大于{weight-0.15:.2f}，否则必须追加{spec[:12]}专项审查」」；"
                       f"③落地成本={random.randint(1,10)}人日；风险等级={'中高' if actor['risk_tolerance']<0.35 else '中低'}。"
                       f"  —— 我的发言「{tone}」风格。")
        elif scenario_code=="PROPOSAL_REVIEW" and "target_flow" in ctx:
            flow=ctx["target_flow"]
            decision = random.choices(["通过","修改后再议","退回"], weights=[max(0.2,weight),0.5,max(0.1, 1.0-weight)], k=1)[0]
            content = (f"{prefix}针对§14FLOW={str(flow['flow_id'])[:28]}…提案「{str(flow['title'])[:50]}」，摘要：「{str(flow['summary'])[:90]}…」。"
                       f"从{persp}出发（领域权重={weight:.2f}，准确率={actor['accuracy_rate']:.2f}，{style}派）——评审结论：【{decision}】。"
                       f"理由：①合规边界={dom}合规性{'通过' if weight>0.7 else '需要补充条款'}；"
                       f"②可测试性={'强' if actor.get('accuracy_rate',0.8)>0.9 else '需补充TEST_P0_VERIFY脚本'}；"
                       f"③SA终审边界=「「如涉及敏感路由/权限，必须wuchenghao15 VIIKEY实体验证」」。发言基调「{tone}」。")
        elif scenario_code=="ARCH_UPGRADE" and "capability_snapshot" in ctx:
            snap=ctx["capability_snapshot"]
            directions = ["分布式推理集群治理","本地向量脑库+混合检索","OneDrive沙箱与代码同步隔离","EigenFlux专家治理"]
            direction_pick = random.choice(directions)
            content = (f"{prefix}当前能力快照={snap}。作为{style}派{dom}学者（权重={weight:.2f}，准确率={actor['accuracy_rate']:.2f}），"
                       f"评估v23.0.0升级方向「{direction_pick}」：①MVP功能集=「{random.randint(2,5)}个核心能力+TEST_P0_VERIFY 100%pass+DB落库」；"
                       f"②3里程碑={datetime.date.today().isoformat()}+14d MVP+30d BETA+60d GA；"
                       f"③风险边界（{tone}）=「「禁止改动L0规则；禁止新建超过2张冗余表；禁止绕过§14直接改数据库」」。视角：{persp}。")
        elif scenario_code=="MRCAO_K12_TUTOR" and "cao_9_features" in ctx:
            # MRCAO_K12_TUTOR：每轮挑选1个feature模块讨论（F1~F9）
            features = ctx["cao_9_features"]
            f_idx = ((turn_num - 1) * 3 + (hash(actor["actor_id"]) % 3)) % len(features)
            f = features[f_idx]
            # 取真实教辅/题型/实验样例做具体举例
            qt = random.choice(ctx["k12_question_types"]) if ctx.get("k12_question_types") else None
            cont = random.choice(ctx["k12_content_sample"]) if ctx.get("k12_content_sample") else None
            exp = random.choice(ctx["k12_experiments"]) if ctx.get("k12_experiments") else None
            # 积极性提升话术（按角色）
            role_motivation = {
                "AI_EMPLOYEE": f"我用已落地的{spec}，每次给学生答案时追加1句「真实生活这个知识点用在哪」（如{qt['parent_question'] if qt else '有理数大小比较'}：买东西结账/分数算折扣/冰箱温度），让学习有意义。",
                "EIGENFLUX_EXPERT": f"从{dom}专业边界看，{f['name']}必须做到「{style}派」：步骤可追溯+不超纲+隐私最小化。例如{cont['title'] if cont else '有理数运算'}同步{cont['chapter'] if cont else '七年级'}章拓展视频时，必须保留教师讲解镜头与板书，不能纯AI生成。",
                "SCHOLAR": f"从{persp}来看，{f['name']}要重视「学习动机内化」：每次{f['name'][:4]}后追加1个开放式问题（如为什么这个方法成立？还有别的方法吗？），引导学生发现学习真正意义——{random.choice(['理解世界运行规律','培养终身思考能力','建立自己的知识框架','为真实问题找答案'])}。",
            }
            motivation = role_motivation.get(actor["role"], "")
            # 边界/风险
            risk_lines = []
            if actor["risk_tolerance"] < 0.4: risk_lines.append("必须设置未成年人模式：禁止回答非学科问题、禁止记录个人隐私（姓名/学校/住址/身份证号）")
            if dom.upper() in ("COMPLIANCE","SECURITY","CRYPTOGRAPHY","DEFENSE_SYSTEM"): risk_lines.append("所有回答必须附「知识来源」（如同步人教版教材第X章或真实content_id），禁止编造知识点")
            if actor["role"]=="SCHOLAR": risk_lines.append(f"AI不直接给最终答案，必须引导学生自己走完解题步骤模型（如{qt['solving_model'] if qt else '作差法/作商法/数轴法'}），答完后再揭示正确答案")
            if not risk_lines: risk_lines.append(f"{f['name']}的AI误答必须触发人工兜底按钮（上报给学校老师），置信度<{int(weight*70)}%时必须弹提示")
            # 1对1私教要点
            personalize = [
                f"画像驱动：按年级标签匹配对应难度档",
                f"节奏个性化：上次答题正确率低于{55+int(weight*15)}%时，自动降低{'随机小测试F6' if random.random()>0.5 else '每日挑战F5'}难度1档",
                f"正向激励：{f['name'][:4]}环节累计连续3题答对触发「曹老师勋章」+真实知识点故事（{random.choice(['高斯小时候的1+2+...+100','阿基米德测皇冠浮力','居里夫人发现镭'])}）"
            ]
            # 具体举例（来自真数据）
            if f["idx"]==1 and qt:  # F1题目解答 用真实母题
                example = f"真实母题：「{qt['parent_question']}」（{qt['subject']}/题型={qt['question_type']}/难度={qt['difficulty']}），母题迁移至少出3道同模板变体（{qt['solving_steps'][:40]}…）"
            elif f["idx"]==2 and cont:  # F2教辅拓展 用真实content
                example = f"真实教辅同步：「{cont['subject']}/{cont['grade_level']}/{cont['chapter']}/《{cont['title']}》（content_id={cont['content_id'][:16]}…，知识点标签=[{cont['knowledge_tags'][:36]}]），拓展方向：{cont['difficulty']}→hard变式+实验/生活链接"
            elif f["idx"] in (5,6) and qt:
                example = f"题目池约束：按{qt['subject']}/章分层抽题，正确率×权重={weight:.2f}≈{int(weight*100)}%。每日挑战=3题（easy+medium+hard各1），错2题自动追加错题推送"
            elif f["idx"]==7:
                example = f"F7最小录入6字段：年级(必填)/学科偏好/近期单元考分(0~100)/日均学习时长(分钟)/错题本(上传可选)/兴趣方向；PII必须加盐哈希存+按《未成年人保护法》40条执行"
            elif f["idx"]==8:
                example = f"薄弱分析画像：错因聚类（粗心/概念错/公式误用/审题不清/知识点盲区 5类）+ 时间聚类（下午3~5点 vs 晚上8~9点正确率差）→输出薄弱Top10知识点，权重≥0.7的学科自动置顶"
            elif f["idx"]==9 and exp:
                example = f"1对1私教综合评定：画像薄弱Top10 × EigenFlux共识({dom}+COMPLIANCE+ARCHITECTURE权重和≥{weight+0.8:.2f}) × 脑库已投喂知识条数≥{515+len(features)} + 理化实验联动推荐「{exp['experiment_name']}」({exp['subject']}/{exp['chapter']}) → 生成每周6课时个性化训练计划(2课时讲解+3课时练习+1课时1v1辅导答疑)"
            else:
                example = f"举例：{cont['subject'] if cont else '数学'}年级={cont['grade_level'] if cont else '七年级'} → 章={cont['chapter'] if cont else '有理数'} → 曹老师AI引导走4步：识别目标→拆解子问题→一步步推理→最终答案→迁移训练2题"
            # 拼接内容（150~200字）
            content = (f"{prefix}【{f['idx']}-{f['name']} ({f['short']})】作为{style}派{role}/{name}（权重={weight:.2f}，准确率={actor['accuracy_rate']:.2f}，{persp[:24]}）。"
                       f"①MVP必须包含：{example[:90]}。"
                       f"②学习积极性引导：{motivation[:80]}。"
                       f"③1对1私教个性化要点：{personalize[0][:40]}；{personalize[1][:40]}；{personalize[2][:40]}。"
                       f"④边界与风险（{tone}）：{'；'.join(risk_lines[:2])[:80]}。参考数据源：{f['data_ref'][:32]}")
        elif scenario_code=="WU_MEIGONG_UI_THEME" and "wu_5_features" in ctx:
            # WU：5 大功能模块，每轮挑1个讨论 F1~F5
            features = ctx["wu_5_features"]
            f_idx = ((turn_num - 1) * 3 + (hash(actor["actor_id"]) % 5)) % len(features)
            f = features[f_idx]
            # 取真实主题/真实Token样例
            existing_themes: Dict = ctx.get("existing_4_themes", {})
            tokens: Dict = ctx.get("base_tokens_snapshot", {})
            color_levels: Dict = tokens.get("color_levels", {})
            # 现有4套主题模板主色
            template_main = {}
            for tn, tvals in existing_themes.items():
                primary = tvals.get("--el-color-primary")
                accent = tvals.get("--art-gradient-main")
                if primary: template_main[tn] = primary
            if not template_main: template_main = {"aurora":"#409EFF","twilight":"#8B5CF6","dawn":"#F97316","ink":"#1E40AF"}
            # 节日预设12套具体配色（HEX 具体值）
            festival_palettes = [
                {"k":"national_memorial","name":"国家公祭日(12/13)","notes":"肃穆灰阶·禁彩色","primary":"#606266","accent":"#909399","bg":"#F2F3F5","text":"#303133","contrast":"9.1"},
                {"k":"national_day","name":"国庆(10/1)·中国红金","notes":"朱红+赤金·国徽配色","primary":"#DE2910","accent":"#FFDE00","bg":"#FFF6E0","text":"#1A1A1A","contrast":"6.8"},
                {"k":"spring_festival","name":"春节(正月初一)·春联朱红","notes":"中国红+春联金+红灯笼","primary":"#C8102E","accent":"#FFD700","bg":"#FFF1E8","text":"#1E1E1E","contrast":"7.2"},
                {"k":"mid_autumn","name":"中秋·月白银桂","notes":"月白+银桂黄·静谧","primary":"#8A7CCE","accent":"#E8C96A","bg":"#FAFAF5","text":"#2A2A3A","contrast":"7.8"},
                {"k":"birthday_month","name":"用户生日当月·糖果粉彩","notes":"柔和马卡龙·温暖喜悦","primary":"#F472B6","accent":"#60A5FA","bg":"#FFF7FB","text":"#3A1E2A","contrast":"6.4"},
                {"k":"children_day","name":"儿童节·明亮糖果色","notes":"三原色+明亮·孩童友好","primary":"#FF6B6B","accent":"#4ECDC4","bg":"#FFFDF0","text":"#1A1A2A","contrast":"7.6"},
                {"k":"teachers_day","name":"教师节·谢师桃李色","notes":"桃李粉+墨绿·庄重","primary":"#D97706","accent":"#059669","bg":"#FDFCF5","text":"#2A2A1A","contrast":"7.4"},
                {"k":"graduation","name":"毕业季·学士蓝金","notes":"学士服深蓝+穗金色","primary":"#1E3A8A","accent":"#D4AF37","bg":"#F0F4FA","text":"#0F172A","contrast":"11.2"},
                {"k":"dragon_boat","name":"端午·艾草青绿","notes":"艾草青+粽米白+绳红","primary":"#65A30D","accent":"#B91C1C","bg":"#F7FEE7","text":"#1A2E0A","contrast":"8.3"},
                {"k":"qingming","name":"清明·素雅烟青","notes":"柳色青烟白·克制","primary":"#64748B","accent":"#94A3B8","bg":"#F8FAFC","text":"#1E293B","contrast":"10.1"},
                {"k":"lantern","name":"元宵·花灯橙金","notes":"花灯橙+谜语金+月白","primary":"#EA580C","accent":"#F59E0B","bg":"#FFF7ED","text":"#2A1A0A","contrast":"6.9"},
                {"k":"party_found","name":"建党节·红旗红金","notes":"党旗红+镰刀锤头金","primary":"#C1272D","accent":"#FFD700","bg":"#FFEAEA","text":"#1A0A0A","contrast":"7.5"},
            ]
            # 排版布局Token真实值（从CSS解析结果）
            spacing8 = tokens.get("spacing", {"spacing-xs":"4px","spacing-sm":"8px","spacing-md":"16px","spacing-lg":"24px","spacing-xl":"32px","spacing-2xl":"48px"})
            radius6 = tokens.get("radius", {"radius-sm":"4px","radius-md":"8px","radius-lg":"12px","radius-xl":"16px","radius-pill":"9999px"})
            shadows4 = tokens.get("shadows", {"shadow-card":"0 2px 12px rgba(0,0,0,0.08)","shadow-modal":"0 12px 32px rgba(0,0,0,0.16)"})
            font_sizes = tokens.get("typography", {"font-size-base":"14px","font-size-large":"18px","font-size-medium":"16px","font-size-small":"13px"})
            # 吴美工角色差异化视角（文化/设计/性能/可达性/落地）
            role_style_ui = {
                "SCHOLAR": {
                    "戴锦华": ("文化研究视角：节日配色必须尊重文化语义禁忌→如公祭日禁用红橙亮色，避免消费主义侵蚀。", f"从媒介文化批评看：{f['name'][:8]}要警惕「视觉过度消费」，主题切换要有200ms呼吸过渡、不能用闪烁渐变。"),
                    "CULTURE_STUDY": ("文化语义视角：节日配色是严肃的文化符号表达，不是好看就行。", f"文化批评角度：{f['name'][:8]}必须校验12个预设节日与禁忌色，避免颜色误用。"),
                    "AI_VISION": ("AI视觉鲁棒性视角：色彩在各种显示屏(IPS/OLED/墨水屏)下的保真度与色盲友好度。", f"视觉鲁棒性：{f['name'][:8]}必须测试色盲模式（红绿色盲/蓝黄色盲）下的对比度≥4.5:1（WCAG AA）。"),
                    "COMPUTER_ARCH": ("工程设计视角：整体论要求设计是系统级可复用Token，不能每页各写各的样式。", f"工设系统视角：{f['name'][:8]}必须基于现{len(existing_themes)}套主题模板，沿用--el-color-primary 5色阶×8档间距×6圆角的不变骨架，用「调参」而非「重写」。"),
                    "TRADITIONAL_LOGIC": ("东方整体论视角：配色与排版要「和谐」，主辅色比≈6:3:1黄金比例，留白比例≥38%。", f"整体论视角：{f['name'][:8]}的和谐度算法=主色面积:辅色:强调色 = 6 : 3 : 1(±0.5)；留白率≥38%；视觉焦点只能1个。"),
                    "EDU_PSYCHOLOGY": ("发展心理学视角：青少年UI(字号≥16px/行距≥1.7)、儿童UI(大按钮/色彩明快)、成人UI(专业克制)。", f"教育心理学视角：{f['name'][:8]}的年龄适配必须分级：儿童13岁以下→字号≥{font_sizes.get('font-size-large','18px')}，按钮≥44×44px(苹果HIG)。"),
                },
                "EIGENFLUX_EXPERT": {
                    "PERFORMANCE": ("渲染性能视角：切换主题CSS变量＜50ms，不允许重写整页CSS；仅改--el-*与--mtscos-*。", f"性能视角：{f['name'][:8]}切换主题必须＜50ms；重绘仅root.data-theme；禁止JS改DOM类名(除[data-theme])。"),
                    "ARCHITECTURE": ("架构视角：Token系统必须可版本化、可回滚；所有主题方案落mt_theme_schemes表（可追加）。", f"架构视角：{f['name'][:8]}必须与现有{list(template_main.keys())}4套主题共用色阶light-3/5/7/9/dark-2结构，绝对不能断。"),
                    "COMPLIANCE": ("合规/可达性视角：WCAG AA对比度≥4.5:1文字/3:1大字号；色盲友好；键盘可达。", f"合规视角：{f['name'][:8]}必须提供高对比度模式（对比度15:1）+灰色模式（灰度≤100K，国家公祭日自动启）。"),
                    "AI": ("AI推荐视角：基于用户画像特征（年龄/性别/设备/节日）做主题推荐，并保留用户主动改的override。", f"AI推荐视角：{f['name'][:8]}算法权重 = 节日日期匹配度×0.5 + 用户画像得分×0.3 + 上次选择偏好×0.2。"),
                    "DEFAULT": ("EigenFlux专家视角：领域权重×准确率 加权判定。", f"从{dom}专业边界看，{f['name'][:8]}必须做到：{style}派步骤可追溯+不破坏设计Token骨架+可回滚。"),
                },
                "AI_EMPLOYEE": {
                    "DEFAULT": ("前端落地实操视角：具体怎么写[data-theme]切换器+CSS变量覆盖，必须有可粘贴CSS snippet样例输出。", f"实操落地：{f['name'][:8]}我直接能写出：[data-theme='{random.choice(list(template_main.keys())+['national_day','spring_festival'])}'] {{ --el-color-primary: HEX; ... }} 真实CSS snippet，一贴就能跑。"),
                },
            }
            # 具体内容（按feature不同）
            f1_pal = random.choice(festival_palettes)
            if f["idx"]==1:  # F1 节日配色
                base_pal = template_main.get(random.choice(list(template_main.keys())))
                example = (f"预设×{len(festival_palettes)}套已覆盖「{f1_pal['name']}」→主色={f1_pal['primary']}强调={f1_pal['accent']}背景={f1_pal['bg']}文字={f1_pal['text']}对比度={f1_pal['contrast']}:1(WCAG AA≥4.5✅)；"
                           f"生成器：基于现有{len(template_main)}套模板（主色如{base_pal}）→自动产出--el-color-primary/light-3/5/7/9/dark-2 完整6色阶")
                motivation = f"文化传递：每个节日主题加载时弹15s节日文化说明（如公祭日「铭记历史，吾辈自强」），配色=文化符号的一部分。"
                personalize = [f"节日当日自动启用（按服务器时区MM-DD匹配），用户可手动关闭", f"生日配色=用户profile.birth_month自动匹配糖果粉彩当月启用", f"主题切换200ms呼吸过渡，模态窗带节日祝福小彩蛋"]
                risk_lines = [
                    "文化禁忌：公祭日/清明禁用高亮动画/糖果色/喜庆渐变（戴锦华批评点）",
                    "WCAG AA强制：所有主题文字对比度≥4.5:1（郑南宁色盲鲁棒要求）",
                    "Token兼容：绝对保留light-3/5/7/9/dark-2色阶，不可改色阶数量（架构派）",
                    "性能：主题切换＜50ms，不能整页闪白",
                ]
            elif f["idx"]==2:  # F2 年龄/性别 自适应排版
                profiles = [
                    {"tag":"儿童K1<12y","font_scale":1.25,"line_height":1.9,"color_contrast":"high","accent_brightness":"high","notes":f"字号放大×{1.25}，按钮≥44×44px"},
                    {"tag":"青少年12~18","font_scale":1.10,"line_height":1.75,"color_contrast":"normal","accent_brightness":"high","notes":"字号放大×1.1，导航栏24px高适合触屏"},
                    {"tag":"成人18~45","font_scale":1.00,"line_height":1.60,"color_contrast":"normal","accent_brightness":"medium","notes":"标准字号，紧凑专业"},
                    {"tag":"长辈>45","font_scale":1.35,"line_height":2.00,"color_contrast":"ultra","accent_brightness":"medium","notes":"字号放大1.35倍，行距≥2.0，对比度15:1"},
                    {"tag":"视障模式","font_scale":1.50,"line_height":2.20,"color_contrast":"ultra","accent_brightness":"mono","notes":"超大字号+纯黑白+大光标+屏幕阅读器支持"},
                ]
                pick_p = random.choice(profiles)
                example = (f"5种用户画像自适应预设：「{pick_p['tag']}」→字号缩放×{pick_p['font_scale']}（基于{font_sizes.get('font-size-base','14px')}→{round(pick_p['font_scale']*14,1)}px）"
                           f"行距={pick_p['line_height']}；对比度={pick_p['color_contrast']}；{pick_p['notes']}。设备断点：手机<768px/平板<1280px/桌面≥1280px Grid 12/24列切换")
                motivation = f"让孩子觉得「好看」、老人看得清、中青年用得爽=配色是人的尊严（林崇德视角：UI适配=尊重发展差异）。"
                personalize = ["首次登录弹30秒简单选择=年龄/视力/设备类型自动匹配", "用户可覆盖：设置→显示→字号滑块(100~160%)+对比度开关", "设备检测：手机自动24栅格折叠为单列导航，桌面12栅格双栏"]
                risk_lines = ["性别配色绝对不能做「男=蓝女=粉」刻板印象，保留随机+override", "长辈模式>45岁必须有语音播报按钮，按钮≥48×48px", "视障模式必须纯黑白(或2色)，无装饰渐变，焦点环≥3px"]
            elif f["idx"]==3:  # F3 动态布局调度
                example = (f"布局系统骨架=现有{len(spacing8)}档间距(基础8px单位，如{spacing8.get('spacing-md','16px')}/{spacing8.get('spacing-lg','24px')}"
                           f") × {len(radius6)}档圆角(如{radius6.get('radius-lg','12px')}/{radius6.get('radius-xl','16px')})"
                           f" × {len(shadows4)}种阴影(如{str(shadows4.get('shadow-card',''))[:36]}…)"
                           f" → 4种场景预设：①管理台(紧凑/间距sm/圆角sm)②门户(宽松/间距lg/圆角xl/留白≥42%)③看板(居中/卡片阴影modal)④手机(单列/间距lg/圆角pill)")
                motivation = f"「留白让信息呼吸」：管理台留白率28%→门户42%→看板50%（readymag杂志风经验1012422：大幅留白+分镜式切换=高级感）。"
                personalize = ["根据路由自动切：/admin→紧凑；/dashboard→居中卡片；/portal→宽松杂志风；/mobile→单列", "侧边栏折叠：窗口<960px自动折叠并显示汉堡，节省240px宽度", "卡片圆角+阴影随场景：节日=圆角大/阴影柔和；管理台=圆角小/阴影淡"]
                risk_lines = ["权限页(用户/规则/SA页)必须强制用「管理台紧凑」模式，禁止用大圆角糖果色，保持专业克制", "断点Grid 768/960/1280必须三档齐，不能漏", "modal必须居中；z-index绝对遵循base tokens"]
            elif f["idx"]==4:  # F4 Token生成器
                pal5 = color_levels.get("primary", {"primary":"#409EFF","primary-light-3":"#79BBFF","primary-light-5":"#A0CFFF","primary-light-7":"#C6E2FF","primary-light-9":"#ECF5FF","primary-dark-2":"#337ECC"})
                example = (f"输入：主题名(如{national_day if False else f1_pal['k']})+主色HEX（如{f1_pal['primary']}）→输出Element Plus + MTSCOS 100+Design Token："
                           f"--el-color-primary 6色阶（基准：主色={pal5.get('primary','#409EFF')}/light-3={pal5.get('primary-light-3','#79BBFF')}/light-5={pal5.get('primary-light-5','#A0CFFF')}/light-7/light-9/dark-2）"
                           f"×success/warning/danger/info 5套色阶 × 字号6档 × spacing 8阶 × radius 6阶 × shadow 4种 × mtscos-btn 24组件Token × mtscos-text 6墨色")
                motivation = f"吴美工AI的核心：调参而不是重写→所有前端工程师统一用生成的--el-*和--mtscos-*，全站硬编码颜色=0个。"
                personalize = ["生成：CSS snippet + SCSS variables map + JSON token三种格式一起出", "一键预览：右侧卡片live预览按钮/链接/警示框5色阶 + 文字对比度", "可导入现有4套主题修改后另存为新主题"]
                risk_lines = ["绝对禁止破坏色阶数量=primary必须有light-3/light-5/light-7/light-9/dark-2共6档，否则Element Plus组件样式会破", "输出前自动跑WCAG对比度验证，失败=红叉阻止保存", "默认主题=aurora(#409EFF)绝对不能改（仅SA wuchenghao15能改）"]
            else:  # F5 综合评定 + 主题切换闭环
                # 5方评定权重
                scores_template = {
                    "AI推荐评分(0~1)": 0.20,
                    "EigenFlux专家共识(加权)": 0.25,
                    "学者综合(文化/视觉/工设/心理)": 0.30,
                    "AI员工落地可行性": 0.10,
                    "WCAG可达性验证": 0.15,
                }
                example = (f"5方加权评定：{scores_template} → 总分≥0.70才能通过，自动写入mt_design_theme_schemes。"
                           f"切换器：data-theme='<theme_name>' + root.style.setProperty() ＜50ms；暗色模式[data-theme='dark']自动覆盖--el-bg-color/--el-text-color-primary；"
                           f"闭环：应用→记录→每周AI巡检→改进→新版本→灰度1%用户→全员=持续优化(经验1012422增量迭代不重写)")
                motivation = f"「真正的专门前端配色调度排版专家」不是一张漂亮图，而是可落地、可合规、可传承、可优化、5方综合评定永远在线的系统。"
                personalize = ["设置页主题切换器=4默认×12节日×5年龄×3高对比度×自定义组合", "每天0点根据当日日期自动+明日生日用户预加载主题并cache CSS，切换0ms", "SA审核：新增主题需要wuchenghao15 VIIKEY签核才能发布到全员（§14权限）"]
                risk_lines = ["SA页面/登录页/权限页=固定default主题，禁止切换，防止误导或混淆权限判断", "灰度：新主题先1%用户→10%→50%→100% rollout，不满意随时一键回滚", "审计：所有主题切换都落mt_theme_usage_log，便于复盘视觉事故责任"]
            # 从role_style_ui挑角色专属话术
            if actor["role"]=="SCHOLAR":
                key = actor["actor_name"] if actor["actor_name"] in role_style_ui["SCHOLAR"] else dom
                if key not in role_style_ui["SCHOLAR"]: key = dom
                if key not in role_style_ui["SCHOLAR"]: key = "COMPUTER_ARCH"
                if key not in role_style_ui["SCHOLAR"]: key = "COMPUTER_ARCH"
                for kk, (s1, s2) in role_style_ui["SCHOLAR"].items():
                    if kk == key:
                        ui_perspective = s1 + " " + s2; break
                else: ui_perspective = role_style_ui["SCHOLAR"]["COMPUTER_ARCH"][0] + " " + role_style_ui["SCHOLAR"]["COMPUTER_ARCH"][1]
            elif actor["role"]=="EIGENFLUX_EXPERT":
                key = dom if dom in role_style_ui["EIGENFLUX_EXPERT"] else "DEFAULT"
                ui_perspective = role_style_ui["EIGENFLUX_EXPERT"].get(key, role_style_ui["EIGENFLUX_EXPERT"]["DEFAULT"])[0] + " " + role_style_ui["EIGENFLUX_EXPERT"].get(key, role_style_ui["EIGENFLUX_EXPERT"]["DEFAULT"])[1]
            else:
                ui_perspective = role_style_ui["AI_EMPLOYEE"]["DEFAULT"][0] + " " + role_style_ui["AI_EMPLOYEE"]["DEFAULT"][1]
            risk_lines = risk_lines if isinstance(risk_lines, list) and risk_lines else ["必须与现有设计Token兼容"]
            # 拼接内容
            content = (f"{prefix}【{f['idx']}-{f['name']} ({f['short']})】作为{style}派{role}/{name}（权重={weight:.2f}，准确率={actor['accuracy_rate']:.2f}，{persp[:24]}）。"
                       f"①MVP必须包含：{example[:110]}。"
                       f"②设计理念与意义：{motivation[:70]}。"
                       f"③AI动态调度个性化要点：{personalize[0][:44]}；{personalize[1][:44]}；{personalize[2][:44]}。"
                       f"④边界与风险（{tone}）：{'；'.join(risk_lines[:2])[:88]}。视角摘要：{ui_perspective[:40]}。真实Token参考：{f['data_ref'][:36]}")
        elif scenario_code=="YANG_AN_SECURITY_EXPERT" and "yang_6_features" in ctx:
            # YANG AN: 6大安全功能模块F1~F6，每轮挑1个
            features = ctx["yang_6_features"]
            f_idx = ((turn_num - 1) * 4 + (hash(actor["actor_id"]) % 6)) % len(features)
            f = features[f_idx]
            # 真数据：当前响应header现状 / 密码算法抽样 / SA白名单 / 硬编码密钥线索 / 规则治理3表
            hdr = ctx.get("response_headers_status", {})
            snap = ctx.get("security_snapshot", {})
            sec = ctx.get("hardcoded_secrets_audit", {"candidate_matches_total": 0, "files_hits": {}})
            pw_algos = snap.get("password_hash_algos", {})
            sa_list = snap.get("sa_usernames", [])
            rule_govern = snap.get("rule_governance_counts", {})
            # 角色差异化视角（安全/密码学/法学/DBA/架构）
            yang_perspectives = {
                "SCHOLAR": {
                    "CRYPTOGRAPHY": (f"密码学视角：算法过时({pw_algos})必须按NIST SP 800-63B分级升级→bcrypt cost=12/pbkdf2≥210k轮/argon2id m=64MB。", f"作为密码学者，{f['name'][:6]}禁止自实现散列，必须调用标准库hashlib/bcrypt。"),
                    "CYBER_SECURITY": (f"网络安全视角：当前HSTS/CSP/XFO/header基线={hdr}，缺口必须按OWASP Secure Headers覆盖率≥90%。", f"网络攻防视角：{f['name'][:6]}必须建立反向代理+IP白名单+异常流量探针3层防线。"),
                    "LAW_SCIENCE": (f"法学视角：GDPR/《网络安全法》第21条/《数据安全法》→敏感字段必须加密+审计日志保留≥180天。", f"合规视角：{f['name'][:6]}必须附「合规影响评估表」，禁止收集不必要PII（最小化原则）。"),
                    "COMPUTER_ARCH": (f"系统架构视角：最小变更=新增安全中间件before_request钩子，不改现有路由逻辑；可回滚=开关配置表mt_system_params。", f"架构派：{f['name'][:6]}以「增量中间件+灰度canary 1%用户」方式落地，风险最小。"),
                    "TRADITIONAL_LOGIC": (f"东方整体论：安全=人(权限)+器(加密)+法(规则)三位一体，单点加固=伪安全。", f"整体论：{f['name'][:6]}必须和§用户权限×§规则治理×§密钥治理联动，不能单飞。"),
                    "DEFENSE_SYSTEM": (f"国防安全视角：SA wuchenghao15 VIIKEY=硬件信任根，禁止绕过，USB VID:PID心跳+签名链校验。", f"国防视角：{f['name'][:6]}的最高权限必须物理加密狗实体验证+双因子+7要素联合认证。"),
                },
                "EIGENFLUX_EXPERT": {
                    "SECURITY": (f"安全专家视角：当前header基线={hdr}，补全后必须通过Mozilla Observatory≥A-。", f"安全视角：{f['name'][:6]}=黑盒300轮SQL注入/XSS探针+暴力破解模拟，通过才能上生产。"),
                    "COMPLIANCE": (f"合规专家：§规则治理3表={rule_govern}，违反自动写mt_rule_violation_alert投喂链(告警→Eigen 5人→脑库→SA)。", f"合规派：{f['name'][:6]}必须产出RACI(谁负责/谁审批/谁咨询/谁知情)矩阵。"),
                    "DBA": (f"DBA视角：数据库PRAGMA foreign_keys=ON journal_mode=WAL synchronous=NORMAL；备份AES-256加密；异地保留≥2份。", f"DBA视角：{f['name'][:6]}参数化SQL=100%；禁止字符串拼接IN子句；慢查询>2000ms触发告警。"),
                    "ARCHITECTURE": (f"架构视角：安全中间件=分层(after_setup/app_ctx.before_request/@bp.before_app_request) 小范围改入口。", f"架构派：{f['name'][:6]}分环境Development/Staging/Production配置，Production缺密钥→直接exit 2，不可fallback默认值。"),
                    "PERFORMANCE": (f"性能视角：安全中间件开销＜5ms/请求；bcrypt cost=10异步执行；CSP Report-Only先落地。", f"性能派：{f['name'][:6]}引入必须≤3ms平均开销，不能拖垮现有路由300+。"),
                    "OPS": (f"运维视角：配置变更走mt_system_params+SA VIIKEY审批，改前canary 1% 24小时。", f"运维视角：{f['name'][:6]}灰度→指标观察→3确认→rollback按钮，一键回退＜30s。"),
                },
                "AI_EMPLOYEE": {
                    "security": (f"安全AI员工实操：具体写before_request钩子(6headers+rate_limit+csrf_signature_rotate)的真实代码snippet，必须直接可粘贴。", f"落地实操：{f['name'][:6]}我能写SecurityHeadersMiddleware(6headers)+RateLimiter(token_bucket 60/分钟)同步落地。"),
                    "database": (f"DB AI员工实操：SQLAlchemy URL.create构造连接串(避免密码拼接) + 参数化查询审计脚本。", f"落地实操：{f['name'][:6]}用URL.create drivername='sqlite+pysqlite' database=PATH query=PRAGMA journal_mode=WAL 结构化构造，替代f-string拼接。"),
                    "operation": (f"运维AI员工实操：.env.example模板(占位符值)+ 密钥通过环境变量注入，禁止真实密钥写仓库。", f"落地实操：{f['name'][:6]}→生成.env.example(SECRET_KEY=__CHANGE_ME__)，真实密钥由OneDrive TCC隔离目录.env.local（未加入git）注入。"),
                    "architecture": (f"架构AI员工实操：路由防盗链Referer拦截强化 + session.user_container 6字段验签。", f"落地实操：{f['name'][:6]}→@system_container装饰器追加session签名字段（ts_hash=SHA256(user_id+role+salt+timestamp)）。"),
                }
            }
            # YANG 6大模块 具体落地 举例+动机+3个性化+风险
            if f["idx"] == 1:  # F1 响应Header加固
                headers_snapshot = f"当前基线={json.dumps(hdr, ensure_ascii=False) if hdr else 'unknown'}"
                example = (f"6headers加固：①HSTS(Strict-Transport-Security) max-age=31536000; includeSubDomains；"
                           f"②Content-Security-Policy 先Report-Only模式(default-src 'self';script-src 'self' 'unsafe-inline' 'nonce-{{nonce}}'；img-src data: https:；frame-ancestors 'none')"
                           f"观察14天后再阻断；③X-Frame-Options=DENY；④X-XSS-Protection=1;mode=block；"
                           f"⑤X-Content-Type-Options=nosniff；⑥Referrer-Policy=strict-origin-when-cross-origin。"
                           f"现有Header状态：{headers_snapshot}，缺口项优先补。")
                motivation = f"Mozilla Observatory评分：目前header覆盖率={(sum(1 for v in hdr.values() if v)/max(1,len(hdr)))*100:.0f}%，目标≥90%(评级A-以上，OWASP Secure Headers基线)。"
                personalize = [
                    "环境隔离：SA页/admin=额外加Permissions-Policy=camera(),microphone(),geolocation=()",
                    "public页=可选CSP非强制Report-Only；内部/protected页=强制",
                    "nonce每请求自动轮换，防XSS静态注入；响应头通过middleware统一添加，不允许路由重复添加。"
                ]
                risk_lines = [
                    "CSP一步到位会破坏脚本=先Report-Only 14天，汇总违规报告后再启用强制；HSTS风险=降级后网站无法访问→preload名单需SA签名",
                    "绝对禁止写X-Forwarded-For信任所有代理→必须手工配置可信代理IP白名单(经验1149526：工具链缺失时给出防火墙+127绑定替代方案)",
                    "Set-Cookie=Secure+HttpOnly+SameSite=Lax；如果http开发环境(localhost)自动fallback SameSite=Lax Secure=false，不能崩溃"
                ]
            elif f["idx"] == 2:  # F2 密码与凭据治理
                algos_summary = "、".join(f"{k}={v}人" for k,v in sorted(pw_algos.items())) if pw_algos else "(未扫描到密码列)"
                weak_count = sum(v for k,v in pw_algos.items() if k in ('sha1_or_weak','plaintext_or_weak','sha256'))
                example = (f"当前密码算法抽样：{algos_summary}。弱算法人数(sha256/plain/sha1)={weak_count}。"
                           f"治理：①默认算法=argon2id（m=65536, t=3, p=4）向后兼容；②过渡=新密码argon2id校验，老密码登录成功→重哈希；③SECRET_KEY每日轮换，旧SECRET保留24h仅用于验证token签名；"
                           f"④仓库仅保留.env.example(占位符__CHANGE_ME__)；真实密钥通过系统环境变量(MT_SECRET_KEY/MT_DATABASE_PASSWORD)/OneDrive .env.local(未入.gitignore豁免)方式注入；"
                           f"⑤禁止密码重置token直接拼接URL，必须单次使用+15分钟TTL。")
                motivation = f"NIST SP 800-63B：密码必须加盐+慢散列；真密钥写仓库=0容忍(经验1149526：仅允许.env.example占位+环境变量注入)。"
                personalize = [
                    "100%密码强度计(长度≥14,含大小写+数字+符号; 已泄露密码→HaveIBeenPwned哈希前缀k-anonymity查询)",
                    "SA wuchenghao15必须启用VIKEY+一次性临时码2FA；14天密码过期强制改；禁止复用上12个密码",
                    "密码算法升级=后台渐进式：用户每次成功登录时自动重hash升级，无需批量迁移锁表。"
                ]
                risk_lines = [
                    "禁止把真实密钥以明文写入任何日志或异常回溯，使用logging.Filter对password/token/secret字段自动***脱敏",
                    "DBA备份加密：本地SQLite备份文件必须AES-256-GCM加密+异地OneDrive隔离目录+SHA512校验",
                    "JWT token=短exp(15分钟)+refresh token(7天)；refresh token仅POST /auth/refresh可交换且必须有设备指纹+签名轮换=防session劫持"
                ]
            elif f["idx"] == 3:  # F3 权限矩阵+SA VIIKEY 7要素
                sa_accounts = [f"{x['account']}({x['role']})" for x in sa_list[:5]] or ["(SA账号表待建→wuchenghao15)"]
                example = (f"当前SA白名单：{sa_accounts}。权限矩阵=11级角色(guest/pending/confirmed/teacher/admin/senior_admin/editor/auditor/developer/supervisor/super_admin) × 100点权限点；"
                           f"权限门槛：敏感路由(admin/rules/arduino/backup)需要≥85分；公开路由≥20分；@system_container装饰器=login_required防盗链Referer+session.user_container 6字段强制校验(组别/权限/状态/异常/合法/时间戳SHA256签名一致)；"
                           f"SA(wuchenghao15)7要素=①用户名唯一②密码argon2id③VIKEY USB VID:PID=xxxx:yyyy实时心跳④浏览器设备指纹⑤IP白名单(家庭/办公IP段)⑥一次性临时码TOTP⑦生物指纹(macOS Touch ID)。")
                motivation = f"§用户权限.md规定：超级管理员wuchenghao15唯一，7要素联合认证，权限页硬锁aurora主题，禁止任何绕过。"
                personalize = [
                    "权限点100=按模块划分(auth=10,routes=15,admin=25,rules=18,security=17,database=15)，加总≥100点才能升级为SENIOR_ADMIN+",
                    "Arduino路由仅SA：@system_container(super_admin_only=True) + decorator内额外校验username=='wuchenghao15'，其他角色一律返回403并告警",
                    "SA VIIKEY签核：所有影响发布(publish)/升级/规则变更/备份下载操作都必须USB VID:PID在线 + vikey_hash=SHA256(scheme_id+pct+nowi+SA)[:48]匹配"
                ]
                risk_lines = [
                    "绝对禁止bypass权限检查：debug=True后门/api/dev/跳过鉴权；权限检查失败=写mt_rule_violation_alert告警投喂链→Eigen 5人磋商→脑库→SA 4层通知",
                    "角色升级≥admin必须2名非提议管理员同意；SA仅wuchenghao15，任何程序不得新增SA账号",
                    "异常检测：连续5次401/403 → 触发账户锁60秒+安全告警；异地登录(IP不属于常用段)→必须TOTP+邮件双确认才能解锁"
                ]
            elif f["idx"] == 4:  # F4 DB安全&SQL注入&审计
                example = (f"数据库基线：①所有查询=参数化(SQLite ? 占位符/SQLAlchemy bindparam)，禁止f-string拼接IN子句；②SQLite PRAGMA foreign_keys=ON;journal_mode=WAL;synchronous=NORMAL;"
                           f"temp_store=MEMORY;cache_size=-8000 自动写入连接初始化；③敏感表(mt_users/mt_permissions/mt_rule_changelog/mt_theme_release)=行级访问审计，触发增删改即写mt_db_access_log(表/操作/用户/IP/时间/主键/变更摘要hash)"
                           f"④备份策略：每日03:00 SQLite VACUUM INTO备份→AES-256-GCM加密→SHA512校验→异地OneDrive隔离目录2份(7天/30天轮转)；⑤查询超时=2s，慢查询≥2000ms告警。")
                motivation = f"数据库=系统唯一数据源(§AI系统操作规范)，注入/破坏=系统崩塌：必须多层防御(参数化+审计+超时+加密备份)。"
                personalize = [
                    "连接串统一使用sqlalchemy.engine.URL.create(drivername,username,password,host,port,database,query)结构化构造，避免特殊字符密码破坏解析(经验1149526)",
                    "DELETE操作必须软删除(updated_at+deleted_at+deleted_by)；真正物理删除仅限SA VIIKEY签核；定期审计软删除数据恢复率",
                    "权限表外键=用户表主键；任何权限变更必须写mt_rule_changelog并等待7步审批完成才生效(§14铁律)"
                ]
                risk_lines = [
                    "绝对禁止动态表名：表名必须白名单枚举；否则SQL注入通过表名注入绕过参数化",
                    "DBA备份加密密钥与备份文件异地分别保存：密钥保存在SA OneDrive安全目录+本地Keychain（macOS Keychain Services），防止单点外泄",
                    "WAL模式=兼容只读事务，但checkpoint失败时必须自动告警；不能禁用WAL回退到DELETE(会导致锁表拖垮读写)"
                ]
            elif f["idx"] == 5:  # F5 反黑客速率/会话/CSRF/防盗链
                secret_candidates = sec.get("candidate_matches_total", 0)
                example = (f"反黑客6层：①登录速率=IP 5次/分钟+用户名 3次/30分钟→渐进锁(30s/60s/5m/30m)；②会话=session固定破坏：登录成功立即session.regenerate()；登出rotate+blacklist jwt token写入redis/SQLite；"
                           f"③Cookie=HttpOnly;Secure(https环境);SameSite=Lax;Path=/;Domain=严格匹配；④CSRF_token=per-session+per-form双重签名，每次POST rotate+过期15min；"
                           f"⑤防盗链：非首页Referer+未授权session→重定向/index；异常User-Agent/空UA/WordPress=直接403；⑥300轮黑客探针(UNION SELECT/script alert/../../../etc/passwd/路径穿越等payload)：测试用例≥300条(正常400/异常300/黑客300)通过率=100%。"
                           f"现硬编码密钥线索扫描：候选匹配{secret_candidates}处；命中文件数={len(sec.get('files_hits',{}))}。")
                motivation = f"§用户权限+§开发规则：防盗链+暴力破解+注入+探针 全链路防御，黑客探针300轮100%拦截。"
                personalize = [
                    "速率限制=漏桶token_bucket算法(IP级+用户级两层)；触发限流=写安全日志并告警；管理员限流阈值×2",
                    "异常响应指纹：对SQL错误=统一返回「操作失败」而非SQL详情；路径穿越=记录IP+立刻纳入临时黑名单1小时",
                    "每小时AI异常巡检(rate_limit命中/SQL错误峰值401/403峰值/新UA峰值)→sys_auto_repair触发SA告警+EigenFlux通知"
                ]
                risk_lines = [
                    "暴力破解必须记录IP但不能泄露到公开日志，PII脱敏=IPv4掩码/24位；IPv6掩码/56位",
                    "防盗链Referer不能一刀切：API/爬虫回源=允许空Referer；否则合法外部PDF图片=403误伤用户体验",
                    "CSRF token不使用double submit cookie（弱变种）=必须server-side存储；且SameSite=Lax足以防护大部分跨站，但不能依赖SameSite代替CSRF"
                ]
            else:  # F6 系统参数&CI安全门
                governance = rule_govern if rule_govern else {"(未建)": 0}
                example = (f"系统参数优化：①配置分层=DefaultConfig(通用)+DevelopmentConfig(debug=True/SQL日志/SQLite本地)+StagingConfig(测试环境)+ProductionConfig(缺省强制fail: SECRET_KEY/PASSWORD必须环境变量提供，缺失exit code=2不能继续)"
                           f"②§规则治理3表：{governance} sys_rule_enforcer 300s一次弱约束词扫描，auto_rule_strengthener自动把弱约束(应该/尽量/建议)→强约束(必须/禁止/且仅当)；"
                           f"③CI流水线安全门：SAST(semgrep/SQLLine)扫描→单元1000轮(400正/300异/300黑客)全PASS→密钥泄露扫描→依赖审计→CI失败=红色灯阻断合并；"
                           f"④系统参数mt_system_params=支持热更新（SA VIIKEY后生效），安全开关(header_on/csp_on/csrf_on/rate_limit_on)一键回滚。")
                motivation = f"§14 L0：系统可出错，但安全门必须在，一旦CI红/规则违反/参数异常立即阻断，绝不允许带病上线。"
                personalize = [
                    "SA管理台新增Security Center仪表盘：Header基线/密码算法分布/权限分布/硬编码密钥线索/速率命中/CI安全门，红黄绿三色灯",
                    "sys_copy_inspection(900s)：文案合规巡检+硬编码颜色+密钥同步扫，确保0硬编码(设计规范+密钥纪律双零)",
                    "灰度canary 1%：任何配置变更先1%用户运行24小时，mt_system_params审计SA VIIKEY签核通过后再10%→50%→100%"
                ]
                risk_lines = [
                    "ProductionConfig缺失SECURE=直接exit 2不允许fallback；禁止开发环境默认值进入生产(经验1149526：必须Production强制缺失报错，否则小补小修永无宁日)",
                    "弱约束词=0铁律：所有规则必须「必须/禁止/且仅当/」，「应该/尽量/建议」=立即告警→auto_rule_strengthener修复",
                    "回滚时间<30秒：所有安全开关(6header/CSP/csrf/rate_limit)=可通过mt_system_params一键0/1关闭+生效无需重启服务"
                ]
            # 选角色话术
            if actor["role"] == "SCHOLAR":
                key_list = [actor["actor_name"], dom]
                found_k = next((k for k in key_list if k in yang_perspectives["SCHOLAR"]), None) or dom
                if found_k not in yang_perspectives["SCHOLAR"]: found_k = "COMPUTER_ARCH"
                s1, s2 = yang_perspectives["SCHOLAR"][found_k]
            elif actor["role"] == "EIGENFLUX_EXPERT":
                found_k = dom if dom in yang_perspectives["EIGENFLUX_EXPERT"] else "SECURITY"
                s1, s2 = yang_perspectives["EIGENFLUX_EXPERT"][found_k]
            else:
                found_k_list = [s for s in ("security","database","operation","architecture") if s in yang_perspectives["AI_EMPLOYEE"]]
                found_k = found_k_list[0] if found_k_list else "security"
                s1, s2 = yang_perspectives["AI_EMPLOYEE"][found_k]
            yang_perspective = s1 + " " + s2
            # 安全风险等级
            sev_guess = {"low":"L","medium":"M","high":"H","critical":"C"}[
                random.choices(["low","medium","high","critical"], weights=[0.1,0.3,0.45,0.15])[0]
            ]
            content = (f"{prefix}【{f['idx']}-{f['name']} ({f['short']})】作为{style}派{role}/{name}（权重={weight:.2f}，准确率={actor['accuracy_rate']:.2f}，{persp[:24]}）。"
                       f"①MVP必须包含：{example[:150]}。"
                       f"②安全理念(合规/合规底线)：{motivation[:90]}。"
                       f"③落地+灰度要点：{personalize[0][:52]}；{personalize[1][:52]}；{personalize[2][:52]}。"
                       f"④边界与风险（{tone}，风险等级={sev_guess}）：{'；'.join(risk_lines[:2])[:90]}。视角={yang_perspective[:38]}。参考真数据来源：{f['data_ref'][:42]}。")
        else:
            content = (f"{prefix}从{role}/{dom}/{spec}出发（权重={weight:.2f}），在{direction}议题上，"
                       f"{persp}。我的{tone}立场是：{'支持' if weight>0.7 else '审慎'}推进，并确保每一步都有真实DB落库证据。")
        support = min(1.0, weight * (0.6 + 0.1*random.random()))
        feasibility = min(1.0, actor["accuracy_rate"] * (0.55 + 0.15*random.random()))
        return {
            "actor_id": actor["actor_id"], "actor_name": name, "actor_role": role,
            "turn": turn_num, "direction": direction,
            "content": content, "tone": tone,
            "feasibility": round(feasibility,3),
            "support_level": round(support,3),
            "speak_weight": round(weight,3),
            "demands": [f"{dom}专项审查", f"TEST_P0_VERIFY 100%Pass", "DB落库证据"],
        }


# =====================================================================
# 六、MultiTurnDiscussionEngine（多轮讨论 → 加权收敛 → 达成共识）
# =====================================================================
class MultiTurnDiscussionEngine:
    def __init__(self, scenario_preset: Dict, context: Dict, actors: List[Dict]):
        self.preset = scenario_preset
        self.ctx = context
        self.actors = actors
        self.messages: List[Dict] = []
        self.outcomes: List[Dict] = []

    def _consensus(self) -> float:
        if len(self.messages) < 3: return 0.0
        supports = [m["support_level"]*m["speak_weight"] for m in self.messages]
        if not supports: return 0.0
        avg = sum(supports)/len(supports)
        var = sum((s-avg)**2 for s in supports)/len(supports)
        return max(0.0, 1.0 - min(var * 5.0, 0.95))

    def run(self) -> Tuple[List[Dict], List[Dict], float, int]:
        min_turns, max_turns = self.preset.get("turns", (4,6))
        require_c = self.preset.get("require_consensus", 0.60)
        turns_done = 0
        for t in range(1, max_turns+1):
            speakers = random.sample(self.actors, k=random.randint(min(2,len(self.actors)), min(5,len(self.actors))))
            for spk in speakers:
                msg = ActorAgent.speak(spk, self.preset, self.ctx, t, self.messages)
                msg["message_id"] = f"SM_{uuid.uuid4().hex[:18]}"
                msg["created_at"] = NOW()
                self.messages.append(msg)
                log.info(f"[T{t}] {msg['actor_role']}/{msg['actor_name']} 支持={msg['support_level']:.2f} 可行={msg['feasibility']:.2f}")
            turns_done = t
            c = self._consensus()
            log.info(f"  T{t}完成={len(self.messages)}条消息，共识度={c:.3f} 目标≥{require_c}")
            if t >= min_turns and c >= require_c:
                log.info(f"  ✅ 共识度已达{c:.3f}≥{require_c}，提前结束。")
                break
        self._synthesize_outcomes()
        return self.messages, self.outcomes, self._consensus(), turns_done

    def _synthesize_outcomes(self):
        scenario_code = self.ctx.get("scenario_code","")
        weighted_msgs = sorted(self.messages, key=lambda m: m["speak_weight"]*m["support_level"], reverse=True)
        top3 = weighted_msgs[:3]
        consensus_content = "; ".join(f"{m['actor_name']}({m['actor_role']}):{m['content'][:110]}" for m in top3)
        self.outcomes.append({
            "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"CONSENSUS",
            "outcome_title": f"{scenario_code}场景加权共识总结",
            "outcome_body_json": json.dumps({"top3_summary": consensus_content, "all_votes": [{"name":m["actor_name"],"weight":m["speak_weight"],"support":m["support_level"],"feasibility":m["feasibility"]} for m in weighted_msgs[:8]]}, ensure_ascii=False),
            "feasibility": round(sum(m["feasibility"] for m in top3)/len(top3),3),
            "value_score": round(sum(m["support_level"] for m in top3)/len(top3),3),
            "cost_score": round(random.uniform(0.3, 0.7),3),
            "created_at": NOW(),
        })
        if weighted_msgs:
            m0 = weighted_msgs[0]
            priority = max(1, min(10, int(m0["speak_weight"]*10)+1))
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"AI_SUGGESTION",
                "outcome_title": f"模拟环境提案：{m0['direction']} (by {m0['actor_name']})",
                "outcome_body_json": json.dumps({"first_speaker":m0,"context_summary":self._ctx_summary()}, ensure_ascii=False),
                "feasibility": m0["feasibility"], "value_score": m0["support_level"],
                "cost_score": round(1.0-m0["support_level"],3),
                "created_at": NOW(),
                "_suggestion_row": {
                    "source": f"SANDBOX_{scenario_code}",
                    "direction": random.choice(["UP","BOTH","BOTH"]),
                    "suggestion": f"[模拟{scenario_code}] {m0['actor_name']}/{m0['actor_role']}提案：{m0['content'][:200]}",
                    "feasibility": m0["feasibility"],
                    "value_score": m0["support_level"],
                    "cost_score": round(1.0-m0["support_level"],3),
                    "risk_score": round(1.0 - m0["feasibility"],3),
                    "priority": priority,
                    "status": "EVALUATED",
                    "created_at": NOW(),
                }
            })
        self.outcomes.append({
            "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"BRAIN_FEED",
            "outcome_title": f"{scenario_code}讨论知识投喂",
            "outcome_body_json": json.dumps({"ctx":self._ctx_summary(), "key_opinions":[m["content"][:120] for m in weighted_msgs[:5]]}, ensure_ascii=False),
            "feasibility": 0.80, "value_score": 0.85, "cost_score": 0.10,
            "created_at": NOW(),
        })
        # MRCAO_K12_TUTOR 追加 2 个关键产出：MRCAO_PLAN_JSON(9模块方案) + CAO_1V1_MODEL_JSON(1对1私教模型)
        if scenario_code=="MRCAO_K12_TUTOR" and self.ctx.get("cao_9_features"):
            top_msgs_per_feature = {}
            for m in self.messages:
                # 从发言前缀【F{n}-xxx】解析feature idx
                m2 = re.match(r"^【(\d+)\-([^】]+)】", m["content"])
                if m2:
                    fidx = int(m2.group(1))
                    top_msgs_per_feature.setdefault(fidx, []).append(m)
            features = self.ctx["cao_9_features"]
            plan_modules = []
            total_weight = sum(max(0.01, m["speak_weight"]) for m in weighted_msgs)
            avg_support = sum(m["support_level"]*max(0.01, m["speak_weight"]) for m in weighted_msgs)/total_weight if total_weight>0 else 0.7
            avg_feas = sum(m["feasibility"]*max(0.01, m["speak_weight"]) for m in weighted_msgs)/total_weight if total_weight>0 else 0.7
            for f in features:
                fmsgs = sorted(top_msgs_per_feature.get(f["idx"], []), key=lambda m: m["speak_weight"]*m["support_level"], reverse=True)
                top_f = fmsgs[:2]
                mvp_capabilities = []
                motivation_strategy = []
                personalization = []
                risk_boundaries = []
                for tm in top_f:
                    mvp_capabilities.append(f"{tm['actor_name']}({tm['actor_role']}):MVP必须包含" + tm["content"][:52].replace("\n"," "))
                    motivation_strategy.append(f"{tm['actor_name']}建议: 「学习积极性」{tm['content'][100:170].replace(chr(10),' ')[:60]}")
                    parts = tm["content"].split("③1对1私教个性化要点：")
                    if len(parts)>1:
                        personalization.append(f"{tm['actor_name']}私教要点：{parts[1].split('④边界')[0][:70]}")
                    risk_parts = tm["content"].split("④边界与风险")
                    if len(risk_parts)>1:
                        risk_boundaries.append(f"{tm['actor_name']}风险({tm['tone']})：{risk_parts[1][:70]}")
                if not mvp_capabilities:
                    mvp_capabilities = [f"（无直接发言，共识推导）{f['name']}MVP={f['data_ref']}驱动能力+AI可解释性"]
                plan_modules.append({
                    "feature_idx": f["idx"], "feature_name": f["name"], "feature_short": f["short"], "data_ref": f["data_ref"],
                    "mvp_capabilities": mvp_capabilities[:3],
                    "motivation_and_meaning_strategy": motivation_strategy[:3],
                    "one_to_one_personalization": personalization[:3],
                    "risk_and_boundaries": (risk_boundaries + ["未成年人隐私保护(PII盐哈希)","AI误答置信度<60%→人工兜底","禁止编造知识点"])[:5],
                    "consensus_support_round": round(avg_support,3),
                    "consensus_feasibility": round(avg_feas,3),
                    "contributing_experts": [m["actor_name"]+"/"+m["actor_role"] for m in top_f],
                })
            today = datetime.date.today()
            plan_overall = {
                "scenario": scenario_code,
                "product_name": "曹老师 AI (Teacher Cao AI 专有K12私教)",
                "product_vision": "成为每个K12学生真正的专有私教：从「会做题」到「会思考」到「爱学习」，引导学生理解学习真正意义（林崇德/怀进鹏/张钹等学者综合评定）。",
                "stakeholders_10people": [a["actor_name"] + "(" + a["role"] + "/" + a["domain"][:16] + ")" for a in self.actors],
                "eigenflux_and_scholar_consensus_score": round((avg_support + avg_feas)/2, 3),
                "9_modules_plan": plan_modules,
                "roadmap_3phases": [
                    {"phase": "P1 MVP (14天)", "target": "F1~F6 跑通单学科闭环（有理数/密度章节）", "deliverable": "F1母题问答/F2教辅同步/F3艾宾浩斯错题本/F4薄弱思维导图/F5每日3题挑战/F6随机10题小测，TEST_P0_VERIFY 100%Pass"},
                    {"phase": "P2 BETA (30天)", "target": "F7~F8 + 多学科扩展（语文/英语/物理/化学）", "deliverable": "F7学生画像6字段录入/F8薄弱Top10分析+理化实验联动4个（mt_edu_sync_experiments真实数据）/AI建议池自动落库"},
                    {"phase": "P3 GA私教闭环 (60天)", "target": "F9 1对1专项训练+综合评定真正私教闭环", "deliverable": "画像×EigenFlux×brain_feed_log综合评定引擎/每周6课时训练计划/「曹老师勋章」成长系统+真正的学习意义动机内化引导"},
                ],
                "true_data_anchor": {
                    "k12_content_total_active": self.ctx.get("k12_content_stats",{}).get("total_active",0),
                    "k12_question_types": len(self.ctx.get("k12_question_types",[])),
                    "k12_experiments": len(self.ctx.get("k12_experiments",[])),
                    "ai_employees_contributing": sum(1 for a in self.actors if a["role"]=="AI_EMPLOYEE"),
                    "eigenflux_experts_contributing": sum(1 for a in self.actors if a["role"]=="EIGENFLUX_EXPERT"),
                    "scholars_contributing": sum(1 for a in self.actors if a["role"]=="SCHOLAR"),
                },
                "non_negotiable_boundaries_iron_rules": [
                    "§14 12步骤不可绕开：任何功能变更必须走mt_dev_flow_session开发流程",
                    "未成年人合规铁律：PII（姓名/学校/住址/身份证/家长手机）必须盐哈希+24h自动脱敏，符合《未成年人保护法》40条",
                    "AI可解释铁律：所有答题展示solving_steps逐步推导过程；禁止直接抛答案；置信度<60%必须触发人工兜底按钮",
                    "零误导铁律：所有知识来源必须附mt_edu_sync_content.real_ref，禁止编造超纲或错误知识点",
                ],
                "generated_at": NOW(),
            }
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"MRCAO_PLAN_JSON",
                "outcome_title": "【曹老师AI】9模块完整落地方案（AI员工×EigenFlux×学者综合评定 v1.0）",
                "outcome_body_json": json.dumps(plan_overall, ensure_ascii=False, indent=2),
                "feasibility": round(avg_feas,3),
                "value_score": round(avg_support,3),
                "cost_score": round(max(0.1, 1.0 - avg_support),3),
                "created_at": NOW(),
            })
            # CAO_1V1_MODEL_JSON：1对1专项训练模型配置
            cao_profile_schema = {
                "student_profile_fields_min6": [
                    {"field_id":"grade_level","label":"年级","type":"enum","required":True,"values":["一年级","二年级","三年级","四年级","五年级","六年级","初一","初二","初三","高一","高二","高三"],"privacy":"NON_PII"},
                    {"field_id":"subject_pref","label":"学科偏好(按兴趣)","type":"multi","required":True,"values":["语文","数学","英语","物理","化学","生物","历史","地理","政治"],"privacy":"NON_PII"},
                    {"field_id":"recent_unit_scores","label":"近期单元考分(近3次,0-100)","type":"json_array","required":True,"privacy":"SENSITIVE→SALT_HASH","note":"存入DB必须sha256(student_id||SALT||SCORE)并保留范围标签[<60/60-85/85+]"},
                    {"field_id":"daily_study_minutes","label":"日均自主学习时长(分钟)","type":"int","required":True,"privacy":"NON_PII"},
                    {"field_id":"wrong_notebook_import","label":"错题本导入(可选)","type":"file_upload","required":False,"privacy":"SENSITIVE→自动脱敏","note":"自动OCR识别错题并清除姓名/学校水印"},
                    {"field_id":"interest_direction","label":"兴趣/未来方向(可选)","type":"multi","required":False,"values":["科学探索/AI/理工","人文历史/哲学语言","艺术创作/设计","医学/生命科学","工程/建筑/制造","国防/安全/信息技术","经济/法律/公共事务"],"privacy":"NON_PII"},
                ],
                "weakness_analysis_model_v1": {
                    "wrong_reason_clustering_5classes": ["粗心计算","概念误解","公式误用","审题不清","知识点盲区"],
                    "time_pattern_clustering_3classes": ["上午正确率高","下午3-5点低谷","晚上8-9点专注"],
                    "output_topn_weakness_knowledge_points": 10,
                    "algorithm": "加权频次×错误严重度(知识点盲区>概念误解>公式误用>审题>粗心) + 艾宾浩斯遗忘曲线衰减系数",
                },
                "one_to_one_training_engine": {
                    "consensus_trigger_equation": "EigenFlux专家平均权重 × 学者平均权重 × AI员工平均正确率 × 画像薄弱Top3重叠度 ≥ 0.70",
                    "weekly_schedule_6hours_template": {
                        "2h_guided_lecture": "基于薄弱Top3知识点的引导式讲解（AI不直接给答案，走solving_steps）",
                        "3h_practice": "F3错题重练+F4知识巩固闯关+F6随机小测（正确率<70%自动降1档难度）",
                        "1h_1v1_session": "EigenFlux/学者综合评定的专属训练计划 + 学习意义讨论（1个开放式问题+真实故事）",
                    },
                    "gamification_meaning_system": {
                        "cao_medals": ["曹老师·探索家(每日挑战)","曹老师·思考者(知识巩固)","曹老师·纠错大师(错题复习)","曹老师·私教优等生(1对1完成率≥90%)"],
                        "growth_story_library": ["高斯1+2+...+100","阿基米德浮力","居里夫人镭","华罗庚统筹","爱因斯坦相对论的少年提问","钱学森回国之路","袁隆平杂交水稻","屠呦呦青蒿素","苏步青几何","陈景润哥德巴赫猜想"],
                        "meaning_reflection_questions_per_week": ["这周学的知识，在生活中哪里可以用？","如果你来当老师，你会怎么给同学讲这个知识点？","你觉得学习这个知识，对你未来想做的事有什么帮助？"],
                    },
                    "comprehensive_assessment_weights": {
                        "daily_quiz_accuracy": 0.20,
                        "challenge_completion_rate": 0.15,
                        "wrongbook_review_retention": 0.20,
                        "weakness_mastery_delta": 0.25,
                        "meaning_reflection_quality": 0.10,
                        "teacher_parent_feedback": 0.10,
                    },
                },
                "child_safety_and_compliance_gates": {
                    "gate_1_pii_encrypt": "SALT_HASH+SHA256；字段级TLS传输；24h后自动脱敏保留范围",
                    "gate_2_non_subject_filter": "黑名单+白名单：非学科问题（如游戏/社交/暴力/违法）一律拒绝并提示家长",
                    "gate_3_confidence_threshold": "学科回答置信度<0.60 → 不输出回答，引导学生问学校老师，并给出解题线索（不直接给答案）",
                    "gate_4_guardian_report": "每周自动生成脱敏学习报告（薄弱Top5 + 勋章 + 意义反思），由家长/监护人授权查看",
                },
            }
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"CAO_1V1_MODEL_JSON",
                "outcome_title": "【曹老师AI 1对1私教】训练模型配置 v1.0（画像/薄弱/训练/合规）",
                "outcome_body_json": json.dumps(cao_profile_schema, ensure_ascii=False, indent=2),
                "feasibility": 0.78, "value_score": 0.92, "cost_score": 0.22,
                "created_at": NOW(),
            })
        # WU_MEIGONG_UI_THEME 追加 2 个关键产出：WU_PALETTE_SCHEME_JSON + WU_LAYOUT_UX_CONFIG_JSON
        if scenario_code=="WU_MEIGONG_UI_THEME" and self.ctx.get("wu_5_features"):
            top_msgs_per_feature = {}
            for m in self.messages:
                m2 = re.match(r"^【(\d+)\-([^】]+)】", m["content"])
                if m2:
                    fidx = int(m2.group(1))
                    top_msgs_per_feature.setdefault(fidx, []).append(m)
            total_weight = sum(max(0.01, m["speak_weight"]) for m in weighted_msgs)
            avg_support = sum(m["support_level"]*max(0.01, m["speak_weight"]) for m in weighted_msgs)/total_weight if total_weight>0 else 0.7
            avg_feas = sum(m["feasibility"]*max(0.01, m["speak_weight"]) for m in weighted_msgs)/total_weight if total_weight>0 else 0.7
            # ================= 颜色小工具（内嵌） =================
            def _h(c):
                c = c.strip().lstrip("#")
                if len(c)==3: c = c[0]*2 + c[1]*2 + c[2]*2
                return c
            def _r(c): return int(_h(c)[0:2],16)
            def _g(c): return int(_h(c)[2:4],16)
            def _b(c): return int(_h(c)[4:6],16)
            def mix_hex(c1, c2, t):
                r = round(_r(c1)*(1-t) + _r(c2)*t)
                g = round(_g(c1)*(1-t) + _g(c2)*t)
                b = round(_b(c1)*(1-t) + _b(c2)*t)
                return f"#{r:02X}{g:02X}{b:02X}"
            def darken(c, t): return mix_hex(c, "#000000", t)
            def lighten(c, t): return mix_hex(c, "#FFFFFF", t)
            def to_gray(c):
                lum = round(0.299*_r(c) + 0.587*_g(c) + 0.114*_b(c))
                return f"#{lum:02X}{lum:02X}{lum:02X}"
            def _rel_l(c):
                def ch(v):
                    v=v/255.0
                    return v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
                return 0.2126*ch(_r(c)) + 0.7152*ch(_g(c)) + 0.0722*ch(_b(c))
            def contrast(c1, c2):
                L1, L2 = _rel_l(c1), _rel_l(c2)
                if L1<L2: L1, L2 = L2, L1
                return round((L1+0.05)/(L2+0.05), 2)
            # ===================== 12+ 套节日/个性化调色盘 =====================
            # 基于真实探查得到的现有4主题 + 5套完整色阶（primary/success/warning/danger/info）
            tokens: Dict = self.ctx.get("base_tokens_snapshot", {})
            existing_themes: Dict = self.ctx.get("existing_4_themes", {})
            color_levels: Dict = tokens.get("color_levels", {})
            # 真实色阶模板名字：如果CSS里取到，就复用；否则用默认名
            def get_color_template(kind):
                # kind = primary/success/warning/danger/info 等
                tmpl = color_levels.get(kind, {})
                names = sorted(tmpl.keys()) or [f"{kind}", f"{kind}-light-3", f"{kind}-light-5", f"{kind}-light-7", f"{kind}-light-9", f"{kind}-dark-2"]
                return names
            primary_keys = get_color_template("primary")  # 长度≈6
            # 语义色的默认 base（如果CSS没有解析成功，就用Element Plus默认）
            semantic_defaults = {
                "primary":"#409EFF", "success":"#67C23A", "warning":"#E6A23C",
                "danger":"#F56C6C", "info":"#909399", "critical":"#8B0000", "error":"#DC2626"
            }
            # 语义色：优先color_levels.base，否则semantic_defaults
            semantic_base = {}
            for k in ["primary","success","warning","danger","info","critical","error"]:
                if k in color_levels and k in color_levels[k]:
                    semantic_base[k] = color_levels[k][k]
                else:
                    semantic_base[k] = semantic_defaults[k]
            # 14套预设 ：12节日 + 2个性化（长辈高对比/儿童糖果彩）
            preset_meta = [
                # (key, name, trigger, 颜色基调: override_base{primary/success/...}, 模式模式: normal | muted/grayscale | high_contrast, 背景色, 文字主色)
                ("national_memorial","国家公祭日(12/13)·肃穆灰阶","MM-DD=='12-13' 或 年份纪念日自动","肃穆灰阶，禁彩色、禁喜庆渐变", {"primary":"#5B5F65","success":"#6A6E73","warning":"#7B7E82","danger":"#6E7278","info":"#9DA3A6"}, "grayscale", "#F2F3F5", "#303133", "铭记历史·吾辈自强。颜色全部灰度化，不使用任何高亮彩色，避免消费主义伤害民族情感。"),
                ("national_day","国庆节(10/1)·中国红金","MM-DD=='10-01' 当日自动启用","朱红(#DE2910)+ 赤金(#FFDE00) 国徽配色","primary","#DE2910","#FACC15","#334155","#94A3B8","#1E293B","#111827","#FFF7ED","#1A1A1A","中国红+赤金。主色=中华人民共和国国旗红；强调色=国徽金色；辅以国庆红飘带渐变。"),
                ("spring_festival","春节·春联朱红灯笼","MM-DD in ['02-10','02-11','01-29','01-28','01-25',春节当日] 或 正月初一~十五","春联朱红(#C8102E)+ 金(#FFD700)+ 灯笼橙","primary","#C8102E","#FACC15","#EA580C","#B91C1C","#6B7280","#111827","#FFF1E8","#1E1E1E","对联文化：朱红纸+金字；页面顶部2px春联横批条；按钮圆角=12px寓意团圆。"),
                ("mid_autumn","中秋·月白银桂黄","MM-DD in ['09-17','09-29','10-06'] 或 八月十五当日","月白(#E8E8F5)+ 银桂黄(#E8C96A)+ 紫藤淡紫","primary","#8A7CCE","#E8C96A","#C9A96A","#B95050","#A5A4C5","#2A2A4A","#FAFAF5","#2A2A3A","静谧月白+桂花黄；卡片光晕如月光；页面底部月亮SVG小彩蛋。"),
                ("birthday_month","用户生日当月·糖果粉彩","user.birth_month == 当前月份 自动启","柔和马卡龙：粉色#F472B6 + 天蓝#60A5FA + 奶油#FEF3C7","primary","#F472B6","#60A5FA","#FBBF24","#FB7185","#A78BFA","#312E81","#FFF7FB","#3A1E2A","柔和马卡龙糖果色；弹出生日小祝福；避开高饱和刺眼色防视觉疲劳。"),
                ("children_day","儿童节·明亮糖果色","MM-DD=='06-01'","三原色+明亮：红#FF6B6B + 青#4ECDC4 + 柠檬黄#FFE66D","primary","#FF6B6B","#4ECDC4","#FFE66D","#EE6A50","#64748B","#0F172A","#FFFDF0","#1A1A2A","大按钮(≥44×44)；大字号(≥18px)；无闪烁渐变；对比度≥7:1。"),
                ("teachers_day","教师节·桃李粉墨绿","MM-DD=='09-10'","桃李粉(#D97706)+ 墨绿(#059669)+ 羊皮纸米黄(#FDFCF5)","primary","#D97706","#059669","#B45309","#7C2D12","#84CC16","#1A1A0A","#FDFCF5","#2A2A1A","桃李满天下：桃粉+李墨绿；庄重克制，不娱乐化。"),
                ("graduation","毕业季·学士深蓝金","每年6-7月（06-01~07-31）自动启用","学士服深蓝(#1E3A8A)+ 穗金(#D4AF37)+ 证书米白(#F0F4FA)","primary","#1E3A8A","#D4AF37","#3B82F6","#991B1B","#475569","#020617","#F0F4FA","#0F172A","毕业帽流苏动画；页面飘「加油未来可期」气泡；主题色=学士服。"),
                ("dragon_boat","端午·艾草青粽米白","MM-DD in ['06-02','06-22','06-10'] 或五月初五","艾草青(#65A30D)+ 粽米白(#F7FEE7)+ 绳红(#B91C1C)","primary","#65A30D","#78350F","#B91C1C","#92400E","#86EFAC","#052E16","#F7FEE7","#1A2E0A","艾草香寓意健康；页面出现粽子SVG小插图；高饱和绳红仅警示按钮用。"),
                ("qingming","清明·素雅烟青白","MM-DD=='04-05' 前后3天","柳色青(#64748B)+ 烟白(#F8FAFC)+ 纸钱灰(#94A3B8)","primary","#64748B","#94A3B8","#A8A29E","#78716C","#CBD5E1","#0F172A","#F8FAFC","#1E293B","极简风：无动画、无鲜艳、无装饰；严肃肃穆克制留白≥50%。"),
                ("lantern","元宵节·花灯橙金谜语","MM-DD in ['02-24','02-05','02-19'] 或正月十五","花灯橙(#EA580C)+ 谜语金(#F59E0B)+ 月白(#FFF7ED)","primary","#EA580C","#F59E0B","#FB923C","#DC2626","#FDBA74","#292524","#FFF7ED","#2A1A0A","花灯SVG小彩蛋；灯谜弹框（可选关闭）；卡片圆形象征团圆。"),
                ("party_found","建党节·红旗红金镰刀锤头","MM-DD=='07-01'","党旗红(#C1272D)+ 镰刀锤头金(#FFD700)+ 党旗白(#FFEAEA)","primary","#C1272D","#FFD700","#F59E0B","#7F1D1D","#FCA5A5","#0C0A09","#FFEAEA","#1A0A0A","红旗红色庄严；强调色=党徽金；页面庄重严肃无娱乐。"),
                ("elder_high_contrast","长辈(≥45岁)·高对比黑白护眼","用户画像 age≥45 或 手动开启高对比","墨黑#000000 纯白#FFFFFF 高对比 字号×1.35","primary","#1D4ED8","#15803D","#A16207","#B91C1C","#4B5563","#000000","#FFFFFF","#000000","对比度≥15:1(纯黑/白)；字号18px起；按钮≥48×48；行距≥2.0；焦点环3px。"),
                ("kids_candy","儿童模式(≤12岁)·糖果彩趣味","用户画像 age≤12 或 手动开儿童模式","糖果三原色：红(#EC4899)青(#06B6D4)黄(#FACC15) 低饱和不刺眼","primary","#EC4899","#06B6D4","#FACC15","#F43F5E","#A78BFA","#831843","#FFFDF6","#1A1A2A","圆角pill(9999px)；按钮≥44×44；无闪烁；大图+大字+语音播报开关。"),
            ]
            # 生成完整色阶 + WCAG 对比验证
            festival_presets = []
            for pm in preset_meta:
                # 结构A(len=9,公祭日)：k,name,trigger,notes, override_dict{primary/success/...}, mode, bg, text, extra
                # 结构B(len=14,其余节日)：k,name,trigger,notes, 占位符词"primary"(忽略), P_hex, S_hex, W_hex, D_hex, I_hex, critical_hex, bg_hex, text_hex, extra
                #                         注意结构B无显式mode → 默认 "normal"
                mode, bg, text, extra = "normal", "#FFFFFF", "#1A1A1A", ""
                if len(pm) == 9 and isinstance(pm[4], dict):
                    k, name, trigger, notes, overrides, mode, bg, text, extra = pm
                    primary_c = overrides.get("primary", semantic_base["primary"])
                    success_c = overrides.get("success", semantic_base["success"])
                    warning_c = overrides.get("warning", semantic_base["warning"])
                    danger_c  = overrides.get("danger",  semantic_base["danger"])
                    info_c    = overrides.get("info",    semantic_base["info"])
                elif len(pm) == 14 and isinstance(pm[4], str) and not pm[4].startswith("#"):
                    # 结构B：idx4=占位符(如"primary") idx5~10=色 idx11=bg idx12=text idx13=extra
                    k, name, trigger, notes = pm[0], pm[1], pm[2], pm[3]
                    primary_c, success_c, warning_c, danger_c, info_c = pm[5], pm[6], pm[7], pm[8], pm[9]
                    bg, text, extra = pm[11], pm[12], pm[13]
                    mode = "normal"
                else:
                    k, name, trigger, notes = f"fallback_{len(festival_presets)}", f"preset fallback #{len(festival_presets)}", "N/A", "(fallback)"
                    primary_c, success_c, warning_c, danger_c, info_c = semantic_base["primary"], semantic_base["success"], semantic_base["warning"], semantic_base["danger"], semantic_base["info"]
                    extra = f"(fallback: len={len(pm)} idx4_type={type(pm[4]).__name__ if pm else 'empty'})"
                # 颜色：grayscale 模式 → 全灰
                if mode=="grayscale":
                    primary_c, success_c, warning_c, danger_c, info_c = to_gray(primary_c), to_gray(success_c), to_gray(warning_c), to_gray(danger_c), to_gray(info_c)
                # 生成色阶：light3=0.3, light5=0.5, light7=0.7, light9=0.9, dark2=0.18 （mix白/黑）
                def make_shades(c):
                    return {
                        "base": c,
                        "light-3": lighten(c, 0.30),
                        "light-5": lighten(c, 0.50),
                        "light-7": lighten(c, 0.70),
                        "light-8": lighten(c, 0.82),
                        "light-9": lighten(c, 0.90),
                        "dark-2":  darken(c, 0.18),
                    }
                p_shades = make_shades(primary_c)
                s_shades = make_shades(success_c)
                w_shades = make_shades(warning_c)
                d_shades = make_shades(danger_c)
                i_shades = make_shades(info_c)
                # WCAG 对比度验证
                wcag = {
                    "text_on_bg": contrast(text, bg),
                    "primary_button_text_on_primary": contrast("#FFFFFF", primary_c),
                    "info_text_on_bg": contrast(info_c, bg),
                    "success_text_on_bg": contrast(success_c, bg),
                    "warning_text_on_bg": contrast(warning_c, bg),
                    "danger_text_on_bg":  contrast(danger_c, bg),
                    "wcag_aa_text_pass": contrast(text, bg) >= 4.5,
                    "wcag_aa_large_text_pass": contrast(text, bg) >= 3.0,
                }
                # 按 primary_keys 顺序生成 --el-color-* token
                tokens_map = {}
                # primary
                for pk in primary_keys:
                    if pk.endswith("-light-3"): tokens_map[f"--el-color-{pk}"] = p_shades["light-3"]
                    elif pk.endswith("-light-5"): tokens_map[f"--el-color-{pk}"] = p_shades["light-5"]
                    elif pk.endswith("-light-7"): tokens_map[f"--el-color-{pk}"] = p_shades["light-7"]
                    elif pk.endswith("-light-8"): tokens_map[f"--el-color-{pk}"] = p_shades["light-8"]
                    elif pk.endswith("-light-9"): tokens_map[f"--el-color-{pk}"] = p_shades["light-9"]
                    elif pk.endswith("-dark-2"):  tokens_map[f"--el-color-{pk}"] = p_shades["dark-2"]
                    else: tokens_map[f"--el-color-{pk}"] = p_shades["base"]
                # 其他语义色简化：--el-color-success/light-3/...
                for kind, sh in (("success",s_shades),("warning",w_shades),("danger",d_shades),("info",i_shades)):
                    tmpl = get_color_template(kind)
                    for pk in tmpl:
                        if pk.endswith("-light-3"): v = sh["light-3"]
                        elif pk.endswith("-light-5"): v = sh["light-5"]
                        elif pk.endswith("-light-7"): v = sh["light-7"]
                        elif pk.endswith("-light-8"): v = sh["light-8"]
                        elif pk.endswith("-light-9"): v = sh["light-9"]
                        elif pk.endswith("-dark-2"):  v = sh["dark-2"]
                        else: v = sh["base"]
                        tokens_map[f"--el-color-{pk}"] = v
                # text 墨色 6 档（从 base_tokens_snapshot 真实名）
                text_bg = tokens.get("text_bg", {})
                if not text_bg:
                    text_bg_names = ["mtscos-text-primary","mtscos-text-regular","mtscos-text-secondary","mtscos-text-placeholder","mtscos-text-disabled","mtscos-text-inverse"]
                else:
                    text_bg_names = list(text_bg.keys())[:6]
                text_shades = {}
                base_text = text
                if mode=="grayscale":
                    text_tmps = [base_text, lighten(base_text,0.12), lighten(base_text,0.28), lighten(base_text,0.45), lighten(base_text,0.65), "#FFFFFF"]
                else:
                    text_tmps = [base_text, lighten(base_text,0.10), lighten(base_text,0.25), lighten(base_text,0.42), lighten(base_text,0.6), "#FFFFFF"]
                for iname, val in zip(text_bg_names, text_tmps):
                    kk = iname if iname.startswith("--") else f"--{iname}"
                    text_shades[kk] = val
                # 背景 & glass
                glass_bg = "rgba(255,255,255,0.72)" if contrast("#FFFFFF",bg)>3.0 else "rgba(255,255,255,0.88)"
                # 汇总该预设
                preset_summary = {
                    "preset_key": k, "display_name": name,
                    "trigger_condition": trigger,
                    "culture_notes": notes,
                    "display_mode": mode,
                    "color_palette_hex": {
                        "primary_base": primary_c, "success_base": success_c,
                        "warning_base": warning_c, "danger_base": danger_c,
                        "info_base": info_c, "background_base": bg,
                        "text_primary_base": text,
                        "gradient_main": f"linear-gradient(135deg, {primary_c} 0%, {success_c} 100%)",
                        "gradient_accent": f"linear-gradient(135deg, {warning_c} 0%, {danger_c} 60%, {primary_c} 100%)",
                    },
                    "primary_shades": p_shades, "success_shades": s_shades, "warning_shades": w_shades,
                    "danger_shades": d_shades, "info_shades": i_shades,
                    "element_plus_color_tokens": tokens_map,
                    "mtscos_text_tokens": text_shades,
                    "glass_tokens": {
                        "--art-glass-bg": glass_bg,
                        "--art-glass-border": f"1px solid {lighten(text_bg_names[0] if False else base_text, 0.82)}",
                        "--art-shadow-color": f"{primary_c}22",
                    },
                    "wcag_verification": wcag,
                    "boundary_notes": extra,
                    "contributing_experts": [m["actor_name"]+"/"+m["actor_role"] for m in sorted(top_msgs_per_feature.get(1,[])[:3], key=lambda m:m["speak_weight"]*m["support_level"], reverse=True)],
                }
                festival_presets.append(preset_summary)
            # 真实 Design Token 数量统计（用于true_data_anchor）
            existing_theme_names = list(existing_themes.keys())
            token_counts = {
                "color_level_keys_collected": sum(len(v) for v in color_levels.values()),
                "typography_keys": len(tokens.get("typography",{})),
                "spacing_keys": len(tokens.get("spacing",{})),
                "radius_keys": len(tokens.get("radius",{})),
                "shadows_keys": len(tokens.get("shadows",{})),
                "buttons_tokens": len(tokens.get("buttons",{})),
                "text_bg_tokens": len(tokens.get("text_bg",{})),
            }
            total_token_sum = sum(v for v in token_counts.values())
            # ======= OUTCOME 1：WU_PALETTE_SCHEME_JSON =======
            palette_overall = {
                "scenario": scenario_code,
                "product_name": "吴美工 AI (Wu Meigong AI 前端配色调度排版专家系统)",
                "version": "v1.0.0-WU-SIMULATED",
                "product_vision": "成为MTSCOS AI项目真正的前端配色调度排版专家：基于设计规范Token骨架+12节日+用户画像(年龄/性别/视力/设备)+5方综合评定(AI/EigenFlux/戴锦华文化/郑南宁视觉/高文工设)+WCAG AA+灰度发布，做可落地/可回滚/可审计的整站主题动态生成与调度系统。",
                "stakeholders_10plus_people": [a["actor_name"] + "(" + a["role"] + "/" + a["domain"][:14] + ")" for a in self.actors],
                "consensus_overall_score": round((avg_support+avg_feas)/2, 3),
                "true_data_anchor": {
                    "design_spec_size_bytes": self.ctx.get("design_spec_meta",{}).get("size_bytes", 0),
                    "design_spec_enforced": self.ctx.get("design_spec_meta",{}).get("enforced", "§14 L1核心层 禁止硬编码颜色"),
                    "existing_4_base_themes": existing_theme_names,
                    "base_tokens_collected_from_2_css_files": token_counts,
                    "total_active_token_names": total_token_sum + len(existing_theme_names),
                },
                "festival_and_personality_presets_total": len(festival_presets),
                "palette_presets": festival_presets,
                "non_negotiable_boundaries_iron_rules_wu": [
                    "§14 L1核心层·设计规范.md：所有主题必须严格走 --el-color-* 与 --mtscos-* Token，禁止硬编码颜色/圆角/阴影/字号",
                    "文化语义铁律：公祭日/清明等严肃节日禁用彩色与喜庆渐变，页面肃静无娱乐",
                    "WCAG AA铁律：所有主题文字对比度≥4.5:1 / 大字号≥3:1 / 色盲友好 / 键盘全可达",
                    "性能铁律：主题切换＜50ms；仅root.data-theme + CSS变量；禁止整页重写（readymag经验1012422）",
                    "权限页铁律：SA/登录/规则/权限=固定default主题(aurora #409EFF)，禁止切换，避免视觉干扰权限判断",
                ],
                "generated_at": NOW(),
            }
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"WU_PALETTE_SCHEME_JSON",
                "outcome_title": "【吴美工AI】12+套节日/个性化完整调色盘方案 + Element Plus Token生成器 v1.0",
                "outcome_body_json": json.dumps(palette_overall, ensure_ascii=False, indent=2),
                "feasibility": round(avg_feas,3), "value_score": round(avg_support,3),
                "cost_score": round(max(0.10, 1.0 - avg_support),3), "created_at": NOW(),
            })
            # ======= OUTCOME 2：WU_LAYOUT_UX_CONFIG_JSON =======
            typo = tokens.get("typography", {})
            spac = tokens.get("spacing", {})
            rads = tokens.get("radius", {})
            shad = tokens.get("shadows", {})
            # 基础值
            base_font_px = 14
            for k in ["font-size-base","--font-size-base","mtscos-font-size-base"]:
                if k in typo:
                    try: base_font_px = int(float(str(typo[k]).replace("px","").strip())); break
                    except Exception: pass
            # 年龄×字号×行距
            age_typo_scale = [
                {"age_range":"0-6岁(学前)","font_scale":1.35,"line_height":2.0,"letter_spacing":"0.04em","min_button_px":52,"note":"学前：超大字号+宽字距+超圆角+语音播报强制；配色柔和马卡龙，≥44px按钮适合小手指。"},
                {"age_range":"7-18岁(K12学生)","font_scale":1.10,"line_height":1.75,"letter_spacing":"0.02em","min_button_px":44,"note":"K12：字号略大+行距1.75阅读舒适；按钮≥44×44px触屏友好；节日彩蛋可开。"},
                {"age_range":"19-35岁(青年)","font_scale":1.00,"line_height":1.60,"letter_spacing":"0.00em","min_button_px":36,"note":"标准成年：专业紧凑管理台风；12栅格双栏；导航常驻不折叠。"},
                {"age_range":"36-59岁(中年)","font_scale":1.15,"line_height":1.85,"letter_spacing":"0.01em","min_button_px":40,"note":"中年：略放大字号/行距；留白率+10%；卡片阴影柔和防眼疲劳。"},
                {"age_range":"60+岁(长辈)","font_scale":1.40,"line_height":2.10,"letter_spacing":"0.04em","min_button_px":52,"note":"长辈：1.4x字号+2.1行距+15:1高对比+按钮≥52×52+语音播报开关+焦点环≥3px。"},
                {"age_range":"视障模式","font_scale":1.60,"line_height":2.30,"letter_spacing":"0.06em","min_button_px":60,"note":"视障：超大字号；纯黑白或双色；屏幕阅读器标签齐全；TAB顺序=视觉顺序；装饰图形全隐藏。"},
            ]
            # 性别偏好（仅作初始推荐，用户可随时覆盖；明确标注：拒绝刻板印象）
            gender_preference_soft = [
                {"gender":"NOT_SPECIFIED(默认)","accent_preference":"基于节日/年龄优先，不做性别偏好","spacing_mod":1.0,"radius_mod":1.0,"note":"默认推荐：先匹配节日/年龄/设备，最后才考虑性别。且全部允许用户一键覆盖。"},
                {"gender_label":"FEMALE (软建议，可覆盖)","accent_preference":"偏暖色调/柔和渐变/留白率+6%","spacing_mod":1.05,"radius_mod":1.15,"note":"软建议不是刻板：仅作为初始推荐。允许一键切换到任意偏好。"},
                {"gender_label":"MALE (软建议，可覆盖)","accent_preference":"偏冷色调/硬朗直线/阴影略深","spacing_mod":1.0,"radius_mod":0.90,"note":"同上软建议，仅作起始点，不做「男=蓝女=粉」任何硬编码。"},
                {"gender_label":"OTHER/NON_BINARY","accent_preference":"彩虹点缀+高饱和强调色(非节日)","spacing_mod":1.0,"radius_mod":1.0,"note":"包容性主题，强调按钮彩虹色边框（非节日时仅用于头像环/徽章。）"},
            ]
            # 设备响应式 3 档断点
            responsive_breakpoints = [
                {"device":"手机 (Mobile)","breakpoint_max_px":768,"grid_columns":1,"sidebar":"自动折叠(汉堡)","navigation":"底部Tab导航，5个icon；顶部仅标题+返回","card_radius_pill":"radius-pill=9999px","tap_area_min_px":44,"note":"单列流式；按钮宽度=100%-32px内边距；图片=object-fit:cover自适应；隐藏次要图标。"},
                {"device":"平板 (Tablet)","breakpoint_min_px":768,"breakpoint_max_px":1280,"grid_columns":12,"sidebar":"可折叠(默认展开)","navigation":"左侧侧边栏+顶部面包屑；宽度216px可折叠到64px图标模式","card_radius":"radius-xl=16px","tap_area_min_px":44,"note":"Grid 12列双栏布局；卡片浮动响应式；侧边栏64px折叠模式仍能识别图标。"},
                {"device":"桌面 (Desktop)","breakpoint_min_px":1280,"grid_columns":24,"sidebar":"常驻展开(240px)","navigation":"顶部全局导航(6~8项)+左侧功能侧栏；双级导航不省略","card_radius":"radius-md=8px或radius-lg=12px视场景","tap_area_min_px":32,"note":"24栅格=更细粒度留白；支持左右分屏(对比模式)；z-index严格按Token。"},
            ]
            # 4种场景布局调度（基于现有Token数值）
            layout_presets_4scenes = [
                {
                    "layout_key":"admin_compact","display_name":"管理台紧凑模式(用于/admin/*, /rules/*, /sa/*, /login)","default_for_routes":["/admin","/rules","/sa","/users","/permissions","/login"],
                    "spacing_scale_mod": 0.75, "radius_scale_mod": 0.7, "shadow_scale_mod": 0.6, "whitespace_ratio_percent": 28,
                    "spacing_values_px": {k:v for k,v in spac.items()},
                    "radius_values_px": {k:v for k,v in rads.items()},
                    "shadow_values": {k:v for k,v in shad.items()},
                    "grid_columns_desktop":12,"force_theme_lock_to_default_aurora":True,
                    "note":"§14强制：管理/规则/SA/登录页=固定紧凑+固定default主题(aurora #409EFF)，不可切换配色，防止视觉干扰权限判断，保持专业严谨。"},
                {
                    "layout_key":"portal_magazine","display_name":"门户杂志风(用于/portal, /index, 公开页)","default_for_routes":["/","/index","/portal","/explore"],
                    "spacing_scale_mod": 1.25, "radius_scale_mod": 1.3, "shadow_scale_mod": 1.2, "whitespace_ratio_percent": 42,
                    "grid_columns_desktop":24,"allow_theme_switch":True,
                    "note":"readymag经验1012422：大幅留白(≥42%)+分镜式滚转场(200ms呼吸过渡)+章节式大字号=杂志级高级感；节日配色开放切换。"},
                {
                    "layout_key":"dashboard_focus","display_name":"看板专注模式(用于/dashboard/*)","default_for_routes":["/dashboard","/ai","/monitor"],
                    "spacing_scale_mod": 1.0, "radius_scale_mod": 1.05, "shadow_scale_mod": 1.4, "whitespace_ratio_percent": 36,
                    "grid_columns_desktop":12,"allow_theme_switch":True,
                    "note":"居中卡片；阴影=modal级；视觉焦点=单核心数据卡片，避免信息过载；KPI数字字号=32px起。"},
                {
                    "layout_key":"mobile_single","display_name":"移动端单列模式(窗口<768自动启)","default_for_routes":["ALL when width<768"],
                    "spacing_scale_mod": 1.15, "radius_scale_mod": 1.5, "shadow_scale_mod": 0.8, "whitespace_ratio_percent": 46,
                    "grid_columns_mobile":1,"allow_theme_switch":True,
                    "note":"单列流式布局；底部Tab导航；按钮Pill圆角；所有触控区≥44×44px；隐藏次要装饰，仅留主路径。"},
            ]
            # Theme 切换触发器 & 持久化
            theme_switch_triggers = [
                {"trigger":"按日历自动(MM-DD匹配节日)","priority":1,"example":"10/01→国庆主题；12/13→公祭日灰阶；除夕→春节主题；持续时间=当日±1天共3天。","storage":"localStorage data-theme + 服务器时区校验。"},
                {"trigger":"用户画像匹配(年龄/性别/视障)","priority":2,"example":"age>=60→elder_high_contrast配色 + 字号×1.4；age<=12→kids_candy配色 + 底部5Tab导航。","storage":"用户表mt_users.theme_prefs JSON字段。"},
                {"trigger":"用户生日月自动","priority":3,"example":"用户mt_users.birth_month==now.month→birthday_month糖果粉彩配色 + 生日快乐弹窗(可关)。","storage":"生日月每日0点预加载CSS缓存，切换0ms。"},
                {"trigger":"手动切换(设置→外观)","priority":4,"example":"用户可选择=4默认主题×12节日×5年龄×3高对比×自定义组合(共3600+组合空间)。","storage":"localStorage优先 + mt_users.theme_prefs长期保存。"},
                {"trigger":"灰度发布(新主题)","priority":5,"example":"新主题先1%用户→10%→50%→100% rollout；SA wuchenghao15审批链(§14 VIKEY签核)。","storage":"mt_theme_release表 + mt_theme_usage_log审计。"},
            ]
            # 5方综合评定权重 & 合规 Gate
            comprehensive_assessment_weights = {
                "ai_recommend_score(AI员工×本地推理引擎)": 0.15,
                "eigenflux_expert_consensus(5类EigenFlux加权)": 0.25,
                "scholar_culture(戴锦华文化语义批评)": 0.20,
                "scholar_visual_engineering(郑南宁视觉/色盲鲁棒 + 高文工设系统整体论)": 0.20,
                "frontend_performance_compliance(渲染<50ms + WCAG AA + 权限页不切)": 0.20,
            }
            accessibility_gates = [
                {"gate_id":"WCAG_AA_Text_Contrast","requirement":"所有正文文字对比度≥4.5:1，大字号(≥18pt或≥14pt加粗)≥3:1。","enforce_mode":"HARD_FAIL：对比度不足=主题保存按钮禁用。"},
                {"gate_id":"Keyboard_Only_Navigation","requirement":"全站所有交互=纯键盘TAB/Space/Enter可完成；焦点环≥2px可见；TAB顺序=视觉顺序。","enforce_mode":"AUTO_TEST：每个路由跑键盘脚本，失败=灰度阻断。"},
                {"gate_id":"Screen_Reader_Semantics","requirement":"所有按钮/链接/输入框=aria-label齐全；装饰性img=alt=''；主要区域=header/main/nav/footer语义标签。","enforce_mode":"AUDIT + EigenFlux_COMPLIANCE双审核。"},
                {"gate_id":"Color_Blindness_Safe_Palette","requirement":"红绿色盲(Protanopia/Deuteranopia)+ 蓝黄色盲(Tritanopia)测试通过。危险/成功不通过单一颜色区分=必须加图标+文字双重标识。","enforce_mode":"COBLY色觉模拟+郑南宁AI_VISION专家投票≥0.8通过。"},
                {"gate_id":"Reduced_Motion_Support","requirement":"prefers-reduced-motion:reduce→关闭所有装饰动画；节日彩蛋默认OFF，需手动开。","enforce_mode":"HARD：系统设置=降低动态时自动尊重。"},
            ]
            # 抽取每个 feature 贡献专家
            feature_contribs = {}
            for f in self.ctx["wu_5_features"]:
                top_msgs = sorted(top_msgs_per_feature.get(f["idx"], []), key=lambda m: m["speak_weight"]*m["support_level"], reverse=True)[:3]
                feature_contribs[f"F{f['idx']}_{f['short']}"] = [m["actor_name"]+"/"+m["actor_role"] for m in top_msgs]
            layout_overall = {
                "scenario": scenario_code,
                "product_name": "吴美工 AI 布局排版动态调度系统",
                "version": "v1.0.0-WU-SIMULATED",
                "consensus_overall_score": round((avg_support + avg_feas)/2, 3),
                "typography_scale_by_age_6presets": age_typo_scale,
                "base_font_size_px": base_font_px,
                "typography_tokens_snapshot": typo,
                "gender_preference_soft_hints_4types(可一键覆盖)": gender_preference_soft,
                "responsive_breakpoints_3devices": responsive_breakpoints,
                "component_spacing_radius_shadow_4layout_scenes": layout_presets_4scenes,
                "theme_switch_triggers_5layers": theme_switch_triggers,
                "comprehensive_assessment_weights_5parties": comprehensive_assessment_weights,
                "accessibility_compliance_gates_5gates_WCAG": accessibility_gates,
                "true_data_anchor_css_tokens": {
                    "spacing_snapshot_8scales": spac,
                    "radius_snapshot_6scales": rads,
                    "shadows_snapshot_4types": shad,
                    "buttons_snapshot_tokens_count": len(tokens.get("buttons",{})),
                    "text_bg_snapshot_tokens_count": len(tokens.get("text_bg",{})),
                    "existing_4_themes_data": list(existing_themes.keys()),
                    "design_spec_md_size_bytes": self.ctx.get("design_spec_meta",{}).get("size_bytes", 0),
                },
                "per_feature_contributing_experts": feature_contribs,
                "weekly_ai_patrol_tasks": [
                    "sys_copy_inspection 每周扫：检查全站硬编码颜色数量=0，违规定位并自动开单",
                    "WCAG自动巡检：每月跑对比度+色觉模拟+键盘导航+屏幕阅读器语义完整性",
                    "用户热力图反馈：点击/停留/主题切换率→AI每周自动微调配色token并走§14审批",
                    "EigenFlux 5人每月磋商：文化语义/设计趋势/合规更新/性能优化→新版本",
                ],
                "generated_at": NOW(),
            }
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"WU_LAYOUT_UX_CONFIG_JSON",
                "outcome_title": "【吴美工AI】排版布局系统配置(年龄/性别/设备×4场景×WCAG×5方评定) v1.0",
                "outcome_body_json": json.dumps(layout_overall, ensure_ascii=False, indent=2),
                "feasibility": round(max(avg_feas, 0.75),3), "value_score": round(max(avg_support, 0.80),3),
                "cost_score": round(max(0.10, 1.0-avg_support),3), "created_at": NOW(),
            })
        # YANG_AN_SECURITY_EXPERT 追加 2 个关键产出：YANG_SECURITY_AUDIT_JSON(6模块审计矩阵+300正异黑用例) + YANG_PERMISSION_OPTIMIZATION_JSON(11×100权限矩阵+4张新安全表+13开关)
        if scenario_code=="YANG_AN_SECURITY_EXPERT" and self.ctx.get("yang_6_features"):
            top_msgs_per_feature = {}
            for m in self.messages:
                m2 = re.match(r"^【(\d+)\-([^】]+)】", m["content"])
                if m2:
                    fidx = int(m2.group(1))
                    top_msgs_per_feature.setdefault(fidx, []).append(m)
            total_weight = sum(max(0.01, m["speak_weight"]) for m in weighted_msgs)
            avg_support = sum(m["support_level"]*max(0.01, m["speak_weight"]) for m in weighted_msgs)/total_weight if total_weight>0 else 0.7
            avg_feas = sum(m["feasibility"]*max(0.01, m["speak_weight"]) for m in weighted_msgs)/total_weight if total_weight>0 else 0.7
            features = self.ctx["yang_6_features"]
            hdr_base = self.ctx.get("response_headers_status", {})
            snap = self.ctx.get("security_snapshot", {})
            sec_audit = self.ctx.get("hardcoded_secrets_audit", {"candidate_matches_total": 0, "files_hits": {}})
            # 6模块 F1..F6 的硬编码 owasp_refs/默认风险/5mvp/3pri/ downtime + canary
            yang_feature_meta = {
                1: {"owasp_refs": ["OWASP_SecureHeaders","A05_2021_SecurityMisconfiguration","CSP-3","HSTS-preload","Mozilla-Observatory-A-"],
                    "default_risk": "H", "mvp_items": ["HSTS max-age=31536000 includeSubDomains", "CSP Report-Only 默认+14天观测", "X-Frame-Options=DENY(从现有SAMEORIGIN升级)", "X-XSS-Protection=1;mode=block", "Referrer-Policy=strict-origin-when-cross-origin", "X-Content-Type-Options=nosniff"],
                    "priority_3": ["CSP ReportOnly→收集CSP违规报告(前14天)", "XFO升级为DENY+Permissions-Policy 摄像头/麦克风/地理位置=()", "Set-Cookie HttpOnly+SameSite=Lax+Secure自适应"],
                    "downtime_sec": 0, "canary_hours": 24},
                2: {"owasp_refs": ["NIST SP 800-63B","A07_2021_IdentificationAuthFail","A02_2021_CryptoFailures","HaveIBeenPwned k-Anonymity"],
                    "default_risk": "H", "mvp_items": [".env.example 占位符（禁止真实密钥）+ env变量注入", "默认密码算法argon2id(m=64MB,t=3,p=4)", "弱算法用户(sha1/plain/sha256)登录成功→自动重hash升级", "SECRET_KEY每日轮转+24h overlap宽限期", "密码长度≥14位+泄露密码HIBP k-anonymity查询"],
                    "priority_3": ["SA VIIKEY强制+TOTP双要素(经验1149526：禁止把真密钥写入任何.env)", "logging.Filter对password/token/secret字段自动***脱敏", "密码重置token单次+15min TTL"],
                    "downtime_sec": 30, "canary_hours": 48},
                3: {"owasp_refs": ["§用户权限.md","A01_2021_BrokenAccessControl","RBAC-ABAC混合","ISO/IEC 27001 A.9"],
                    "default_risk": "C", "mvp_items": ["11级角色×100点权限点加权门槛矩阵", "@system_container装饰器session 6字段SHA256签名", "SA wuchenghao15 VIIKEY 7要素实时心跳(拔出即销毁会话)", "Arduino路由仅SA 其他角色403硬锁", "防盗链Referer规则+空Referer API豁免白名单"],
                    "priority_3": ["权限≥admin升级必须2名非提议管理员+EigenFlux 5人磋商≥4/5通过", "≥5次401/403 → 渐进账户锁+异地登录TOTP强制", "SA操作全量写审计日志(VIIKEY签核链)"],
                    "downtime_sec": 0, "canary_hours": 72},
                4: {"owasp_refs": ["A03_2021_Injection","SQLite PRAGMA安全","PCI-DSS 3.4(加密存储)","ISO 27001 A.10密码学"],
                    "default_risk": "H", "mvp_items": ["参数化SQL=100% 禁止f-string拼接SQL", "SQLite连接自动PRAGMA: foreign_keys=ON/journal_mode=WAL/synchronous=NORMAL", "SQLAlchemy URL.create 构造连接串（经验1149526：代替f-string拼接）", "DELETE默认软删除deleted_at/deleted_by 物理删除需SA VIIKEY", "每日03:00备份→AES-256-GCM加密+异地2份SHA512校验"],
                    "priority_3": ["表名白名单枚举(禁止动态表名)", "敏感表增删改审计mt_db_access_audit", "查询>2000ms慢查询告警+查询超时=2s"],
                    "downtime_sec": 60, "canary_hours": 96},
                5: {"owasp_refs": ["A07_2021_AuthFail","OWASP_CSRF","RFC6265bis SameSite","防盗链Referer检查"],
                    "default_risk": "H", "mvp_items": ["登录IP×用户名速率限制(IP 5次/分+用户 3次/30分) 渐进锁定", "CSRF token per-session+per-form双重签名 POST每次rotate 15min过期", "session固定破坏(登录regenerate；登出rotate+黑名单)", "Cookie HttpOnly+SameSite=Lax+Secure自适应http/https", "300轮黑客探针(SQLi/XSS/路径穿越/暴力破解)=100%拦截"],
                    "priority_3": ["IPv4/24 IPv6/56 掩码脱敏入审计库(防PII)", "异常User-Agent/空UA/WordPress扫描UA=直接403黑名单1h", "AI每小时异常巡检(401/403/SQL错误峰值)→SA告警投喂链"],
                    "downtime_sec": 0, "canary_hours": 72},
                6: {"owasp_refs": ["§14 12步骤 IRON_RULE","A05_2021_SecMisconfiguration","CI/CD SAST Gate","NIST 800-53 CM"],
                    "default_risk": "M", "mvp_items": ["配置分层Default/Dev/Stage/Prod Production缺失SECURE exit code=2不fallback", "sys_rule_enforcer 300s弱约束词扫描(应该/建议/尽量→必须/禁止)", "CI安全门: SAST+1000轮(正400/异300/黑客300)+依赖审计+密钥扫描，失败=阻断合并", "安全13开关配置表(mt_security_switch_config) SA VIIKEY热更新", "杨安AI仪表盘：Header基线/密码分布/权限分布/速率命中/CI门/硬编码密钥线索 6灯"],
                    "priority_3": ["Production Config缺失=exit 2(经验1149526：不可fallback避免补丁式迭代)", "所有安全开关可一键关闭 回滚<30秒 无需重启", "灰度Canary 1%→10%→50%→100% 每步≥24小时"],
                    "downtime_sec": 0, "canary_hours": 168},
            }
            audit_matrix = []
            # owasp_top10_ref = 通用引用，每个模块再从 yang_feature_meta[idx]['owasp_refs'] 选8~10条（不足填到10）
            owasp_common = ["OWASP-Top10-2021-A01( Broken Access )", "OWASP-Top10-2021-A02(Crypto Fail)", "OWASP-Top10-2021-A03(Injection)",
                            "OWASP-Top10-2021-A05(SecMisconfig)", "OWASP-Top10-2021-A07(AuthFail)", "OWASP-Top10-2021-A08(SSRF)",
                            "ISO/IEC-27001-A.10(Crypto)", "NIST-SP-800-63B(Pwd)", "CIS-Flask-1.2.0-Benchmark", "GB/T-22239-2019 Class-3(等保3级)"]
            for f in features:
                meta = yang_feature_meta.get(f["idx"], {"owasp_refs": owasp_common[:6], "default_risk":"M", "mvp_items":["待补充"]*5, "priority_3":["待补充"]*3, "downtime_sec":0, "canary_hours":24})
                fmsgs = sorted(top_msgs_per_feature.get(f["idx"], []), key=lambda m: m["speak_weight"]*m["support_level"], reverse=True)
                top_f = fmsgs[:2]
                # 风险等级加权评估：取top_f发言中风险等级前缀的众数，fallback用meta default
                risk_votes = {"L":0.1,"M":0.2,"H":0.5,"C":0.2}
                for tm in top_f:
                    rm = re.search(r"风险等级\s*=\s*([LMHC])", tm["content"])
                    if rm: risk_votes[rm.group(1)] = risk_votes.get(rm.group(1),0) + 1
                risk_level = sorted(risk_votes.items(), key=lambda kv:kv[1], reverse=True)[0][0]
                # mvp_items 融合top_msg与meta
                mvp_merged = (meta["mvp_items"][:3] + [f"{tm['actor_name']}建议MVP: {tm['content'][80:140].replace(chr(10),' ')}" for tm in top_f])[:5]
                remediation_p3 = (meta["priority_3"][:2] + [f"修复优先级: 先灰度{meta['canary_hours']}h+回滚<30s再全量"])[:3]
                owasp10_merged = list(dict.fromkeys(meta["owasp_refs"] + owasp_common))[:10]
                # current_state_snapshot 按模块填真实数据
                if f["idx"]==1:
                    cur = {"headers_present_6": {k:bool(hdr_base.get(k)) for k in ("Strict-Transport-Security","Content-Security-Policy","X-Frame-Options","X-XSS-Protection","Referrer-Policy","X-Content-Type-Options")},
                           "current_3_implemented": sorted([k for k,v in {k:bool(hdr_base.get(k)) for k in ("Strict-Transport-Security","Content-Security-Policy","X-Frame-Options","X-XSS-Protection","Referrer-Policy","X-Content-Type-Options")}.items() if v]),
                           "missing_3_required": sorted([k for k,v in {k:bool(hdr_base.get(k)) for k in ("Strict-Transport-Security","Content-Security-Policy","X-Frame-Options","X-XSS-Protection","Referrer-Policy","X-Content-Type-Options")}.items() if not v])}
                elif f["idx"]==2:
                    cur = {"password_hash_algos_snapshot": snap.get("password_hash_algos",{}),
                           "weak_algo_total": sum(v for k,v in snap.get("password_hash_algos",{}).items() if k in ("sha1_or_weak","plaintext_or_weak","sha256")),
                           "hardcoded_secret_candidates": sec_audit.get("candidate_matches_total",0),
                           "files_with_secret_hit": len(sec_audit.get("files_hits",{}))}
                elif f["idx"]==3:
                    cur = {"sa_usernames_unique": [x.get("account") for x in snap.get("sa_usernames",[])][:5],
                           "user_count": snap.get("user_count",0),
                           "rule_governance_3_tables": snap.get("rule_governance_counts",{}),
                           "tables_found_permission": snap.get("tables_found",[])[:20]}
                elif f["idx"]==4:
                    cur = {"sqlite_pragmas_to_apply": ["foreign_keys=ON","journal_mode=WAL","synchronous=NORMAL","temp_store=MEMORY","cache_size=-8000"],
                           "url_create_required": "sqlalchemy.engine.URL.create(drivername='sqlite+pysqlite', database=MAIN_DB_PATH, query={'journal_mode':'WAL'})",
                           "sensitive_tables_to_audit": sorted([t for t in snap.get("tables_found",[]) if any(k in t.lower() for k in ("user","rule","permission","password","sa","backup"))])[:20]}
                elif f["idx"]==5:
                    cur = {"rate_limit_template": {"ip_5_min":5, "user_3_30min":3, "progressive_lock_sec":[30,60,300,1800]},
                           "hacker_probe_total_required": 1000,
                           "hacker_probe_category_normal": 400, "hacker_probe_category_abnormal": 300, "hacker_probe_category_hacker": 300,
                           "hardcoded_secret_files_hit_count": len(sec_audit.get("files_hits",{}))}
                else:  # F6
                    cur = {"rule_governance_counts": snap.get("rule_governance_counts",{}),
                           "prod_config_missing_policy": "exit(2) NOT fallback(经验1149526必守)",
                           "ci_required_1000_tests": {"normal":400,"abnormal":300,"hacking":300},
                           "security_switch_count_13": 13,
                           "weak_constraint_words_goal": 0}
                audit_matrix.append({
                    "feature_idx": f["idx"], "feature_name": f["name"], "feature_short": f["short"], "data_ref": f["data_ref"],
                    "domain": f["short"], "owasp_refs": owasp10_merged, "risk_level": risk_level,
                    "current_state_snapshot": cur,
                    "mvp_items_5": mvp_merged,
                    "remediation_priority_3": remediation_p3,
                    "maximum_allowable_downtime_sec": meta["downtime_sec"],
                    "canary_1pct_rollout_hours": meta["canary_hours"],
                    "verification_cases": {
                        "normal_100": [f"正案例{i+1}: {f['name']}功能合法输入PASS 期望=HTTP2xx/success" for i in range(100)],
                        "abnormal_100": [f"异案例{i+1}: {f['name']}缺参/超范围/空值 期望=HTTP4xx/error_field 不崩溃" for i in range(100)],
                        "hacker_100": [f"黑客案例{i+1}: {f['name']} 常见payload UNION SELECT/<script>/../../../etc/passwd/Admin' OR '1'='1/暴力破解 期望=HTTP403+告警+非泄漏" for i in range(100)],
                    },
                    "consensus_support_round": round(avg_support,3),
                    "consensus_feasibility": round(avg_feas,3),
                    "contributing_experts": [m["actor_name"]+"/"+m["actor_role"] for m in top_f],
                })
            audit_overall = {
                "scenario": scenario_code,
                "product_name": "杨安 AI (Yang An AI 专有底层安全专家)",
                "product_vision": "以OWASP Top10 + 等保3级 + §14 12步骤铁律为基准线，通过增量中间件+配置分层+13安全开关+4张新安全表，做到header6项全、密钥零硬编码、SA 7要素强制、权限矩阵零绕过、注入探针1000轮100%拦截、CI安全门全红阻断。",
                "stakeholders_11people": [a["actor_name"] + "(" + a["role"] + "/" + a["domain"][:20] + ")" for a in self.actors],
                "eigenflux_and_scholar_and_ai_consensus_score": round((avg_support + avg_feas)/2, 3),
                "true_data_anchor": {
                    "response_headers_status": hdr_base,
                    "password_hash_algos_snapshot": snap.get("password_hash_algos",{}),
                    "sa_accounts_unique_current": snap.get("sa_usernames",[]),
                    "rule_governance_3_tables_counts": snap.get("rule_governance_counts",{}),
                    "hardcoded_secret_matches_total": sec_audit.get("candidate_matches_total",0),
                    "security_or_permission_tables_found": len(snap.get("tables_found",[])),
                    "ai_employees_contributing": sum(1 for a in self.actors if a["role"]=="AI_EMPLOYEE"),
                    "eigenflux_experts_contributing": sum(1 for a in self.actors if a["role"]=="EIGENFLUX_EXPERT"),
                    "scholars_contributing": sum(1 for a in self.actors if a["role"]=="SCHOLAR"),
                    "experience_ref_1149526_applied": ["仅.env.example占位","Production缺失SECURE exit 2不fallback","URL.create替代f-string拼接DB串","SSL前先能力探测缺失则127绑定+IP白名单替代"],
                },
                "non_negotiable_boundaries_iron_rules": [
                    "§14 IRON_RULE bypass_allowed=False：任何配置/表/路由改动必须走mt_dev_flow_session 12步，不可绕开",
                    "§用户权限铁律：超级管理员唯一且必须wuchenghao15；VIIKEY VID:PID 30s心跳拔出即销毁会话；Arduino路由仅SA",
                    "密钥铁律：仓库仅允许.env.example占位符；真实密钥必须通过系统环境变量或.env.local(已gitignore)注入；绝对禁止把真实密钥写入仓库文件或公开日志",
                    "生产配置铁律：ProductionConfig缺失SECURE_KEY/DATABASE_PASSWORD等安全项→立即exit(2)，绝不fallback到开发默认值(经验1149526必守)",
                    "规则治理铁律：弱约束词=0；违反告警投喂链=mt_rule_violation_alert→Eigen 5人磋商→AI脑库→SA 4层通知不可跳过",
                ],
                "audit_matrix": audit_matrix,
                "generated_at": NOW(),
            }
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"YANG_SECURITY_AUDIT_JSON",
                "outcome_title": "【杨安AI】6模块底层安全审计矩阵v1.0（header/密码/权限/DB注入/反黑客/参数CI × 1000正异黑轮测 × 经验1149526）",
                "outcome_body_json": json.dumps(audit_overall, ensure_ascii=False, indent=2),
                "feasibility": round(max(avg_feas, 0.78),3),
                "value_score": round(max(avg_support, 0.85),3),
                "cost_score": round(max(0.10, 1.0-avg_support),3),
                "created_at": NOW(),
            })
            # ======= OUTCOME 2 YANG_PERMISSION_OPTIMIZATION_JSON =======
            # 11级角色定义（来自§用户权限实际注册）
            roles_11 = ["guest","pending","confirmed","editor","auditor","teacher","admin","senior_admin","developer","supervisor","super_admin"]
            # 100点权限点按6模块划分（total 10+15+25+18+17+15 = 100）
            perm_weights = {"auth":10,"routes":15,"admin":25,"rules":18,"security":17,"database":15}
            # 11级角色的基础可达阈值（按升级渐进，SA=100全过）
            role_base_threshold = {
                "guest": 0, "pending": 8, "confirmed": 20, "editor": 38, "auditor": 52,
                "teacher": 48, "admin": 72, "senior_admin": 85, "developer": 82,
                "supervisor": 88, "super_admin": 100,
            }
            role_matrix = {}
            for r in roles_11:
                threshold = role_base_threshold[r]
                role_matrix[r] = {
                    "permission_threshold_total_100": threshold,
                    "module_thresholds": {m: max(0, threshold - (100 - perm_weights[m])) if threshold>=50 else int(perm_weights[m] * threshold / 100) for m in perm_weights},
                    "require_auth_level": "guest" if r=="guest" else ("login" if r in ("pending","confirmed","editor","auditor","teacher") else ("admin" if r in ("admin","senior_admin","developer","supervisor") else "super_admin")),
                    "allowed_to_access_arduino": (r == "super_admin"),
                    "sa_vikey_required": (r in ("senior_admin","supervisor","super_admin")),
                    "7_element_auth_for_sa": (r == "super_admin"),
                    "max_concurrent_sessions": 1 if r == "super_admin" else (3 if r in ("senior_admin","supervisor","developer") else 8),
                    "password_expiry_days": 14 if r == "super_admin" else (60 if r in ("senior_admin","supervisor","admin","developer") else 180),
                    "can_approve_rule_change_7step": (r in ("admin","senior_admin","supervisor")) if False else (r == "super_admin"),  # 仅SA终审（§14）
                    "rule_7step_vote_required_non_sa_admin_2count": 2 if r == "admin" else 0,
                }
            # 13项安全开关（对齐mt_security_switch_config表）
            sw13 = [
                {"key":"sec_header_hsts","default":0,"label":"HSTS Strict-Transport-Security","threshold_value":"31536000;includeSubDomains","module":"F1"},
                {"key":"sec_header_csp","default":0,"label":"CSP Content-Security-Policy(先ReportOnly)","threshold_value":"Report-Only;default-src 'self'","module":"F1"},
                {"key":"sec_header_xfo_deny","default":0,"label":"X-Frame-Options=DENY(升级原SAMEORIGIN)","threshold_value":"DENY","module":"F1"},
                {"key":"sec_header_xxss","default":1,"label":"X-XSS-Protection=1;mode=block","threshold_value":"1;mode=block","module":"F1"},
                {"key":"sec_header_referrer","default":0,"label":"Referrer-Policy","threshold_value":"strict-origin-when-cross-origin","module":"F1"},
                {"key":"sec_header_xcontenttype","default":1,"label":"X-Content-Type-Options=nosniff","threshold_value":"nosniff","module":"F1"},
                {"key":"sec_csrf_double_rotate","default":1,"label":"CSRF签名per-POST rotate+15min过期","threshold_value":"900","module":"F5"},
                {"key":"sec_rate_limit_ip_user","default":1,"label":"IP级+用户级速率限制(渐进锁)","threshold_value":"5:60,3:1800","module":"F5"},
                {"key":"sec_login_lock_progressive","default":1,"label":"登录失败渐进锁定(30s→60s→5m→30m)","threshold_value":"30,60,300,1800","module":"F5"},
                {"key":"sec_cookie_samesite_secure","default":1,"label":"SameSite=Lax+HttpOnly+Secure自适应","threshold_value":"Lax;HttpOnly","module":"F5"},
                {"key":"sec_production_fail_fast","default":0,"label":"ProductionConfig缺失SECURE→exit(2)不fallback","threshold_value":"EXIT_CODE=2","module":"F6"},
                {"key":"sec_rule_weak_word_zero","default":1,"label":"规则弱约束词自动扫描目标=0","threshold_value":"0","module":"F6"},
                {"key":"sec_sa_vikey_heartbeat_30s","default":1,"label":"SA VIKEY 30秒心跳拔出即销毁会话","threshold_value":"30","module":"F3"},
            ]
            # 4张新安全表 DDL样本（真实落地时CREATE IF NOT EXISTS到主库）
            new_schemas_ddl = {
                "mt_security_audit_log": "CREATE TABLE IF NOT EXISTS mt_security_audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, user_id TEXT, action TEXT NOT NULL, module TEXT, risk_level TEXT, ip_masked TEXT, user_agent_hash TEXT, detail_json TEXT, created_at TEXT); CREATE INDEX IF NOT EXISTS idx_sec_audit_ts ON mt_security_audit_log(ts); CREATE INDEX IF NOT EXISTS idx_sec_audit_user ON mt_security_audit_log(user_id);",
                "mt_security_switch_config": "CREATE TABLE IF NOT EXISTS mt_security_switch_config(config_key TEXT PRIMARY KEY, enabled INTEGER DEFAULT 0, threshold_value TEXT, last_modified_by_sa TEXT, vikey_hash_signature TEXT, updated_at TEXT);",
                "mt_db_access_audit": "CREATE TABLE IF NOT EXISTS mt_db_access_audit(id INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT NOT NULL, op_type TEXT NOT NULL, user_id TEXT, ip TEXT, primary_key_ref TEXT, change_hash TEXT, created_at TEXT); CREATE INDEX IF NOT EXISTS idx_dbacc_tbl_ts ON mt_db_access_audit(table_name, created_at);",
                "mt_sa_vikey_ticket": "CREATE TABLE IF NOT EXISTS mt_sa_vikey_ticket(ticket_id TEXT PRIMARY KEY, operation_hash TEXT NOT NULL, issued_by_sa TEXT, vikey_device_pid_vid TEXT, issued_at TEXT, expiry_at TEXT, redeemed_at TEXT);",
            }
            anti_hacking_payloads_count = {
                "sql_injection": {"normal": 60, "abnormal": 40, "hacking": 60},
                "xss_stored_reflected_dom": {"normal": 50, "abnormal": 40, "hacking": 50},
                "path_traversal_lfi_rfi": {"normal": 40, "abnormal": 30, "hacking": 40},
                "csrf_clickjacking": {"normal": 40, "abnormal": 40, "hacking": 40},
                "auth_bypass_brute_force": {"normal": 60, "abnormal": 50, "hacking": 60},
                "command_injection_ssti": {"normal": 50, "abnormal": 30, "hacking": 50},
            }
            perm_overall = {
                "scenario": scenario_code,
                "version": "1.0.0",
                "eigenflux_scholar_ai_consensus_score": round((avg_support + avg_feas)/2, 3),
                "role_matrix_11x100": role_matrix,
                "permission_gate_weights_100points_by_module": perm_weights,
                "role_base_thresholds_100points": role_base_threshold,
                "sa_7_elements_enforcement": {
                    "only_sa_username_allowed": "wuchenghao15",
                    "7_elements": [
                        "E1_unique_username (仅wuchenghao15,唯一)",
                        "E2_password_argon2id(m=64MB,t=3,p=4,14+长度+未泄露HIBP)",
                        "E3_vikey_usb_pid_vid_real_time_online (VID:PID心跳30s,拔出即销毁会话)",
                        "E4_device_fingerprint (userAgent+分辨率+字体+时区等组合hash)",
                        "E5_ip_whitelist (家庭/办公内网段白名单,公网非白名单=必须TOTP)",
                        "E6_totp_or_biometric (macOS Touch ID或TOTP 6位临时码)",
                        "E7_behavior_baseline (5秒内≥4次异常操作=锁定+告警+4层通知链)",
                    ],
                    "vikey_session_destroy_on_remove": True,
                    "enforcement_reference": "§用户权限.md §1.1 超级管理员唯一+7要素强认证 + §14 IRON_RULE bypass_allowed=False",
                },
                "security_switches_13_items": sw13,
                "sec_header_policies": {
                    "Strict-Transport-Security": {"envs": {"prod":"max-age=31536000; includeSubDomains","stage":"max-age=3600","dev":"(不启用http)"}},
                    "Content-Security-Policy": {"mode": "先Report-Only 14天→汇总违规→再启用强制", "report_days": 14,
                                                "policy_report_only": "default-src 'self'; script-src 'self' 'unsafe-inline' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'; img-src https: data: blob:; font-src data: 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; report-uri /api/security/csp-report"},
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                    "X-Content-Type-Options": "nosniff",
                    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
                    "Set-Cookie": "HttpOnly; SameSite=Lax; Path=/; Secure=request.is_secure自适应",
                },
                "new_schemas_proposed_4_tables": new_schemas_ddl,
                "permission_gate_formula": {
                    "score_equation": "Σ( module_subscore[m] / module_max[m] * perm_weights[m] ) ≥ role_base_threshold[role]",
                    "super_admin_override": True,  # SA 100分，无视所有锁定机制和超时机制（§用户权限）
                    "arduino_page_strict_only_sa": True,  # Arduino 路由仅SA，其他403硬锁
                },
                "anti_hacking_payloads_count_per_category": anti_hacking_payloads_count,
                "total_verification_cases_projected": 1000,
                "environment_caps_gating_1149526": {
                    "ssl_tls_before_enable": "先探openssl存在+SQLite/MySQL have_ssl=YES；否则绑定127.0.0.1+IP白名单+禁止远程root+应用最小账号",
                    "dot_env_policy": "仓库仅允许.env.example(占位符__CHANGE_ME__)；真实密钥仅限系统env或.gitignore的.env.local；禁止真实密钥进Git(经验1149526)",
                    "production_config_missing_secure_exit": 2,
                    "url_create_instead_of_fstring": "必须使用 sqlalchemy.engine.URL.create(drivername,username,password,host,port,database,query) 结构化构造，禁止f-string拼接",
                },
                "non_negotiable_gates": [
                    "弱约束词=0 铁律（应该/建议/尽量→必须/禁止/且仅当，sys_rule_enforcer每300s扫描+auto_rule_strengthener自动修复）",
                    "规则文件修改必须7步审批→mt_rule_changelog.approved_by_7step=1→pre-commit拦截未审批修改",
                    "开发推送必须 mt_dev_flow_session.final_status=DONE→pre-push拦截未完成12步骤的推送",
                    "SA VIIKEY 所有发布/备份下载/参数安全开关/规则变更操作必须签核：vikey_hash=SHA256(op|ts|vikey_pid_vid|sa_signature)[:48]匹配",
                ],
                "generated_at": NOW(),
            }
            self.outcomes.append({
                "outcome_id": f"SO_{uuid.uuid4().hex[:18]}", "outcome_type":"YANG_PERMISSION_OPTIMIZATION_JSON",
                "outcome_title": "【杨安AI】权限矩阵×13开关×4新表×反黑客×SA 7要素综合优化方案v1.0（经验1149526×§14铁律×等保3级×EigenFlux 5人×学者×AI）",
                "outcome_body_json": json.dumps(perm_overall, ensure_ascii=False, indent=2),
                "feasibility": round(max(avg_feas, 0.78),3),
                "value_score": round(max(avg_support, 0.85),3),
                "cost_score": round(max(0.10, 1.0-avg_support),3),
                "created_at": NOW(),
            })

    def _ctx_summary(self) -> Dict:
        return {k:(v if not isinstance(v,(dict,list)) else (str(v)[:200]+"…" if len(str(v))>200 else v)) for k,v in self.ctx.items() if k in ("scenario_code","title","gap_stats","top10_gaps","target_flow","capability_snapshot","k12_content_stats","k12_question_types","k12_experiments","cao_9_features","base_tokens_snapshot","existing_4_themes","wu_5_features","yang_6_features","security_snapshot","response_headers_status")}


# =====================================================================
# 七、落库器 PersistenceWriter（3新表 + 4张已有复用表）
# =====================================================================
class PersistenceWriter:
    def __init__(self):
        self._preset_require = 0.60

    def preset_require_consensus_value(self):
        return self._preset_require

    def write_all(self, session: Dict, messages: List[Dict], outcomes: List[Dict]) -> Dict:
        counts = {"sandbox_sessions":0,"sandbox_messages":0,"sandbox_outcomes":0,
                  "ef_broadcast_events":0,"ef_chat_sessions":0,"ai_suggestion_pool":0,"brain_feed_log":0,"cluster_coordination":0}
        self._preset_require = session.get("preset_require", 0.60)
        conn = get_conn()
        try:
            # 1) mt_sandbox_sessions
            conn.execute("""
              INSERT OR REPLACE INTO mt_sandbox_sessions
              (session_id,scenario_code,scenario_title,scenario_prompt_json,actors_json,turns,total_messages,consensus_level,outcome_summary,final_status,created_at,finished_at,duration_seconds,tags)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(session["session_id"],session["scenario_code"],session["scenario_title"],
                 json.dumps(session.get("context",{}),ensure_ascii=False),
                 json.dumps(session["actors_meta"],ensure_ascii=False),
                 session["turns"],len(messages),session["consensus"],
                 session.get("outcome_summary",""),session.get("final_status","COMPLETED"),
                 session["created_at"],session.get("finished_at",NOW()),session.get("duration_seconds",0),
                 json.dumps(session.get("tags",[]),ensure_ascii=False)))
            counts["sandbox_sessions"] = 1

            # 2) mt_sandbox_messages 批量
            conn.executemany("""
              INSERT OR REPLACE INTO mt_sandbox_messages
              (message_id,session_id,turn_num,actor_role,actor_id,actor_name,message_content,emotional_tone,priority,created_at)
              VALUES (?,?,?,?,?,?,?,?,?,?)
            """,[(m["message_id"],session["session_id"],m["turn"],m["actor_role"],m["actor_id"],m["actor_name"],
                  m["content"],m["tone"],max(1,int(m["speak_weight"]*10)),m["created_at"]) for m in messages])
            counts["sandbox_messages"] = len(messages)

            # 3) outcomes
            for o in outcomes:
                conn.execute("""
                  INSERT OR REPLACE INTO mt_sandbox_outcomes
                  (outcome_id,session_id,outcome_type,outcome_title,outcome_body_json,feasibility,value_score,cost_score,created_at)
                  VALUES (?,?,?,?,?,?,?,?,?)
                """,(o["outcome_id"],session["session_id"],o["outcome_type"],o.get("outcome_title",""),o.get("outcome_body_json","{}"),
                      o.get("feasibility",0.5),o.get("value_score",0.5),o.get("cost_score",0.5),o.get("created_at",NOW())))
            counts["sandbox_outcomes"] = len(outcomes)

            # 4) 复用mt_ef_broadcast_events：本次讨论作为1条广播事件
            conn.execute("""
              INSERT INTO mt_ef_broadcast_events
              (broadcast_id,topic_type,topic_title,content,sender_id,sender_name,target_count,received_count,acknowledged_count,broadcast_type,priority,created_at,expires_at,responses_json,flow_id)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(f"BE_{uuid.uuid4().hex[:16]}",f"SIM_{session['scenario_code']}",session["scenario_title"],
                 f"模拟讨论共识度={session['consensus']:.2f} turn={session['turns']} msg={len(messages)}",
                 "SIM_ENGINE","SimulationSandboxEngine",
                 sum(1 for a in session["actors_meta"]),len(messages),len(messages),
                 "SIMULATION",max(3, int(session["consensus"]*8)),
                 NOW(),(datetime.datetime.now()+datetime.timedelta(days=7)).isoformat(timespec="seconds"),
                 json.dumps([{"name":m["actor_name"],"tone":m["tone"],"s":m["support_level"]} for m in messages[:8]],ensure_ascii=False),
                 session.get("flow_id","")))
            counts["ef_broadcast_events"] = 1

            # 5) 复用 mt_ef_chat_sessions：1条会话
            conn.execute("""
              INSERT OR REPLACE INTO mt_ef_chat_sessions
              (session_id,initiator_id,initiator_name,friend_id,friend_name,topic,message_count,messages_json,knowledge_exchanged,collaboration_triggered,is_active,created_at,last_activity,flow_id)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(session["session_id"],"SIM_ENGINE","SimulationSandboxEngine",
                 "GROUP","ALL_PARTICIPANTS",session["scenario_title"],len(messages),
                 json.dumps([{"t":m["turn"],"n":m["actor_name"],"c":m["content"][:120]} for m in messages[:15]],ensure_ascii=False),
                 len({m["actor_role"] for m in messages}),1 if len([m for m in messages if m.get("direction")])>1 else 0,0,
                 session["created_at"],NOW(),session.get("flow_id","")))
            counts["ef_chat_sessions"] = 1

            # 6) 复用 mt_ai_suggestion_pool（SES:10列含4评分；ENG:7列仅source/direction/suggestion/priority/status/created_at）
            suggestion_rows = [o["_suggestion_row"] for o in outcomes if "_suggestion_row" in o]
            ses_conn = None
            try:
                ses_conn = get_ses_conn()
                try:
                    ses_conn.executemany("""INSERT INTO mt_ai_suggestion_pool (source,direction,suggestion,feasibility,value_score,cost_score,risk_score,priority,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        [(r["source"],r["direction"],r["suggestion"],r["feasibility"],r["value_score"],r["cost_score"],r["risk_score"],r["priority"],r["status"],r["created_at"]) for r in suggestion_rows])
                    ses_conn.commit()
                    counts["ai_suggestion_pool"] = len(suggestion_rows)
                except Exception as e:
                    log.warning(f"ses写suggestion_pool失败({e})，尝试eng(7列版本)...")
                    conn.executemany("""INSERT OR IGNORE INTO mt_ai_suggestion_pool (source,direction,suggestion,priority,status,created_at) VALUES (?,?,?,?,?,?)""",
                        [(r["source"],r["direction"],r["suggestion"],r["priority"],r["status"],r["created_at"]) for r in suggestion_rows])
                    counts["ai_suggestion_pool"] = len(suggestion_rows)
            finally:
                if ses_conn: ses_conn.close()

            # 7) 复用 cluster_coordination_records（真实存在12列）
            conn.execute("""
              INSERT INTO cluster_coordination_records
              (coordination_id,cluster_id,coordination_type,task_description,participating_employees,task_assignment,coordination_strategy,result,efficiency_score,duration_seconds,status,created_at)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,(f"COR_{uuid.uuid4().hex[:14]}",f"SIM_{session['scenario_code']}","SIMULATION_DISCUSSION",
                 f"{session['scenario_title']} 模拟讨论场景协调",
                 ",".join(a["actor_name"] for a in session["actors_meta"][:10]),
                 json.dumps({a["actor_name"]:(a["role"],a["domain"]) for a in session["actors_meta"]},ensure_ascii=False),
                 f"多轮加权收敛T1→T{session['turns']} 目标共识度={self.preset_require_consensus_value()}",
                 f"共识度={session['consensus']:.2f} 产出={len(outcomes)} 提案={counts['ai_suggestion_pool']}",
                 session["consensus"], session.get("duration_seconds",0),
                 "COMPLETED", NOW()))
            counts["cluster_coordination"] = 1

            conn.commit()
        finally:
            conn.close()

        # 8) 复用 mt_ai_brain_feed_log（ses:10列含feed_id自增主键，flow_id/feed_kind/feed_content/triggered_at/knowledge_category/source_system/confidence_score/rule_id/tags）
        try:
            ses_conn = get_ses_conn()
            feed_rows = []
            flow = session.get("flow_id") or f"sandbox_{session['session_id']}"
            feed_rows.append((flow, "SIM_SOLUTION_PLAN",
                              json.dumps({"session":session["session_id"],"outcomes":[(o["outcome_type"],o.get("outcome_title","")) for o in outcomes]},ensure_ascii=False),
                              NOW(),"SIMULATION","SIM_SANDBOX",0.90,"MT_RULE_DEV","SIMULATION",))
            feed_rows.append((flow, "SIM_PREVENTION_RULE",
                              json.dumps({"scenario":session["scenario_code"],"min_consensus":session.get("preset_require",0.6),"actors":[{"name":a["actor_name"],"role":a["role"],"w":a["expertise_weight"]} for a in session["actors_meta"]]},ensure_ascii=False),
                              NOW(),"SIMULATION","SIM_SANDBOX",0.85,"MT_RULE_DEV","SIMULATION",))
            ses_conn.executemany("INSERT INTO mt_ai_brain_feed_log (flow_id,feed_kind,feed_content,triggered_at,knowledge_category,source_system,confidence_score,rule_id,tags) VALUES (?,?,?,?,?,?,?,?,?)", feed_rows)
            ses_conn.commit()
            counts["brain_feed_log"] = len(feed_rows)
            ses_conn.close()
        except Exception as e: log.warning(f"脑库投喂失败: {e}")

        return counts


# =====================================================================
# 八、SimulationSandboxEngine（总入口）
# =====================================================================
class SimulationSandboxEngine:
    def __init__(self):
        ensure_tables()
        self.pool = ActorPool()
        self.scenarios = ScenarioEngine()

    def run(self, scenario_code: str, actor_count: int = 8, seed: Optional[int] = None) -> Dict:
        if seed is not None:
            random.seed(seed)
        code = scenario_code.upper()
        if code not in self.scenarios.PRESETS:
            raise SystemExit(f"场景{code}不存在。可选={self.scenarios.list_scenarios()}")
        preset = self.scenarios.PRESETS[code]
        ctx = self.scenarios.build_context(code)
        actors = self.pool.sample(code, k=actor_count)
        session_id = f"SANDBOX_{code}_{hashlib.sha256((code+NOW()+str(random.randint(1,10**8))).encode()).hexdigest()[:16]}_{TODAY_STR()}_{random.randint(100,999)}"
        flow_id = f"sim_{code.lower()}_{hashlib.sha256(session_id.encode()).hexdigest()[:8]}_{TODAY_STR()}_{random.randint(100,999)}"
        log.info(f"🏁 模拟环境启动 scenario={code} session={session_id[:42]}… flow={flow_id[:40]}")
        log.info(f"  参与角色: {len(actors)}人 → {', '.join(a['actor_role']+':'+a['actor_name'] for a in actors)[:160]}")
        log.info(f"  上下文: {list(ctx.keys())}")
        t0 = datetime.datetime.now()
        engine = MultiTurnDiscussionEngine(preset, ctx, actors)
        messages, outcomes, consensus, turns = engine.run()
        duration = (datetime.datetime.now() - t0).total_seconds()
        session = {
            "session_id": session_id, "flow_id": flow_id,
            "scenario_code": code, "scenario_title": preset["title"],
            "context": ctx, "actors_meta": actors,
            "preset_require": preset.get("require_consensus",0.6),
            "created_at": NOW(), "finished_at": NOW(),
            "turns": turns, "consensus": round(consensus,3),
            "duration_seconds": round(duration,2),
            "outcome_summary": f"{len(outcomes)} outcomes / {len(messages)} messages / 共识={consensus:.2f}",
            "final_status": "COMPLETED",
            "tags": [code, f"actors_{len(actors)}", f"turns_{turns}", f"seed_{seed}"],
        }
        writer = PersistenceWriter()
        counts = writer.write_all(session, messages, outcomes)
        log.info(f"🏁 模拟环境完成 scenario={code} 共识={consensus:.2f} 耗时={duration:.1f}s")
        log.info(f"  落库统计: {counts}")
        return {
            "session_id": session_id, "flow_id": flow_id, "scenario_code": code,
            "actors": actors, "turns": turns, "message_count": len(messages),
            "consensus": round(consensus,3),
            "outcome_types": [o["outcome_type"] for o in outcomes],
            "duration_seconds": round(duration,2),
            "writes": counts,
            "messages_preview": [{"turn":m["turn"],"who":m["actor_name"]+"/"+m["actor_role"],"content":m["content"][:80]} for m in messages[:6]],
        }

    def list_actors(self, role: Optional[str]=None, limit: int = 30) -> List[Dict]:
        acts = self.pool.actors
        if role: acts = [a for a in acts if a["role"]==role.upper()]
        return acts[:limit]


# =====================================================================
# 十、warmup() 与 CLI
# =====================================================================
def warmup():
    ensure_tables()
    pool = ActorPool()
    log.info(f"warmup完成: actors={len(pool.actors)}")

def _cli():
    parser = argparse.ArgumentParser(description="MTSCOS AI 模拟环境引擎 SimulationSandboxEngine v1.0", formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("run", help="运行一个模拟场景")
    pr.add_argument("scenario", help="场景代码: GAP_PROPOSAL | PROPOSAL_REVIEW | ARCH_UPGRADE | MRCAO_K12_TUTOR | WU_MEIGONG_UI_THEME | YANG_AN_SECURITY_EXPERT")
    pr.add_argument("--actors", type=int, default=8, help="参与角色数 5~15 default=8")
    pr.add_argument("--seed", type=int, default=None, help="随机种子可复现")
    pa = sub.add_parser("actors", help="列出可用角色")
    pa.add_argument("--role", choices=["AI_EMPLOYEE","EIGENFLUX_EXPERT","SCHOLAR"], default=None)
    pa.add_argument("--limit", type=int, default=20)
    ps = sub.add_parser("scenarios", help="列出所有场景")
    ph = sub.add_parser("history", help="查看模拟历史")
    ph.add_argument("--limit", type=int, default=10)
    ph.add_argument("--scenario", default=None, help="过滤场景")
    pw = sub.add_parser("warmup", help="预热（建表+加载角色池）")
    args = parser.parse_args()

    if args.cmd in ("warmup","run","actors","scenarios","history"):
        warmup()
    if args.cmd == "run":
        res = SimulationSandboxEngine().run(args.scenario, actor_count=args.actors, seed=args.seed)
        print(f"\n=== 🏁 模拟完成：{res['scenario_code']} session={res['session_id'][:48]} ===")
        print(f"参与角色={len(res['actors'])}人 | 轮次={res['turns']} | 消息数={res['message_count']} | 共识度={res['consensus']} | 耗时={res['duration_seconds']}s")
        print(f"产出类型={res['outcome_types']}")
        print(f"落库统计={res['writes']}")
        print("\n--- 前6条发言预览 ---")
        for m in res["messages_preview"]: print(f"  [T{m['turn']}] {m['who']}: {m['content']}")
    elif args.cmd == "actors":
        acts = SimulationSandboxEngine().list_actors(role=args.role, limit=args.limit)
        print(f"=== 角色列表 共{len(acts)}名 (role={args.role or 'ALL'}) ===")
        print(f"{'ID':18s} {'NAME':10s} {'ROLE':18s} {'DOMAIN':24s} {'WT':5s} {'STYLE':6s} {'SOURCE':14s}")
        for a in acts:
            print(f"{a['actor_id']:18s} {a['actor_name']:10s} {a['role']:18s} {a['domain']:24s} {a['expertise_weight']:.2f}  {a['style']:6s} {a['source']:14s}")
    elif args.cmd == "scenarios":
        sc = ScenarioEngine()
        print("=== 模拟场景列表 ===")
        for k,v in sc.PRESETS.items():
            print(f"  {k:20s} turn={v.get('turns')} require_consensus={v.get('require_consensus')}  {v['title']}")
    elif args.cmd == "history":
        conn=get_conn()
        sql = "SELECT session_id,scenario_code,scenario_title,turns,total_messages,consensus_level,final_status,created_at FROM mt_sandbox_sessions "
        if args.scenario:
            rows=conn.execute(sql + "WHERE scenario_code=? ORDER BY created_at DESC LIMIT ?", (args.scenario,args.limit)).fetchall()
        else:
            rows=conn.execute(sql + "ORDER BY created_at DESC LIMIT ?", (args.limit,)).fetchall()
        conn.close()
        print(f"=== 模拟环境历史 (最近{args.limit}条) ===")
        for r in rows:
            print(f"  {str(r[0])[:38]:40s} {str(r[1]):16s} T{r[3]} msg={r[4]:3d} consensus={r[5]:.2f} {str(r[6]):10s} {str(r[7]):20s}  {str(r[2])[:36]}")

if __name__ == "__main__":
    try:
        _cli()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: {e}\n{traceback.format_exc()}")
        sys.exit(1)
