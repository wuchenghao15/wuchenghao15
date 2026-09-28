#!/usr/bin/env python3
"""
test_andromeda_status_page.py — 仙女座状态页单元测试

覆盖:
  1. /api/data 正常返回
  2. /api/employees 搜索分页 (33,525 人)
  3. /api/employees 边界 (空查询、limit 超限、page 负数)
  4. /api/employees 搜索 name / type / source
  5. /api/sync/refresh
  6. /api/sync/push (mini 离线 400 / mock mini 在线 200)
  7. HTML /andromeda 页面关键元素存在
  8. DB 表完整性 (ai_employees 精选专家 + mt_andromeda 大表)
  9. mini 同步对比 8 表结构
  10. 守护进程 watchdog_status_page.py 健康检查

运行: python3 -m pytest engines/test_andromeda_status_page.py -v
     或 python3 engines/test_andromeda_status_page.py
"""
import os, sys, json, time, subprocess, unittest, sqlite3
from unittest.mock import patch, MagicMock

# 让 engines 包可导入
_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
_FLASK_APP_DIR = os.path.dirname(_ENGINES_DIR)
_DB_PATH = os.path.join(_FLASK_APP_DIR, "database", "app.db")

# 导入被测模块 (Flask app)
sys.path.insert(0, _ENGINES_DIR)
import andromeda_status_page as asp


