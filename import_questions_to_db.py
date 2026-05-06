#!/usr/bin/env python3
"""
将JSON文件数据上传到数据库脚本
支持多种JSON文件格式，可指定要上传的文件

import os
import sys
# JSON import removed - using database
import sqlite3
import argparse


def get_db_connection(db_path='flask-app/app.db'):
    """获取数据库连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def parse_difficulty(difficulty_value):
    """解析题目难度，将不同格式转换为1-5的整数"""
    if isinstance(difficulty_value, int):
        return max(1, min(5, difficulty_value))
    elif isinstance(difficulty_value, str):
        difficulty_str = difficulty_value.lower()
        if difficulty_str in ['easy', 'beginner', '初级', '简单']:
            return 1
        elif difficulty_str in ['medium', 'intermediate', '中级', '一般']:
            return 2
        elif difficulty_str in ['hard', 'advanced', '高级', '困难']:
            return 3
        elif difficulty_str in ['very hard', 'expert', '专家', '非常困难']:
            return 4
        elif difficulty_str in ['extreme', 'master', '大师', '极致']:
            return 5
    return 1

def parse_question(question):
    """解析不同格式的题目数据，返回标准化格式"""
    # 提取题目文本
    if 'question_text' in question:
        question_text = question['question_text']
    elif 'question' in question:
        question_text = question['question']
    else:
        return None

    # 提取选项
    if 'options' in question:
        options = question['options']
    elif all(key in question for key in ['optionA', 'optionB', 'optionC', 'optionD']):
        options = [question['optionA'], question['optionB'], question['optionC'], question['optionD']]
    else:
        return None
    # 提取正确答案
        correct_answer = question['correct_answer']
    elif 'answer' in question:
        # 如果answer是索引，转换为选项值
        answer_index = question['answer']
        if isinstance(answer_index, int) and 0 <= answer_index < len(options):
            correct_answer = options[answer_index]
        else:
            correct_answer = str(answer_index)
        return None
    # 提取分类
    category = question.get('category', 'vocabulary')

    difficulty = parse_difficulty(question.get('difficulty', 1))

    # 提取解释
    explanation = question.get('explanation', '')

    return {
        'question_text': question_text,
        'options': options,
        'correct_answer': correct_answer,
        'category': category,
        'difficulty': difficulty,
        'explanation': explanation
    }


def import_questions_from_file(json_file, language='japanese', db_path='flask-app/app.db'):
    """从指定的JSON文件导入题目到数据库

    Args:
        json_file: JSON文件路径
        language: 语言（japanese或english）
        db_path: 数据库文件路径
    # 检查文件是否存在
    if not os.path.exists(json_file):
        print(f"错误：文件 {json_file} 不存在")
        return False

    # 读取题目文件
    with open(json_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"从 {json_file} 加载了 {len(questions)} 道题目")

    # 连接数据库
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # 创建题目表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                content TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        inserted_count = 0
        skipped_count = 0

        for question in questions:
            # 解析题目数据
            parsed_question = parse_question(question)
            if not parsed_question:
                skipped_count += 1
                continue

            try:
                # 将选项转换为JSON字符串
                options_json = str(parsed_question['options'])

                # 插入题目
                cursor.execute('''
                    INSERT INTO question_bank (language, category, difficulty, content, options, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    language,
                    parsed_question['category'],
                    parsed_question['difficulty'],
                    parsed_question['question_text'],
                    options_json,
                    parsed_question['explanation']
                ))

                inserted_count += 1

                if inserted_count % 10 == 0:
                    print(f"已导入 {inserted_count} 道题目...")
            except Exception as e:
                print(f"处理题目失败: {str(e)}")
                skipped_count += 1
                continue

        # 提交事务
        conn.commit()

        print(f"成功导入 {inserted_count} 道 {language} 题目到数据库")
        print(f"跳过了 {skipped_count} 道无效或格式不支持的题目")
        return True
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()


def import_all_question_files(db_path='flask-app/app.db'):
    """导入所有找到的题目JSON文件"""
    print("=== 导入所有题目文件到数据库 ===")
    # 查找所有题目相关的JSON文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json') and any(keyword in file.lower() for keyword in ['question', '题库', 'vocab', 'grammar']):
                question_files.append(os.path.join(root, file))

    if not question_files:
        print("没有找到题目JSON文件")
        return

    print(f"找到 {len(question_files)} 个题目JSON文件")

    # 导入每个文件
    for file_path in question_files:
        print(f"\n处理文件: {file_path}")
        # 根据文件名判断语言
        if any(lang in file_path.lower() for lang in ['japanese', '日语', 'jlpt']):
            language = 'japanese'
        elif any(lang in file_path.lower() for lang in ['english', '英语', 'toefl', 'ielts']):
            language = 'english'
        else:
            language = 'japanese'  # 默认日语


    print("\n=== 所有文件导入完成 ===")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将JSON文件数据上传到数据库')

    # 选项：指定要导入的文件
    parser.add_argument('json_files', nargs='*', help='要导入的JSON文件路径')

    # 选项：指定语言
    parser.add_argument('--language', '-l', default='japanese', choices=['japanese', 'english'],
                        help='题目语言（默认：japanese）')

    # 选项：指定数据库路径
    parser.add_argument('--db', '-d', default='flask-app/app.db',
                        help='数据库文件路径（默认：flask-app/app.db）')

    # 选项：导入所有找到的题目文件
    parser.add_argument('--all', '-a', action='store_true',
                        help='导入所有找到的题目JSON文件')

    args = parser.parse_args()

    # 检查数据库路径
    if not os.path.exists(args.db):
        print(f"警告：数据库文件 {args.db} 不存在，将在运行时创建")

    if args.all:
        # 导入所有题目文件
        import_all_question_files(args.db)
    elif args.json_files:
        # 导入指定的JSON文件
        for json_file in args.json_files:
            print(f"\n=== 导入 {json_file} 到数据库 ===")
            import_questions_from_file(json_file, args.language, args.db)
        print("\n=== 所有指定文件导入完成 ===")
    else:
        # 如果没有指定文件，显示帮助信息
        parser.print_help()


if __name__ == "__main__":
    main()
