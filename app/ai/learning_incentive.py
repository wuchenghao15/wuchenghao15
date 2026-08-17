#!/usr/bin/env python3
import sqlite3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AILearningIncentive:
    """AI学习激励系统 - 激励用户持续学习"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """创建激励相关表"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                badge_name TEXT,
                badge_type TEXT,
                description TEXT,
                icon TEXT,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, badge_name)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                points INTEGER DEFAULT 0,
                earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                source TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                next_level_exp INTEGER DEFAULT 100,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def award_points(self, user_id, points, reason, source='system'):
        """奖励积分"""
        self.cursor.execute('''
            INSERT INTO user_points (user_id, points, reason, source)
            VALUES (?, ?, ?, ?)
        ''', (user_id, points, reason, source))
        
        self._update_user_level(user_id, points)
        self._check_badges(user_id)
        
        self.conn.commit()
    
    def _update_user_level(self, user_id, exp_gained):
        """更新用户等级"""
        self.cursor.execute('''
            SELECT * FROM user_levels WHERE user_id = ?
        ''', (user_id,))
        
        row = self.cursor.fetchone()
        
        if row:
            experience = row['experience'] + exp_gained
            level = row['level']
            next_exp = row['next_level_exp']
            
            while experience >= next_exp:
                experience -= next_exp
                level += 1
                next_exp = int(next_exp * 1.5)
            
            self.cursor.execute('''
                UPDATE user_levels 
                SET experience = ?, level = ?, next_level_exp = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (experience, level, next_exp, user_id))
        else:
            self.cursor.execute('''
                INSERT INTO user_levels (user_id, experience, next_level_exp)
                VALUES (?, ?, ?)
            ''', (user_id, exp_gained, 100))
    
    def _check_badges(self, user_id):
        """检查徽章解锁条件"""
        badges = []
        
        self.cursor.execute('SELECT COUNT(*) FROM learning_records')
        total_learning = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            SELECT COUNT(DISTINCT strftime('%Y-%m-%d', learned_at)) FROM learning_records
        ''')
        active_days = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT AVG(confidence_score) FROM learning_records')
        avg_score = self.cursor.fetchone()[0] or 0
        
        if total_learning >= 10 and not self._has_badge(user_id, '学习新手'):
            badges.append({
                'name': '学习新手',
                'type': 'milestone',
                'description': '完成10次学习',
                'icon': '⭐'
            })
        
        if total_learning >= 50 and not self._has_badge(user_id, '学习达人'):
            badges.append({
                'name': '学习达人',
                'type': 'milestone',
                'description': '完成50次学习',
                'icon': '🏆'
            })
        
        if total_learning >= 100 and not self._has_badge(user_id, '学习大师'):
            badges.append({
                'name': '学习大师',
                'type': 'milestone',
                'description': '完成100次学习',
                'icon': '👑'
            })
        
        if active_days >= 7 and not self._has_badge(user_id, '坚持一周'):
            badges.append({
                'name': '坚持一周',
                'type': 'streak',
                'description': '连续学习7天',
                'icon': '🔥'
            })
        
        if active_days >= 30 and not self._has_badge(user_id, '月度冠军'):
            badges.append({
                'name': '月度冠军',
                'type': 'streak',
                'description': '连续学习30天',
                'icon': '💯'
            })
        
        if avg_score >= 0.8 and not self._has_badge(user_id, '学霸'):
            badges.append({
                'name': '学霸',
                'type': 'achievement',
                'description': '平均置信度达到80%',
                'icon': '🎓'
            })
        
        for badge in badges:
            self._award_badge(user_id, badge)
    
    def _has_badge(self, user_id, badge_name):
        """检查用户是否已获得徽章"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM user_badges WHERE user_id = ? AND badge_name = ?
        ''', (user_id, badge_name))
        return self.cursor.fetchone()[0] > 0
    
    def _award_badge(self, user_id, badge):
        """奖励徽章"""
        self.cursor.execute('''
            INSERT INTO user_badges 
            (user_id, badge_name, badge_type, description, icon)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, badge['name'], badge['type'], badge['description'], badge['icon']))
    
    def get_user_stats(self, user_id):
        """获取用户激励统计"""
        self.cursor.execute('SELECT COALESCE(SUM(points), 0) FROM user_points WHERE user_id = ?', (user_id,))
        total_points = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT * FROM user_levels WHERE user_id = ?', (user_id,))
        level_data = self.cursor.fetchone()
        
        self.cursor.execute('SELECT * FROM user_badges WHERE user_id = ?', (user_id,))
        badges = [dict(row) for row in self.cursor.fetchall()]
        
        level_info = {
            'level': 1,
            'experience': 0,
            'next_level_exp': 100,
            'progress': 0
        }
        
        if level_data:
            level_info = {
                'level': level_data['level'],
                'experience': level_data['experience'],
                'next_level_exp': level_data['next_level_exp'],
                'progress': min(100, level_data['experience'] / level_data['next_level_exp'] * 100)
            }
        
        return {
            'user_id': user_id,
            'total_points': total_points,
            'level': level_info['level'],
            'experience': level_info['experience'],
            'next_level_exp': level_info['next_level_exp'],
            'level_progress': round(level_info['progress'], 2),
            'badges': badges,
            'badge_count': len(badges)
        }
    
    def get_leaderboard(self, limit=10):
        """获取排行榜"""
        self.cursor.execute('''
            SELECT ul.user_id, u.username, ul.level, ul.experience, COALESCE(SUM(up.points), 0) as total_points
            FROM user_levels ul
            LEFT JOIN users u ON ul.user_id = u.id
            LEFT JOIN user_points up ON ul.user_id = up.user_id
            GROUP BY ul.user_id
            ORDER BY ul.level DESC, ul.experience DESC, total_points DESC
            LIMIT ?
        ''', (limit,))
        
        leaderboard = []
        for i, row in enumerate(self.cursor.fetchall(), 1):
            leaderboard.append({
                'rank': i,
                'user_id': row['user_id'],
                'username': row['username'],
                'level': row['level'],
                'experience': row['experience'],
                'total_points': row['total_points']
            })
        
        return leaderboard
    
    def get_available_badges(self):
        """获取所有可用徽章"""
        return [
            {'name': '学习新手', 'type': 'milestone', 'description': '完成10次学习', 'icon': '⭐', 'requirement': '10次学习'},
            {'name': '学习达人', 'type': 'milestone', 'description': '完成50次学习', 'icon': '🏆', 'requirement': '50次学习'},
            {'name': '学习大师', 'type': 'milestone', 'description': '完成100次学习', 'icon': '👑', 'requirement': '100次学习'},
            {'name': '坚持一周', 'type': 'streak', 'description': '连续学习7天', 'icon': '🔥', 'requirement': '7天连续学习'},
            {'name': '月度冠军', 'type': 'streak', 'description': '连续学习30天', 'icon': '💯', 'requirement': '30天连续学习'},
            {'name': '学霸', 'type': 'achievement', 'description': '平均置信度达到80%', 'icon': '🎓', 'requirement': '置信度80%'}
        ]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    incentive = AILearningIncentive()
    
    logger.info("=== AI学习激励系统 ===")
    
    logger.info("\n=== 用户激励统计 ===")
    stats = incentive.get_user_stats(1)
    logger.info(f"用户ID: {stats['user_id']}")
    logger.info(f"总积分: {stats['total_points']}")
    logger.info(f"等级: {stats['level']}")
    logger.info(f"经验值: {stats['experience']}/{stats['next_level_exp']}")
    logger.info(f"升级进度: {stats['level_progress']}%")
    logger.info(f"徽章数量: {stats['badge_count']}")
    
    if stats['badges']:
        logger.info("\n获得的徽章:")
        for badge in stats['badges']:
            logger.info(f"  {badge['icon']} {badge['name']}: {badge['description']}")
    
    logger.info("\n=== 排行榜 ===")
    leaderboard = incentive.get_leaderboard(5)
    for item in leaderboard:
        logger.info(f"{item['rank']}. {item['username']}: Lv.{item['level']}, {item['experience']}经验,{item['total_points']}积分")
    
    logger.info("\n=== 可用徽章 ===")
    available = incentive.get_available_badges()
    for badge in available:
        logger.info(f"  {badge['icon']} {badge['name']}: {badge['requirement']}")
    
    incentive.award_points(1, 50, '每日登录奖励')
    logger.info("\n奖励50积分成功！")
    
    updated_stats = incentive.get_user_stats(1)
    logger.info(f"更新后积分: {updated_stats['total_points']}")
    
    incentive.close()