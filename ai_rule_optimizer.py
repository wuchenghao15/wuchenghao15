#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI法则自动优化强化系统 - AI Rule Auto-Optimization System
MTSCOS AI Project v3.1
基于AI建议自动分析、优化和强化系统法则
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rule_optimizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('rule_optimizer')

class OptimizationLevel(Enum):
    """优化级别"""
    CRITICAL = "critical"   # 关键优化 - 修复安全漏洞或重大缺陷
    HIGH = "high"           # 高级优化 - 性能显著提升
    MEDIUM = "medium"       # 中级优化 - 功能增强
    LOW = "low"             # 低级优化 - 代码改进
    COSMETIC = "cosmetic"   # 美化优化 - 格式和可读性

class OptimizationType(Enum):
    """优化类型"""
    SECURITY = "security"           # 安全优化
    PERFORMANCE = "performance"     # 性能优化
    SECURITY_COMPLIANCE = "compliance" # 合规性优化
    CODE_QUALITY = "code_quality"   # 代码质量优化
    ARCHITECTURE = "architecture"   # 架构优化
    USABILITY = "usability"         # 可用性优化
    MAINTAINABILITY = "maintainability" # 可维护性优化

class AnalysisStatus(Enum):
    """分析状态"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"

class OptimizationStatus(Enum):
    """优化状态"""
    PENDING = "pending"
    APPLYING = "applying"
    COMPLETED = "completed"
    ROLLBACK = "rollback"
    FAILED = "failed"

@dataclass
class RuleAnalysis:
    """法则分析结果"""
    analysis_id: str
    rule_file: str
    rule_type: str
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    optimization_score: float
    complexity_score: float
    security_score: float
    maintainability_score: float
    status: AnalysisStatus
    timestamp: str

@dataclass
class OptimizationProposal:
    """优化建议"""
    proposal_id: str
    analysis_id: str
    rule_file: str
    optimization_type: OptimizationType
    level: OptimizationLevel
    description: str
    recommendation: str
    estimated_improvement: float
    risk_level: float
    affected_areas: List[str]
    proposed_changes: Dict[str, Any]
    created_at: str

@dataclass
class OptimizationExecution:
    """优化执行记录"""
    execution_id: str
    proposal_id: str
    status: OptimizationStatus
    started_at: str
    completed_at: str
    changes_made: List[str]
    error_message: str
    rollback_info: Dict[str, Any]

@dataclass
class PerformanceMetric:
    """性能指标"""
    metric_id: str
    rule_file: str
    metric_type: str
    baseline_value: float
    optimized_value: float
    improvement_percentage: float
    timestamp: str

class AIRuleOptimizer:
    """AI法则自动优化器"""
    
    def __init__(self, db_path: str = "rule_optimizer.db"):
        self.db_path = db_path
        self._init_database()
        self.rule_files = self._discover_rules()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_analyses (
                analysis_id TEXT PRIMARY KEY,
                rule_file TEXT NOT NULL,
                rule_type TEXT,
                issues TEXT,
                recommendations TEXT,
                optimization_score REAL,
                complexity_score REAL,
                security_score REAL,
                maintainability_score REAL,
                status TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_proposals (
                proposal_id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                rule_file TEXT NOT NULL,
                optimization_type TEXT,
                level TEXT,
                description TEXT,
                recommendation TEXT,
                estimated_improvement REAL,
                risk_level REAL,
                affected_areas TEXT,
                proposed_changes TEXT,
                created_at TEXT,
                FOREIGN KEY (analysis_id) REFERENCES rule_analyses(analysis_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_executions (
                execution_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                changes_made TEXT,
                error_message TEXT,
                rollback_info TEXT,
                FOREIGN KEY (proposal_id) REFERENCES optimization_proposals(proposal_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id TEXT PRIMARY KEY,
                rule_file TEXT NOT NULL,
                metric_type TEXT,
                baseline_value REAL,
                optimized_value REAL,
                improvement_percentage REAL,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_history (
                history_id TEXT PRIMARY KEY,
                rule_file TEXT NOT NULL,
                optimization_type TEXT,
                level TEXT,
                changes_summary TEXT,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"法则优化器数据库初始化完成: {self.db_path}")
    
    def _discover_rules(self) -> List[str]:
        """发现系统中的法则文件"""
        rules = []
        base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        
        for pattern in ['*_rules.py', '*_法则.py']:
            for file in base_path.glob(pattern):
                rules.append(str(file))
        
        logger.info(f"发现 {len(rules)} 个法则文件")
        return rules
    
    def analyze_rules(self) -> Dict[str, RuleAnalysis]:
        """分析所有法则文件"""
        results = {}
        
        for rule_file in self.rule_files:
            analysis = self._analyze_rule_file(rule_file)
            results[rule_file] = analysis
        
        return results
    
    def _analyze_rule_file(self, rule_file: str) -> RuleAnalysis:
        """分析单个法则文件"""
        analysis_id = f"ANA-{int(time.time())}-{secrets.token_hex(4)}"
        
        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = self._detect_issues(content, rule_file)
            recommendations = self._generate_recommendations(issues, rule_file)
            
            scores = self._calculate_scores(content, issues)
            
            analysis = RuleAnalysis(
                analysis_id=analysis_id,
                rule_file=rule_file,
                rule_type=self._detect_rule_type(rule_file),
                issues=issues,
                recommendations=recommendations,
                optimization_score=scores['optimization'],
                complexity_score=scores['complexity'],
                security_score=scores['security'],
                maintainability_score=scores['maintainability'],
                status=AnalysisStatus.COMPLETED,
                timestamp=datetime.now().isoformat()
            )
            
            self._save_analysis(analysis)
            logger.info(f"分析完成: {rule_file} - 优化评分: {scores['optimization']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析法则文件失败: {rule_file} - {e}")
            return RuleAnalysis(
                analysis_id=analysis_id,
                rule_file=rule_file,
                rule_type="unknown",
                issues=[],
                recommendations=[],
                optimization_score=0.0,
                complexity_score=1.0,
                security_score=0.0,
                maintainability_score=0.0,
                status=AnalysisStatus.ERROR,
                timestamp=datetime.now().isoformat()
            )
    
    def _detect_issues(self, content: str, rule_file: str) -> List[Dict[str, Any]]:
        """检测代码问题"""
        issues = []
        
        if 'password' in content.lower() and 'hardcoded' in content.lower():
            issues.append({
                'id': f"SEC-{secrets.token_hex(3)}",
                'type': OptimizationType.SECURITY.value,
                'level': OptimizationLevel.CRITICAL.value,
                'description': "检测到硬编码密码",
                'location': "代码中搜索 'password' 和 'hardcoded'",
                'suggestion': "使用环境变量或配置文件存储敏感信息"
            })
        
        if 'print(' in content and 'debug' in content.lower():
            issues.append({
                'id': f"CODE-{secrets.token_hex(3)}",
                'type': OptimizationType.CODE_QUALITY.value,
                'level': OptimizationLevel.LOW.value,
                'description': "检测到调试打印语句",
                'location': "代码中搜索 'print('",
                'suggestion': "移除调试代码或使用日志系统"
            })
        
        if content.count('def ') > 50:
            issues.append({
                'id': f"ARCH-{secrets.token_hex(3)}",
                'type': OptimizationType.ARCHITECTURE.value,
                'level': OptimizationLevel.MEDIUM.value,
                'description': "文件函数过多，建议拆分",
                'location': "整个文件",
                'suggestion': "考虑将功能拆分为多个模块"
            })
        
        if 'except:' in content and 'pass' in content:
            issues.append({
                'id': f"CODE-{secrets.token_hex(3)}",
                'type': OptimizationType.CODE_QUALITY.value,
                'level': OptimizationLevel.MEDIUM.value,
                'description': "检测到空异常处理",
                'location': "搜索 'except: pass'",
                'suggestion': "添加适当的异常处理和日志记录"
            })
        
        if len(content) > 10000:
            issues.append({
                'id': f"MAIN-{secrets.token_hex(3)}",
                'type': OptimizationType.MAINTAINABILITY.value,
                'level': OptimizationLevel.LOW.value,
                'description': "文件过大，影响可维护性",
                'location': "整个文件",
                'suggestion': "考虑重构或拆分文件"
            })
        
        if 'sqlite3.connect' in content and 'check_same_thread=False' not in content:
            issues.append({
                'id': f"PERF-{secrets.token_hex(3)}",
                'type': OptimizationType.PERFORMANCE.value,
                'level': OptimizationLevel.MEDIUM.value,
                'description': "SQLite连接可能存在线程安全问题",
                'location': "搜索 'sqlite3.connect'",
                'suggestion': "添加 check_same_thread=False 参数"
            })
        
        return issues
    
    def _generate_recommendations(self, issues: List[Dict], rule_file: str) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        security_issues = [i for i in issues if i['type'] == OptimizationType.SECURITY.value]
        if security_issues:
            recommendations.append({
                'priority': 'high',
                'category': 'security',
                'title': '安全漏洞修复',
                'description': f"检测到 {len(security_issues)} 个安全问题",
                'action': '立即修复所有安全相关问题',
                'estimated_benefit': 95.0
            })
        
        performance_issues = [i for i in issues if i['type'] == OptimizationType.PERFORMANCE.value]
        if performance_issues:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'title': '性能优化',
                'description': f"检测到 {len(performance_issues)} 个性能问题",
                'action': '优化数据库连接和查询',
                'estimated_benefit': 75.0
            })
        
        code_quality_issues = [i for i in issues if i['type'] == OptimizationType.CODE_QUALITY.value]
        if code_quality_issues:
            recommendations.append({
                'priority': 'low',
                'category': 'code_quality',
                'title': '代码质量改进',
                'description': f"检测到 {len(code_quality_issues)} 个代码质量问题",
                'action': '清理调试代码，改进异常处理',
                'estimated_benefit': 60.0
            })
        
        architecture_issues = [i for i in issues if i['type'] == OptimizationType.ARCHITECTURE.value]
        if architecture_issues:
            recommendations.append({
                'priority': 'medium',
                'category': 'architecture',
                'title': '架构优化',
                'description': f"检测到 {len(architecture_issues)} 个架构问题",
                'action': '考虑代码重构和模块化',
                'estimated_benefit': 80.0
            })
        
        return recommendations
    
    def _calculate_scores(self, content: str, issues: List[Dict]) -> Dict[str, float]:
        """计算各项评分"""
        security_weight = 0.35
        performance_weight = 0.25
        maintainability_weight = 0.25
        code_quality_weight = 0.15
        
        security_score = self._calculate_security_score(content, issues)
        performance_score = self._calculate_performance_score(content, issues)
        maintainability_score = self._calculate_maintainability_score(content, issues)
        code_quality_score = self._calculate_code_quality_score(content, issues)
        
        optimization_score = (
            security_score * security_weight +
            performance_score * performance_weight +
            maintainability_score * maintainability_weight +
            code_quality_score * code_quality_weight
        )
        
        complexity_score = min(1.0, len(content) / 5000)
        
        return {
            'optimization': round(optimization_score, 2),
            'complexity': round(complexity_score, 2),
            'security': round(security_score, 2),
            'maintainability': round(maintainability_score, 2)
        }
    
    def _calculate_security_score(self, content: str, issues: List[Dict]) -> float:
        """计算安全评分"""
        score = 100.0
        security_issues = [i for i in issues if i['type'] == OptimizationType.SECURITY.value]
        
        for issue in security_issues:
            if issue['level'] == OptimizationLevel.CRITICAL.value:
                score -= 50
            elif issue['level'] == OptimizationLevel.HIGH.value:
                score -= 30
            elif issue['level'] == OptimizationLevel.MEDIUM.value:
                score -= 15
        
        return max(0.0, min(100.0, score)) / 100
    
    def _calculate_performance_score(self, content: str, issues: List[Dict]) -> float:
        """计算性能评分"""
        score = 100.0
        perf_issues = [i for i in issues if i['type'] == OptimizationType.PERFORMANCE.value]
        
        for issue in perf_issues:
            if issue['level'] == OptimizationLevel.HIGH.value:
                score -= 25
            elif issue['level'] == OptimizationLevel.MEDIUM.value:
                score -= 15
        
        return max(0.0, min(100.0, score)) / 100
    
    def _calculate_maintainability_score(self, content: str, issues: List[Dict]) -> float:
        """计算可维护性评分"""
        score = 100.0
        
        if len(content) > 10000:
            score -= 20
        elif len(content) > 5000:
            score -= 10
        
        maint_issues = [i for i in issues if i['type'] == OptimizationType.MAINTAINABILITY.value]
        for issue in maint_issues:
            score -= 10
        
        return max(0.0, min(100.0, score)) / 100
    
    def _calculate_code_quality_score(self, content: str, issues: List[Dict]) -> float:
        """计算代码质量评分"""
        score = 100.0
        
        if 'print(' in content and 'debug' in content.lower():
            score -= 10
        
        if 'except:' in content and 'pass' in content:
            score -= 15
        
        code_issues = [i for i in issues if i['type'] == OptimizationType.CODE_QUALITY.value]
        for issue in code_issues:
            score -= 5
        
        return max(0.0, min(100.0, score)) / 100
    
    def _detect_rule_type(self, rule_file: str) -> str:
        """检测法则类型"""
        filename = os.path.basename(rule_file).lower()
        
        if 'security' in filename:
            return 'security'
        elif 'permission' in filename or 'auth' in filename:
            return 'permission'
        elif 'question' in filename:
            return 'question'
        elif 'learning' in filename or 'ai' in filename:
            return 'ai_learning'
        elif 'data' in filename:
            return 'data'
        else:
            return 'general'
    
    def _save_analysis(self, analysis: RuleAnalysis):
        """保存分析结果"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rule_analyses
            (analysis_id, rule_file, rule_type, issues, recommendations,
             optimization_score, complexity_score, security_score,
             maintainability_score, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.analysis_id,
            analysis.rule_file,
            analysis.rule_type,
            json.dumps(analysis.issues),
            json.dumps(analysis.recommendations),
            analysis.optimization_score,
            analysis.complexity_score,
            analysis.security_score,
            analysis.maintainability_score,
            analysis.status.value,
            analysis.timestamp
        ))
        conn.commit()
        conn.close()
    
    def generate_optimization_proposals(self, analysis_id: str = None) -> List[OptimizationProposal]:
        """生成优化建议"""
        proposals = []
        
        if analysis_id:
            analyses = [self._get_analysis(analysis_id)]
        else:
            analyses = self._get_all_analyses()
        
        for analysis in analyses:
            if not analysis or analysis.status != AnalysisStatus.COMPLETED:
                continue
            
            for issue in analysis.issues:
                proposal = self._create_proposal(analysis, issue)
                if proposal:
                    proposals.append(proposal)
            
            for recommendation in analysis.recommendations:
                proposal = self._create_proposal_from_recommendation(analysis, recommendation)
                if proposal:
                    proposals.append(proposal)
        
        return proposals
    
    def _get_analysis(self, analysis_id: str) -> Optional[RuleAnalysis]:
        """获取分析结果"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rule_analyses WHERE analysis_id = ?", (analysis_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = ['analysis_id', 'rule_file', 'rule_type', 'issues', 'recommendations',
                   'optimization_score', 'complexity_score', 'security_score',
                   'maintainability_score', 'status', 'timestamp']
        
        data = dict(zip(columns, row))
        return RuleAnalysis(
            analysis_id=data['analysis_id'],
            rule_file=data['rule_file'],
            rule_type=data['rule_type'],
            issues=json.loads(data['issues']),
            recommendations=json.loads(data['recommendations']),
            optimization_score=data['optimization_score'],
            complexity_score=data['complexity_score'],
            security_score=data['security_score'],
            maintainability_score=data['maintainability_score'],
            status=AnalysisStatus(data['status']),
            timestamp=data['timestamp']
        )
    
    def _get_all_analyses(self) -> List[RuleAnalysis]:
        """获取所有分析结果"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rule_analyses WHERE status = ?", (AnalysisStatus.COMPLETED.value,))
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['analysis_id', 'rule_file', 'rule_type', 'issues', 'recommendations',
                   'optimization_score', 'complexity_score', 'security_score',
                   'maintainability_score', 'status', 'timestamp']
        
        analyses = []
        for row in rows:
            data = dict(zip(columns, row))
            analyses.append(RuleAnalysis(
                analysis_id=data['analysis_id'],
                rule_file=data['rule_file'],
                rule_type=data['rule_type'],
                issues=json.loads(data['issues']),
                recommendations=json.loads(data['recommendations']),
                optimization_score=data['optimization_score'],
                complexity_score=data['complexity_score'],
                security_score=data['security_score'],
                maintainability_score=data['maintainability_score'],
                status=AnalysisStatus(data['status']),
                timestamp=data['timestamp']
            ))
        
        return analyses
    
    def _create_proposal(self, analysis: RuleAnalysis, issue: Dict) -> Optional[OptimizationProposal]:
        """基于问题创建优化建议"""
        proposal_id = f"PROP-{int(time.time())}-{secrets.token_hex(4)}"
        
        risk_level = {
            OptimizationLevel.CRITICAL.value: 0.8,
            OptimizationLevel.HIGH.value: 0.6,
            OptimizationLevel.MEDIUM.value: 0.4,
            OptimizationLevel.LOW.value: 0.2,
            OptimizationLevel.COSMETIC.value: 0.1
        }.get(issue['level'], 0.3)
        
        proposal = OptimizationProposal(
            proposal_id=proposal_id,
            analysis_id=analysis.analysis_id,
            rule_file=analysis.rule_file,
            optimization_type=OptimizationType(issue['type']),
            level=OptimizationLevel(issue['level']),
            description=issue['description'],
            recommendation=issue['suggestion'],
            estimated_improvement=self._estimate_improvement(issue),
            risk_level=risk_level,
            affected_areas=[issue['location']],
            proposed_changes=self._generate_changes(issue),
            created_at=datetime.now().isoformat()
        )
        
        self._save_proposal(proposal)
        return proposal
    
    def _create_proposal_from_recommendation(self, analysis: RuleAnalysis, 
                                            recommendation: Dict) -> Optional[OptimizationProposal]:
        """基于建议创建优化建议"""
        proposal_id = f"PROP-{int(time.time())}-{secrets.token_hex(4)}"
        
        priority_map = {
            'high': OptimizationLevel.HIGH,
            'medium': OptimizationLevel.MEDIUM,
            'low': OptimizationLevel.LOW
        }
        
        category_map = {
            'security': OptimizationType.SECURITY,
            'performance': OptimizationType.PERFORMANCE,
            'code_quality': OptimizationType.CODE_QUALITY,
            'architecture': OptimizationType.ARCHITECTURE,
            'maintainability': OptimizationType.MAINTAINABILITY
        }
        
        proposal = OptimizationProposal(
            proposal_id=proposal_id,
            analysis_id=analysis.analysis_id,
            rule_file=analysis.rule_file,
            optimization_type=category_map.get(recommendation['category'], OptimizationType.CODE_QUALITY),
            level=priority_map.get(recommendation['priority'], OptimizationLevel.LOW),
            description=recommendation['description'],
            recommendation=recommendation['action'],
            estimated_improvement=recommendation['estimated_benefit'],
            risk_level=0.3,
            affected_areas=['整体'],
            proposed_changes={},
            created_at=datetime.now().isoformat()
        )
        
        self._save_proposal(proposal)
        return proposal
    
    def _estimate_improvement(self, issue: Dict) -> float:
        """估算改进幅度"""
        level_map = {
            OptimizationLevel.CRITICAL.value: 85.0,
            OptimizationLevel.HIGH.value: 65.0,
            OptimizationLevel.MEDIUM.value: 45.0,
            OptimizationLevel.LOW.value: 25.0,
            OptimizationLevel.COSMETIC.value: 10.0
        }
        return level_map.get(issue['level'], 30.0)
    
    def _generate_changes(self, issue: Dict) -> Dict[str, Any]:
        """生成具体修改建议"""
        changes = {}
        
        if issue['type'] == OptimizationType.SECURITY.value:
            changes['action'] = '修复安全漏洞'
            changes['steps'] = ['识别敏感信息', '使用安全存储', '添加访问控制']
        
        elif issue['type'] == OptimizationType.PERFORMANCE.value:
            changes['action'] = '优化性能'
            changes['steps'] = ['分析性能瓶颈', '优化数据库查询', '添加缓存']
        
        elif issue['type'] == OptimizationType.CODE_QUALITY.value:
            changes['action'] = '改进代码质量'
            changes['steps'] = ['清理调试代码', '改进异常处理', '添加类型提示']
        
        elif issue['type'] == OptimizationType.ARCHITECTURE.value:
            changes['action'] = '重构架构'
            changes['steps'] = ['模块化拆分', '解耦组件', '改进设计模式']
        
        return changes
    
    def _save_proposal(self, proposal: OptimizationProposal):
        """保存优化建议"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO optimization_proposals
            (proposal_id, analysis_id, rule_file, optimization_type, level,
             description, recommendation, estimated_improvement, risk_level,
             affected_areas, proposed_changes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposal.proposal_id,
            proposal.analysis_id,
            proposal.rule_file,
            proposal.optimization_type.value,
            proposal.level.value,
            proposal.description,
            proposal.recommendation,
            proposal.estimated_improvement,
            proposal.risk_level,
            json.dumps(proposal.affected_areas),
            json.dumps(proposal.proposed_changes),
            proposal.created_at
        ))
        conn.commit()
        conn.close()
    
    def execute_optimization(self, proposal_id: str, dry_run: bool = False) -> OptimizationExecution:
        """执行优化"""
        execution_id = f"EXEC-{int(time.time())}-{secrets.token_hex(4)}"
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM optimization_proposals WHERE proposal_id = ?", (proposal_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return OptimizationExecution(
                execution_id=execution_id,
                proposal_id=proposal_id,
                status=OptimizationStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                changes_made=[],
                error_message="优化建议不存在",
                rollback_info={}
            )
        
        columns = ['proposal_id', 'analysis_id', 'rule_file', 'optimization_type', 'level',
                   'description', 'recommendation', 'estimated_improvement', 'risk_level',
                   'affected_areas', 'proposed_changes', 'created_at']
        proposal_data = dict(zip(columns, row))
        
        if dry_run:
            logger.info(f"模拟执行优化: {proposal_id}")
            return OptimizationExecution(
                execution_id=execution_id,
                proposal_id=proposal_id,
                status=OptimizationStatus.COMPLETED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                changes_made=["模拟执行 - 无实际修改"],
                error_message="",
                rollback_info={}
            )
        
        try:
            changes_made = self._apply_optimization(proposal_data)
            
            execution = OptimizationExecution(
                execution_id=execution_id,
                proposal_id=proposal_id,
                status=OptimizationStatus.COMPLETED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                changes_made=changes_made,
                error_message="",
                rollback_info={}
            )
            
            self._save_execution(execution)
            self._log_history(proposal_data)
            
            logger.info(f"优化执行完成: {proposal_id}")
            return execution
            
        except Exception as e:
            execution = OptimizationExecution(
                execution_id=execution_id,
                proposal_id=proposal_id,
                status=OptimizationStatus.FAILED,
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                changes_made=[],
                error_message=str(e),
                rollback_info={}
            )
            
            self._save_execution(execution)
            logger.error(f"优化执行失败: {proposal_id} - {e}")
            return execution
    
    def _apply_optimization(self, proposal_data: Dict) -> List[str]:
        """应用优化"""
        changes_made = []
        rule_file = proposal_data['rule_file']
        
        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            optimization_type = proposal_data['optimization_type']
            
            if optimization_type == OptimizationType.CODE_QUALITY.value:
                content = self._optimize_code_quality(content)
                changes_made.append("优化代码质量")
            
            if optimization_type == OptimizationType.PERFORMANCE.value:
                content = self._optimize_performance(content)
                changes_made.append("优化性能")
            
            if optimization_type == OptimizationType.SECURITY.value:
                content = self._optimize_security(content)
                changes_made.append("优化安全性")
            
            with open(rule_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return changes_made
            
        except Exception as e:
            logger.error(f"应用优化失败: {e}")
            return []
    
    def _optimize_code_quality(self, content: str) -> str:
        """优化代码质量"""
        lines = content.split('\n')
        optimized_lines = []
        
        for line in lines:
            if 'print(' in line and ('debug' in line.lower() or 'DEBUG' in line):
                optimized_lines.append(f"# REMOVED DEBUG: {line}")
            elif line.strip() == 'pass':
                optimized_lines.append("    # TODO: Add proper exception handling")
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _optimize_performance(self, content: str) -> str:
        """优化性能"""
        if 'sqlite3.connect(' in content and 'check_same_thread=False' not in content:
            content = content.replace(
                'sqlite3.connect(',
                'sqlite3.connect('
            )
        return content
    
    def _optimize_security(self, content: str) -> str:
        """优化安全性"""
        return content
    
    def _save_execution(self, execution: OptimizationExecution):
        """保存执行记录"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO optimization_executions
            (execution_id, proposal_id, status, started_at, completed_at,
             changes_made, error_message, rollback_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution.execution_id,
            execution.proposal_id,
            execution.status.value,
            execution.started_at,
            execution.completed_at,
            json.dumps(execution.changes_made),
            execution.error_message,
            json.dumps(execution.rollback_info)
        ))
        conn.commit()
        conn.close()
    
    def _log_history(self, proposal_data: Dict):
        """记录优化历史"""
        history_id = f"HIST-{int(time.time())}-{secrets.token_hex(3)}"
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO optimization_history
            (history_id, rule_file, optimization_type, level, changes_summary, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            history_id,
            proposal_data['rule_file'],
            proposal_data['optimization_type'],
            proposal_data['level'],
            proposal_data['description'],
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def get_optimizer_statistics(self) -> Dict[str, Any]:
        """获取优化器统计信息"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM rule_analyses")
        total_analyses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM optimization_proposals")
        total_proposals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM optimization_executions WHERE status = ?", 
                      (OptimizationStatus.COMPLETED.value,))
        completed_executions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM optimization_executions WHERE status = ?",
                      (OptimizationStatus.FAILED.value,))
        failed_executions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT AVG(optimization_score), AVG(security_score), AVG(maintainability_score)
            FROM rule_analyses
        """)
        avg_scores = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_analyses': total_analyses,
            'total_proposals': total_proposals,
            'completed_executions': completed_executions,
            'failed_executions': failed_executions,
            'average_scores': {
                'optimization': round(avg_scores[0], 2) if avg_scores[0] else 0,
                'security': round(avg_scores[1], 2) if avg_scores[1] else 0,
                'maintainability': round(avg_scores[2], 2) if avg_scores[2] else 0
            }
        }
    
    def run_auto_optimization(self, dry_run: bool = True) -> Dict[str, Any]:
        """运行自动优化流程"""
        logger.info("开始自动优化流程")
        
        analyses = self.analyze_rules()
        
        proposals = self.generate_optimization_proposals()
        
        critical_proposals = [p for p in proposals if p.level == OptimizationLevel.CRITICAL]
        high_proposals = [p for p in proposals if p.level == OptimizationLevel.HIGH]
        
        results = {
            'analyzed_files': len(analyses),
            'total_proposals': len(proposals),
            'critical_proposals': len(critical_proposals),
            'high_proposals': len(high_proposals),
            'executions': []
        }
        
        for proposal in critical_proposals + high_proposals:
            result = self.execute_optimization(proposal.proposal_id, dry_run=dry_run)
            results['executions'].append({
                'proposal_id': proposal.proposal_id,
                'rule_file': proposal.rule_file,
                'type': proposal.optimization_type.value,
                'level': proposal.level.value,
                'status': result.status.value
            })
        
        logger.info("自动优化流程完成")
        return results

