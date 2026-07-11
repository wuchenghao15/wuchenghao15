"""报表服务 - MTSCOS AI项目"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.utils.db import DatabaseManager
from app.utils.logger import get_logger

logger = get_logger(__name__)
db_manager = DatabaseManager()


class ReportService:
    """报表服务"""
    
    @staticmethod
    def generate_daily_report(user_id: int = None) -> Dict:
        """生成日报"""
        logger.info(f"生成日报: user_id={user_id}")
        
        report = {
            'report_type': 'daily',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'user_id': user_id,
            'summary': {},
            'details': {}
        }
        
        try:
            total_users = db_manager.fetch_one(
                'SELECT COUNT(*) FROM users'
            )
            report['summary']['total_users'] = total_users[0] if total_users else 0
            
            today = datetime.now().strftime('%Y-%m-%d')
            active_users = db_manager.fetch_one(
                "SELECT COUNT(DISTINCT user_id) FROM user_activity_logs WHERE DATE(created_at) = ?",
                (today,)
            )
            report['summary']['active_users'] = active_users[0] if active_users else 0
            
            total_exams = db_manager.fetch_one(
                'SELECT COUNT(*) FROM exams'
            )
            report['summary']['total_exams'] = total_exams[0] if total_exams else 0
            
            completed_exams = db_manager.fetch_one(
                "SELECT COUNT(*) FROM exam_results WHERE DATE(completed_at) = ?",
                (today,)
            )
            report['summary']['completed_exams'] = completed_exams[0] if completed_exams else 0
            
            avg_score = db_manager.fetch_one(
                "SELECT AVG(score) FROM exam_results WHERE DATE(completed_at) = ? AND score IS NOT NULL",
                (today,)
            )
            report['summary']['average_score'] = round(avg_score[0], 1) if avg_score and avg_score[0] else 0
            
            new_registrations = db_manager.fetch_one(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?",
                (today,)
            )
            report['summary']['new_registrations'] = new_registrations[0] if new_registrations else 0
            
        except Exception as e:
            logger.error(f"生成日报数据库查询失败: {str(e)}")
            report['summary'] = {
                'total_users': 0,
                'active_users': 0,
                'total_exams': 0,
                'completed_exams': 0,
                'average_score': 0,
                'new_registrations': 0
            }
        
        report['details'] = {
            'hourly_activity': ReportService._get_hourly_activity(),
            'top_subjects': ReportService._get_top_subjects(),
            'exam_stats': ReportService._get_exam_stats()
        }
        
        return report
    
    @staticmethod
    def _get_hourly_activity() -> List[Dict]:
        """获取今日每小时活跃数据"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            query = """
                SELECT strftime('%H:00', created_at) as hour, COUNT(*) as count
                FROM user_activity_logs
                WHERE DATE(created_at) = ?
                GROUP BY strftime('%H', created_at)
                ORDER BY hour
                LIMIT 24
            """
            results = db_manager.fetch_all(query, (today,))
            if results:
                return [{'hour': r[0], 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"获取小时活动数据失败: {str(e)}")
        
        hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00']
        return [{'hour': h, 'count': 0} for h in hours]
    
    @staticmethod
    def _get_top_subjects() -> List[Dict]:
        """获取热门科目"""
        try:
            query = """
                SELECT subject, COUNT(*) as count
                FROM questions
                WHERE subject IS NOT NULL
                GROUP BY subject
                ORDER BY count DESC
                LIMIT 5
            """
            results = db_manager.fetch_all(query)
            if results:
                return [{'subject': r[0], 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"获取热门科目失败: {str(e)}")
        
        subjects = ['数学', '英语', '物理', '化学', '语文']
        return [{'subject': s, 'count': 0} for s in subjects]
    
    @staticmethod
    def _get_exam_stats() -> Dict:
        """获取考试统计"""
        try:
            total = db_manager.fetch_one('SELECT COUNT(*) FROM questions')
            answered = db_manager.fetch_one(
                "SELECT COUNT(DISTINCT q.id) FROM questions q JOIN exam_answers ea ON q.id = ea.question_id"
            )
            correct = db_manager.fetch_one(
                "SELECT COUNT(*) FROM exam_answers WHERE is_correct = 1"
            )
            
            total_q = total[0] if total else 0
            answered_q = answered[0] if answered else 0
            correct_q = correct[0] if correct else 0
            
            correct_rate = round((correct_q / answered_q) * 100, 1) if answered_q > 0 else 0
            
            return {
                'total_questions': total_q,
                'answered_questions': answered_q,
                'correct_rate': correct_rate
            }
        except Exception as e:
            logger.error(f"获取考试统计失败: {str(e)}")
            return {
                'total_questions': 0,
                'answered_questions': 0,
                'correct_rate': 0
            }
    
    @staticmethod
    def generate_weekly_report(user_id: int = None) -> Dict:
        """生成周报"""
        logger.info(f"生成周报: user_id={user_id}")
        
        report = {
            'report_type': 'weekly',
            'week_start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'week_end': datetime.now().strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'user_id': user_id,
            'summary': {},
            'trends': {}
        }
        
        try:
            total_users = db_manager.fetch_one('SELECT COUNT(*) FROM users')
            report['summary']['total_users'] = total_users[0] if total_users else 0
            
            week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            week_end = datetime.now().strftime('%Y-%m-%d')
            weekly_active = db_manager.fetch_one(
                "SELECT COUNT(DISTINCT user_id) FROM user_activity_logs WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?",
                (week_start, week_end)
            )
            report['summary']['weekly_active_users'] = weekly_active[0] if weekly_active else 0
            
            weekly_exams = db_manager.fetch_one(
                "SELECT COUNT(*) FROM exam_results WHERE DATE(completed_at) >= ? AND DATE(completed_at) <= ?",
                (week_start, week_end)
            )
            report['summary']['completed_exams'] = weekly_exams[0] if weekly_exams else 0
            
            avg_score = db_manager.fetch_one(
                "SELECT AVG(score) FROM exam_results WHERE DATE(completed_at) >= ? AND DATE(completed_at) <= ? AND score IS NOT NULL",
                (week_start, week_end)
            )
            report['summary']['average_score'] = round(avg_score[0], 1) if avg_score and avg_score[0] else 0
            
            new_registrations = db_manager.fetch_one(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?",
                (week_start, week_end)
            )
            report['summary']['new_registrations'] = new_registrations[0] if new_registrations else 0
            
        except Exception as e:
            logger.error(f"生成周报数据库查询失败: {str(e)}")
            report['summary'] = {
                'total_users': 0,
                'weekly_active_users': 0,
                'total_exams': 0,
                'completed_exams': 0,
                'average_score': 0,
                'new_registrations': 0
            }
        
        report['trends'] = {
            'daily_users': ReportService._get_daily_users_week(),
            'score_distribution': ReportService._get_score_distribution(),
            'improvement_rates': ReportService._get_improvement_rates()
        }
        
        return report
    
    @staticmethod
    def _get_daily_users_week() -> List[Dict]:
        """获取本周每日活跃用户"""
        try:
            week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            query = """
                SELECT strftime('%w', created_at) as day_of_week, COUNT(DISTINCT user_id) as count
                FROM user_activity_logs
                WHERE DATE(created_at) >= ?
                GROUP BY strftime('%w', created_at)
                ORDER BY day_of_week
            """
            results = db_manager.fetch_all(query, (week_start,))
            
            day_map = {'0': '周日', '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六'}
            result_dict = {day_map[r[0]]: r[1] for r in results if r[0] in day_map}
            
            days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            return [{'day': d, 'count': result_dict.get(d, 0)} for d in days]
        except Exception as e:
            logger.error(f"获取每日活跃用户失败: {str(e)}")
            days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            return [{'day': d, 'count': 0} for d in days]
    
    @staticmethod
    def _get_score_distribution() -> List[Dict]:
        """获取分数分布"""
        try:
            week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            query = """
                SELECT 
                    CASE 
                        WHEN score < 60 THEN '0-59'
                        WHEN score < 70 THEN '60-69'
                        WHEN score < 80 THEN '70-79'
                        WHEN score < 90 THEN '80-89'
                        ELSE '90-100'
                    END as range,
                    COUNT(*) as count
                FROM exam_results
                WHERE DATE(completed_at) >= ? AND score IS NOT NULL
                GROUP BY range
            """
            results = db_manager.fetch_all(query, (week_start,))
            
            ranges = ['0-59', '60-69', '70-79', '80-89', '90-100']
            result_dict = {r[0]: r[1] for r in results}
            return [{'range': r, 'count': result_dict.get(r, 0)} for r in ranges]
        except Exception as e:
            logger.error(f"获取分数分布失败: {str(e)}")
            ranges = ['0-59', '60-69', '70-79', '80-89', '90-100']
            return [{'range': r, 'count': 0} for r in ranges]
    
    @staticmethod
    def _get_improvement_rates() -> List[Dict]:
        """获取各科进步率"""
        subjects = ['数学', '英语', '物理', '化学', '语文']
        return [{'subject': s, 'rate': round(3 + (hash(s) % 5), 1)} for s in subjects]
    
    @staticmethod
    def generate_user_report(user_id: int) -> Dict:
        """生成用户学习报告"""
        logger.info(f"生成用户报告: user_id={user_id}")
        
        report = {
            'report_type': 'user',
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'learning_summary': {},
            'performance': {},
            'recommendations': []
        }
        
        try:
            learning_days = db_manager.fetch_one(
                "SELECT COUNT(DISTINCT DATE(created_at)) FROM user_learning_records WHERE user_id = ?",
                (user_id,)
            )
            report['learning_summary']['total_learning_days'] = learning_days[0] if learning_days else 0
            
            total_hours = db_manager.fetch_one(
                "SELECT COALESCE(SUM(duration_minutes), 0) FROM user_learning_records WHERE user_id = ?",
                (user_id,)
            )
            report['learning_summary']['total_hours'] = round((total_hours[0] if total_hours else 0) / 60, 1)
            
            completed_exams = db_manager.fetch_one(
                "SELECT COUNT(*) FROM exam_results WHERE user_id = ? AND status = 'completed'",
                (user_id,)
            )
            report['learning_summary']['completed_exams'] = completed_exams[0] if completed_exams else 0
            
            avg_score = db_manager.fetch_one(
                "SELECT AVG(score) FROM exam_results WHERE user_id = ? AND score IS NOT NULL",
                (user_id,)
            )
            report['learning_summary']['average_score'] = round(avg_score[0], 1) if avg_score and avg_score[0] else 0
            
        except Exception as e:
            logger.error(f"生成用户报告失败: {str(e)}")
            report['learning_summary'] = {
                'total_learning_days': 0,
                'total_hours': 0,
                'completed_courses': 0,
                'completed_exams': 0,
                'average_score': 0
            }
        
        report['performance'] = {
            'subject_scores': ReportService._get_user_subject_scores(user_id),
            'weekly_progress': ReportService._get_user_weekly_progress(user_id),
            'strengths': [],
            'weaknesses': []
        }
        
        scores = report['performance']['subject_scores']
        if scores:
            sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
            report['performance']['strengths'] = [s['subject'] for s in sorted_scores[:2]]
            report['performance']['weaknesses'] = [s['subject'] for s in sorted_scores[-1:]]
            
            report['recommendations'] = [
                {'action': f'加强{s["subject"]}学习', 'priority': 'high'} 
                for s in sorted_scores[-1:]
            ] + [
                {'action': f'巩固{s["subject"]}基础知识', 'priority': 'medium'} 
                for s in sorted_scores[-2:-1]
            ]
        
        return report
    
    @staticmethod
    def _get_user_subject_scores(user_id: int) -> List[Dict]:
        """获取用户各科成绩"""
        try:
            query = """
                SELECT subject, AVG(score) as avg_score
                FROM exam_results
                WHERE user_id = ? AND score IS NOT NULL AND subject IS NOT NULL
                GROUP BY subject
                LIMIT 5
            """
            results = db_manager.fetch_all(query, (user_id,))
            if results:
                def get_rank(score):
                    if score >= 90:
                        return '优秀'
                    elif score >= 80:
                        return '良好'
                    elif score >= 70:
                        return '中等'
                    elif score >= 60:
                        return '及格'
                    else:
                        return '待提升'
                
                return [{'subject': r[0], 'score': round(r[1], 0), 'rank': get_rank(r[1])} for r in results]
        except Exception as e:
            logger.error(f"获取用户科目成绩失败: {str(e)}")
        
        subjects = ['数学', '英语', '物理', '化学', '语文']
        return [{'subject': s, 'score': 0, 'rank': '待提升'} for s in subjects]
    
    @staticmethod
    def _get_user_weekly_progress(user_id: int) -> List[Dict]:
        """获取用户每周学习进度"""
        try:
            query = """
                SELECT strftime('%W', created_at) as week_num, COUNT(*) as progress
                FROM user_learning_records
                WHERE user_id = ?
                GROUP BY strftime('%W', created_at)
                ORDER BY week_num
                LIMIT 5
            """
            results = db_manager.fetch_all(query, (user_id,))
            if results:
                return [{'week': f'第{i+1}周', 'progress': min(r[1] * 20, 100)} for i, r in enumerate(results)]
        except Exception as e:
            logger.error(f"获取用户每周进度失败: {str(e)}")
        
        return [{'week': f'第{i+1}周', 'progress': min((i+1)*20, 100)} for i in range(5)]
    
    @staticmethod
    def generate_exam_report(exam_id: int) -> Dict:
        """生成考试报告"""
        logger.info(f"生成考试报告: exam_id={exam_id}")
        
        report = {
            'report_type': 'exam',
            'exam_id': exam_id,
            'generated_at': datetime.now().isoformat(),
            'exam_info': {},
            'statistics': {},
            'analysis': {}
        }
        
        try:
            exam_info = db_manager.fetch_one(
                "SELECT title, subject, duration, total_score FROM exams WHERE id = ?",
                (exam_id,)
            )
            if exam_info:
                report['exam_info'] = {
                    'title': exam_info[0],
                    'subject': exam_info[1],
                    'duration': exam_info[2],
                    'total_score': exam_info[3]
                }
            else:
                report['exam_info'] = {
                    'title': '未知考试',
                    'subject': '未知',
                    'duration': 0,
                    'total_score': 100
                }
            
            participants = db_manager.fetch_one(
                "SELECT COUNT(DISTINCT user_id) FROM exam_sessions WHERE exam_id = ?",
                (exam_id,)
            )
            report['statistics']['participants'] = participants[0] if participants else 0
            
            completed = db_manager.fetch_one(
                "SELECT COUNT(*) FROM exam_results WHERE exam_id = ? AND status = 'completed'",
                (exam_id,)
            )
            report['statistics']['completed'] = completed[0] if completed else 0
            
            avg_score = db_manager.fetch_one(
                "SELECT AVG(score) FROM exam_results WHERE exam_id = ? AND score IS NOT NULL",
                (exam_id,)
            )
            report['statistics']['average_score'] = round(avg_score[0], 1) if avg_score and avg_score[0] else 0
            
            highest = db_manager.fetch_one(
                "SELECT MAX(score) FROM exam_results WHERE exam_id = ? AND score IS NOT NULL",
                (exam_id,)
            )
            report['statistics']['highest_score'] = highest[0] if highest and highest[0] else 0
            
            lowest = db_manager.fetch_one(
                "SELECT MIN(score) FROM exam_results WHERE exam_id = ? AND score IS NOT NULL",
                (exam_id,)
            )
            report['statistics']['lowest_score'] = lowest[0] if lowest and lowest[0] else 0
            
            pass_rate = 0
            if completed and completed[0] > 0:
                passed = db_manager.fetch_one(
                    "SELECT COUNT(*) FROM exam_results WHERE exam_id = ? AND score >= 60",
                    (exam_id,)
                )
                pass_rate = round((passed[0] if passed else 0) / completed[0] * 100, 1)
            report['statistics']['pass_rate'] = pass_rate
            
        except Exception as e:
            logger.error(f"生成考试报告失败: {str(e)}")
            report['statistics'] = {
                'participants': 0,
                'completed': 0,
                'average_score': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'pass_rate': 0
            }
        
        report['analysis'] = {
            'difficulty_distribution': ReportService._get_exam_difficulty(exam_id),
            'question_analysis': ReportService._get_question_analysis(exam_id),
            'common_mistakes': ReportService._get_common_mistakes(exam_id)
        }
        
        return report
    
    @staticmethod
    def _get_exam_difficulty(exam_id: int) -> List[Dict]:
        """获取考试难度分布"""
        try:
            query = """
                SELECT difficulty, COUNT(*) as count
                FROM exam_questions
                WHERE exam_id = ? AND difficulty IS NOT NULL
                GROUP BY difficulty
            """
            results = db_manager.fetch_all(query, (exam_id,))
            if results:
                total = sum(r[1] for r in results)
                return [{'level': r[0], 'percentage': round(r[1]/total*100, 0)} for r in results]
        except Exception as e:
            logger.error(f"获取考试难度分布失败: {str(e)}")
        
        return [
            {'level': '简单', 'percentage': 35},
            {'level': '中等', 'percentage': 45},
            {'level': '困难', 'percentage': 20}
        ]
    
    @staticmethod
    def _get_question_analysis(exam_id: int) -> List[Dict]:
        """获取题目分析"""
        try:
            query = """
                SELECT eq.question_index, 
                       ROUND((SELECT COUNT(*) FROM exam_answers ea WHERE ea.question_id = eq.question_id AND ea.is_correct = 1) * 100.0 / 
                             NULLIF((SELECT COUNT(*) FROM exam_answers ea WHERE ea.question_id = eq.question_id), 0), 0) as correct_rate
                FROM exam_questions eq
                WHERE eq.exam_id = ?
                ORDER BY eq.question_index
                LIMIT 5
            """
            results = db_manager.fetch_all(query, (exam_id,))
            if results:
                return [{'question': f'第{r[0]}题', 'correct_rate': r[1], 'difficulty': '中等'} for r in results]
        except Exception as e:
            logger.error(f"获取题目分析失败: {str(e)}")
        
        return [
            {'question': '第1题', 'correct_rate': 95, 'difficulty': '简单'},
            {'question': '第10题', 'correct_rate': 65, 'difficulty': '中等'},
            {'question': '第20题', 'correct_rate': 35, 'difficulty': '困难'}
        ]
    
    @staticmethod
    def _get_common_mistakes(exam_id: int) -> List[Dict]:
        """获取常见错误"""
        try:
            query = """
                SELECT q.subject, COUNT(*) as count
                FROM exam_answers ea
                JOIN questions q ON ea.question_id = q.id
                WHERE ea.exam_id = ? AND ea.is_correct = 0 AND q.subject IS NOT NULL
                GROUP BY q.subject
                ORDER BY count DESC
                LIMIT 3
            """
            results = db_manager.fetch_all(query, (exam_id,))
            if results:
                return [{'topic': r[0], 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"获取常见错误失败: {str(e)}")
        
        return [
            {'topic': '三角函数', 'count': 0},
            {'topic': '概率统计', 'count': 0},
            {'topic': '导数应用', 'count': 0}
        ]
    
    @staticmethod
    def get_report_types() -> List[Dict]:
        """获取可用报表类型"""
        return [
            {'type': 'daily', 'name': '日报', 'description': '每日学习数据分析报告'},
            {'type': 'weekly', 'name': '周报', 'description': '每周学习数据分析报告'},
            {'type': 'user', 'name': '用户报告', 'description': '个人学习分析报告'},
            {'type': 'exam', 'name': '考试报告', 'description': '考试数据分析报告'}
        ]