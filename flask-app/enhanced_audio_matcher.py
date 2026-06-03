# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版听力题与音频匹配系统
基于内容相似度的智能匹配
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
from difflib import SequenceMatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EnhancedAudioMatcher')

class EnhancedAudioMatcher:
    """增强版音频匹配器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.audio_dir = self.base_path / "static" / "audio"
        self.db_path = self.base_path / "app.db"
        
        self.stats = {
            'total_audio': 0,
            'total_questions': 0,
            'listening_questions': 0,
            'matched': 0,
            'updated': 0
        }
        
        self.audio_files = []
        self.questions = []
    
    def scan_audio_files(self):
        """扫描音频文件"""
        logger.info("扫描音频文件...")
        
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        
        for ext in audio_extensions:
            for audio_file in self.audio_dir.rglob(f"*{ext}"):
                rel_path = audio_file.relative_to(self.base_path)
                
                info = {
                    'path': str(rel_path),
                    'name': audio_file.name,
                    'stem': audio_file.stem,
                    'size': audio_file.stat().st_size,
                    'number': self._extract_number(audio_file.stem),
                    'level': self._extract_level(str(rel_path)),
                    'category': self._extract_category(str(rel_path))
                }
                
                self.audio_files.append(info)
        
        self.stats['total_audio'] = len(self.audio_files)
        logger.info(f"发现 {len(self.audio_files)} 个音频文件")
        
        return self.audio_files
    
    def _extract_number(self, stem: str) -> int:
        """提取编号"""
        numbers = re.findall(r'\d+', stem)
        return int(numbers[-1]) if numbers else 0
    
    def _extract_level(self, path: str) -> str:
        """提取级别"""
        path_lower = path.lower()
        
        levels = ['n1', 'n2', 'n3', 'n4', 'n5', 'advanced', 'intermediate', 'basic', 
                  'ielts', 'toefl', 'beginner', 'elementary']
        
        for level in levels:
            if level in path_lower:
                return level
        
        return 'general'
    
    def _extract_category(self, path: str) -> str:
        """提取类别"""
        path_lower = path.lower()
        
        if 'japanese' in path_lower:
            return 'japanese'
        elif 'english' in path_lower:
            return 'english'
        elif 'chinese' in path_lower:
            return 'chinese'
        return 'general'
    
    def load_questions(self):
        """加载题目"""
        logger.info("加载数据库题目...")
        
        if not self.db_path.exists():
            logger.error("数据库不存在")
            return []
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        tables = ['questions', 'exam_questions', 'question_bank', 'listening_questions']
        
        all_questions = []
        
        for table in tables:
            try:
                # 获取所有列
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                if not columns:
                    continue
                
                # 查询所有记录
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                id_col = columns[0]
                content_col = self._find_column(columns, ['question', 'content', 'text'])
                subject_col = self._find_column(columns, ['subject', 'type'])
                grade_col = self._find_column(columns, ['grade', 'level'])
                audio_col = self._find_column(columns, ['audio', 'sound', 'audio_path'])
                
                for row in rows:
                    row_dict = dict(row)
                    content = str(row_dict.get(content_col, ''))
                    subject = str(row_dict.get(subject_col, '')).lower()
                    grade = str(row_dict.get(grade_col, '')).lower()
                    
                    # 判断是否为听力题
                    is_listening = (
                        '听力' in content or
                        'listening' in subject or
                        'listening' in grade or
                        '日语' in content or
                        '英语' in content or
                        '日本語' in content
                    )
                    
                    if is_listening:
                        question = {
                            'id': row_dict.get(id_col),
                            'content': content,
                            'subject': subject,
                            'grade': grade,
                            'table': table,
                            'audio_path': row_dict.get(audio_col, ''),
                            'columns': columns
                        }
                        
                        # 提取题目编号
                        numbers = re.findall(r'\d+', content[:100])
                        question['number'] = int(numbers[0]) if numbers else 0
                        
                        all_questions.append(question)
                
                logger.info(f"表 {table}: {len(rows)} 条记录")
                
            except sqlite3.OperationalError:
                continue
        
        conn.close()
        
        self.questions = all_questions
        self.stats['total_questions'] = len(all_questions)
        self.stats['listening_questions'] = len(all_questions)
        
        logger.info(f"加载完成: {len(all_questions)} 个听力题")
        
        return all_questions
    
    def _find_column(self, columns: list, keywords: list) -> str:
        """查找匹配的列"""
        for col in columns:
            col_lower = col.lower()
            for kw in keywords:
                if kw in col_lower:
                    return col
        return columns[0] if columns else None
    
    def smart_match(self):
        """智能匹配"""
        logger.info("开始智能匹配...")
        
        matched = []
        unmatched = []
        
        for question in self.questions:
            match_result = self._find_best_match(question)
            
            if match_result:
                matched.append({
                    'question': question,
                    'audio': match_result['audio'],
                    'score': match_result['score']
                })
                self.stats['matched'] += 1
            else:
                unmatched.append(question)
        
        logger.info(f"匹配完成: {self.stats['matched']} 个成功, {len(unmatched)} 个未匹配")
        
        return matched, unmatched
    
    def _find_best_match(self, question: dict) -> dict:
        """查找最佳匹配"""
        best_match = None
        best_score = 0
        
        content = question['content']
        number = question['number']
        subject = question['subject']
        grade = question['grade']
        
        # 提取关键词
        keywords = self._extract_keywords(content)
        
        for audio in self.audio_files:
            score = 0
            
            # 1. 编号匹配 (最高优先级)
            if number > 0 and audio['number'] == number:
                score += 50
            
            # 2. 级别匹配
            audio_level = audio['level']
            if audio_level in grade or grade in audio_level:
                score += 30
            
            # 3. 类别匹配
            if 'japanese' in subject or '日语' in content:
                if audio['category'] == 'japanese':
                    score += 20
            elif 'english' in subject or '英语' in content:
                if audio['category'] == 'english':
                    score += 20
            
            # 4. 关键词匹配
            for kw in keywords[:5]:
                if kw.lower() in audio['path'].lower():
                    score += 10
            
            # 5. 内容相似度匹配
            similarity = self._calculate_similarity(content, audio['stem'])
            score += similarity * 20
            
            if score > best_score and score >= 25:
                best_score = score
                best_match = audio
        
        if best_match:
            return {'audio': best_match, 'score': best_score}
        return None
    
    def _extract_keywords(self, content: str) -> list:
        """提取关键词"""
        # 中文关键词
        chinese_kw = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        
        # 英文关键词
        english_kw = re.findall(r'[a-zA-Z]{3,}', content)
        
        # 数字
        numbers = re.findall(r'\d+', content[:200])
        
        return chinese_kw[:5] + english_kw[:5] + numbers
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算相似度"""
        text1_clean = re.sub(r'[^\w]', '', text1.lower()[:100])
        text2_clean = re.sub(r'[^\w]', '', text2.lower())
        
        return SequenceMatcher(None, text1_clean, text2_clean).ratio()
    
    def update_database(self, matched: list):
        """更新数据库"""
        logger.info("更新数据库...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        updated = 0
        
        # 按表分组
        by_table = defaultdict(list)
        for item in matched:
            q = item['question']
            by_table[q['table']].append(item)
        
        for table, items in by_table.items():
            try:
                # 查找音频列
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                audio_col = None
                id_col = columns[0]
                
                for col in columns:
                    if 'audio' in col.lower():
                        audio_col = col
                        break
                
                if not audio_col:
                    # 尝试添加列
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN audio_path TEXT")
                        audio_col = 'audio_path'
                        logger.info(f"表 {table} 添加了 audio_path 列")
                    except Exception:
                        continue
                
                # 更新记录
                for item in items:
                    q = item['question']
                    audio = item['audio']
                    
                    try:
                        cursor.execute(
                            f"UPDATE {table} SET {audio_col} = ? WHERE {id_col} = ?",
                            (audio['path'], q['id'])
                        )
                        updated += 1
                    except Exception as e:
                        logger.debug(f"更新失败: {str(e)}")
                
            except Exception as e:
                logger.error(f"表 {table} 更新失败: {str(e)}")
        
        conn.commit()
        conn.close()
        
        self.stats['updated'] = updated
        logger.info(f"数据库更新完成: {updated} 条记录")
        
        return updated
    
    def generate_report(self, matched: list, unmatched: list) -> dict:
        """生成报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats.copy(),
            'matched_samples': [
                {
                    'question_id': str(m['question']['id']),
                    'question_preview': m['question']['content'][:80],
                    'audio_path': m['audio']['path'],
                    'match_score': round(m['score'], 2)
                }
                for m in matched[:50]
            ],
            'audio_distribution': self._count_audio_distribution(),
            'recommendations': self._generate_recommendations(matched, unmatched)
        }
        
        return report
    
    def _count_audio_distribution(self) -> dict:
        """统计音频分布"""
        dist = defaultdict(int)
        for audio in self.audio_files:
            key = f"{audio['category']}/{audio['level']}"
            dist[key] += 1
        return dict(dist)
    
    def _generate_recommendations(self, matched: list, unmatched: list) -> list:
        """生成建议"""
        recs = []
        
        match_rate = (self.stats['matched'] / max(self.stats['listening_questions'], 1)) * 100
        
        if match_rate > 80:
            recs.append({'type': 'success', 'message': f'匹配率: {match_rate:.1f}%, 匹配效果良好'})
        elif match_rate > 50:
            recs.append({'type': 'warning', 'message': f'匹配率: {match_rate:.1f}%, 建议优化匹配规则'})
        else:
            recs.append({'type': 'error', 'message': f'匹配率: {match_rate:.1f}%, 需要检查音频和题目的命名规范'})
        
        if unmatched:
            recs.append({
                'type': 'info',
                'message': f'有 {len(unmatched)} 个题目未能匹配, 可能需要补充音频文件或调整题目格式'
            })
        
        return recs
    
    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 70)
        print("增强版听力题与音频智能匹配系统")
        print("=" * 70 + "\n")
        
        # 1. 扫描音频
        self.scan_audio_files()
        
        # 2. 加载题目
        self.load_questions()
        
        # 3. 智能匹配
        matched, unmatched = self.smart_match()
        
        # 4. 更新数据库
        if matched:
            self.update_database(matched)
        
        # 5. 生成报告
        report = self.generate_report(matched, unmatched)
        
        print("\n📊 匹配统计:")
        print(f"   音频文件: {self.stats['total_audio']} 个")
        print(f"   听力题目: {self.stats['listening_questions']} 个")
        print(f"   成功匹配: {self.stats['matched']} 个")
        print(f"   数据库更新: {self.stats['updated']} 条")
        
        print("\n📂 音频分布:")
        for cat, count in report['audio_distribution'].items():
            print(f"   {cat}: {count} 个")
        
        if matched:
            print("\n🎧 匹配示例 (前5个):")
            for m in report['matched_samples'][:5]:
                print(f"   题号: {m['question_id']}")
                print(f"   题目: {m['question_preview']}...")
                print(f"   音频: {m['audio_path']}")
                print(f"   匹配度: {m['match_score']}%")
                print()
        
        print("\n💡 建议:")
        for rec in report['recommendations']:
            icon = "✅" if rec['type'] == 'success' else "⚠️" if rec['type'] == 'warning' else "❌"
            print(f"   {icon} {rec['message']}")
        
        # 保存报告
        report_file = self.base_path / "enhanced_audio_matching_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_file}")
        print("\n" + "=" * 70)
        
        return report


def main():
    """主函数"""
    base_path = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
    
    matcher = EnhancedAudioMatcher(base_path)
    report = matcher.run()
    
    return report


if __name__ == "__main__":
    main()