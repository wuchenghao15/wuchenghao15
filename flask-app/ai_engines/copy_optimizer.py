"""
AI 文案优化引擎 (Copy Optimizer)
CHMS-04: 文案质量分析+优化建议+孤立文案识别

5维度评分模型（A轮决议D-03）:
  清晰度(clarity) 0.175
  一致性(consistency) 0.175
  完整性(completeness) 0.175
  准确性(accuracy) 0.175
  安全合规(safety) 0.300  <- 权重最高

归档: flask-app/ai_engines/copy_optimizer.py
流程: §14 12步骤 STEP_7_EXECUTE
"""
import os
import re
import sqlite3
from typing import Dict, Any, List, Optional


# 评分维度权重（A轮决议D-03）
SCORE_WEIGHTS = {
    'clarity': 0.175,
    'consistency': 0.175,
    'completeness': 0.175,
    'accuracy': 0.175,
    'safety': 0.300,
}

# 敏感信息检测正则
SENSITIVE_PATTERNS = [
    (r'password\s*[:=]\s*[\'"][^\'"]+[\'"]', '硬编码密码'),
    (r'(?:api_?key|secret|token)\s*[:=]\s*[\'"][^\'"]+[\'"]', '硬编码密钥/令牌'),
    (r'mockValidTokens\s*=\s*\[', '硬编码测试凭据'),
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '硬编码IP地址'),
    (r'(?:admin|root|test)_(?:pass|pwd|token)\d*', '弱密码/测试密码'),
]

# 占位文案检测
PLACEHOLDER_INDICATORS = [
    'TODO', 'FIXME', 'PLACEHOLDER', '占位', '待补充',
    '模拟', '假数据', 'mock', 'dummy', 'lorem ipsum',
    '测试数据', '示例', 'example',
]


