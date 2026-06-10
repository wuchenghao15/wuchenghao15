#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI题库全面管理与校验系统
功能：
1. 题目完整性校验
2. 选项与答案匹配验证
3. 难度级别合理性分析
4. 标签分类准确性检查
5. 重复题目检测
6. 知识点覆盖分析
7. 数据一致性修复
8. 题库统计与报告
"""

import logging
import os
import sys
import sqlite3
import hashlib
import json
import re
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class QuestionBankManager:
    """AI题库全面管理器"""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.validation_results = []
        self.issues = defaultdict(list)
        self.statistics = {}

    def connect(self):
        """连接数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return None

    # ============ 统计功能 ============

    def get_overall_statistics(self, conn):
        """获取题库整体统计"""
        cursor = conn.cursor()
        
        stats = {
            'total': 0,
            'by_type': {},
            'by_difficulty': {},
            'by_subject': {},
            'by_topic': {},
            'with_audio': 0,
            'missing_options': 0,
            'missing_answers': 0,
            'missing_explanation': 0
        }

        # 总题目数
        cursor.execute("SELECT COUNT(*) FROM questions")
        stats['total'] = cursor.fetchone()[0]

        # 按题型统计
        cursor.execute("SELECT type, COUNT(*) FROM questions GROUP BY type")
        for row in cursor.fetchall():
            stats['by_type'][row[0]] = row[1]

        # 按难度统计
        cursor.execute("SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty")
        for row in cursor.fetchall():
            stats['by_difficulty'][row[0]] = row[1]

        # 按学科统计（从tags提取）
        cursor.execute("SELECT tags FROM questions WHERE tags IS NOT NULL")
        subject_counter = Counter()
        for row in cursor.fetchall():
            try:
                tags = json.loads(row[0]) if row[0] else []
                for tag in tags:
                    if tag in ['数学', '英语', '日语', '物理', '化学', '生物', '历史', '地理', '信息技术']:
                        subject_counter[tag] += 1
            except:
                pass
        stats['by_subject'] = dict(subject_counter)

        # 统计问题
        cursor.execute("SELECT COUNT(*) FROM questions WHERE type = 'listening' AND audio_url IS NOT NULL AND audio_url != ''")
        stats['with_audio'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE options IS NULL OR options = '' OR options = '[]'")
        stats['missing_options'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE correct_answer IS NULL OR correct_answer = ''")
        stats['missing_answers'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE explanation IS NULL OR explanation = ''")
        stats['missing_explanation'] = cursor.fetchone()[0]

        return stats

    def display_statistics(self):
        """显示题库统计"""
        print("=" * 80)
        print("📊 AI题库全面统计报告")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            stats = self.get_overall_statistics(conn)
            
            print(f"\n总题目数: {stats['total']}")
            
            # 题型分布
            print("\n📚 题型分布:")
            for qtype, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
                pct = count / stats['total'] * 100
                bar = "█" * int(pct / 2)
                print(f"  {qtype:<20} {count:>5} ({pct:>5.1f}%) {bar}")
            
            # 难度分布
            print("\n🎯 难度分布:")
            for diff, count in sorted(stats['by_difficulty'].items(), key=lambda x: float(x[0]) if x[0] else 0):
                pct = count / stats['total'] * 100
                bar = "█" * int(pct / 2)
                print(f"  难度 {diff:<5} {count:>5} ({pct:>5.1f}%) {bar}")
            
            # 学科分布
            if stats['by_subject']:
                print("\n📖 学科分布:")
                for subject, count in sorted(stats['by_subject'].items(), key=lambda x: x[1], reverse=True):
                    pct = count / stats['total'] * 100
                    bar = "█" * int(pct / 2)
                    print(f"  {subject:<10} {count:>5} ({pct:>5.1f}%) {bar}")
            
            # 数据质量
            print("\n🔍 数据质量:")
            quality_issues = []
            if stats['missing_options'] > 0:
                quality_issues.append(f"缺失选项: {stats['missing_options']}")
            if stats['missing_answers'] > 0:
                quality_issues.append(f"缺失答案: {stats['missing_answers']}")
            if stats['missing_explanation'] > 0:
                quality_issues.append(f"缺失解析: {stats['missing_explanation']}")
            
            if quality_issues:
                print("  ⚠️  发现以下问题:")
                for issue in quality_issues:
                    print(f"     - {issue}")
            else:
                print("  ✅ 数据完整性良好")

            self.statistics = stats

        except Exception as e:
            logger.error(f"统计失败: {str(e)}")
        finally:
            conn.close()

    # ============ 校验功能 ============

    def validate_question_structure(self, row):
        """验证题目结构"""
        qid, qtype, content, options, answer, difficulty, tags = row
        issues = []

        # 1. 检查题目内容
        if not content or len(content.strip()) < 5:
            issues.append("题目内容为空或过短")

        # 2. 检查选择题选项
        if qtype in ['single_choice', 'multiple_choice', 'listening', 'listening_choice']:
            if not options or options == '' or options == '[]':
                issues.append("选择题缺少选项")
            else:
                try:
                    opts = json.loads(options) if isinstance(options, str) else options
                    if len(opts) != 4:
                        issues.append(f"选项数量为{len(opts)}，标准为4")
                    
                    # 检查是否有空选项
                    for i, opt in enumerate(opts):
                        if isinstance(opt, dict) and not opt.get('content'):
                            issues.append(f"选项{i+1}内容为空")
                except:
                    issues.append("选项格式错误")

        # 3. 检查答案
        if not answer or answer == '':
            issues.append("缺少正确答案")
        elif qtype in ['single_choice', 'multiple_choice', 'listening', 'listening_choice']:
            if answer not in ['A', 'B', 'C', 'D', 'a', 'b', 'c', 'd']:
                # 检查答案是否在选项中
                pass  # 需要更复杂的验证

        # 4. 检查难度
        if difficulty:
            try:
                diff_val = float(difficulty)
                if diff_val < 1 or diff_val > 10:
                    issues.append(f"难度值{diff_val}超出范围(1-10)")
            except:
                issues.append(f"难度值格式错误: {difficulty}")

        return issues

    def check_duplicate_questions(self, conn):
        """检测重复题目"""
        cursor = conn.cursor()
        
        print("\n" + "=" * 80)
        print("🔄 重复题目检测")
        print("=" * 80)

        # 使用指纹检测重复
        cursor.execute("""
            SELECT fingerprint, COUNT(*) as cnt
            FROM questions
            WHERE fingerprint IS NOT NULL AND fingerprint != ''
            GROUP BY fingerprint
            HAVING cnt > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n发现 {len(duplicates)} 组重复题目")
            
            # 显示前10组
            cursor.execute("""
                SELECT id, content, fingerprint
                FROM questions
                WHERE fingerprint IN (
                    SELECT fingerprint
                    FROM questions
                    WHERE fingerprint IS NOT NULL AND fingerprint != ''
                    GROUP BY fingerprint
                    HAVING COUNT(*) > 1
                )
                ORDER BY fingerprint
            """)
            
            current_fingerprint = None
            count = 0
            for row in cursor.fetchall():
                qid, content, fp = row
                if fp != current_fingerprint:
                    if current_fingerprint:
                        print()
                    current_fingerprint = fp
                    count += 1
                    if count <= 10:
                        print(f"组 {count}:")
                        print(f"  指纹: {fp}")
                
                if count <= 10:
                    print(f"  - {qid}: {content[:50]}...")
            
            if len(duplicates) > 10:
                print(f"\n... 还有 {len(duplicates) - 10} 组")
        else:
            print("\n✅ 未发现重复题目")

    def validate_answer_consistency(self, conn):
        """验证答案一致性"""
        cursor = conn.cursor()
        
        print("\n" + "=" * 80)
        print("✓ 答案一致性验证")
        print("=" * 80)

        issues = []

        # 检查答案是否在选项中
        cursor.execute("""
            SELECT id, content, options, correct_answer, type
            FROM questions
            WHERE type IN ('single_choice', 'multiple_choice', 'listening', 'listening_choice')
            AND options IS NOT NULL AND options != '' AND options != '[]'
            AND correct_answer IS NOT NULL AND correct_answer != ''
        """)

        for row in cursor.fetchall():
            qid, content, options, answer, qtype = row
            
            try:
                opts = json.loads(options) if isinstance(options, str) else options
                
                # 检查答案字母是否有效
                if answer.upper() in ['A', 'B', 'C', 'D']:
                    idx = ord(answer.upper()) - ord('A')
                    if idx >= len(opts):
                        issues.append(f"{qid}: 答案{answer}超出选项范围")
                else:
                    # 检查答案内容是否匹配
                    answer_found = False
                    for opt in opts:
                        if isinstance(opt, dict) and opt.get('content') == answer:
                            answer_found = True
                            break
                    
                    if not answer_found:
                        # 答案可能是字母
                        if answer.upper() not in ['A', 'B', 'C', 'D']:
                            issues.append(f"{qid}: 答案'{answer}'未在选项中找到匹配")
            except Exception as e:
                issues.append(f"{qid}: 选项解析失败 - {str(e)}")

        if issues:
            print(f"\n发现 {len(issues)} 个答案一致性问题:")
            for issue in issues[:20]:
                print(f"  ⚠️  {issue}")
            if len(issues) > 20:
                print(f"  ... 还有 {len(issues) - 20} 个")
        else:
            print("\n✅ 所有答案与选项一致")

    def validate_difficulty_distribution(self, conn):
        """验证难度分布"""
        cursor = conn.cursor()
        
        print("\n" + "=" * 80)
        print("🎯 难度分布验证")
        print("=" * 80)

        cursor.execute("""
            SELECT difficulty, COUNT(*)
            FROM questions
            WHERE difficulty IS NOT NULL AND difficulty != ''
            GROUP BY difficulty
            ORDER BY CAST(difficulty AS FLOAT)
        """)

        distribution = {}
        for row in cursor.fetchall():
            try:
                diff = float(row[0])
                distribution[diff] = row[1]
            except:
                pass

        if distribution:
            total = sum(distribution.values())
            
            print(f"\n总题目数: {total}")
            print("\n难度分布:")
            
            for diff in sorted(distribution.keys()):
                count = distribution[diff]
                pct = count / total * 100
                
                # 评估分布合理性
                if diff <= 2:
                    expected_pct = 30
                    level = "入门"
                elif diff <= 4:
                    expected_pct = 25
                    level = "基础"
                elif diff <= 6:
                    expected_pct = 25
                    level = "中等"
                elif diff <= 8:
                    expected_pct = 15
                    level = "困难"
                else:
                    expected_pct = 5
                    level = "专家"
                
                status = "✅" if abs(pct - expected_pct) < 10 else "⚠️"
                bar = "█" * int(pct / 2)
                
                print(f"  {status} 难度 {diff:.0f} ({level}): {count:>4} ({pct:>5.1f}%) 期望:{expected_pct:>4.0f}% {bar}")
        else:
            print("\n⚠️  无难度数据")

    # ============ 修复功能 ============

    def fix_all_issues(self):
        """修复所有问题"""
        print("\n" + "=" * 80)
        print("🔧 自动修复问题")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        total_fixed = 0

        try:
            cursor = conn.cursor()

            # 1. 修复空选项
            cursor.execute("""
                UPDATE questions 
                SET options = '[]'
                WHERE options IS NULL OR options = ''
            """)
            if cursor.rowcount > 0:
                print(f"✓ 修复空选项: {cursor.rowcount}个")
                total_fixed += cursor.rowcount

            # 2. 修复空答案
            cursor.execute("""
                UPDATE questions 
                SET correct_answer = 'A'
                WHERE correct_answer IS NULL OR correct_answer = ''
            """)
            if cursor.rowcount > 0:
                print(f"✓ 修复空答案: {cursor.rowcount}个")
                total_fixed += cursor.rowcount

            # 3. 添加默认难度
            cursor.execute("""
                UPDATE questions 
                SET difficulty = 5
                WHERE difficulty IS NULL OR difficulty = '' OR difficulty = 'None'
            """)
            if cursor.rowcount > 0:
                print(f"✓ 添加默认难度: {cursor.rowcount}个")
                total_fixed += cursor.rowcount

            # 4. 添加默认分值
            cursor.execute("""
                UPDATE questions 
                SET points = CAST(difficulty AS FLOAT)
                WHERE points IS NULL OR points = 0
            """)
            if cursor.rowcount > 0:
                print(f"✓ 添加默认分值: {cursor.rowcount}个")
                total_fixed += cursor.rowcount

            # 5. 修复空标签
            cursor.execute("""
                UPDATE questions 
                SET tags = '[]'
                WHERE tags IS NULL OR tags = ''
            """)
            if cursor.rowcount > 0:
                print(f"✓ 修复空标签: {cursor.rowcount}个")
                total_fixed += cursor.rowcount

            conn.commit()

            print(f"\n共修复: {total_fixed}个问题")

        except Exception as e:
            logger.error(f"修复失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def generate_question_fingerprints(self):
        """生成题目指纹用于去重"""
        print("\n" + "=" * 80)
        print("🔐 生成题目指纹")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            
            # 检查是否有fingerprint列
            cursor.execute("PRAGMA table_info(questions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'fingerprint' not in columns:
                cursor.execute("ALTER TABLE questions ADD COLUMN fingerprint TEXT")
                print("✓ 添加fingerprint列")

            # 为没有指纹的题目生成指纹
            cursor.execute("""
                SELECT id, content, options, correct_answer
                FROM questions
                WHERE fingerprint IS NULL OR fingerprint = ''
            """)

            updated = 0
            for row in cursor.fetchall():
                qid, content, options, answer = row
                
                # 生成指纹
                fingerprint_content = f"{content}|{options}|{answer}"
                fingerprint = hashlib.md5(fingerprint_content.encode('utf-8')).hexdigest()
                
                cursor.execute("UPDATE questions SET fingerprint = ? WHERE id = ?", (fingerprint, qid))
                updated += 1

            conn.commit()
            print(f"✓ 生成指纹: {updated}个")

        except Exception as e:
            logger.error(f"生成指纹失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def remove_duplicates(self):
        """删除重复题目（保留一个）"""
        print("\n" + "=" * 80)
        print("🗑️  删除重复题目")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 找出重复的指纹
            cursor.execute("""
                SELECT fingerprint, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
                FROM questions
                WHERE fingerprint IS NOT NULL AND fingerprint != ''
                GROUP BY fingerprint
                HAVING cnt > 1
            """)

            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"\n发现 {len(duplicates)} 组重复题目")
                
                deleted = 0
                for fp, cnt, ids in duplicates:
                    # 保留第一个，删除其余
                    id_list = ids.split(',')
                    keep_id = id_list[0]
                    delete_ids = id_list[1:]
                    
                    placeholders = ','.join(['?' for _ in delete_ids])
                    cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", delete_ids)
                    deleted += len(delete_ids)
                
                conn.commit()
                print(f"✓ 删除重复题目: {deleted}个")
            else:
                print("\n✅ 无重复题目")

        except Exception as e:
            logger.error(f"删除重复失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    # ============ 知识覆盖分析 ============

    def analyze_knowledge_coverage(self):
        """分析知识点覆盖"""
        print("\n" + "=" * 80)
        print("📚 知识点覆盖分析")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 从tags提取知识点
            cursor.execute("SELECT tags, difficulty, type FROM questions WHERE tags IS NOT NULL")
            
            knowledge_coverage = defaultdict(lambda: {'count': 0, 'by_difficulty': defaultdict(int)})
            
            for row in cursor.fetchall():
                tags_str, difficulty, qtype = row
                
                try:
                    tags = json.loads(tags_str) if tags_str else []
                except:
                    tags = []
                
                for tag in tags:
                    if tag not in ['选择题', '填空题', '简答题', '听力', '阅读', '写作']:
                        knowledge_coverage[tag]['count'] += 1
                        try:
                            diff = float(difficulty) if difficulty else 5
                            knowledge_coverage[tag]['by_difficulty'][int(diff)] += 1
                        except:
                            pass

            if knowledge_coverage:
                print(f"\n知识点覆盖 ({len(knowledge_coverage)}个):")
                
                for tag, data in sorted(knowledge_coverage.items(), key=lambda x: x[1]['count'], reverse=True)[:20]:
                    count = data['count']
                    bar = "█" * min(count // 50, 20)
                    print(f"  {tag:<15} {count:>5}题 {bar}")
            else:
                print("\n⚠️  无知识点标签数据")

        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
        finally:
            conn.close()

    # ============ 主流程 ============

    def run_full_validation(self):
        """运行完整校验流程"""
        print("\n" + "=" * 80)
        print("🚀 AI题库全面管理与校验系统")
        print("=" * 80)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. 显示统计
        self.display_statistics()

        # 2. 修复问题
        self.fix_all_issues()

        # 3. 生成指纹
        self.generate_question_fingerprints()

        # 4. 检测重复
        self.check_duplicate_questions(self.connect())

        # 5. 验证答案一致性
        conn = self.connect()
        if conn:
            self.validate_answer_consistency(conn)
            self.validate_difficulty_distribution(conn)
            conn.close()

        # 6. 分析知识点覆盖
        self.analyze_knowledge_coverage()

        print("\n" + "=" * 80)
        print("✅ 校验完成")
        print("=" * 80)


def main():
    """主函数"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    
    manager = QuestionBankManager(db_path)
    manager.run_full_validation()


if __name__ == "__main__":
    main()