# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
布局调节AI员工 - LayoutAdjusterAIEmployee
职责：
1. 实时接收前端上报的页面排版快照
2. 基于20条排版割裂检测规则诊断布局问题
3. 生成动态CSS修复指令并下发前端
4. 记录所有操作日志供AI学习
"""
import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

logger = logging.getLogger(__name__)

SPLIT_AI_DB = os.path.join(BASE_DIR, 'split_databases', 'ai.db')

try:
    from ai_engines.ai_employees import AIEmployee
    _BASE_AVAILABLE = True
except ImportError:
    _BASE_AVAILABLE = False
    class AIEmployee:
        def __init__(self, employee_id: str, name: str, role: str, skills: list):
            self.employee_id = employee_id
            self.name = name
            self.role = role
            self.skills = skills
            self.status = 'active'
            self.created_at = datetime.now().isoformat()
            self.last_task = None
            self.empowerment_enabled = False

        def execute_task(self, task):
            return {'success': True, 'employee_id': self.employee_id, 'result': 'done', 'timestamp': datetime.now().isoformat()}


# ==================== 20条排版割裂检测规则 ====================
LAYOUT_FRAGMENTATION_RULES: List[Dict[str, Any]] = [
    {
        'rule_id': 'LF001', 'name': '主内容区水平溢出', 'category': 'overflow',
        'severity': 'critical', 'enabled': 1,
        'description': 'mtscos-main / .mtscos-content-scroll 水平溢出导致横向滚动条',
        'detection': 'main.clientWidth < main.scrollWidth - 2 OR content.scrollWidth > viewport.w * 0.82',
        'threshold': {'overflow_pixels': 4},
        'fix_template': '{{selector}} { overflow-x: hidden; max-width: 100%; box-sizing: border-box; }'
    },
    {
        'rule_id': 'LF002', 'name': '卡片高度超出可视区', 'category': 'overflow',
        'severity': 'high', 'enabled': 1,
        'description': '卡片/面板内容超出父容器导致内容被裁切',
        'detection': 'el.h > parent.h * 1.1 && el.h - parent.h > 30',
        'threshold': {'excess_ratio': 1.1, 'min_pixels': 30},
        'fix_template': '{{selector}} { max-height: {{parent_h}}px; overflow-y: auto; }'
    },
    {
        'rule_id': 'LF003', 'name': '侧边栏内容纵向溢出', 'category': 'overflow',
        'severity': 'high', 'enabled': 1,
        'description': '侧边栏菜单项过多导致底部用户信息/退出按钮被挤出可视区',
        'detection': 'sidebar_nav.h > sidebar.h - 180',
        'threshold': {'max_nav_height_ratio': 0.75},
        'fix_template': '.mtscos-sidebar-nav { flex: 1 1 auto; overflow-y: auto; scrollbar-width: none; } .mtscos-sidebar-nav::-webkit-scrollbar { display: none; }'
    },
    {
        'rule_id': 'LF004', 'name': '元素重叠（覆盖）', 'category': 'overlap',
        'severity': 'critical', 'enabled': 1,
        'description': '任意两个非嵌套可见元素的矩形交集面积>0',
        'detection': 'rectsIntersect(a,b) && intersectionArea > threshold',
        'threshold': {'min_intersection_area': 100},
        'fix_template': '{{selector}} { position: relative; z-index: {{z}}; }'
    },
    {
        'rule_id': 'LF005', 'name': '侧边栏宽度偏移(20%)', 'category': 'sidebar',
        'severity': 'high', 'enabled': 1,
        'description': '非mini态下侧边栏宽度不是视图宽度的20%±3px',
        'detection': '!body.sidebar-mini && Math.abs(sidebar.w - viewport.w*0.2) > 3',
        'threshold': {'tolerance_px': 3, 'expected_ratio': 0.20},
        'fix_template': '.mtscos-sidebar { width: 20% !important; } .mtscos-main { margin-left: 20% !important; }'
    },
    {
        'rule_id': 'LF006', 'name': 'mini侧边栏宽度偏移(10%)', 'category': 'sidebar',
        'severity': 'high', 'enabled': 1,
        'description': 'mini态下侧边栏宽度不是10%±3px',
        'detection': 'body.sidebar-mini && !body.sidebar-hovered && Math.abs(sidebar.w - viewport.w*0.1) > 3',
        'threshold': {'tolerance_px': 3, 'expected_ratio': 0.10},
        'fix_template': 'body.sidebar-mini .mtscos-sidebar { width: 10% !important; } body.sidebar-mini .mtscos-main { margin-left: 10% !important; }'
    },
    {
        'rule_id': 'LF007', 'name': '首页三区块比例偏离1:7:2', 'category': 'homepage',
        'severity': 'medium', 'enabled': 1,
        'description': '首页Header/Main/Footer高度比例明显偏离1:7:2',
        'detection': 'isHome && Math.abs(header_h/main_h - 1/7) > 0.15 || Math.abs(footer_h/main_h - 2/7) > 0.25',
        'threshold': {'header_ratio': 0.1428, 'main_ratio': 1.0, 'footer_ratio': 0.2857, 'tolerance': 0.15},
        'fix_template': '.home-header { min-height: 10vh; } .home-main { min-height: 70vh; } .home-footer { min-height: 20vh; }'
    },
    {
        'rule_id': 'LF008', 'name': '字体过小(可读性)', 'category': 'typography',
        'severity': 'medium', 'enabled': 1,
        'description': '可见文本节点计算font-size<11px导致难以阅读',
        'detection': 'el.computedStyle.fontSize < 11px && el.offsetParent !== null',
        'threshold': {'min_font_px': 11},
        'fix_template': '{{selector}} { font-size: 12px !important; line-height: 1.5 !important; }'
    },
    {
        'rule_id': 'LF009', 'name': '文本行高不足', 'category': 'typography',
        'severity': 'low', 'enabled': 1,
        'description': '多行文本行高<字体尺寸*1.35导致行文字粘连',
        'detection': 'el.lineHeight / el.fontSize < 1.35 && el.text.lines > 2',
        'threshold': {'min_ratio': 1.35},
        'fix_template': '{{selector}} { line-height: 1.6 !important; }'
    },
    {
        'rule_id': 'LF010', 'name': 'Flex容器子项压缩过度', 'category': 'flexgrid',
        'severity': 'high', 'enabled': 1, 'description': 'display:flex容器中某子项宽度 < 其min-content宽度的85%',
        'detection': 'el.width < el.scrollWidth * 0.85 && parent.style.display=="flex"',
        'threshold': {'min_shrink_ratio': 0.85},
        'fix_template': '{{selector}} { flex-shrink: 0; min-width: fit-content; }'
    },
    {
        'rule_id': 'LF011', 'name': 'Grid网格项塌陷', 'category': 'flexgrid',
        'severity': 'high', 'enabled': 1,
        'description': 'Grid项实际宽高小于预期的1/fr等价尺寸',
        'detection': 'gridItem.w < expectedW * 0.7 || gridItem.h < expectedH * 0.7',
        'threshold': {'min_ratio': 0.7},
        'fix_template': '{{selector}} { min-width: 0; min-height: 0; overflow: hidden; }'
    },
    {
        'rule_id': 'LF012', 'name': '表格列过度压缩', 'category': 'table',
        'severity': 'high', 'enabled': 1,
        'description': '表格单元格宽度<内填充*2+最小可读宽度，内容换行过多',
        'detection': 'td/th.width < 60 && td.textContent.length > 4',
        'threshold': {'min_cell_px': 60},
        'fix_template': '{{table_selector}} { table-layout: auto; width: 100%; } {{td_selector}} { white-space: nowrap; min-width: 80px; }'
    },
    {
        'rule_id': 'LF013', 'name': '固定定位元素遮挡主内容', 'category': 'position',
        'severity': 'critical', 'enabled': 1,
        'description': 'position:fixed元素底部边缘与main区顶部重叠>50%',
        'detection': 'fixedEl.bottom > main.top && overlapArea/fixedEl.area > 0.5',
        'threshold': {'min_overlap_ratio': 0.5},
        'fix_template': '.mtscos-main { padding-top: {{fixed_bottom}}px; }'
    },
    {
        'rule_id': 'LF014', 'name': '内边距/外边距负值过大', 'category': 'spacing',
        'severity': 'medium', 'enabled': 1,
        'description': '负margin绝对值 > 元素自身宽/高的30%',
        'detection': 'Math.abs(el.marginTop) > el.h*0.3 || Math.abs(el.marginLeft) > el.w*0.3',
        'threshold': {'max_negative_ratio': 0.30},
        'fix_template': '{{selector}} { margin: 0 !important; transform: none !important; }'
    },
    {
        'rule_id': 'LF015', 'name': '图片未缩放导致排版破裂', 'category': 'image',
        'severity': 'high', 'enabled': 1,
        'description': 'img/video等元素naturalWidth > parent.width*1.2且未设置max-width',
        'detection': 'img.naturalWidth > parent.w*1.2 && img.style.maxWidth===""',
        'threshold': {'max_ratio': 1.2},
        'fix_template': '{{selector}} { max-width: 100%; height: auto; object-fit: contain; }'
    },
    {
        'rule_id': 'LF016', 'name': '内容区域滚动与页面滚动冲突', 'category': 'scroll',
        'severity': 'medium', 'enabled': 1,
        'description': 'body/html出现纵向滚动条(应该由.mtscos-content-scroll承担)',
        'detection': 'document.documentElement.scrollHeight > window.innerHeight + 4',
        'threshold': {'tolerance_px': 4},
        'fix_template': 'html, body { overflow: hidden !important; height: 100vh !important; } .mtscos-content-scroll { overflow-y: auto !important; }',
        'skip_condition': 'no .mtscos-content-scroll element on page (normal body scrolling)'
    },
    {
        'rule_id': 'LF017', 'name': '主题CSS变量缺失', 'category': 'theme',
        'severity': 'medium', 'enabled': 1,
        'description': '[data-theme]下核心CSS变量(accent, bg-page, text-primary)值为undefined或initial',
        'detection': 'getComputedStyle(document.body).getPropertyValue("--accent") === ""',
        'threshold': {'required_vars': ['--accent', '--bg-page', '--text-primary', '--border-subtle']},
        'fix_template': 'body[data-theme="{{current_theme}}"] { --accent: #6366f1; --bg-page: #0a0a1a; --text-primary: #f8fafc; --border-subtle: rgba(99,102,241,.12); }'
    },
    {
        'rule_id': 'LF018', 'name': '毛玻璃backdrop-filter被禁用', 'category': 'glass',
        'severity': 'low', 'enabled': 1,
        'description': 'glass类元素计算backdrop-filter为none/blur(0px)',
        'detection': 'el.classList.contains("glass-effect") && computed.backdropFilter.indexOf("blur(0")>=0',
        'threshold': {'min_blur_px': 16},
        'fix_template': '{{selector}} { backdrop-filter: blur(24px) saturate(180%) !important; -webkit-backdrop-filter: blur(24px) saturate(180%) !important; }'
    },
    {
        'rule_id': 'LF019', 'name': '侧边栏菜单项垂直间距过小', 'category': 'sidebar',
        'severity': 'low', 'enabled': 1,
        'description': '.mtscos-nav-item相邻项间距<4px导致点击区域粘连',
        'detection': 'adjacentNavItems[1].top - adjacentNavItems[0].bottom < 4',
        'threshold': {'min_gap_px': 4},
        'fix_template': '.mtscos-sidebar-nav { gap: 6px !important; } .mtscos-nav-item { margin: 2px 0 !important; }'
    },
    {
        'rule_id': 'LF020', 'name': '按钮/输入框高度不一致(表单对齐)', 'category': 'form',
        'severity': 'medium', 'enabled': 1,
        'description': '同一表单容器内button/input/select高度差异>6px',
        'detection': 'max(heights) - min(heights) > 6 && count(items) >= 2',
        'threshold': {'max_diff_px': 6},
        'fix_template': '{{form_selector}} input, {{form_selector}} button, {{form_selector}} select { height: 38px !important; box-sizing: border-box; }'
    },
]


# ==================== 数据库表初始化 ====================
def init_layout_tables() -> bool:
    """创建4张布局相关表：layout_rules / layout_snapshots / layout_adjustment_logs / layout_employee_configs"""
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS layout_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                severity TEXT DEFAULT 'medium',
                description TEXT,
                detection TEXT,
                threshold_json TEXT DEFAULT '{}',
                fix_template TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS layout_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_uuid TEXT UNIQUE NOT NULL,
                page_url TEXT,
                page_title TEXT,
                user_id INTEGER,
                username TEXT,
                viewport_w INTEGER,
                viewport_h INTEGER,
                sidebar_w INTEGER,
                main_w INTEGER,
                theme_key TEXT,
                sidebar_mini INTEGER DEFAULT 0,
                elements_json TEXT DEFAULT '[]',
                scroll_json TEXT DEFAULT '{}',
                computed_json TEXT DEFAULT '{}',
                detected_issues_json TEXT DEFAULT '[]',
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS layout_adjustment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                snapshot_uuid TEXT,
                page_url TEXT,
                rule_id TEXT,
                issue_summary TEXT,
                severity TEXT,
                generated_css TEXT,
                css_selector TEXT,
                fix_applied INTEGER DEFAULT 0,
                frontend_ack INTEGER DEFAULT 0,
                before_measure_json TEXT DEFAULT '{}',
                after_measure_json TEXT DEFAULT '{}',
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS layout_employee_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                employee_name TEXT,
                auto_apply INTEGER DEFAULT 0,
                confidence_threshold REAL DEFAULT 0.75,
                max_css_per_snapshot INTEGER DEFAULT 5,
                debounce_ms INTEGER DEFAULT 800,
                enabled_rules_json TEXT DEFAULT '[]',
                custom_overrides_json TEXT DEFAULT '{}',
                last_active TEXT,
                updated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_layout_snap_url ON layout_snapshots(page_url);
            CREATE INDEX IF NOT EXISTS idx_layout_snap_time ON layout_snapshots(created_at);
            CREATE INDEX IF NOT EXISTS idx_layout_log_rule ON layout_adjustment_logs(rule_id);
            CREATE INDEX IF NOT EXISTS idx_layout_log_emp ON layout_adjustment_logs(employee_id);
        ''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"初始化布局表失败: {e}")
        return False


def seed_layout_rules() -> int:
    """把20条规则写入layout_rules表（幂等，按rule_id去重）"""
    rows = 0
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for r in LAYOUT_FRAGMENTATION_RULES:
            c.execute("SELECT id FROM layout_rules WHERE rule_id=?", (r['rule_id'],))
            if c.fetchone():
                continue
            c.execute('''
                INSERT INTO layout_rules
                (rule_id, name, category, severity, description, detection, threshold_json, fix_template, enabled, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                r['rule_id'], r['name'], r['category'], r['severity'],
                r['description'], r['detection'],
                json.dumps(r.get('threshold', {}), ensure_ascii=False),
                r.get('fix_template', ''),
                r.get('enabled', 1), now, now
            ))
            rows += 1
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"播种布局规则失败: {e}")
    return rows


def get_enabled_rules() -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM layout_rules WHERE enabled=1 ORDER BY severity DESC, rule_id")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        for r in rows:
            try:
                r['threshold'] = json.loads(r.get('threshold_json') or '{}')
            except Exception:
                r['threshold'] = {}
        return rows
    except Exception as e:
        logger.error(f"读取布局规则失败: {e}")
        return [r for r in LAYOUT_FRAGMENTATION_RULES if r.get('enabled', 1)]


def save_snapshot(payload: Dict[str, Any]) -> str:
    """保存前端上报快照并返回snapshot_uuid"""
    import uuid as _uuid
    snap_id = 'snap_' + _uuid.uuid4().hex[:12]
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        vp = payload.get('viewport', {}) or {}
        sb = payload.get('sidebar', {}) or {}
        c.execute('''
            INSERT INTO layout_snapshots
            (snapshot_uuid, page_url, page_title, user_id, username,
             viewport_w, viewport_h, sidebar_w, main_w, theme_key, sidebar_mini,
             elements_json, scroll_json, computed_json, detected_issues_json, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            snap_id,
            payload.get('url') or '',
            payload.get('title') or '',
            payload.get('user_id'),
            payload.get('username') or '',
            int(vp.get('w', 0) or 0),
            int(vp.get('h', 0) or 0),
            int(sb.get('w', 0) or 0),
            int((payload.get('main') or {}).get('w', 0) or 0),
            payload.get('theme') or '',
            1 if payload.get('sidebar_mini') else 0,
            json.dumps(payload.get('elements') or [], ensure_ascii=False),
            json.dumps(payload.get('scroll') or {}, ensure_ascii=False),
            json.dumps(payload.get('computed') or {}, ensure_ascii=False),
            json.dumps(payload.get('detected_issues') or [], ensure_ascii=False),
            now,
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"保存布局快照失败: {e}")
    return snap_id


def save_adjustment_log(log: Dict[str, Any]) -> int:
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            INSERT INTO layout_adjustment_logs
            (employee_id, snapshot_uuid, page_url, rule_id, issue_summary, severity,
             generated_css, css_selector, fix_applied, frontend_ack,
             before_measure_json, after_measure_json, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            log.get('employee_id', ''),
            log.get('snapshot_uuid') or '',
            log.get('page_url') or '',
            log.get('rule_id') or '',
            log.get('issue_summary') or '',
            log.get('severity') or 'medium',
            log.get('generated_css') or '',
            log.get('css_selector') or '',
            1 if log.get('fix_applied') else 0,
            1 if log.get('frontend_ack') else 0,
            json.dumps(log.get('before') or {}, ensure_ascii=False),
            json.dumps(log.get('after') or {}, ensure_ascii=False),
            now,
        ))
        lid = c.lastrowid
        conn.commit()
        conn.close()
        return lid
    except Exception as e:
        logger.error(f"保存调节日志失败: {e}")
        return 0


def get_employee_config(employee_id: str) -> Dict[str, Any]:
    default = {
        'employee_id': employee_id, 'auto_apply': 1,
        'confidence_threshold': 0.75, 'max_css_per_snapshot': 5,
        'debounce_ms': 800, 'enabled_rules': [], 'custom_overrides': {},
    }
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM layout_employee_configs WHERE employee_id=?", (employee_id,))
        row = c.fetchone()
        conn.close()
        if row:
            d = dict(row)
            default['auto_apply'] = d.get('auto_apply', 1)
            default['confidence_threshold'] = d.get('confidence_threshold', 0.75)
            default['max_css_per_snapshot'] = d.get('max_css_per_snapshot', 5)
            default['debounce_ms'] = d.get('debounce_ms', 800)
            try:
                default['enabled_rules'] = json.loads(d.get('enabled_rules_json') or '[]')
            except Exception:
                default['enabled_rules'] = []
            try:
                default['custom_overrides'] = json.loads(d.get('custom_overrides_json') or '{}')
            except Exception:
                default['custom_overrides'] = {}
    except Exception:
        pass
    return default


def upsert_employee_config(cfg: Dict[str, Any]) -> bool:
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            INSERT INTO layout_employee_configs
            (employee_id, employee_name, auto_apply, confidence_threshold, max_css_per_snapshot,
             debounce_ms, enabled_rules_json, custom_overrides_json, last_active, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(employee_id) DO UPDATE SET
                employee_name=excluded.employee_name,
                auto_apply=excluded.auto_apply,
                confidence_threshold=excluded.confidence_threshold,
                max_css_per_snapshot=excluded.max_css_per_snapshot,
                debounce_ms=excluded.debounce_ms,
                enabled_rules_json=excluded.enabled_rules_json,
                custom_overrides_json=excluded.custom_overrides_json,
                last_active=excluded.last_active,
                updated_at=excluded.updated_at
        ''', (
            cfg['employee_id'],
            cfg.get('employee_name', ''),
            int(cfg.get('auto_apply', 1)),
            float(cfg.get('confidence_threshold', 0.75)),
            int(cfg.get('max_css_per_snapshot', 5)),
            int(cfg.get('debounce_ms', 800)),
            json.dumps(cfg.get('enabled_rules') or [], ensure_ascii=False),
            json.dumps(cfg.get('custom_overrides') or {}, ensure_ascii=False),
            now, now,
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"更新员工配置失败: {e}")
        return False


# ==================== 布局调节AI员工类 ====================
class LayoutAdjusterAIEmployee(AIEmployee):
    """
    布局调节AI员工
    - 继承 AIEmployee 基类，可参与 AI员工管理器调度
    - 输入：前端快照JSON（含元素尺寸/位置/滚动信息）
    - 输出：针对当前快照的修复CSS列表 + 命中的问题列表
    """

    EMPLOYEE_ID = 'ai_layout_adj_001'
    EMPLOYEE_NAME = 'AI布局调节师'
    EMPLOYEE_ROLE = 'designer'
    EMPLOYEE_SKILLS = ['CSS排版', '响应式布局', '断点适配', 'Flex/Grid诊断', '主题系统']

    def __init__(self):
        if _BASE_AVAILABLE:
            super().__init__(self.EMPLOYEE_ID, self.EMPLOYEE_NAME, self.EMPLOYEE_ROLE, self.EMPLOYEE_SKILLS)
        else:
            AIEmployee.__init__(self, self.EMPLOYEE_ID, self.EMPLOYEE_NAME, self.EMPLOYEE_ROLE, self.EMPLOYEE_SKILLS)
        self._rules: List[Dict[str, Any]] = []
        self._config: Dict[str, Any] = {}
        self._last_loaded_cfg = 0
        self.reload_runtime()

    def reload_runtime(self):
        init_layout_tables()
        seed_layout_rules()
        self._rules = get_enabled_rules()
        self._config = get_employee_config(self.EMPLOYEE_ID)
        if not self._config.get('enabled_rules'):
            self._config['enabled_rules'] = [r['rule_id'] for r in self._rules]
            upsert_employee_config({
                'employee_id': self.EMPLOYEE_ID,
                'employee_name': self.EMPLOYEE_NAME,
                'enabled_rules': self._config['enabled_rules'],
                'auto_apply': 1,
            })
        self._last_loaded_cfg = datetime.now().timestamp()

    # ---------- 公开入口：分析快照 + 生成修复 ----------
    def analyze_and_fix(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        主流程：接收前端快照 → 检测问题 → 生成CSS → 入库 → 返回结果
        返回: {
            'snapshot_uuid': str,
            'issues': [{rule_id, name, severity, summary, selector, confidence}],
            'fix_css': str,     /* 合成后的最终CSS块 */
            'fix_count': int,
            'auto_apply': bool,
            'employee': {'id','name'}
        }
        """
        if datetime.now().timestamp() - self._last_loaded_cfg > 60:
            self.reload_runtime()

        payload = payload or {}
        snap_id = save_snapshot(payload)

        issues: List[Dict[str, Any]] = []
        css_parts: List[str] = []
        max_css = int(self._config.get('max_css_per_snapshot', 5))
        threshold = float(self._config.get('confidence_threshold', 0.75))
        enabled_rule_ids = set(self._config.get('enabled_rules') or [])

        detections = self._run_all_detections(payload, enabled_rule_ids)
        for det in detections:
            if len(issues) >= max_css:
                break
            confidence = float(det.get('confidence', 1.0))
            if confidence < threshold:
                continue
            rule_meta = self._find_rule_meta(det['rule_id'])
            summary = det.get('summary') or (rule_meta or {}).get('description', '')
            css = self._render_fix_template((rule_meta or {}).get('fix_template', ''), det.get('vars', {}))
            if not css:
                continue
            issues.append({
                'rule_id': det['rule_id'],
                'name': (rule_meta or {}).get('name', det['rule_id']),
                'category': (rule_meta or {}).get('category', ''),
                'severity': (rule_meta or {}).get('severity', 'medium'),
                'summary': summary,
                'selector': det.get('selector', ''),
                'confidence': round(confidence, 3),
            })
            css_parts.append(f"/* [{det['rule_id']}] {(rule_meta or {}).get('name','')} — {summary} */\n{css}")

            save_adjustment_log({
                'employee_id': self.EMPLOYEE_ID,
                'snapshot_uuid': snap_id,
                'page_url': payload.get('url') or '',
                'rule_id': det['rule_id'],
                'issue_summary': summary,
                'severity': (rule_meta or {}).get('severity', 'medium'),
                'generated_css': css,
                'css_selector': det.get('selector', ''),
                'fix_applied': 1 if self._config.get('auto_apply') else 0,
                'before': det.get('measure_before', {}),
            })

        upsert_employee_config({
            'employee_id': self.EMPLOYEE_ID,
            'employee_name': self.EMPLOYEE_NAME,
        })

        final_css = '\n\n'.join(css_parts).strip()
        return {
            'snapshot_uuid': snap_id,
            'issues': issues,
            'fix_css': final_css,
            'fix_count': len(issues),
            'auto_apply': bool(self._config.get('auto_apply', 0)),
            'employee': {'id': self.EMPLOYEE_ID, 'name': self.EMPLOYEE_NAME},
            'timestamp': datetime.now().isoformat(),
        }

    # ---------- 20条规则的Python端补充检测逻辑（前端也检测，这里做二次判定/增强） ----------
    def _run_all_detections(self, payload: Dict[str, Any], enabled_ids: set) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        vp = payload.get('viewport') or {}
        vp_w = int(vp.get('w', 0) or 0)
        vp_h = int(vp.get('h', 0) or 0)
        sb = payload.get('sidebar') or {}
        sb_w = int(sb.get('w', 0) or 0)
        mn = payload.get('main') or {}
        mn_w = int(mn.get('w', 0) or 0)
        scroll = payload.get('scroll') or {}
        elements = payload.get('elements') or []
        sidebar_mini = bool(payload.get('sidebar_mini'))
        computed = payload.get('computed') or {}

        def _add(rule_id, confidence, summary, selector='', vars=None, before=None):
            if rule_id not in enabled_ids:
                return
            results.append({
                'rule_id': rule_id, 'confidence': confidence,
                'summary': summary, 'selector': selector,
                'vars': vars or {}, 'measure_before': before or {},
            })

        # LF005/LF006：侧边栏宽度比例
        if vp_w and sb_w:
            ratio = sb_w / vp_w
            tol = 0.03
            if not sidebar_mini and abs(ratio - 0.20) > tol:
                _add('LF005', min(1.0, abs(ratio - 0.20) * 25),
                     f'侧边栏宽度比例异常 {ratio:.3f} (期望0.20)',
                     '.mtscos-sidebar', {'expected': 0.20, 'actual': ratio},
                     {'sb_w': sb_w, 'vp_w': vp_w})
            if sidebar_mini and abs(ratio - 0.10) > tol:
                _add('LF006', min(1.0, abs(ratio - 0.10) * 25),
                     f'mini态侧边栏比例异常 {ratio:.3f} (期望0.10)',
                     'body.sidebar-mini .mtscos-sidebar',
                     {'expected': 0.10, 'actual': ratio},
                     {'sb_w': sb_w, 'vp_w': vp_w})

        # LF001：主内容水平溢出
        if mn_w and vp_w and mn_w > vp_w * 0.82 + 4:
            _add('LF001', 0.9,
                 f'主内容宽度 {mn_w}px 超过视图82%',
                 '.mtscos-main, .mtscos-content-scroll',
                 {'selector': '.mtscos-main, .mtscos-content-scroll'},
                 {'mn_w': mn_w, 'vp_w': vp_w})

        # LF016：body/html出现纵向滚动条（仅在有 .mtscos-content-scroll 容器的页面生效）
        body_sh = int(scroll.get('body_scroll_height') or 0)
        has_content_scroll = bool(payload.get('has_mtscos_content_scroll') or payload.get('elements', {}).get('mtscos_content_scroll'))
        if body_sh and vp_h and body_sh > vp_h + 8 and has_content_scroll:
            _add('LF016', 0.85,
                 f'body.scrollHeight={body_sh} > viewport.h={vp_h}，外层出现滚动条',
                 'html, body',
                 {}, {'body_sh': body_sh, 'vp_h': vp_h})

        # LF007：首页1:7:2检测（首页由url=='/'或title判断）
        url = (payload.get('url') or '').rstrip('/')
        title = (payload.get('title') or '').lower()
        if url in ('', '/') or ('首页' in title or 'home' in title):
            home = payload.get('home_sections') or {}
            hh = int(home.get('header_h', 0) or 0)
            mh = int(home.get('main_h', 0) or 0)
            fh = int(home.get('footer_h', 0) or 0)
            if mh and abs((hh / mh) - 1 / 7) > 0.18:
                _add('LF007', 0.7,
                     f'首页Header/Main比例 {hh/mh:.3f} 偏离1:7',
                     '.home-header, .home-main, .home-footer',
                     {'parent_h': fh}, {'hh': hh, 'mh': mh, 'fh': fh})

        # LF017：主题变量
        theme_vars = computed.get('theme_vars') or {}
        missing = [v for v in ['--accent', '--bg-page', '--text-primary']
                   if not (theme_vars.get(v) or '').strip()]
        if missing:
            _add('LF017', 0.8,
                 f'主题缺失CSS变量: {",".join(missing)}',
                 f'body[data-theme="{payload.get("theme","")}"]',
                 {'current_theme': payload.get('theme', 'deep_blue')})

        # 前端上报的 issues 直接汇入（confidence由前端评估，这里做二次复核）
        frontend_issues = payload.get('detected_issues') or []
        for fi in frontend_issues:
            rid = fi.get('rule_id') or fi.get('id')
            if not rid or rid in {r['rule_id'] for r in results}:
                continue
            conf = float(fi.get('confidence') or 0.8)
            _add(rid, conf,
                 fi.get('summary') or fi.get('description') or '',
                 fi.get('selector') or '',
                 fi.get('vars') or {},
                 fi.get('before') or {})

        # 按 severity→confidence 排序（critical/high先处理）
        severity_rank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        def _sort_key(r):
            meta = self._find_rule_meta(r['rule_id']) or {}
            return (severity_rank.get(meta.get('severity', 'medium'), 2), -r['confidence'])
        results.sort(key=_sort_key)
        return results

    def _find_rule_meta(self, rule_id: str) -> Optional[Dict[str, Any]]:
        for r in self._rules:
            if r.get('rule_id') == rule_id:
                return r
        return None

    def _render_fix_template(self, template: str, vars: Dict[str, Any]) -> str:
        if not template:
            return ''
        out = template
        try:
            for k, v in (vars or {}).items():
                out = out.replace('{{' + str(k) + '}}', str(v))
        except Exception:
            pass
        return out

    # ---------- 兼容基类 execute_task ----------
    def execute_task(self, task) -> Dict[str, Any]:
        self.last_task = task
        if isinstance(task, dict) and task.get('type') == 'layout_analyze':
            result = self.analyze_and_fix(task.get('payload') or {})
            return {
                'success': True,
                'employee_id': self.EMPLOYEE_ID,
                'employee_name': self.EMPLOYEE_NAME,
                'task': 'layout_analyze',
                'result': result,
                'timestamp': datetime.now().isoformat(),
            }
        return super().execute_task(task)