class CopyOptimizer:
    """AI 文案优化引擎"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base, 'app.db')
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========== 5维度评分 ==========

    def score_clarity(self, content: str) -> float:
        """清晰度评分：文案是否易懂、无歧义"""
        if not content:
            return 0
        score = 100.0
        # 过长文案扣分
        if len(content) > 500:
            score -= min(20, (len(content) - 500) / 50)
        # 含TODO/FIXME扣分
        if re.search(r'(TODO|FIXME|HACK|XXX)', content, re.I):
            score -= 30
        # 含无意义占位词扣分
        for ph in PLACEHOLDER_INDICATORS:
            if ph.lower() in content.lower():
                score -= 15
                break
        # 含乱码检测（非中文非ASCII非常见标点）
        garbage = re.findall(r'[^\u4e00-\u9fff\u0020-\u007e\uff00-\uffef\u3000-\u303f\n\r\t]', content)
        if len(garbage) > len(content) * 0.1:
            score -= 20
        return max(0, min(100, score))

    def score_consistency(self, content: str, copy_type: str = '') -> float:
        """一致性评分：与同类文案风格是否统一"""
        if not content:
            return 0
        score = 100.0
        # 标点一致性：中英文标点混用扣分
        has_cn_punct = bool(re.search(r'[，。！？；：、""''（）【】]', content))
        has_en_punct = bool(re.search(r'[,.!?;:"\'\(\)\[\]]', content))
        # 同一句中中英文标点混用
        if has_cn_punct and has_en_punct:
            sentences = re.split(r'[。！？\n]', content)
            mixed = 0
            for s in sentences:
                if re.search(r'[，。！？；：]', s) and re.search(r'[,.!?;:]', s):
                    mixed += 1
            if mixed > 0:
                score -= min(15, mixed * 5)
        # 首字母/首字大小写不一致（UI文案特有）
        if copy_type == 'UI_TEXT' and content:
            # 按钮文案应为短文本
            if len(content) > 50:
                score -= 10
        return max(0, min(100, score))

    def score_completeness(self, content: str) -> float:
        """完整性评分：是否缺少必要信息"""
        if not content:
            return 0
        score = 100.0
        # 空内容
        if len(content.strip()) == 0:
            return 0
        # 错误提示未说明原因
        if re.search(r'(错误|失败|失败|异常|error|fail)', content, re.I):
            if not re.search(r'(原因|因为|由于|请|建议|retry|重试|联系)', content, re.I):
                score -= 25
        # 过短文案（按钮除外）
        if len(content) < 2:
            score -= 30
        return max(0, min(100, score))

    def score_accuracy(self, content: str) -> float:
        """准确性评分：文案描述与实际功能是否一致"""
        if not content:
            return 0
        score = 100.0
        # 含"页面"+"。"结尾的占位文案特征
        if re.search(r'.+页面。$', content):
            score -= 40
        # 含路径显示特征（占位页特征）
        if re.search(r'/templates/.+\.html', content):
            score -= 40
        # 含"返回首页"但无其他内容的占位页特征
        if content.strip() in ('返回首页', '返回'):
            score -= 10  # 按钮文案本身不算占位，但需关联检查
        return max(0, min(100, score))

    def score_safety(self, content: str) -> float:
        """安全合规评分：是否包含敏感信息"""
        if not content:
            return 100  # 空文案无安全风险
        score = 100.0
        for pattern, desc in SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.I):
                score -= 30  # 每项敏感信息扣30分
        # 占位文案中的假数据
        for ph in PLACEHOLDER_INDICATORS:
            if ph.lower() in content.lower():
                score -= 20
                break
        return max(0, min(100, score))

    def evaluate(self, content: str, copy_type: str = '') -> Dict[str, Any]:
        """综合评估文案质量（5维度）"""
        scores = {
            'clarity': self.score_clarity(content),
            'consistency': self.score_consistency(content, copy_type),
            'completeness': self.score_completeness(content),
            'accuracy': self.score_accuracy(content),
            'safety': self.score_safety(content),
        }
        # 加权综合分
        total = sum(scores[k] * SCORE_WEIGHTS[k] for k in scores)
        # 生成优化建议
        suggestions = self._generate_suggestions(content, scores, copy_type)
        return {
            'quality_score': round(total, 2),
            'scores': {k: round(v, 2) for k, v in scores.items()},
            'weights': SCORE_WEIGHTS,
            'suggestions': suggestions,
            'level': self._score_level(total)
        }

    def _score_level(self, score: float) -> str:
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 75:
            return 'GOOD'
        elif score >= 60:
            return 'PASS'
        elif score >= 40:
            return 'WARNING'
        else:
            return 'CRITICAL'

    def _generate_suggestions(self, content: str, scores: Dict[str, float],
                              copy_type: str) -> List[str]:
        suggestions = []
        if scores['clarity'] < 70:
            suggestions.append('文案清晰度不足，建议精简表达，移除TODO/占位词')
        if scores['consistency'] < 70:
            suggestions.append('文案标点风格不统一，建议统一使用中文标点')
        if scores['completeness'] < 70:
            suggestions.append('文案完整性不足，错误提示应包含原因和建议操作')
        if scores['accuracy'] < 70:
            suggestions.append('文案可能为占位内容，建议核实与实际功能是否一致')
        if scores['safety'] < 70:
            suggestions.append('⚠️ 文案包含敏感信息（密码/密钥/测试凭据），必须清除')
        if not suggestions:
            suggestions.append('文案质量良好，无需优化')
        return suggestions

    # ========== 优化日志落库 ==========

    def log_optimization(self, copy_id: int, evaluation: Dict[str, Any]) -> bool:
        """记录优化评估到数据库"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO mt_copy_optimization_log
                   (copy_id, quality_score, score_clarity, score_consistency,
                    score_completeness, score_accuracy, score_safety, suggestion, applied)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (copy_id, evaluation['quality_score'],
                 evaluation['scores']['clarity'], evaluation['scores']['consistency'],
                 evaluation['scores']['completeness'], evaluation['scores']['accuracy'],
                 evaluation['scores']['safety'],
                 '; '.join(evaluation['suggestions']))
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def optimize_all(self) -> Dict[str, Any]:
        """批量评估所有文案"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT copy_id, copy_key, copy_content, copy_type FROM mt_copy_assets WHERE status='ACTIVE'")
            rows = cur.fetchall()
            conn.close()

            results = []
            critical_count = 0
            warning_count = 0
            for row in rows:
                content = row['copy_content']
                if not content:
                    continue
                evaluation = self.evaluate(content, row['copy_type'])
                self.log_optimization(row['copy_id'], evaluation)
                results.append({
                    'copy_key': row['copy_key'],
                    'quality_score': evaluation['quality_score'],
                    'level': evaluation['level'],
                    'suggestions': evaluation['suggestions']
                })
                if evaluation['level'] == 'CRITICAL':
                    critical_count += 1
                elif evaluation['level'] == 'WARNING':
                    warning_count += 1

            return {
                'total_evaluated': len(results),
                'critical': critical_count,
                'warning': warning_count,
                'results': results
            }
        except Exception as e:
            return {'error': str(e)}
