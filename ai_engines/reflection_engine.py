# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
反思引擎
深度反思和复盘修复过程，防止类似问题反复出现
"""

import os
import json
import uuid
import sqlite3
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ReflectionEngine:
    """反思引擎"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reflection_engine.db')
        self._create_tables()
        self.reflections = []
        self.lessons_learned = []

    def _create_tables(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reflection_id TEXT UNIQUE,
                    repair_id TEXT,
                    issue_id TEXT,
                    category TEXT,
                    severity TEXT,
                    root_cause TEXT,
                    contributing_factors TEXT,
                    prevention_rules TEXT,
                    lessons_learned TEXT,
                    action_items TEXT,
                    reflection_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prevention_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT UNIQUE,
                    rule_name TEXT,
                    rule_category TEXT,
                    description TEXT,
                    severity TEXT,
                    action TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recurring_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_pattern TEXT UNIQUE,
                    category TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    last_occurrence TEXT,
                    prevention_rule_id TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            conn.commit()
            logger.info("[ReflectionEngine] 数据库表创建完成")

    def reflect_on_repair(self, repair: Dict, issue: Dict, solution: Dict) -> Dict[str, Any]:
        """对修复进行反思"""
        reflection_id = f"reflect_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"[ReflectionEngine] 开始反思: {reflection_id}")
        
        root_cause = self._analyze_root_cause(issue, repair)
        contributing_factors = self._identify_contributing_factors(issue, repair)
        prevention_rules = self._generate_prevention_rules(root_cause, contributing_factors)
        lessons_learned = self._extract_lessons_learned(issue, repair, solution)
        action_items = self._generate_action_items(prevention_rules)
        
        reflection = {
            'reflection_id': reflection_id,
            'repair_id': repair.get('repair_id', ''),
            'issue_id': issue.get('issue_id', ''),
            'category': issue.get('category', ''),
            'severity': issue.get('severity', ''),
            'root_cause': root_cause,
            'contributing_factors': contributing_factors,
            'prevention_rules': prevention_rules,
            'lessons_learned': lessons_learned,
            'action_items': action_items,
            'reflection_time': datetime.now().isoformat()
        }
        
        self._save_reflection(reflection)
        self.reflections.append(reflection)
        self.lessons_learned.extend(lessons_learned)
        
        for rule in prevention_rules:
            self._save_prevention_rule(rule)
        
        self._check_recurring_issue(issue)
        
        logger.info(f"[ReflectionEngine] 反思完成: {reflection_id}")
        return reflection

    def _analyze_root_cause(self, issue: Dict, repair: Dict) -> str:
        """分析根本原因"""
        category = issue.get('category', '')
        
        root_causes = {
            'hardcoded_credentials': '开发人员将敏感凭证直接写入代码，缺乏安全意识和代码审查流程',
            'code_execution': '使用了不安全的eval/exec函数，缺乏输入验证和安全编码规范',
            'command_injection': '未使用参数化命令执行，直接拼接用户输入到命令中',
            'deserialization': '使用了不安全的pickle序列化，缺乏数据签名验证机制',
            'sql_injection': '未使用参数化查询，直接拼接用户输入到SQL语句中',
            'debug_enabled': '生产环境未禁用调试模式，缺乏配置管理和环境隔离',
            'weak_secret_key': 'SECRET_KEY设置不当或长度不足，缺乏密钥管理规范',
            'db_permissions': '数据库文件权限过于开放，缺乏最小权限原则执行',
            'env_file': '.env文件未添加到.gitignore或权限设置不当'
        }
        
        return root_causes.get(category, '需要进一步分析根本原因')

    def _identify_contributing_factors(self, issue: Dict, repair: Dict) -> List[str]:
        """识别影响因素"""
        factors = []
        
        if issue.get('severity') in ['critical', 'high']:
            factors.append('安全意识不足')
            factors.append('代码审查缺失')
        
        if 'config' in issue.get('category', ''):
            factors.append('配置管理不当')
            factors.append('环境隔离不足')
        
        if 'code' in issue.get('category', ''):
            factors.append('安全编码规范未执行')
            factors.append('输入验证缺失')
        
        factors.append('自动化测试覆盖率不足')
        factors.append('安全扫描频率不够')
        
        return factors

    def _generate_prevention_rules(self, root_cause: str, factors: List[str]) -> List[Dict]:
        """生成预防规则"""
        rules = []
        
        if '代码审查' in root_cause or '代码审查' in factors:
            rules.append({
                'rule_id': f"prevention_{uuid.uuid4().hex[:8]}",
                'rule_name': '强制代码审查规则',
                'rule_category': 'code_review',
                'description': '所有代码提交必须经过安全代码审查',
                'severity': 'high',
                'action': 'enforce'
            })
        
        if '输入验证' in root_cause or '输入验证' in factors:
            rules.append({
                'rule_id': f"prevention_{uuid.uuid4().hex[:8]}",
                'rule_name': '输入验证规则',
                'rule_category': 'input_validation',
                'description': '所有用户输入必须经过严格验证和过滤',
                'severity': 'critical',
                'action': 'enforce'
            })
        
        if '配置' in root_cause or '配置' in factors:
            rules.append({
                'rule_id': f"prevention_{uuid.uuid4().hex[:8]}",
                'rule_name': '配置管理规则',
                'rule_category': 'configuration',
                'description': '生产环境配置必须与开发环境隔离，敏感配置使用环境变量',
                'severity': 'high',
                'action': 'enforce'
            })
        
        if '权限' in root_cause or '权限' in factors:
            rules.append({
                'rule_id': f"prevention_{uuid.uuid4().hex[:8]}",
                'rule_name': '最小权限原则',
                'rule_category': 'permissions',
                'description': '所有文件和数据库权限必须遵循最小权限原则',
                'severity': 'medium',
                'action': 'enforce'
            })
        
        rules.append({
            'rule_id': f"prevention_{uuid.uuid4().hex[:8]}",
            'rule_name': '定期安全扫描规则',
            'rule_category': 'security_scanning',
            'description': '系统必须每周执行一次安全扫描',
            'severity': 'medium',
            'action': 'schedule'
        })
        
        return rules

    def _extract_lessons_learned(self, issue: Dict, repair: Dict, solution: Dict) -> List[str]:
        """提取经验教训"""
        lessons = []
        
        lessons.append(f"{issue.get('category_name', issue.get('category'))}问题需要优先修复")
        
        if repair.get('status') == 'completed':
            lessons.append(f"成功修复方案: {solution.get('title', '')}")
        else:
            lessons.append(f"修复失败，需要改进修复策略")
        
        if issue.get('severity') in ['critical', 'high']:
            lessons.append("Critical/High级别问题必须立即处理")
        
        lessons.append("修复后必须进行回滚测试验证")
        
        return lessons

    def _generate_action_items(self, rules: List[Dict]) -> List[str]:
        """生成行动项"""
        items = []
        
        for rule in rules:
            if rule['action'] == 'enforce':
                items.append(f"强制执行规则: {rule['rule_name']}")
            elif rule['action'] == 'schedule':
                items.append(f"按计划执行: {rule['rule_name']}")
        
        items.append("更新安全培训材料")
        items.append("审查现有代码库中的类似问题")
        items.append("增加相关测试用例")
        
        return items

    def _save_reflection(self, reflection: Dict):
        """保存反思记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO reflections 
                    (reflection_id, repair_id, issue_id, category, severity, 
                     root_cause, contributing_factors, prevention_rules, 
                     lessons_learned, action_items)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reflection['reflection_id'],
                    reflection['repair_id'],
                    reflection['issue_id'],
                    reflection['category'],
                    reflection['severity'],
                    reflection['root_cause'],
                    json.dumps(reflection.get('contributing_factors', []), ensure_ascii=False),
                    json.dumps(reflection.get('prevention_rules', []), ensure_ascii=False),
                    json.dumps(reflection.get('lessons_learned', []), ensure_ascii=False),
                    json.dumps(reflection.get('action_items', []), ensure_ascii=False)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[ReflectionEngine] 保存反思记录失败: {e}")

    def _save_prevention_rule(self, rule: Dict):
        """保存预防规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO prevention_rules 
                    (rule_id, rule_name, rule_category, description, severity, action, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule['rule_id'],
                    rule['rule_name'],
                    rule['rule_category'],
                    rule['description'],
                    rule['severity'],
                    rule.get('action', 'enforce'),
                    rule.get('enabled', 1)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[ReflectionEngine] 保存预防规则失败: {e}")

    def _check_recurring_issue(self, issue: Dict):
        """检查是否为重复问题"""
        pattern = issue.get('category', '')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM recurring_issues WHERE issue_pattern = ?', (pattern,))
                existing = cursor.fetchone()
                
                if existing:
                    count = existing[3] + 1
                    cursor.execute('''
                        UPDATE recurring_issues SET occurrence_count = ?, last_occurrence = ? WHERE issue_pattern = ?
                    ''', (count, datetime.now().isoformat(), pattern))
                    
                    logger.warning(f"[ReflectionEngine] 发现重复问题: {pattern}, 已出现 {count} 次")
                else:
                    cursor.execute('''
                        INSERT INTO recurring_issues (issue_pattern, category, last_occurrence)
                        VALUES (?, ?, ?)
                    ''', (pattern, issue.get('category', ''), datetime.now().isoformat()))
                
                conn.commit()
        except Exception as e:
            logger.error(f"[ReflectionEngine] 检查重复问题失败: {e}")

    def get_all_reflections(self) -> List[Dict]:
        """获取所有反思记录"""
        return self.reflections

    def get_prevention_rules(self) -> List[Dict]:
        """获取预防规则"""
        rules = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM prevention_rules WHERE enabled = 1')
                for row in cursor.fetchall():
                    rules.append({
                        'rule_id': row[1],
                        'rule_name': row[2],
                        'rule_category': row[3],
                        'description': row[4],
                        'severity': row[5],
                        'action': row[6],
                        'enabled': row[7]
                    })
        except Exception as e:
            logger.error(f"[ReflectionEngine] 获取预防规则失败: {e}")
        return rules

    def get_recurring_issues(self) -> List[Dict]:
        """获取重复出现的问题"""
        issues = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM recurring_issues ORDER BY occurrence_count DESC')
                for row in cursor.fetchall():
                    issues.append({
                        'issue_pattern': row[1],
                        'category': row[2],
                        'occurrence_count': row[3],
                        'last_occurrence': row[4],
                        'status': row[6]
                    })
        except Exception as e:
            logger.error(f"[ReflectionEngine] 获取重复问题失败: {e}")
        return issues

    def feed_to_brain(self) -> Dict[str, Any]:
        """将经验教训投喂到AI脑库"""
        logger.info("[ReflectionEngine] 将经验教训投喂到AI脑库...")
        
        try:
            from app.ai.ai_brain import AIBrain
            brain = AIBrain()
            
            for lesson in self.lessons_learned:
                brain.add_knowledge({
                    'type': 'lesson_learned',
                    'content': lesson,
                    'source': 'reflection_engine',
                    'timestamp': datetime.now().isoformat()
                })
            
            return {
                'success': True,
                'message': f"已投喂 {len(self.lessons_learned)} 条经验教训到脑库",
                'count': len(self.lessons_learned)
            }
        except Exception as e:
            logger.error(f"[ReflectionEngine] 投喂脑库失败: {e}")
            return {'success': False, 'error': str(e)}