class TestDatabase(unittest.TestCase):
    """DB 完整性检查 — 状态页所有 SELECT 的表都应存在"""
    
    def setUp(self):
        self.c = sqlite3.connect(_DB_PATH, timeout=5)
    
    def tearDown(self):
        self.c.close()
    
    def test_ai_employees_has_data(self):
        """精选专家 ai_employees 表有数据"""
        cnt = self.c.execute("SELECT COUNT(*) FROM ai_employees WHERE is_enabled=1").fetchone()[0]
        self.assertGreaterEqual(cnt, 10, f"ai_employees 至少应该有 10 个精选专家, 实际 {cnt}")
    
    def test_mt_andromeda_registry(self):
        """注册中心大表 mt_andromeda_employee_registry 有 33k+"""
        cnt = self.c.execute("SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE enabled=1").fetchone()[0]
        self.assertGreaterEqual(cnt, 30000, f"mt_andromeda_employee_registry 至少 30k, 实际 {cnt}")
    
    def test_mt_andromeda_schema(self):
        """注册中心表有 employee_id / name / employee_type 列"""
        cols = [r[1] for r in self.c.execute(
            "PRAGMA table_info(mt_andromeda_employee_registry)").fetchall()]
        for must_have in ["employee_id", "name", "employee_type", "enabled", "level"]:
            self.assertIn(must_have, cols, f"表缺列: {must_have}")
    
    def test_sync_tables_exist(self):
        """mini 同步对比用的 8 张表都存在"""
        expected = [
            "ai_employees", "ai_brain_enhanced_knowledge", 
            "mt_daemon_registry", "knowledge_graph_nodes",
            "knowledge_graph_relations", "mt_ai_self_evolution_log",
            "ai_learning_records", "system_notifications",
        ]
        actual = [r[0] for r in self.c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in expected:
            self.assertIn(t, actual, f"同步对比表缺失: {t}")
    
    def test_mini_push_tables_exist(self):
        """手动同步 (开发机→mini) 的 7 张表"""
        for t, pk in asp.MINI_SYNC_TABLES:
            cnt = self.c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            self.assertGreaterEqual(cnt, 0, f"{t} 应该可查询")


class TestApiData(unittest.TestCase):
    """/api/data 正常返回"""
    
    def setUp(self):
        self.app = asp.app
        self.client = self.app.test_client()
    
    def test_data_200(self):
        r = self.client.get('/api/data')
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertIn("brain_total", d)
        self.assertIn("daemons", d)
        self.assertIn("notifications", d)
        self.assertIn("employee_total", d)
        self.assertIn("mini", d)
        self.assertIn("mini_sync", d)
        self.assertIn("generated_at", d)
    
    def test_brain_total_positive(self):
        d = self.client.get('/api/data').get_json()
        self.assertGreater(d["brain_total"], 1_000_000, "脑库应 > 100 万条")
    
    def test_employee_total_33k(self):
        """之前的 bug: 读 ai_employees 只有 239"""
        d = self.client.get('/api/data').get_json()
        self.assertGreaterEqual(
            d["employee_total"], 30000,
            f"AI 员工总数应 >= 30k, 实际 {d['employee_total']} — 很可能读错表!"
        )
    
    def test_mini_sync_has_8_tables(self):
        d = self.client.get('/api/data').get_json()
        self.assertEqual(len(d["mini_sync"]["tables"]), 8)
    
    def test_mini_sync_table_labels(self):
        """mini_sync 每表应有 label/local/mini/diff"""
        d = self.client.get('/api/data').get_json()
        for t in d["mini_sync"]["tables"]:
            self.assertIn("label", t)
            self.assertIn("local", t)
            self.assertIn("mini", t)
            self.assertIn("online", d["mini_sync"])


class TestApiEmployees(unittest.TestCase):
    """/api/employees 搜索分页"""
    
    def setUp(self):
        self.app = asp.app
        self.client = self.app.test_client()
    
    def test_default_pagination(self):
        """默认参数 page=1 limit=20"""
        r = self.client.get('/api/employees')
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertTrue(d["ok"])
        self.assertGreaterEqual(d["total"], 30000)
        self.assertEqual(d["page"], 1)
        self.assertEqual(len(d["rows"]), 20)
        self.assertGreaterEqual(d["pages"], 1000)
    
    def test_search_by_name(self):
        """搜 name='expert' — 应该有 33k+ 结果"""
        r = self.client.get('/api/employees?q=expert&limit=3')
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertGreater(d["total"], 30000)
        self.assertEqual(len(d["rows"]), 3)
    
    def test_search_by_type(self):
        """按 employee_type 搜 eigenflux_expert"""
        r = self.client.get('/api/employees?q=eigenflux_expert&limit=2')
        d = r.get_json()
        self.assertGreater(d["total"], 30000)
    
    def test_search_no_match(self):
        """搜不存在的关键词 → 0 结果"""
        r = self.client.get('/api/employees?q=zzzz_not_exist_xyz&limit=5')
        d = r.get_json()
        self.assertEqual(d["total"], 0)
        self.assertEqual(len(d["rows"]), 0)
    
    def test_limit_bounds(self):
        """limit 必须在 1-100 之间"""
        # 超过 100 → 服务器会 cap 到 100
        r = self.client.get('/api/employees?limit=200')
        d = r.get_json()
        self.assertLessEqual(len(d["rows"]), 100)
    
    def test_pagination_page(self):
        """翻到第 2 页, rows 应该不同"""
        r1 = self.client.get('/api/employees?page=1&limit=5')
        r2 = self.client.get('/api/employees?page=2&limit=5')
        d1, d2 = r1.get_json(), r2.get_json()
        self.assertNotEqual(
            d1["rows"][0]["employee_id"], 
            d2["rows"][0]["employee_id"],
            "第 1 页和第 2 页的第一条应该不同"
        )
    
    def test_types_aggregation(self):
        """类型聚合应该有 eigenflux_expert"""
        d = self.client.get('/api/employees?limit=1').get_json()
        types = {t["type"]: t["count"] for t in d["types"]}
        self.assertIn("eigenflux_expert", types)
        self.assertGreater(types["eigenflux_expert"], 30000)
    
    def test_row_structure(self):
        """每行应有 employee_id / name / employee_type 等"""
        d = self.client.get('/api/employees?limit=1').get_json()
        row = d["rows"][0]
        for must_have in ["employee_id", "name", "employee_type", 
                          "call_count", "level", "description"]:
            self.assertIn(must_have, row, f"员工对象缺字段: {must_have}")
    
    def test_negative_page(self):
        """page=-1 应该被 clamp 到 1"""
        r = self.client.get('/api/employees?page=-5')
        d = r.get_json()
        self.assertEqual(d["page"], 1)


class TestApiSyncRefresh(unittest.TestCase):
    """/api/sync/refresh 清缓存"""
    
    def setUp(self):
        self.app = asp.app
        self.client = self.app.test_client()
    
    def test_refresh_200(self):
        r = self.client.post('/api/sync/refresh')
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertTrue(d["ok"])
        self.assertIn("sync", d)
        self.assertIn("tables", d["sync"])


class TestApiSyncPush(unittest.TestCase):
    """/api/sync/push — mini 离线/在线"""
    
    def setUp(self):
        self.app = asp.app
        self.client = self.app.test_client()
    
    def test_push_mini_offline_400(self):
        """mini 离线 → 返回 400"""
        with patch.object(asp, '_check_mini', return_value={"online": False}):
            r = self.client.post('/api/sync/push')
            self.assertEqual(r.status_code, 400)
            d = r.get_json()
            self.assertFalse(d["ok"])
            self.assertIn("离线", d["error"])
    
    def test_push_mini_online_success(self):
        """mock mini 在线 + mock subprocess → 返回 200"""
        mock_mini = {
            "online": True, "ssh_ok": True, "host": "192.168.31.9",
            "name": "HULK-MACMINI", "rtt_ms": 5.0, "uptime": "5 days",
            "load": [1.0, 1.0, 1.0], "users": 2, "last_check": "21:00:00"
        }
        # sync_push 内部调用 4 次 subprocess.run:
        #   1. ping mini (asp._check_mini 里已 mock, 不走这里)
        #   2. ssh_pull  — 期待 stdout 是 JSON (各表 cols/rows)
        #   3. scp push  — 期待 returncode=0
        #   4. ssh_push  — 期待 stdout 是 JSON (results dict)
        # 由于我们 mock 了 _check_mini, 跳过了 ping/ssh_ok 检测,
        # 进入 /api/sync/push 后直接 ssh_pull → scp → ssh_push
        empty_tables = {tbl: {"cols": ["id"], "rows": []}
                        for tbl, _ in asp.MINI_SYNC_TABLES}
        push_results = {
            "ok": True, "mini_push": "OK",
            "results": [f"PUSH {t}: 0 upsert" for t, _ in asp.MINI_SYNC_TABLES],
        }
        
        def _fake_run(*args, **kwargs):
            mock = MagicMock(); mock.returncode = 0; mock.stderr = ""
            # 看命令参数判断是 pull 还是 push
            cmd = args[0] if args else kwargs.get("args", [])
            cmd_str = " ".join(cmd) if cmd else ""
            if "python3 -" in cmd_str and "pull" not in cmd_str:
                # ssh_push (远端同步) — 返回 JSON 结果
                mock.stdout = json.dumps(push_results)
            elif "python3 -" in cmd_str:
                # ssh_pull (拉取 mini 数据) — 返回空表 JSON
                mock.stdout = json.dumps(empty_tables)
            elif "scp" in cmd_str:
                mock.stdout = ""; mock.returncode = 0
            elif "ping" in cmd_str:
                mock.stdout = "ok"; mock.returncode = 0
            else:
                mock.stdout = ""
            return mock
        
        with patch.object(asp, '_check_mini', return_value=mock_mini), \
             patch.object(asp.subprocess, 'run', side_effect=_fake_run):
            r = self.client.post('/api/sync/push')
            self.assertEqual(r.status_code, 200)
            d = r.get_json()
            self.assertTrue(d["ok"])


class TestHtmlPage(unittest.TestCase):
    """/andromeda 页面关键元素"""
    
    def setUp(self):
        self.app = asp.app
        self.client = self.app.test_client()
    
    def test_page_200(self):
        r = self.client.get('/andromeda')
        self.assertEqual(r.status_code, 200)
    
    def test_page_has_kpi(self):
        html = self.client.get('/andromeda').get_data(as_text=True)
        self.assertIn("kpi-brain", html)
        self.assertIn("kpi-daemon", html)
        self.assertIn("kpi-evo", html)
        self.assertIn("kpi-writer", html)
    
    def test_page_has_mini_bar(self):
        html = self.client.get('/andromeda').get_data(as_text=True)
        self.assertIn("mini-bar", html)
        self.assertIn("mini-dot", html)
    
    def test_page_has_sync_panel(self):
        html = self.client.get('/andromeda').get_data(as_text=True)
        self.assertIn("sync-panel", html)
        self.assertIn("btn-sync-refresh", html)
        self.assertIn("btn-sync-push", html)
    
    def test_page_has_employee_center(self):
        """AI 员工注册中心 + 搜索框"""
        html = self.client.get('/andromeda').get_data(as_text=True)
        self.assertIn("emp-search", html)
        self.assertIn("emp-list", html)
        self.assertIn("emp-pager", html)
        self.assertIn("注册中心", html)
    
    def test_page_has_charts(self):
        html = self.client.get('/andromeda').get_data(as_text=True)
        self.assertIn("chart.js", html)
        self.assertIn("brainPie", html)


class TestWatchdogProcess(unittest.TestCase):
    """守护进程健康检查 (只检查状态, 不 kill)"""
    
    def test_watchdog_running(self):
        """watchdog_status_page.py 守护进程在跑"""
        result = subprocess.run(
            ["pgrep", "-f", "watchdog_status_page"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertGreater(
            len(result.stdout.strip()), 0,
            "watchdog_status_page.py 守护进程应该在跑"
        )
    
    def test_status_page_port_8889(self):
        """8889 端口有进程监听"""
        result = subprocess.run(
            ["lsof", "-ti", "tcp:8889"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertGreater(
            len(result.stdout.strip()), 0,
            "8889 端口应该有进程监听"
        )
    
    def test_status_page_api_responsive(self):
        """API /api/data 2 秒内响应"""
        import urllib.request
        try:
            r = urllib.request.urlopen(
                "http://localhost:8889/api/data", timeout=3
            )
            self.assertEqual(r.status, 200)
        except Exception as e:
            self.fail(f"API 无响应: {e}")


if __name__ == "__main__":
    # 先确认 DB 路径存在
    assert os.path.exists(_DB_PATH), f"DB 不存在: {_DB_PATH}"
    print(f"DB: {_DB_PATH}")
    print(f"运行单元测试...\n")
    unittest.main(verbosity=2)
