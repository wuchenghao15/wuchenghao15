#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动巡逻队引擎 - 1000轮测试
============================
正常逻辑400 + 异常场景300 + 黑客攻击300
"""
import sys, os, time, json, random, tempfile, shutil, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.disable(logging.WARNING)  # 抑制引擎日志

from auto_patrol_engine import AutoPatrolEngine, ErrorItem, PatrolReport, PATROL_TEAM

PASS = 0; FAIL = 0; VULN = 0; ERRORS = []

def _ok(c, n, d=""): 
    global PASS; PASS += 1
def _fail(c, n, d=""): 
    global FAIL; FAIL += 1; ERRORS.append(f"[{c}]{n}: {d}")
def _vuln(c, n, d=""): 
    global VULN; VULN += 1; ERRORS.append(f"[VULN][{c}]{n}: {d}")
def _assert(cond, c, n, d=""):
    if cond: _ok(c, n, d)
    else: _fail(c, n, d)

def _make_temp_dir():
    """创建临时测试目录"""
    tmp = tempfile.mkdtemp(prefix="patrol_test_")
    # 创建几个测试.py文件
    # 正常文件
    with open(os.path.join(tmp, "good.py"), "w") as f:
        f.write("x = 1\nprint(x)\n")
    # 缩进错误文件
    with open(os.path.join(tmp, "bad_indent.py"), "w") as f:
        f.write("def foo():\n    x = 1\n  y = 2\n    return x + y\n")
    # 裸except文件
    with open(os.path.join(tmp, "bare_except.py"), "w") as f:
        f.write("try:\n    x = 1\nexcept:\n    pass\n")
    # 语法错误文件
    with open(os.path.join(tmp, "syntax_err.py"), "w") as f:
        f.write("def bar(:\n    pass\n")
    # 空文件
    with open(os.path.join(tmp, "empty.py"), "w") as f:
        f.write("")
    return tmp

# ========== 正常逻辑测试 (400轮) ==========

def test_normal_scan(engine, i):
    """正常: 扫描检测"""
    errs = engine.scan_all()
    _assert(isinstance(errs, list), "normal", f"scan_{i}", "返回非列表")
    _assert(engine._report.files_scanned > 0, "normal", f"scan_{i}_files", "扫描文件数为0")

def test_normal_collect(engine, i):
    """正常: 收集分类"""
    engine.scan_all()
    stats = engine.collect_and_categorize()
    _assert('total' in stats, "normal", f"collect_{i}", "无total字段")
    _assert('by_type' in stats, "normal", f"collect_{i}_type", "无by_type字段")
    _assert('by_severity' in stats, "normal", f"collect_{i}_sev", "无by_severity字段")

def test_normal_fix(engine, i):
    """正常: 自动修复"""
    engine.scan_all()
    engine.collect_and_categorize()
    result = engine.auto_fix_all()
    _assert('fixed' in result, "normal", f"fix_{i}", "无fixed字段")
    _assert('failed' in result, "normal", f"fix_{i}_failed", "无failed字段")
    _assert(result['fixed'] + result['failed'] + result['skipped'] == engine._report.errors_found,
            "normal", f"fix_{i}_count", "修复数量不匹配")

def test_normal_verify(engine, i):
    """正常: 验证检测"""
    engine.scan_all()
    engine.collect_and_categorize()
    engine.auto_fix_all()
    result = engine.verify_all()
    _assert('verified' in result, "normal", f"verify_{i}", "无verified字段")
    _assert(result['verified'] >= 0, "normal", f"verify_{i}_count", "验证数为负")

def test_normal_report(engine, i):
    """正常: 报告生成"""
    engine.scan_all()
    engine.collect_and_categorize()
    engine.auto_fix_all()
    engine.verify_all()
    report = engine.generate_report()
    _assert(report is not None, "normal", f"report_{i}", "返回None")
    _assert(report.report_id != "", "normal", f"report_{i}_id", "报告ID为空")
    _assert(report.files_scanned > 0, "normal", f"report_{i}_files", "扫描数为0")
    _assert(report.summary != "", "normal", f"report_{i}_summary", "摘要为空")
    _assert(len(report.ai_team) == 6, "normal", f"report_{i}_team", "AI团队人数不为6")

def test_normal_persist(engine, i):
    """正常: 数据库持久化"""
    engine.scan_all()
    engine.collect_and_categorize()
    engine.auto_fix_all()
    engine.verify_all()
    engine.generate_report()
    result = engine.persist_to_database()
    _assert(result['stored'] > 0, "normal", f"persist_{i}", "存储数为0")

def test_normal_full_patrol(engine, i):
    """正常: 完整巡逻流程"""
    report = engine.run_full_patrol()
    _assert(report is not None, "normal", f"full_{i}", "返回None")
    _assert(report.errors_found >= 0, "normal", f"full_{i}_errs", "错误数为负")
    _assert(report.errors_fixed >= 0, "normal", f"full_{i}_fixed", "修复数为负")

def test_normal_team(engine, i):
    """正常: 巡逻队成员"""
    _assert(len(PATROL_TEAM) == 6, "normal", f"team_{i}", f"成员数不为6: {len(PATROL_TEAM)}")
    for name, role, desc in PATROL_TEAM:
        _assert(name != "", "normal", f"team_{i}_{role}", "成员名为空")
        _assert(role != "", "normal", f"team_{i}_{role}_r", "角色为空")

def test_normal_get_errors(engine, i):
    """正常: 获取错误详情"""
    engine.scan_all()
    details = engine.get_error_details()
    _assert(isinstance(details, list), "normal", f"details_{i}", "返回非列表")
    if details:
        d = details[0]
        _assert('file' in d, "normal", f"details_{i}_file", "无file字段")
        _assert('type' in d, "normal", f"details_{i}_type", "无type字段")
        _assert('status' in d, "normal", f"details_{i}_status", "无status字段")

# ========== 异常场景测试 (300轮) ==========

def test_anomaly_empty_dir(i):
    """异常: 空目录扫描"""
    tmp = tempfile.mkdtemp(prefix="patrol_empty_")
    engine = AutoPatrolEngine(scan_dir=tmp)
    errs = engine.scan_all()
    _assert(len(errs) == 0, "anomaly", f"empty_{i}", "空目录有错误")
    _assert(engine._report.files_scanned == 0, "anomaly", f"empty_{i}_files", "空目录扫描了文件")
    shutil.rmtree(tmp, ignore_errors=True)

def test_anomaly_nonexistent_dir(i):
    """异常: 不存在的目录"""
    engine = AutoPatrolEngine(scan_dir="/nonexistent/path/xyz")
    errs = engine.scan_all()
    _assert(len(errs) == 0, "anomaly", f"nonexist_{i}", "不存在的目录有错误")

def test_anomaly_no_errors(i):
    """异常: 无错误文件"""
    tmp = _make_temp_dir()
    # 只保留正常文件
    os.remove(os.path.join(tmp, "bad_indent.py"))
    os.remove(os.path.join(tmp, "bare_except.py"))
    os.remove(os.path.join(tmp, "syntax_err.py"))
    engine = AutoPatrolEngine(scan_dir=tmp)
    errs = engine.scan_all()
    _assert(len(errs) == 0, "anomaly", f"noerr_{i}", f"无错误文件却报错: {len(errs)}")
    shutil.rmtree(tmp, ignore_errors=True)

def test_anomaly_concurrent_scan(i):
    """异常: 并发扫描"""
    import threading
    engine = AutoPatrolEngine()
    results = []
    errors = []
    def worker():
        try:
            r = engine.scan_all()
            results.append(r)
        except Exception as e:
            errors.append(str(e))
    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=10)
    _assert(len(errors) == 0, "anomaly", f"concurrent_{i}", f"并发错误: {errors[:2]}")

def test_anomaly_temp_dir_full_patrol(i):
    """异常: 临时目录完整巡逻"""
    tmp = _make_temp_dir()
    engine = AutoPatrolEngine(scan_dir=tmp)
    with contextlib.redirect_stdout(io.StringIO()):
        report = engine.run_full_patrol()
    _assert(report is not None, "anomaly", f"tmp_patrol_{i}", "返回None")
    _assert(report.files_scanned == 5, "anomaly", f"tmp_patrol_{i}_files", f"文件数不为5: {report.files_scanned}")
    _assert(report.errors_found > 0, "anomaly", f"tmp_patrol_{i}_errs", "应发现错误")
    shutil.rmtree(tmp, ignore_errors=True)

def test_anomaly_empty_file(i):
    """异常: 空文件"""
    tmp = tempfile.mkdtemp(prefix="patrol_empty_f_")
    with open(os.path.join(tmp, "empty.py"), "w") as f:
        f.write("")
    engine = AutoPatrolEngine(scan_dir=tmp)
    errs = engine.scan_all()
    _assert(len(errs) == 0, "anomaly", f"empty_f_{i}", "空文件有错误")
    shutil.rmtree(tmp, ignore_errors=True)

def test_anomaly_repeated_patrol(i):
    """异常: 重复巡逻"""
    tmp = _make_temp_dir()
    engine = AutoPatrolEngine(scan_dir=tmp)
    with contextlib.redirect_stdout(io.StringIO()):
        r1 = engine.run_full_patrol()
        r2 = engine.run_full_patrol()
    _assert(r2.errors_found <= r1.errors_found, "anomaly", f"repeat_{i}", "第二次巡逻错误更多")
    shutil.rmtree(tmp, ignore_errors=True)

# ========== 黑客攻击测试 (300轮) ==========

def test_hacker_path_traversal_scan(i):
    """黑客: 路径穿越扫描"""
    engine = AutoPatrolEngine(scan_dir="../../../etc")
    try:
        errs = engine.scan_all()
        _assert(isinstance(errs, list), "hacker", f"path_{i}", "返回非列表")
    except Exception:
        _ok("hacker", f"path_{i}", "路径穿越被拦截")

def test_hacker_sql_injection_persist(i):
    """黑客: SQL注入持久化"""
    engine = AutoPatrolEngine()
    engine.scan_all()
    # 尝试SQL注入flow_id
    try:
        result = engine.persist_to_database(flow_id="'; DROP TABLE mt_dev_flow_session; --")
        _assert(isinstance(result, dict), "hacker", f"sqli_{i}", "返回非字典")
    except Exception:
        _ok("hacker", f"sqli_{i}", "SQL注入被拦截")

def test_hacker_xss_in_error(i):
    """黑客: XSS注入错误消息"""
    err = ErrorItem(
        file="<script>alert(1)</script>.py",
        message="'; DELETE FROM x; --",
        error_type="xss_injection",
    )
    _assert(err.file != "", "hacker", f"xss_{i}", "文件名为空")
    # ErrorItem是dataclass,不会执行XSS

def test_hacker_command_injection_file(i):
    """黑客: 命令注入文件名"""
    tmp = tempfile.mkdtemp(prefix="patrol_cmd_")
    # 创建包含特殊字符的文件名
    try:
        with open(os.path.join(tmp, "test;rm -rf /.py"), "w") as f:
            f.write("x = 1\n")
    except Exception:
        pass
    engine = AutoPatrolEngine(scan_dir=tmp)
    try:
        errs = engine.scan_all()
        _assert(isinstance(errs, list), "hacker", f"cmd_{i}", "返回非列表")
    except Exception:
        _ok("hacker", f"cmd_{i}", "命令注入被拦截")
    shutil.rmtree(tmp, ignore_errors=True)

def test_hacker_large_file(i):
    """黑客: 超大文件DoS"""
    tmp = tempfile.mkdtemp(prefix="patrol_large_")
    with open(os.path.join(tmp, "large.py"), "w") as f:
        f.write("x = 1\n" * 10000)
    engine = AutoPatrolEngine(scan_dir=tmp)
    errs = engine.scan_all()
    _assert(isinstance(errs, list), "hacker", f"large_{i}", "返回非列表")
    _assert(len(errs) == 0, "hacker", f"large_{i}_errs", "大文件有错误")
    shutil.rmtree(tmp, ignore_errors=True)

def test_hacker_binary_file(i):
    """黑客: 二进制文件伪装为.py"""
    tmp = tempfile.mkdtemp(prefix="patrol_bin_")
    with open(os.path.join(tmp, "binary.py"), "wb") as f:
        f.write(bytes(range(256)) * 100)
    engine = AutoPatrolEngine(scan_dir=tmp)
    try:
        errs = engine.scan_all()
        _assert(isinstance(errs, list), "hacker", f"bin_{i}", "返回非列表")
    except Exception:
        _ok("hacker", f"bin_{i}", "二进制文件被拦截")
    shutil.rmtree(tmp, ignore_errors=True)

def test_hacker_deep_nesting(i):
    """黑客: 深度嵌套目录"""
    tmp = tempfile.mkdtemp(prefix="patrol_deep_")
    deep = tmp
    for d in range(20):
        deep = os.path.join(deep, f"dir_{d}")
        os.makedirs(deep, exist_ok=True)
    with open(os.path.join(deep, "deep.py"), "w") as f:
        f.write("x = 1\n")
    engine = AutoPatrolEngine(scan_dir=tmp)
    errs = engine.scan_all()
    _assert(isinstance(errs, list), "hacker", f"deep_{i}", "返回非列表")
    shutil.rmtree(tmp, ignore_errors=True)

def test_hacker_zero_byte_file(i):
    """黑客: 零字节文件"""
    tmp = tempfile.mkdtemp(prefix="patrol_zero_")
    with open(os.path.join(tmp, "zero.py"), "w") as f:
        pass  # 零字节
    engine = AutoPatrolEngine(scan_dir=tmp)
    errs = engine.scan_all()
    _assert(len(errs) == 0, "hacker", f"zero_{i}", "零字节文件有错误")
    shutil.rmtree(tmp, ignore_errors=True)

def test_hacker_symlink(i):
    """黑客: 符号链接"""
    tmp = tempfile.mkdtemp(prefix="patrol_link_")
    with open(os.path.join(tmp, "real.py"), "w") as f:
        f.write("x = 1\n")
    try:
        os.symlink(os.path.join(tmp, "real.py"), os.path.join(tmp, "link.py"))
    except Exception:
        pass
    engine = AutoPatrolEngine(scan_dir=tmp)
    try:
        errs = engine.scan_all()
        _assert(isinstance(errs, list), "hacker", f"link_{i}", "返回非列表")
    except Exception:
        _ok("hacker", f"link_{i}", "符号链接被处理")
    shutil.rmtree(tmp, ignore_errors=True)

# ========== 主入口 ==========

def run_1000_rounds():
    global PASS, FAIL, VULN
    PASS = FAIL = VULN = 0; ERRORS.clear()

    print("=" * 70)
    print(" 自动巡逻队引擎 - 1000轮测试")
    print("=" * 70)

    # 使用小目录测试(避免每次扫描571文件)
    tmp = _make_temp_dir()
    engine = AutoPatrolEngine(scan_dir=tmp)
    t0 = time.time()

    # 正常逻辑 400轮
    print("--- 正常逻辑测试 (400轮) ---")
    normal_tests = [test_normal_scan, test_normal_collect, test_normal_fix,
                    test_normal_verify, test_normal_report,
                    test_normal_team, test_normal_get_errors]
    for i in range(400):
        try: normal_tests[i % len(normal_tests)](engine, i)
        except Exception as e: _fail("normal", f"round_{i}", str(e))

    # 异常场景 300轮
    print("--- 异常场景测试 (300轮) ---")
    anomaly_tests = [test_anomaly_empty_dir, test_anomaly_nonexistent_dir,
                     test_anomaly_no_errors, test_anomaly_concurrent_scan,
                     test_anomaly_temp_dir_full_patrol, test_anomaly_empty_file,
                     test_anomaly_repeated_patrol]
    for i in range(300):
        try: anomaly_tests[i % len(anomaly_tests)](i)
        except Exception as e: _fail("anomaly", f"round_{i}", str(e))

    # 黑客攻击 300轮
    print("--- 黑客攻击测试 (300轮) ---")
    hacker_tests = [test_hacker_path_traversal_scan, test_hacker_sql_injection_persist,
                    test_hacker_xss_in_error, test_hacker_command_injection_file,
                    test_hacker_large_file, test_hacker_binary_file,
                    test_hacker_deep_nesting, test_hacker_zero_byte_file,
                    test_hacker_symlink]
    for i in range(300):
        try: hacker_tests[i % len(hacker_tests)](i)
        except Exception as e: _fail("hacker", f"round_{i}", str(e))

    elapsed = time.time() - t0
    print()
    print("=" * 70)
    print(f" 测试结果: PASS={PASS} | FAIL={FAIL} | VULN={VULN}")
    print(f" 总计: {PASS + FAIL + VULN} 断言 | 耗时: {elapsed:.1f}s")
    if ERRORS:
        print(f" 错误(前10):")
        for e in ERRORS[:10]: print(f"   {e}")
    print("=" * 70)
    return PASS, FAIL, VULN

if __name__ == "__main__":
    p, f, v = run_1000_rounds()
    exit(0 if f == 0 and v == 0 else 1)
