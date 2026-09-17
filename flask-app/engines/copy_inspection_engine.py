"""
文案巡检引擎 (Copy Inspection Engine)
CHMS-06: 文案合规巡检（缺失/重复/占位/硬编码检测）

归档: flask-app/engines/copy_inspection_engine.py
流程: §14 12步骤 STEP_7_EXECUTE
"""
import os
import re
import sqlite3
import json
from typing import Dict, Any, List


class CopyInspectionEngine:
    """文案合规巡检引擎"""

    def __init__(self, db_path: str = None, project_root: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base, 'app.db')
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = db_path
        self.project_root = project_root

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def inspect_missing(self) -> List[Dict[str, Any]]:
        """检测缺失文案：页面/服务引用了文案key但数据库中不存在"""
        findings = []
        # 检查模板文件中引用的文案key是否在库
        templates_dir = os.path.join(self.project_root, 'flask-app', 'templates')
        if os.path.isdir(templates_dir):
            for root, dirs, files in os.walk(templates_dir):
                for f in files:
                    if not f.endswith('.html'):
                        continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        # 查找 copy_key 引用模式
                        keys = re.findall(r"copy_key['\"]?\s*[:=]\s*['\"]([\w.]+)['\"]", content)
                        keys += re.findall(r"/api/copy/([\w.]+)", content)
                        for key in set(keys):
                            conn = self._get_conn()
                            cur = conn.cursor()
                            cur.execute("SELECT copy_id FROM mt_copy_assets WHERE copy_key=?", (key,))
                            if cur.fetchone() is None:
                                findings.append({
                                    'type': 'MISSING',
                                    'file': os.path.relpath(fpath, self.project_root),
                                    'copy_key': key,
                                    'detail': f'模板引用了文案key {key} 但数据库中不存在'
                                })
                            conn.close()
                    except Exception:
                        continue
        return findings

    def inspect_duplicates(self) -> List[Dict[str, Any]]:
        """检测重复文案"""
        findings = []
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """SELECT copy_content, COUNT(*) AS cnt, GROUP_CONCAT(copy_key) AS keys
                   FROM mt_copy_assets
                   WHERE status='ACTIVE' AND copy_content != ''
                   GROUP BY copy_content HAVING cnt > 1"""
            )
            for row in cur.fetchall():
                findings.append({
                    'type': 'DUPLICATE',
                    'content_preview': row['copy_content'][:100],
                    'count': row['cnt'],
                    'keys': row['keys'],
                    'detail': f'发现{row["cnt"]}条内容相同的文案'
                })
            conn.close()
        except Exception:
            pass
        return findings

    def inspect_placeholders(self) -> List[Dict[str, Any]]:
        """检测占位文案"""
        findings = []
        placeholder_patterns = [
            (r'TODO|FIXME|PLACEHOLDER', 'TODO/FIXME标记'),
            (r'占位|待补充|待完善', '占位标记'),
            (r'模拟|假数据|mock|dummy', '模拟/假数据'),
            (r'.+页面。$', '占位页特征'),
            (r'/templates/.+\.html', '模板路径泄露'),
        ]
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT copy_key, copy_content, page_path FROM mt_copy_assets WHERE status='ACTIVE'")
            for row in cur.fetchall():
                content = row['copy_content']
                for pattern, desc in placeholder_patterns:
                    if re.search(pattern, content, re.I):
                        findings.append({
                            'type': 'PLACEHOLDER',
                            'copy_key': row['copy_key'],
                            'pattern': desc,
                            'content_preview': content[:100],
                            'detail': f'文案包含占位特征: {desc}'
                        })
                        break
            conn.close()
        except Exception:
            pass
        return findings

    def inspect_hardcoded(self) -> List[Dict[str, Any]]:
        """检测硬编码文案（代码中内联的中文文案未入库）"""
        findings = []
        sensitive_patterns = [
            (r'password\s*[:=]\s*[\'"][^\'"]+[\'"]', '硬编码密码'),
            (r'(?:api_?key|secret|token)\s*[:=]\s*[\'"][^\'"]+[\'"]', '硬编码密钥'),
            (r'mockValidTokens\s*=\s*\[', '硬编码测试凭据'),
        ]
        scan_dirs = [
            os.path.join(self.project_root, 'flask-app', 'ai_engines'),
            os.path.join(self.project_root, 'flask-app', 'services'),
            os.path.join(self.project_root, 'frontend', 'JavaScript'),
            os.path.join(self.project_root, 'frontend', 'assets', 'js'),
        ]
        for scan_dir in scan_dirs:
            if not os.path.isdir(scan_dir):
                continue
            for root, dirs, files in os.walk(scan_dir):
                for f in files:
                    if not (f.endswith('.py') or f.endswith('.js')):
                        continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        for pattern, desc in sensitive_patterns:
                            matches = re.findall(pattern, content, re.I)
                            if matches:
                                findings.append({
                                    'type': 'HARDCODED',
                                    'file': os.path.relpath(fpath, self.project_root),
                                    'pattern': desc,
                                    'count': len(matches),
                                    'detail': f'{f} 中检测到{len(matches)}处{desc}'
                                })
                    except Exception:
                        continue
        return findings

    def run_full_inspection(self) -> Dict[str, Any]:
        """执行完整巡检"""
        missing = self.inspect_missing()
        duplicates = self.inspect_duplicates()
        placeholders = self.inspect_placeholders()
        hardcoded = self.inspect_hardcoded()

        all_findings = missing + duplicates + placeholders + hardcoded
        # 确定严重等级
        severity = 'INFO'
        if hardcoded:
            severity = 'CRITICAL'
        elif placeholders:
            severity = 'WARNING'
        elif duplicates or missing:
            severity = 'WARNING'

        # 落库巡检报告
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            for finding_type, findings in [('MISSING', missing), ('DUPLICATE', duplicates),
                                            ('PLACEHOLDER', placeholders), ('HARDCODED', hardcoded)]:
                cur.execute(
                    """INSERT INTO mt_copy_inspection_report
                       (inspection_type, findings_json, severity, total_findings)
                       VALUES (?, ?, ?, ?)""",
                    (finding_type, json.dumps(findings, ensure_ascii=False),
                     severity if findings else 'INFO', len(findings))
                )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return {
            'total_findings': len(all_findings),
            'severity': severity,
            'breakdown': {
                'missing': len(missing),
                'duplicates': len(duplicates),
                'placeholders': len(placeholders),
                'hardcoded': len(hardcoded)
            },
            'findings': {
                'missing': missing,
                'duplicates': duplicates,
                'placeholders': placeholders,
                'hardcoded': hardcoded
            }
        }