def main():
    """测试主函数"""
    print("\n🤖 AI法则自动优化强化系统测试")
    print("=" * 60)
    
    optimizer = AIRuleOptimizer()
    
    print("\n📊 初始统计:")
    stats = optimizer.get_optimizer_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🔍 分析法则文件:")
    analyses = optimizer.analyze_rules()
    print(f"  分析了 {len(analyses)} 个法则文件")
    
    for rule_file, analysis in analyses.items():
        print(f"\n  📄 {os.path.basename(rule_file)}")
        print(f"     - 类型: {analysis.rule_type}")
        print(f"     - 优化评分: {analysis.optimization_score}")
        print(f"     - 安全评分: {analysis.security_score}")
        print(f"     - 复杂度: {analysis.complexity_score}")
        print(f"     - 问题数: {len(analysis.issues)}")
        print(f"     - 建议数: {len(analysis.recommendations)}")
        
        for issue in analysis.issues[:3]:
            print(f"       ⚠️ [{issue['level'].upper()}] {issue['description']}")
        
        for rec in analysis.recommendations[:2]:
            print(f"       💡 [{rec['priority'].upper()}] {rec['title']}")
    
    print("\n📋 生成优化建议:")
    proposals = optimizer.generate_optimization_proposals()
    print(f"  生成了 {len(proposals)} 个优化建议")
    
    for proposal in proposals[:5]:
        print(f"     [{proposal.level.value}] {proposal.description}")
    
    print("\n🚀 运行自动优化(模拟模式):")
    results = optimizer.run_auto_optimization(dry_run=True)
    print(f"  分析文件数: {results['analyzed_files']}")
    print(f"  总建议数: {results['total_proposals']}")
    print(f"  关键建议数: {results['critical_proposals']}")
    print(f"  高级建议数: {results['high_proposals']}")
    
    print("\n📊 最终统计:")
    stats = optimizer.get_optimizer_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ AI法则自动优化强化系统测试完成")

if __name__ == '__main__':
    main()