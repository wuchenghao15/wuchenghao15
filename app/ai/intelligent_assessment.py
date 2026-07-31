#!/usr/bin/env python3
import sqlite3
import json
import os
from datetime import datetime
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AIIntelligentAssessment:
    """AI智能评估系统 - 全方位评估用户学习效果和能力水平"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def assess_user_knowledge(self, user_id):
        """评估用户知识掌握程度"""
        assessment = {
            'user_id': user_id,
            'assessment_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'knowledge_areas': [],
            'overall_score': 0,
            'recommendations': []
        }
        
        knowledge_areas = ['Python', '机器学习', '深度学习', '算法', '数据科学', '神经网络', 'NLP', 'Arduino']
        
        for area in knowledge_areas:
            score, details = self._assess_knowledge_area(user_id, area)
            assessment['knowledge_areas'].append({
                'area': area,
                'score': score,
                'level': self._get_level(score),
                'details': details
            })
        
        if assessment['knowledge_areas']:
            assessment['overall_score'] = round(
                sum(a['score'] for a in assessment['knowledge_areas']) / len(assessment['knowledge_areas']),
                2
            )
        
        assessment['recommendations'] = self._generate_recommendations(assessment)
        
        return assessment
    
    def _assess_knowledge_area(self, user_id, area):
        """评估特定知识领域"""
        score = 0.3
        details = {
            'learning_count': 0,
            'completed_tasks': 0,
            'quiz_scores': [],
            'project_count': 0
        }
        
        if area == 'Arduino':
            self.cursor.execute('''
                SELECT COUNT(*) as count 
                FROM arduino_projects 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = self.cursor.fetchone()
            if row:
                details['project_count'] = row['count'] or 0
                
                self.cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM arduino_projects 
                    WHERE user_id = ? AND status = 'completed'
                ''', (user_id,))
                
                completed_row = self.cursor.fetchone()
                details['completed_tasks'] = completed_row['count'] or 0 if completed_row else 0
                
                project_bonus = min(details['project_count'] / 5, 0.3)
                completed_bonus = min(details['completed_tasks'] / 3, 0.3)
                score = 0.3 + project_bonus + completed_bonus
            
            self.cursor.execute('''
                SELECT COUNT(*) as count 
                FROM learning_records 
                WHERE learning_content LIKE ?
            ''', ('%Arduino%',))
            
            row = self.cursor.fetchone()
            if row:
                details['learning_count'] = row['count'] or 0
                learning_bonus = min(details['learning_count'] / 10, 0.2)
                score += learning_bonus
        else:
            self.cursor.execute('''
                SELECT COUNT(*) as count 
                FROM learning_records 
                WHERE learning_content LIKE ?
            ''', (f'%{area}%',))
            
            row = self.cursor.fetchone()
            if row:
                details['learning_count'] = row['count'] or 0
                details['completed_tasks'] = row['count'] or 0
                
                count_bonus = min(details['learning_count'] / 20, 0.3)
                tasks_bonus = min(details['completed_tasks'] / 10, 0.2)
                score = 0.3 + count_bonus + tasks_bonus
        
        self.cursor.execute('''
            SELECT confidence_score 
            FROM learning_records 
            WHERE learning_content LIKE ? AND confidence_score IS NOT NULL
        ''', (f'%{area}%',))
        
        scores = [row['confidence_score'] for row in self.cursor.fetchall()]
        if scores:
            avg_score = sum(scores) / len(scores)
            details['quiz_scores'] = scores
            score = max(score, avg_score)
        
        score = min(score, 0.95)
        
        return round(score, 2), details
    
    def _get_level(self, score):
        """根据分数获取等级"""
        if score >= 0.9:
            return '精通'
        elif score >= 0.7:
            return '熟练'
        elif score >= 0.5:
            return '掌握'
        elif score >= 0.3:
            return '入门'
        else:
            return '零基础'
    
    def _generate_recommendations(self, assessment):
        """根据评估结果生成建议"""
        recommendations = []
        
        weak_areas = [a for a in assessment['knowledge_areas'] if a['score'] < 0.5]
        strong_areas = [a for a in assessment['knowledge_areas'] if a['score'] >= 0.7]
        
        if weak_areas:
            recommendations.append({
                'type': 'priority',
                'title': '重点学习',
                'content': f"建议优先提升以下领域: {', '.join([a['area'] for a in weak_areas])}",
                'action': '增加学习时间，完成基础练习'
            })
        
        if strong_areas:
            recommendations.append({
                'type': 'advanced',
                'title': '进阶学习',
                'content': f"以下领域可以深入学习: {', '.join([a['area'] for a in strong_areas])}",
                'action': '尝试复杂项目，阅读高级文档'
            })
        
        if assessment['overall_score'] < 0.5:
            recommendations.append({
                'type': 'foundation',
                'title': '基础建设',
                'content': '整体知识水平较低，建议系统学习基础知识',
                'action': '制定学习计划，每天坚持学习'
            })
        
        return recommendations
    
    def generate_assessment_report(self, user_id):
        """生成完整评估报告"""
        assessment = self.assess_user_knowledge(user_id)
        
        report = {
            'title': 'AI学习能力评估报告',
            'user_id': user_id,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'overall_score': assessment['overall_score'],
                'overall_level': self._get_level(assessment['overall_score']),
                'strong_points': [a['area'] for a in assessment['knowledge_areas'] if a['score'] >= 0.7],
                'weak_points': [a['area'] for a in assessment['knowledge_areas'] if a['score'] < 0.5]
            },
            'detail': assessment['knowledge_areas'],
            'recommendations': assessment['recommendations'],
            'improvement_plan': self._generate_improvement_plan(assessment)
        }
        
        return report
    
    def _generate_improvement_plan(self, assessment):
        """生成改进计划"""
        plan = []
        
        for area in assessment['knowledge_areas']:
            if area['score'] < 0.7:
                target_score = min(area['score'] + 0.2, 0.9)
                plan.append({
                    'area': area['area'],
                    'current_score': area['score'],
                    'target_score': target_score,
                    'target_level': self._get_level(target_score),
                    'suggestions': [
                        f"增加{area['area']}学习时间，建议每周学习5小时",
                        f"完成{area['area']}相关练习任务5-10个",
                        f"阅读{area['area']}相关技术文档和书籍",
                        f"参与{area['area']}相关项目实践"
                    ]
                })
        
        return plan
    
    def save_assessment(self, report):
        """保存评估结果"""
        overall_score = report.get('overall_score', report.get('summary', {}).get('overall_score', 0.5))
        
        self.cursor.execute('''
            INSERT INTO ai_knowledge 
            (knowledge_id, knowledge_category, knowledge_title, knowledge_content, 
             knowledge_source, relevance_score, confidence_level, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"assess_{report['user_id']}_{datetime.now().strftime('%Y%m%d')}",
            'assessment',
            f"用户{report['user_id']}能力评估",
            json.dumps(report),
            'AI生成',
            overall_score,
            'high',
            '评估报告'
        ))
        
        self.conn.commit()
    
    def get_user_assessment_history(self, user_id, limit=10):
        """获取用户评估历史"""
        self.cursor.execute('''
            SELECT * FROM ai_knowledge 
            WHERE knowledge_category = 'assessment' AND knowledge_content LIKE ?
            ORDER BY created_at DESC LIMIT ?
        ''', (f'%user_id.*{user_id}%', limit))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    assessor = AIIntelligentAssessment()
    
    logger.info("=== AI智能评估系统 ===")
    report = assessor.generate_assessment_report(1)
    
    logger.info(f"\n评估报告: {report['title']}")
    logger.info(f"生成时间: {report['generated_at']}")
    logger.info(f"\n综合评分: {report['summary']['overall_score']}")
    logger.info(f"综合等级: {report['summary']['overall_level']}")
    
    logger.info(f"\n强项: {', '.join(report['summary']['strong_points'])}")
    logger.info(f"弱项: {', '.join(report['summary']['weak_points'])}")
    
    logger.info("\n详细评估:")
    for area in report['detail']:
        logger.info(f"  {area['area']}: {area['score']} ({area['level']})")
        logger.info(f"    学习次数: {area['details']['learning_count']}次")
        logger.info(f"    完成任务: {area['details']['completed_tasks']}个")
    
    logger.info("\n改进建议:")
    for rec in report['recommendations']:
        logger.info(f"  [{rec['type']}] {rec['title']}: {rec['content']}")
    
    assessor.save_assessment(report)
    logger.info("\n评估报告已保存！")
    
    assessor.close()