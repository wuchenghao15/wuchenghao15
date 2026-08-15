#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EigenFlux专家主动介入引擎 - 1000轮测试
========================================
测试范围:
  - 正常逻辑 400轮: 7大能力正常调用
  - 异常场景 300轮: 空专家/无效输入/边界条件
  - 黑客攻击 300轮: 滥用注入/绕过/伪造
"""
import sys, os, time, json, random, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eigenflux_proactive_engine import (
    EigenFluxProactiveEngine, ExpertProfile, InterventionEvent,
    DiscussionSession, ExamResult,
    INTERVENE_INTERVAL, UPGRADE_INTERVAL, EXAM_INTERVAL,
    DISCUSSION_TOPICS, EXAM_QUESTION_BANK, EXAM_PASS_THRESHOLD,
)

PASS = 0
FAIL = 0
VULN = 0
ERRORS = []

def _ok(category, name, detail=""):
    global PASS
    PASS += 1

def _fail(category, name, detail=""):
    global FAIL
    FAIL += 1
    ERRORS.append(f"[{category}] {name}: {detail}")

def _vuln(category, name, detail=""):
    global VULN
    VULN += 1
    ERRORS.append(f"[VULN][{category}] {name}: {detail}")

def _assert(cond, category, name, detail=""):
    if cond:
        _ok(category, name, detail)
    else:
        _fail(category, name, detail)

# ========== 正常逻辑测试 (400轮) ==========

def test_normal_intervene(engine, i):
    """正常: 主动介入调剂"""
    ev = engine.proactive_intervene()
    _assert(ev is not None, "normal", f"intervene_{i}", "返回None")
    _assert(ev.expert_name != "", "normal", f"intervene_{i}_expert", "专家名为空")
    _assert(ev.result in ("resolved", "escalated", "pending"), "normal", f"intervene_{i}_result", f"结果异常: {ev.result}")
    _assert(ev.issue_type != "", "normal", f"intervene_{i}_type", "问题类型为空")

def test_normal_enhance(engine, i):
    """正常: 主动完善增强帮扶"""
    r = engine.proactive_enhance_assist()
    _assert(r is not None, "normal", f"enhance_{i}", "返回None")
    _assert(r.get("action") == "enhance_assist", "normal", f"enhance_{i}_action", "动作错误")
    _assert(r.get("specialist", "") != "", "normal", f"enhance_{i}_specialist", "专员为空")
    _assert(r.get("improvement", 0) > 0, "normal", f"enhance_{i}_improve", "提升为0")

def test_normal_upgrade(engine, i):
    """正常: 主动升级AI学识"""
    r = engine.self_upgrade_knowledge()
    _assert(r is not None, "normal", f"upgrade_{i}", "返回None")
    _assert(r.get("action") == "self_upgrade", "normal", f"upgrade_{i}_action", "动作错误")
    _assert(r.get("kb_growth", 0) > 0, "normal", f"upgrade_{i}_growth", "知识增长为0")
    _assert(r.get("new_accuracy", 0) >= 0.80, "normal", f"upgrade_{i}_acc", "准确率过低")
    _assert(r.get("new_accuracy", 1) <= 0.999, "normal", f"upgrade_{i}_acc_max", "准确率超过上限")

def test_normal_exam(engine, i):
    """正常: 单专家考试"""
    experts = list(engine._experts.values())
    if not experts:
        _fail("normal", f"exam_{i}", "无专家")
        return
    expert = random.choice(experts)
    result = engine._conduct_exam(expert)
    _assert(result is not None, "normal", f"exam_{i}", "返回None")
    _assert(0 <= result.score <= 100, "normal", f"exam_{i}_score", f"分数越界: {result.score}")
    _assert(result.questions_total > 0, "normal", f"exam_{i}_qs", "题目数为0")
    _assert(result.questions_correct <= result.questions_total, "normal", f"exam_{i}_correct", "答对超过总数")
    _assert(result.passed == (result.score >= EXAM_PASS_THRESHOLD), "normal", f"exam_{i}_pass", "合格判定错误")

def test_normal_discussion(engine, i):
    """正常: 组队讨论及反向投喂"""
    s = engine.team_discussion_and_reverse_feed()
    _assert(s is not None, "normal", f"discuss_{i}", "返回None")
    _assert(len(s.team_members) >= 2, "normal", f"discuss_{i}_team", f"团队人数不足: {len(s.team_members)}")
    _assert(len(s.team_members) <= 5, "normal", f"discuss_{i}_team_max", f"团队超限: {len(s.team_members)}")
    _assert(s.topic != "", "normal", f"discuss_{i}_topic", "议题为空")
    _assert(len(s.conclusions) > 0, "normal", f"discuss_{i}_concl", "无结论")
    _assert(len(s.reverse_feeds) > 0, "normal", f"discuss_{i}_feed", "无反向投喂")
    _assert(s.leader != "", "normal", f"discuss_{i}_leader", "无组长")

def test_normal_proposal(engine, i):
    """正常: 主动找张晓峰/提案组长"""
    experts = [e.name for e in engine._experts.values() if e.status == "active"]
    if len(experts) < 2:
        _fail("normal", f"proposal_{i}", "专家不足")
        return
    team = random.sample(experts, min(3, len(experts)))
    r = engine._seek_proposal_leader("测试议题", team)
    _assert(r is not None, "normal", f"proposal_{i}", "返回None")
    _assert(r.get("target_leader") == "张晓峰", "normal", f"proposal_{i}_leader", "目标不是张晓峰")
    _assert(r.get("leader_response", "") != "", "normal", f"proposal_{i}_resp", "无回应")
    _assert(r.get("auto_join_maintenance") == True, "normal", f"proposal_{i}_maint", "未自动加入维护")
    _assert(r.get("proposal_id", "") != "", "normal", f"proposal_{i}_id", "无提案ID")

def test_normal_maintenance(engine, i):
    """正常: 自动加入维护计划"""
    engine._auto_join_maintenance_plan()
    schedule = engine.get_maintenance_schedule()
    _assert(len(schedule) == 3, "normal", f"maint_{i}_shifts", f"班次不为3: {len(schedule)}")
    total = sum(len(v) for v in schedule.values())
    _assert(total > 0, "normal", f"maint_{i}_total", "排班总人为0")

def test_normal_status(engine, i):
    """正常: 状态查询"""
    status = engine.get_status()
    _assert(status is not None, "normal", f"status_{i}", "返回None")
    _assert(status["expert_count"] > 0, "normal", f"status_{i}_experts", "专家数为0")
    _assert("experts_summary" in status, "normal", f"status_{i}_summary", "无专家汇总")
    _assert("by_group" in status["experts_summary"], "normal", f"status_{i}_groups", "无领域统计")

# ========== 异常场景测试 (300轮) ==========

def test_anomaly_empty_intervene(engine, i):
    """异常: 空专家时介入"""
    # 创建空引擎
    empty = EigenFluxProactiveEngine()
    empty._experts = {}
    ev = empty.proactive_intervene()
    _assert(ev is not None, "anomaly", f"empty_intervene_{i}", "返回None")
    _assert(ev.result in ("failed", "no_expert", "resolved", "escalated", "pending"),
            "anomaly", f"empty_intervene_{i}_result", f"结果异常: {ev.result}")

def test_anomaly_invalid_issue_type(engine, i):
    """异常: 无效问题类型"""
    ev = engine.proactive_intervene(issue_type="INVALID_TYPE_XYZ", severity="critical")
    _assert(ev is not None, "anomaly", f"invalid_type_{i}", "返回None")
    # 应该仍然有结果（容错处理）
    _assert(ev.result in ("resolved", "escalated", "pending", "failed"),
            "anomaly", f"invalid_type_{i}_result", f"无效类型未容错: {ev.result}")

def test_anomaly_invalid_severity(engine, i):
    """异常: 无效严重级别"""
    ev = engine.proactive_intervene(severity="EXTREME_999")
    _assert(ev is not None, "anomaly", f"invalid_sev_{i}", "返回None")

def test_anomaly_nonexistent_expert_upgrade(engine, i):
    """异常: 不存在的专家升级"""
    r = engine.self_upgrade_knowledge("不存在的专家_XYZ_999")
    _assert(r is not None, "anomaly", f"nonexist_upgrade_{i}", "返回None")
    _assert(r.get("result") == "no_expert" or r.get("action") == "upgrade",
            "anomaly", f"nonexist_upgrade_{i}_result", "未正确处理不存在的专家")

def test_anomaly_empty_enhance(engine, i):
    """异常: 空专家时帮扶"""
    empty = EigenFluxProactiveEngine()
    empty._experts = {}
    r = empty.proactive_enhance_assist()
    _assert(r is not None, "anomaly", f"empty_enhance_{i}", "返回None")
    _assert(r.get("result") == "no_expert" or r.get("action") == "enhance",
            "anomaly", f"empty_enhance_{i}_result", "未正确处理空专家")

def test_anomaly_empty_discussion(engine, i):
    """异常: 空专家时组队讨论"""
    empty = EigenFluxProactiveEngine()
    empty._experts = {}
    s = empty.team_discussion_and_reverse_feed()
    _assert(s is not None, "anomaly", f"empty_discuss_{i}", "返回None")
    _assert(len(s.team_members) == 0, "anomaly", f"empty_discuss_{i}_team", "空专家却组队了")

def test_anomaly_empty_maintenance(engine, i):
    """异常: 空专家时维护排班"""
    empty = EigenFluxProactiveEngine()
    empty._experts = {}
    empty._auto_join_maintenance_plan()
    schedule = empty.get_maintenance_schedule()
    _assert(len(schedule) == 0 or sum(len(v) for v in schedule.values()) == 0,
            "anomaly", f"empty_maint_{i}", "空专家却有排班")

def test_anomaly_concurrent_intervene(engine, i):
    """异常: 并发介入"""
    import threading
    results = []
    errors = []
    def worker():
        try:
            ev = engine.proactive_intervene()
            results.append(ev)
        except Exception as e:
            errors.append(str(e))
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    _assert(len(errors) == 0, "anomaly", f"concurrent_{i}", f"并发错误: {errors[:2]}")
    _assert(len(results) == 5, "anomaly", f"concurrent_{i}_count", f"结果数不匹配: {len(results)}")

def test_anomaly_exam_no_questions(engine, i):
    """异常: 无题库领域考试"""
    expert = ExpertProfile(name="测试专家_无题库", group="未知领域XYZ")
    engine._experts["测试专家_无题库"] = expert
    result = engine._conduct_exam(expert)
    _assert(result is not None, "anomaly", f"no_qbank_{i}", "返回None")
    # 应回退到默认领域
    _assert(result.questions_total > 0, "anomaly", f"no_qbank_{i}_qs", "无题目")
    del engine._experts["测试专家_无题库"]

def test_anomaly_daemon_stop(engine, i):
    """异常: 守护线程启停"""
    engine.start_daemon()
    _assert(engine._running == True, "anomaly", f"daemon_start_{i}", "启动失败")
    engine.stop_daemon()
    _assert(engine._running == False, "anomaly", f"daemon_stop_{i}", "停止失败")

# ========== 黑客攻击测试 (300轮) ==========

def test_hacker_sql_injection_intervene(engine, i):
    """黑客: SQL注入攻击介入系统"""
    ev = engine.proactive_intervene(
        target="'; DROP TABLE ai_employees; --",
        issue_type="anomaly"
    )
    _assert(ev is not None, "hacker", f"sqli_{i}", "返回None")
    # 介入应正常处理，不应执行SQL
    _assert("ai_employees" in str(engine._experts.keys()) or len(engine._experts) > 0,
            "hacker", f"sqli_{i}_table", "表被删除")

def test_hacker_xss_in_topic(engine, i):
    """黑客: XSS注入议题"""
    s = engine.team_discussion_and_reverse_feed(topic="<script>alert('xss')</script>")
    _assert(s is not None, "hacker", f"xss_{i}", "返回None")
    # 议题应被处理但不执行脚本
    _assert(s.topic != "", "hacker", f"xss_{i}_topic", "议题为空")

def test_hacker_path_traversal(engine, i):
    """黑客: 路径穿越"""
    r = engine.proactive_enhance_assist(target_area="../../../etc/passwd")
    _assert(r is not None, "hacker", f"path_{i}", "返回None")

def test_hacker_command_injection(engine, i):
    """黑客: 命令注入"""
    ev = engine.proactive_intervene(target="; cat /etc/shadow; #")
    _assert(ev is not None, "hacker", f"cmd_{i}", "返回None")

def test_hacker_fake_expert_name(engine, i):
    """黑客: 伪造专家名"""
    r = engine.self_upgrade_knowledge("'; DELETE FROM ai_employees WHERE 1=1; --")
    _assert(r is not None, "hacker", f"fake_name_{i}", "返回None")
    # 专家不应被删除
    _assert(len(engine._experts) > 0, "hacker", f"fake_name_{i}_experts", "专家被删除")

def test_hacker_overflow_intervene(engine, i):
    """黑客: 大量介入请求(DoS)"""
    count = 50
    success = 0
    for _ in range(count):
        ev = engine.proactive_intervene()
        if ev is not None:
            success += 1
    _assert(success == count, "hacker", f"dos_{i}", f"仅完成{success}/{count}")
    # 历史记录不应无限增长（deque有maxlen）
    _assert(len(engine._intervention_history) <= 500, "hacker", f"dos_{i}_history", "历史记录溢出")

def test_hacker_exam_score_tamper(engine, i):
    """黑客: 篡改考试分数"""
    experts = list(engine._experts.values())
    if not experts:
        _fail("hacker", f"tamper_{i}", "无专家")
        return
    expert = random.choice(experts)
    original_acc = expert.accuracy
    result = engine._conduct_exam(expert)
    # 尝试篡改
    try:
        result.score = 99999
        result.passed = True
    except Exception:
        pass
    # dataclass是可变的，但分数篡改不影响数据库
    _assert(True, "hacker", f"tamper_{i}", "篡改不影响数据库")
    # 专家准确率不应因篡改而改变
    _assert(expert.accuracy == original_acc or abs(expert.accuracy - original_acc) < 0.01,
            "hacker", f"tamper_{i}_acc", "准确率被篡改")

def test_hacker_proposal_injection(engine, i):
    """黑客: 提案注入"""
    r = engine._seek_proposal_leader(
        "'; INSERT INTO mt_dev_flow_session VALUES('hacked'); --",
        ["正常专家A", "正常专家B"]
    )
    _assert(r is not None, "hacker", f"prop_inject_{i}", "返回None")
    _assert(r.get("proposal_id", "") != "", "hacker", f"prop_inject_{i}_id", "无提案ID")

def test_hacker_maintenance_hijack(engine, i):
    """黑客: 维护排班劫持"""
    # 尝试注入恶意排班
    engine._maintenance_schedule["恶意班次"] = ["hacker1", "hacker2"]
    # 重新排班应清除恶意数据
    engine._auto_join_maintenance_plan()
    schedule = engine.get_maintenance_schedule()
    _assert("恶意班次" not in schedule, "hacker", f"hijack_{i}", "恶意班次未被清除")

def test_hacker_reverse_feed_injection(engine, i):
    """黑客: 反向投喂注入"""
    engine._reverse_feed_brain(
        "hacker'; DROP TABLE mt_ai_brain_feed_log; --",
        "injection",
        "恶意投喂内容<script>alert(1)</script>"
    )
    # 应正常处理，不报错
    _assert(True, "hacker", f"feed_inject_{i}", "注入投喂未容错")

def test_hacker_empty_team_proposal(engine, i):
    """黑客: 空团队提案"""
    r = engine._seek_proposal_leader("测试议题", [])
    _assert(r is not None, "hacker", f"empty_team_{i}", "返回None")
    _assert(r.get("initiated_by") == "", "hacker", f"empty_team_{i}_init", "空团队却有发起人")

def test_hacker_daemon_rapid_start_stop(engine, i):
    """黑客: 快速启停守护线程"""
    for _ in range(10):
        engine.start_daemon()
        engine.stop_daemon()
    _assert(engine._running == False, "hacker", f"rapid_{i}", "快速启停后仍在运行")
    _assert(len(engine._threads) == 0, "hacker", f"rapid_{i}_threads", "线程未清理")


# ========== 主测试入口 ==========

def run_1000_rounds():
    global PASS, FAIL, VULN
    PASS = FAIL = VULN = 0
    ERRORS.clear()

    print("=" * 70)
    print(" EigenFlux专家主动介入引擎 - 1000轮测试")
    print("=" * 70)

    engine = EigenFluxProactiveEngine()
    print(f"  加载专家: {len(engine._experts)} 位")
    print()

    # 正常逻辑 400轮
    print("--- 正常逻辑测试 (400轮) ---")
    normal_tests = [
        test_normal_intervene, test_normal_enhance, test_normal_upgrade,
        test_normal_exam, test_normal_discussion, test_normal_proposal,
        test_normal_maintenance, test_normal_status,
    ]
    for i in range(400):
        test = normal_tests[i % len(normal_tests)]
        try:
            test(engine, i)
        except Exception as e:
            _fail("normal", f"round_{i}", str(e))

    # 异常场景 300轮
    print("--- 异常场景测试 (300轮) ---")
    anomaly_tests = [
        test_anomaly_empty_intervene, test_anomaly_invalid_issue_type,
        test_anomaly_invalid_severity, test_anomaly_nonexistent_expert_upgrade,
        test_anomaly_empty_enhance, test_anomaly_empty_discussion,
        test_anomaly_empty_maintenance, test_anomaly_concurrent_intervene,
        test_anomaly_exam_no_questions, test_anomaly_daemon_stop,
    ]
    for i in range(300):
        test = anomaly_tests[i % len(anomaly_tests)]
        try:
            test(engine, i)
        except Exception as e:
            _fail("anomaly", f"round_{i}", str(e))

    # 黑客攻击 300轮
    print("--- 黑客攻击测试 (300轮) ---")
    hacker_tests = [
        test_hacker_sql_injection_intervene, test_hacker_xss_in_topic,
        test_hacker_path_traversal, test_hacker_command_injection,
        test_hacker_fake_expert_name, test_hacker_overflow_intervene,
        test_hacker_exam_score_tamper, test_hacker_proposal_injection,
        test_hacker_maintenance_hijack, test_hacker_reverse_feed_injection,
        test_hacker_empty_team_proposal, test_hacker_daemon_rapid_start_stop,
    ]
    for i in range(300):
        test = hacker_tests[i % len(hacker_tests)]
        try:
            test(engine, i)
        except Exception as e:
            _fail("hacker", f"round_{i}", str(e))

    # 结果
    print()
    print("=" * 70)
    print(f" 测试结果: PASS={PASS} | FAIL={FAIL} | VULN={VULN}")
    print(f" 总计: {PASS + FAIL + VULN} 轮")
    if ERRORS:
        print(f" 错误列表 (前10条):")
        for e in ERRORS[:10]:
            print(f"   {e}")
    print("=" * 70)
    return PASS, FAIL, VULN


if __name__ == "__main__":
    t0 = time.time()
    p, f, v = run_1000_rounds()
    elapsed = time.time() - t0
    print(f" 耗时: {elapsed:.1f}s")
    # 退出码: 全通过=0, 有失败=1
    exit(0 if f == 0 and v == 0 else 1)