# ==================== 单例 & 全局入口 ====================
_LAYOUT_ADJUSTER: Optional[LayoutAdjusterAIEmployee] = None


def get_layout_adjuster() -> LayoutAdjusterAIEmployee:
    global _LAYOUT_ADJUSTER
    if _LAYOUT_ADJUSTER is None:
        _LAYOUT_ADJUSTER = LayoutAdjusterAIEmployee()
        logger.info(f"[layout_ai] 已初始化AI员工: {_LAYOUT_ADJUSTER.EMPLOYEE_NAME} ({_LAYOUT_ADJUSTER.EMPLOYEE_ID})")
    return _LAYOUT_ADJUSTER


def init_layout_ai_system() -> Tuple[bool, int]:
    """对外初始化入口：建表、播规则、初始化员工；返回 (建表成功, 新增规则数)"""
    ok = init_layout_tables()
    n = seed_layout_rules()
    try:
        get_layout_adjuster()
    except Exception as e:
        logger.error(f"初始化AI员工失败: {e}")
    return ok, n


def stats_summary() -> Dict[str, Any]:
    """统计摘要：用于API /api/layout_ai/stats"""
    out = {
        'rules': {'total': 0, 'enabled': 0, 'by_category': {}, 'by_severity': {}},
        'snapshots': {'total': 0, 'last_24h': 0, 'unique_pages': 0},
        'adjustments': {'total': 0, 'applied': 0, 'by_rule': {}, 'by_severity': {}},
        'employee': None,
    }
    try:
        conn = sqlite3.connect(SPLIT_AI_DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), SUM(enabled) FROM layout_rules")
        row = c.fetchone() or (0, 0)
        out['rules']['total'] = int(row[0] or 0)
        out['rules']['enabled'] = int(row[1] or 0)
        for cat, sev, cnt in c.execute("SELECT category, severity, COUNT(*) FROM layout_rules GROUP BY category, severity").fetchall():
            out['rules']['by_category'][cat or 'other'] = out['rules']['by_category'].get(cat or 'other', 0) + int(cnt)
            out['rules']['by_severity'][sev or 'medium'] = out['rules']['by_severity'].get(sev or 'medium', 0) + int(cnt)
        c.execute("SELECT COUNT(*) FROM layout_snapshots")
        out['snapshots']['total'] = int((c.fetchone() or (0,))[0])
        c.execute("SELECT COUNT(*) FROM layout_snapshots WHERE datetime(created_at) >= datetime('now','-1 day')")
        out['snapshots']['last_24h'] = int((c.fetchone() or (0,))[0])
        c.execute("SELECT COUNT(DISTINCT page_url) FROM layout_snapshots")
        out['snapshots']['unique_pages'] = int((c.fetchone() or (0,))[0])
        c.execute("SELECT COUNT(*), SUM(fix_applied) FROM layout_adjustment_logs")
        row = c.fetchone() or (0, 0)
        out['adjustments']['total'] = int(row[0] or 0)
        out['adjustments']['applied'] = int(row[1] or 0)
        for rid, cnt in c.execute("SELECT rule_id, COUNT(*) FROM layout_adjustment_logs GROUP BY rule_id ORDER BY cnt DESC LIMIT 10").fetchall():
            out['adjustments']['by_rule'][rid or '?'] = int(cnt)
        for sev, cnt in c.execute("SELECT severity, COUNT(*) FROM layout_adjustment_logs GROUP BY severity").fetchall():
            out['adjustments']['by_severity'][sev or 'medium'] = int(cnt)
        conn.close()
    except Exception as e:
        out['error'] = str(e)
    try:
        emp = get_layout_adjuster()
        out['employee'] = {
            'id': emp.EMPLOYEE_ID, 'name': emp.EMPLOYEE_NAME,
            'status': getattr(emp, 'status', 'active'),
        }
    except Exception:
        pass
    return out


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    ok, n = init_layout_ai_system()
    print(f"init: tables={'OK' if ok else 'FAIL'}, seeded_rules={n}")
    print(json.dumps(stats_summary(), ensure_ascii=False, indent=2))
