# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
听力题与音频文件智能匹配系统
根据题库题目动态匹配听力音频文件
"""

import os
import sys
import json
import sqlite3
import logging
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AudioMatcher')

class ListeningAudioMatcher:
    """听力音频匹配器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.audio_dir = self.base_path / "static" / "audio"
        self.db_path = self.base_path / "app.db"
        
        self.stats = {
            'total_questions': 0,
            'listening_questions': 0,
            'matched': 0,
            'unmatched': 0,
            'audio_files': 0
        }
        
        self.audio_files = []
        self.question_map = {}
    
    def scan_audio_files(self):
        """扫描所有音频文件"""
        logger.info("正在扫描音频文件...")
        
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        
        for ext in audio_extensions:
            for audio_file in self.audio_dir.rglob(f"*{ext}"):
                rel_path = audio_file.relative_to(self.base_path)
                
                audio_info = {
                    'path': str(rel_path),
                    'name': audio_file.name,
                    'stem': audio_file.stem,
                    'size': audio_file.stat().st_size,
                    'category': self._extract_category(str(rel_path)),
                    'level': self._extract_level(str(rel_path)),
                    'type': self._extract_type(str(rel_path)),
                    'number': self._extract_number(audio_file.stem)
                }
                
                self.audio_files.append(audio_info)
        
        self.stats['audio_files'] = len(self.audio_files)
        logger.info(f"扫描完成: 发现 {len(self.audio_files)} 个音频文件")
        
        return self.audio_files
    
    def _extract_category(self, path: str) -> str:
        """提取类别"""
        path_lower = path.lower()
        
        if 'japanese' in path_lower:
            return 'japanese'
        elif 'english' in path_lower or 'ielts' in path_lower or 'toefl' in path_lower:
            return 'english'
        elif 'chinese' in path_lower or 'mandarin' in path_lower:
            return 'chinese'
        else:
            return 'general'
    
    def _extract_level(self, path: str) -> str:
        """提取难度级别"""
        path_lower = path.lower()
        
        # 日语等级
        if 'n1' in path_lower or 'jlpt-n1' in path_lower:
            return 'n1'
        elif 'n2' in path_lower or 'jlpt-n2' in path_lower:
            return 'n2'
        elif 'n3' in path_lower or 'jlpt-n3' in path_lower:
            return 'n3'
        elif 'n4' in path_lower or 'jlpt-n4' in path_lower:
            return 'n4'
        elif 'n5' in path_lower or 'jlpt-n5' in path_lower:
            return 'n5'
        
        # 英语等级
        if 'advanced' in path_lower:
            return 'advanced'
        elif 'intermediate' in path_lower:
            return 'intermediate'
        elif 'basic' in path_lower:
            return 'basic'
        elif 'ielts' in path_lower:
            return 'ielts'
        elif 'toefl' in path_lower:
            return 'toefl'
        
        return 'general'
    
    def _extract_type(self, path: str) -> str:
        """提取类型"""
        path_lower = path.lower()
        
        if 'listening' in path_lower:
            return 'listening'
        elif 'speaking' in path_lower:
            return 'speaking'
        elif 'reading' in path_lower:
            return 'reading'
        elif 'vocabulary' in path_lower:
            return 'vocabulary'
        
        return 'listening'
    
    def _extract_number(self, stem: str) -> str:
        """提取编号"""
        numbers = re.findall(r'\d+', stem)
        return numbers[-1] if numbers else ''
    
    def load_questions_from_db(self):
        """从数据库加载听力题目"""
        logger.info("正在加载数据库题目...")
        
        if not self.db_path.exists():
            logger.error(f"数据库不存在: {self.db_path}")
            return {}
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 尝试不同的表名
        table_names = ['questions', 'listening_questions', 'exam_questions', 'question_bank']
        
        questions = {}
        
        for table_name in table_names:
            try:
                # 获取表结构
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                columns = [desc[0] for desc in cursor.description]
                
                # 查找相关列
                id_col = None
                content_col = None
                subject_col = None
                grade_col = None
                audio_col = None
                
                for col in columns:
                    col_lower = col.lower()
                    if 'id' in col_lower and not id_col:
                        id_col = col
                    elif 'question' in col_lower or 'content' in col_lower or 'text' in col_lower:
                        if not content_col:
                            content_col = col
                    elif 'subject' in col_lower or 'type' in col_lower:
                        if not subject_col:
                            subject_col = col
                    elif 'grade' in col_lower or 'level' in col_lower:
                        if not grade_col:
                            grade_col = col
                    elif 'audio' in col_lower or 'audio_path' in col_lower or 'sound' in col_lower:
                        if not audio_col:
                            audio_col = col
                
                if not id_col or not content_col:
                    continue
                
                # 查询所有题目
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    
                    content = str(row_dict.get(content_col, ''))
                    question_id = str(row_dict.get(id_col, ''))
                    
                    # 判断是否为听力题
                    subject = str(row_dict.get(subject_col, '')).lower()
                    grade = str(row_dict.get(grade_col, '')).lower()
                    
                    is_listening = (
                        '听力' in content or
                        'listening' in subject or
                        'listening' in grade or
                        '日语听力' in content or
                        '英语听力' in content
                    )
                    
                    if is_listening:
                        question_info = {
                            'id': question_id,
                            'content': content,
                            'subject': subject,
                            'grade': grade,
                            'table': table_name,
                            'audio_path': row_dict.get(audio_col, ''),
                            'matched': bool(row_dict.get(audio_col))
                        }
                        
                        key = self._generate_key(content)
                        self.question_map[key] = question_info
                        
                        self.stats['listening_questions'] += 1
                
                self.stats['total_questions'] += len(rows)
                logger.info(f"表 {table_name}: 发现 {len(rows)} 条题目")
                
            except sqlite3.OperationalError:
                continue
        
        conn.close()
        
        logger.info(f"加载完成: 共 {self.stats['total_questions']} 题, 其中听力题 {self.stats['listening_questions']} 题")
        
        return self.question_map
    
    def _generate_key(self, content: str) -> str:
        """生成匹配键"""
        # 清理文本
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', content)
        text = text.lower()[:50]
        
        # 提取关键词
        keywords = re.findall(r'[\u4e00-\u9fff]+', content)
        
        return ' '.join(keywords[:5]) if keywords else text
    
    def match_audio_to_questions(self):
        """智能匹配音频到题目"""
        logger.info("开始智能匹配...")
        
        matched_pairs = []
        unmatched_questions = []
        
        for key, question in self.question_map.items():
            best_match = None
            best_score = 0
            
            content = question['content']
            subject = question['subject']
            grade = question['grade']
            
            # 提取关键词
            keywords = set(re.findall(r'[\u4e00-\u9fff]+', content))
            
            for audio in self.audio_files:
                score = 0
                
                # 类别匹配
                if 'japanese' in subject or '日语' in content:
                    if audio['category'] == 'japanese':
                        score += 30
                elif 'english' in subject or '英语' in content:
                    if audio['category'] == 'english':
                        score += 30
                
                # 级别匹配
                for kw in keywords:
                    if kw in audio['path'].lower():
                        score += 10
                
                # 编号匹配
                question_numbers = re.findall(r'\d+', content)
                for num in question_numbers:
                    if num == audio['number']:
                        score += 20
                
                # 难度匹配
                if audio['level'] in grade.lower():
                    score += 15
                
                if score > best_score and score >= 30:
                    best_score = score
                    best_match = audio
            
            if best_match:
                matched_pairs.append({
                    'question_id': question['id'],
                    'question_content': content[:100],
                    'audio_path': best_match['path'],
                    'audio_name': best_match['name'],
                    'match_score': best_score,
                    'table': question['table']
                })
                self.stats['matched'] += 1
            else:
                unmatched_questions.append({
                    'question_id': question['id'],
                    'question_content': content[:100],
                    'subject': subject,
                    'grade': grade,
                    'table': question['table']
                })
                self.stats['unmatched'] += 1
        
        logger.info(f"匹配完成: 成功匹配 {self.stats['matched']} 题, 未匹配 {self.stats['unmatched']} 题")
        
        return matched_pairs, unmatched_questions
    
    def update_database(self, matched_pairs: list):
        """更新数据库中的音频路径"""
        logger.info("正在更新数据库...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        updated_count = 0
        
        for pair in matched_pairs:
            table = pair['table']
            question_id = pair['question_id']
            audio_path = pair['audio_path']
            
            try:
                # 查找并更新音频路径列
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                # 查找音频路径列
                audio_col = None
                for col in columns:
                    if 'audio' in col.lower():
                        audio_col = col
                        break
                
                if audio_col:
                    cursor.execute(
                        f"UPDATE {table} SET {audio_col} = ? WHERE {columns[0]} = ?",
                        (audio_path, question_id)
                    )
                    updated_count += 1
                
            except Exception as e:
                logger.error(f"更新失败 {question_id}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"数据库更新完成: 更新了 {updated_count} 条记录")
        
        return updated_count
    
    def generate_report(self, matched_pairs: list, unmatched_questions: list) -> dict:
        """生成匹配报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats.copy(),
            'matched_pairs': [
                {
                    'question_id': p['question_id'],
                    'question_preview': p['question_content'],
                    'audio_path': p['audio_path'],
                    'match_score': p['match_score']
                }
                for p in matched_pairs[:100]  # 只保留前100条
            ],
            'unmatched_questions': [
                {
                    'question_id': q['question_id'],
                    'question_preview': q['question_content'],
                    'subject': q['subject']
                }
                for q in unmatched_questions[:50]  # 只保留前50条
            ],
            'audio_categories': self._count_by_category(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _count_by_category(self) -> dict:
        """按类别统计音频"""
        categories = defaultdict(int)
        for audio in self.audio_files:
            categories[f"{audio['category']}_{audio['level']}"] += 1
        return dict(categories)
    
    def _generate_recommendations(self) -> list:
        """生成建议"""
        recommendations = []
        
        if self.stats['unmatched'] > 0:
            recommendations.append({
                'type': 'warning',
                'message': f"有 {self.stats['unmatched']} 个听力题未匹配到音频，建议检查音频文件命名"
            })
        
        if not self.audio_files:
            recommendations.append({
                'type': 'error',
                'message': "未找到任何音频文件，请确认音频目录存在"
            })
        
        unmatched_categories = defaultdict(int)
        for q in self.question_map.values():
            if not q.get('matched'):
                unmatched_categories[q.get('subject', 'unknown')] += 1
        
        if unmatched_categories:
            recommendations.append({
                'type': 'info',
                'message': f"未匹配题目分布: {dict(unmatched_categories)}"
            })
        
        return recommendations
    
    def run(self):
        """运行匹配流程"""
        print("\n" + "=" * 70)
        print("听力题与音频文件智能匹配系统")
        print("=" * 70 + "\n")
        
        # 1. 扫描音频文件
        self.scan_audio_files()
        
        # 2. 加载题目
        self.load_questions_from_db()
        
        # 3. 智能匹配
        matched_pairs, unmatched_questions = self.match_audio_to_questions()
        
        # 4. 更新数据库
        if matched_pairs:
            self.update_database(matched_pairs)
        
        # 5. 生成报告
        report = self.generate_report(matched_pairs, unmatched_questions)
        
        print("\n📊 匹配统计:")
        print(f"   总音频文件: {self.stats['audio_files']}")
        print(f"   总题目数: {self.stats['total_questions']}")
        print(f"   听力题数: {self.stats['listening_questions']}")
        print(f"   成功匹配: {self.stats['matched']}")
        print(f"   未匹配: {self.stats['unmatched']}")
        
        print("\n📂 音频分布:")
        for cat, count in report['audio_categories'].items():
            print(f"   {cat}: {count} 个")
        
        if report['recommendations']:
            print("\n💡 建议:")
            for rec in report['recommendations']:
                icon = "⚠️" if rec['type'] == 'warning' else "❌" if rec['type'] == 'error' else "ℹ️"
                print(f"   {icon} {rec['message']}")
        
        # 保存报告
        report_file = self.base_path / "audio_matching_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_file}")
        print("\n" + "=" * 70)
        
        return report


def main():
    """主函数"""
    base_path = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
    
    matcher = ListeningAudioMatcher(base_path)
    report = matcher.run()
    
    return report


if __name__ == "__main__":
    main()