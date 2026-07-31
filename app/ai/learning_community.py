#!/usr/bin/env python3
import sqlite3
import json
import os
from datetime import datetime
from uuid import uuid4

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AILearningCommunity:
    """AI学习社区系统 - 社交学习平台"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """创建社区相关表"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_posts (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                post_type TEXT DEFAULT 'discussion',
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_comments (
                id TEXT PRIMARY KEY,
                post_id TEXT,
                user_id INTEGER,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id TEXT,
                comment_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, post_id, comment_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER,
                following_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(follower_id, following_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_tags (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def create_post(self, user_id, title, content, post_type='discussion', tags=None):
        """创建帖子"""
        post_id = str(uuid4())
        tags_str = json.dumps(tags or [])
        
        self.cursor.execute('''
            INSERT INTO community_posts 
            (id, user_id, title, content, post_type, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (post_id, user_id, title, content, post_type, tags_str))
        
        if tags:
            for tag in tags:
                self._add_tag(tag)
        
        self.conn.commit()
        return post_id
    
    def _add_tag(self, tag_name):
        """添加标签"""
        self.cursor.execute('''
            INSERT OR IGNORE INTO community_tags (id, name)
            VALUES (?, ?)
        ''', (str(uuid4()), tag_name))
        
        self.cursor.execute('''
            UPDATE community_tags 
            SET count = count + 1 
            WHERE name = ?
        ''', (tag_name,))
    
    def get_posts(self, page=1, page_size=10, post_type=None, tag=None):
        """获取帖子列表"""
        offset = (page - 1) * page_size
        query = '''
            SELECT cp.*, u.username 
            FROM community_posts cp
            JOIN users u ON cp.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if post_type:
            query += ' AND cp.post_type = ?'
            params.append(post_type)
        
        if tag:
            query += ' AND cp.tags LIKE ?'
            params.append(f'%{tag}%')
        
        query += ' ORDER BY cp.created_at DESC LIMIT ? OFFSET ?'
        params.extend([page_size, offset])
        
        self.cursor.execute(query, params)
        posts = [dict(row) for row in self.cursor.fetchall()]
        
        for post in posts:
            post['tags'] = json.loads(post['tags']) if post['tags'] else []
        
        return posts
    
    def get_post_detail(self, post_id):
        """获取帖子详情"""
        self.cursor.execute('''
            SELECT cp.*, u.username 
            FROM community_posts cp
            JOIN users u ON cp.user_id = u.id
            WHERE cp.id = ?
        ''', (post_id,))
        
        post = self.cursor.fetchone()
        if not post:
            return None
        
        post_dict = dict(post)
        post_dict['tags'] = json.loads(post_dict['tags']) if post_dict['tags'] else []
        
        self.cursor.execute('''
            SELECT cc.*, u.username 
            FROM community_comments cc
            JOIN users u ON cc.user_id = u.id
            WHERE cc.post_id = ?
            ORDER BY cc.created_at DESC
        ''', (post_id,))
        
        comments = [dict(row) for row in self.cursor.fetchall()]
        post_dict['comments'] = comments
        
        return post_dict
    
    def add_comment(self, post_id, user_id, content):
        """添加评论"""
        comment_id = str(uuid4())
        
        self.cursor.execute('''
            INSERT INTO community_comments (id, post_id, user_id, content)
            VALUES (?, ?, ?, ?)
        ''', (comment_id, post_id, user_id, content))
        
        self.cursor.execute('''
            UPDATE community_posts 
            SET comments = comments + 1 
            WHERE id = ?
        ''', (post_id,))
        
        self.conn.commit()
        return comment_id
    
    def like_post(self, user_id, post_id):
        """点赞帖子"""
        try:
            self.cursor.execute('''
                INSERT INTO community_likes (user_id, post_id)
                VALUES (?, ?)
            ''', (user_id, post_id))
            
            self.cursor.execute('''
                UPDATE community_posts 
                SET likes = likes + 1 
                WHERE id = ?
            ''', (post_id,))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def like_comment(self, user_id, comment_id):
        """点赞评论"""
        try:
            self.cursor.execute('''
                INSERT INTO community_likes (user_id, comment_id)
                VALUES (?, ?)
            ''', (user_id, comment_id))
            
            self.cursor.execute('''
                UPDATE community_comments 
                SET likes = likes + 1 
                WHERE id = ?
            ''', (comment_id,))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def follow_user(self, follower_id, following_id):
        """关注用户"""
        try:
            self.cursor.execute('''
                INSERT INTO community_follows (follower_id, following_id)
                VALUES (?, ?)
            ''', (follower_id, following_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def unfollow_user(self, follower_id, following_id):
        """取消关注"""
        self.cursor.execute('''
            DELETE FROM community_follows 
            WHERE follower_id = ? AND following_id = ?
        ''', (follower_id, following_id))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_following(self, user_id):
        """获取关注列表"""
        self.cursor.execute('''
            SELECT u.id, u.username 
            FROM community_follows cf
            JOIN users u ON cf.following_id = u.id
            WHERE cf.follower_id = ?
        ''', (user_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_followers(self, user_id):
        """获取粉丝列表"""
        self.cursor.execute('''
            SELECT u.id, u.username 
            FROM community_follows cf
            JOIN users u ON cf.follower_id = u.id
            WHERE cf.following_id = ?
        ''', (user_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_popular_tags(self, limit=10):
        """获取热门标签"""
        self.cursor.execute('''
            SELECT * FROM community_tags 
            ORDER BY count DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_user_posts(self, user_id, page=1, page_size=10):
        """获取用户帖子"""
        offset = (page - 1) * page_size
        
        self.cursor.execute('''
            SELECT cp.*, u.username 
            FROM community_posts cp
            JOIN users u ON cp.user_id = u.id
            WHERE cp.user_id = ?
            ORDER BY cp.created_at DESC LIMIT ? OFFSET ?
        ''', (user_id, page_size, offset))
        
        posts = [dict(row) for row in self.cursor.fetchall()]
        for post in posts:
            post['tags'] = json.loads(post['tags']) if post['tags'] else []
        
        return posts
    
    def delete_post(self, post_id):
        """删除帖子"""
        self.cursor.execute('DELETE FROM community_comments WHERE post_id = ?', (post_id,))
        self.cursor.execute('DELETE FROM community_likes WHERE post_id = ?', (post_id,))
        self.cursor.execute('DELETE FROM community_posts WHERE id = ?', (post_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def search_posts(self, keyword, page=1, page_size=10):
        """搜索帖子"""
        offset = (page - 1) * page_size
        
        self.cursor.execute('''
            SELECT cp.*, u.username 
            FROM community_posts cp
            JOIN users u ON cp.user_id = u.id
            WHERE cp.title LIKE ? OR cp.content LIKE ?
            ORDER BY cp.created_at DESC LIMIT ? OFFSET ?
        ''', (f'%{keyword}%', f'%{keyword}%', page_size, offset))
        
        posts = [dict(row) for row in self.cursor.fetchall()]
        for post in posts:
            post['tags'] = json.loads(post['tags']) if post['tags'] else []
        
        return posts
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    community = AILearningCommunity()
    
    logger.info("=== AI学习社区系统 ===")
    
    logger.info("\n=== 创建测试帖子 ===")
    post_id = community.create_post(
        user_id=1,
        title='Python机器学习入门指南',
        content='分享一个Python机器学习入门的学习路径，包括基础语法、数据分析、机器学习算法等内容。',
        post_type='resource',
        tags=['Python', '机器学习', '入门']
    )
    logger.info(f"创建帖子成功: {post_id}")
    
    logger.info("\n=== 获取帖子列表 ===")
    posts = community.get_posts(page=1, page_size=5)
    logger.info(f"帖子总数: {len(posts)}")
    for post in posts:
        logger.info(f"  {post['title']} - {post['username']} - {post['likes']}赞")
    
    logger.info("\n=== 获取帖子详情 ===")
    detail = community.get_post_detail(post_id)
    if detail:
        logger.info(f"标题: {detail['title']}")
        logger.info(f"作者: {detail['username']}")
        logger.info(f"标签: {detail['tags']}")
        logger.info(f"评论数: {detail['comments']}")
    
    logger.info("\n=== 添加评论 ===")
    comment_id = community.add_comment(post_id, 2, '很棒的分享！')
    logger.info(f"添加评论成功: {comment_id}")
    
    logger.info("\n=== 点赞帖子 ===")
    result = community.like_post(2, post_id)
    logger.info(f"点赞成功: {result}")
    
    logger.info("\n=== 关注用户 ===")
    result = community.follow_user(2, 1)
    logger.info(f"关注成功: {result}")
    
    logger.info("\n=== 获取热门标签 ===")
    tags = community.get_popular_tags()
    for tag in tags:
        logger.info(f"  {tag['name']}: {tag['count']}篇")
    
    logger.info("\n=== 搜索帖子 ===")
    results = community.search_posts('Python')
    logger.info(f"搜索结果: {len(results)}篇")
    
    community.close()