"""规则完善 daemon
==================================
仙女座自动生成 — 周期性执行:
1. 扫描 .trae/rules/ 12 规则文档的硬约束 (必须/禁止/强制)
2. 审计 ai_engines/rules_engine/ 代码覆盖度 (13 模块)
3. 生成缺口矩阵 + 落库 mt_rule_integrity_scan
4. 触发 rule_knowledge_health_check 健康检查
5. 输出补全建议 → 投喂建议池
"""

import os, sys, time, sqlite3, json, logging, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # flask-app/engines/auto_gen_rules/
ENGINES_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))  # flask-app/engines/
FLASK_APP = os.path.abspath(os.path.join(ENGINES_DIR, ".."))  # flask-app/
PROJECT_ROOT = os.path.abspath(os.path.join(FLASK_APP, ".."))  # MTSCOS_AI_Project/
LOG_DIR = os.path.join(PROJECT_ROOT, "_runtime", "logs")
DB_PATH = os.path.join(FLASK_APP, "database", "app.db")  # 主库, 与 smart_mount_engine 一致
RULES_DIR = os.path.join(PROJECT_ROOT, ".trae", "rules")

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] rules_daemon: %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOG_DIR, "auto_gen_rules.log")),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger("rules_daemon")


class RulesDaemon:
    def __init__(self, interval=600):
        self.interval = interval
        log.info(f"RulesDaemon init interval={interval}s")
    
    def scan_rule_constraints(self):
        """扫描 12 规则文档硬约束"""
        rules = []
        for f in sorted(os.listdir(RULES_DIR)):
            if not f.endswith(".md") or ".bak" in f: continue
            content = open(os.path.join(RULES_DIR, f)).read()
            doc = f.replace(".md", "")
            counts = {}
            for kw in ["必须", "禁止", "不得", "强制", "严禁", "铁律", 
                       "不可绕开", "唯一", "有且仅有", "不允许", "一律"]:
                counts[kw] = content.count(kw)
            total = sum(counts.values())
            rules.append({"doc": doc, "file": f, "constraints": total, "breakdown": counts})
        log.info(f"扫描 {len(rules)} 规则文档, 总硬约束={sum(r['constraints'] for r in rules)}")
        return rules
    
    def audit_engine_coverage(self):
        """审计 rules_engine 模块覆盖度"""
        eng_dir = os.path.join(PROJECT_ROOT, "flask-app", "ai_engines", "rules_engine")
        cap_map = {
            "rule_meta":          ("规则元数据解析", ["RULE_META_START", "parse_rule_meta"]),
            "rule_db":            ("规则治理表 DAO", ["RuleDB", "mt_rule_changelog"]),
            "rule_interceptor":   ("Flask before_request", ["before_request", "register_interceptor"]),
            "rule_pre_commit":    ("Git pre-commit", ["pre_commit", "git_hook"]),
            "rule_integrity":     ("完整性自检", ["integrity", "RULE_META"]),
            "rule_version":       ("版本 bump", ["bump_version", "apply_auto_bumps"]),
            "rule_alert":         ("违反告警", ["violation_alert", "alert_violation"]),
            "dev_preflight":      ("开发前置拦截", ["dev_activity_preflight", "flow_id"]),
            "perm_guard":         ("权限守卫", ["register_interceptor", "_perm_guard"]),
            "sa_guard":           ("SA 唯一性", ["wuchenghao15", "_sa ="]),
            "vikey_guard":        ("VIKEY 强制", ["vikey", "detect"]),
            "rule_andromeda_bridge": ("仙女座桥接", ["ingest_rules_to_knowledge", "rule_knowledge_health_check"]),
        }
        
        results = []
        for fname, (label, keywords) in sorted(cap_map.items()):
            found_in = []
            py_files = [f for f in os.listdir(eng_dir) 
                       if f.endswith(".py") and not f.startswith("__")]
            for pyf in py_files:
                content = open(os.path.join(eng_dir, pyf)).read()
                if any(kw in content for kw in keywords):
                    found_in.append(pyf.replace(".py", ""))
            results.append({
                "capability": fname, "label": label,
                "covered": len(found_in) > 0, "found_in": found_in
            })
        
        total = len(cap_map)
        covered = sum(1 for r in results if r["covered"])
        log.info(f"rules_engine 覆盖度: {covered}/{total} ({covered*100//total}%)")
        return results
    
    def ensure_tables(self, conn):
        """确保规则治理表存在"""
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_rule_integrity_scan (
            scan_id TEXT PRIMARY KEY,
            scan_type TEXT,
            doc_count INTEGER,
            total_constraints INTEGER,
            engine_modules INTEGER,
            coverage_pct INTEGER,
            gaps_json TEXT,
            scan_report TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
    
    def iceberg_coverage(self):
        """统计冰山三层架构 × 规则覆盖度"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            layers = {}
            for layer, label in [("Peak", "🏛️ Peak 赤壁"), 
                                 ("Spectrum", "🎨 Spectrum 承天寺"), 
                                 ("Basement", "🧱 Basement 东坡")]:
                rows = conn.execute("""SELECT 
                    COUNT(DISTINCT rule_id),
                    SUM(CASE WHEN enforcement_scope='STRONG' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN enforcement_scope='MEDIUM' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN enforcement_scope='SUPPORT' THEN 1 ELSE 0 END),
                    AVG(coverage_pct)
                    FROM mt_iceberg_rule_mapping WHERE iceberg_layer=?""", (layer,)).fetchone()
                layers[layer] = {
                    "label": label,
                    "rules": rows[0], "strong": rows[1], "medium": rows[2],
                    "support": rows[3], "coverage": round(rows[4] or 0, 1)
                }
            conn.close()
            return layers
        except Exception as e:
            log.warning(f"冰山覆盖度查询失败: {e}")
            return {}
    
    def run_once(self):
        log.info("=== RulesDaemon run_once ===")
        rules = self.scan_rule_constraints()
        coverage = self.audit_engine_coverage()
        iceberg = self.iceberg_coverage()
        
        # 汇总
        total_constraints = sum(r["constraints"] for r in rules)
        covered_caps = sum(1 for c in coverage if c["covered"])
        total_caps = len(coverage)
        
        # 缺口
        gaps = [c for c in coverage if not c["covered"]]
        
        # 落库
        try:
            conn = sqlite3.connect(DB_PATH, timeout=15)
            self.ensure_tables(conn)
            scan_id = f"rules-scan-{int(time.time())}"
            gaps_json = json.dumps(gaps, ensure_ascii=False)
            rules_json = json.dumps(rules, ensure_ascii=False)
            
            conn.execute("""INSERT INTO mt_rule_integrity_scan 
                (scan_id, scan_type, doc_count, total_constraints, engine_modules, 
                 coverage_pct, gaps_json, scan_report)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (scan_id, "ANDROMEDA_AUTO", len(rules), total_constraints,
                 total_caps, covered_caps*100//total_caps, gaps_json, rules_json))
            conn.commit()
            conn.close()
            log.info(f"落库 mt_rule_integrity_scan scan_id={scan_id}")
        except Exception as e:
            log.warning(f"落库失败: {e}")
        
        # 输出报告
        print(f"  📄 规则文档: {len(rules)} 篇, 硬约束关键词: {total_constraints}")
        print(f"  🧩 engine 模块覆盖: {covered_caps}/{total_caps} ({covered_caps*100//total_caps}%)")
        if gaps:
            print(f"  ⚠️ 缺口: {[g['label'] for g in gaps]}")
        else:
            print(f"  ✅ 无缺口!")
        
        # 冰山层级报告
        if iceberg:
            print(f"\n  🧊 冰山三层 × 规则覆盖:")
            for layer, info in iceberg.items():
                bar = "█" * int(info["coverage"] // 5) + "░" * (20 - int(info["coverage"] // 5))
                print(f"    {info['label']}: {info['rules']}规则 STRONG={info['strong']} MEDIUM={info['medium']} SUPPORT={info['support']}  avg={info['coverage']}%")
        
        return {"scan_id": scan_id, "coverage": f"{covered_caps*100//total_caps}%", 
                "gaps": len(gaps)}
    
    def run(self):
        log.info(f"RulesDaemon START loop={self.interval}s")
        while True:
            try:
                self.run_once()
            except Exception as e:
                log.error(f"loop err: {e}")
            time.sleep(self.interval)


if __name__ == "__main__":
    d = RulesDaemon(interval=int(os.environ.get("RULES_POLL_INTERVAL", "600")))
    try:
        d.run()
    except KeyboardInterrupt:
        log.info("RulesDaemon STOPPED")
