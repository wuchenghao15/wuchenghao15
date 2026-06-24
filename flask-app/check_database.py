# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
直接检查数据库中的题目内容

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
# JSON import removed - using database
def check_database():
    直接检查数据库中的题目内容
    print("================================================================================" )
    print("================================================================================" )

    try:
        # 连接到数据库
        with sqlite3.connect('dev.db') as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            # 查询最新的20道题目
            cursor.execute('SELECT id, content FROM questions ORDER BY id DESC LIMIT 20')
            rows = cursor.fetchall()
            
            print(f"\n查询到 {len(rows)} 道最新题目:")
            
            # 打印每道题目的内容
            for i, row in enumerate(rows, 1):
            question_id, content = row
            print(f"\n题目 {i} (ID: {question_id}):")
            print(f"内容: {content}")
            
            # 检查是否包含版本信息
            has_version = any(version in content for version in ['人教版', '北师大版', '苏教版', '沪教版', '鲁教版', '粤教版', '湘教版', '川教版'])
            # 检查是否包含年级信息
            has_grade = any(grade in content for grade in ['小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级', '初中一年级', '初中二年级', '初中三年级'])
            # 检查是否包含考试类型信息
            has_exam_type = any(exam_type in content for exam_type in ['中考题', '高考题', '压轴题'])
            # 检查是否包含学科信息
            has_subject = any(subject in content for subject in ['数学', '英语', '语文'])
            
            print(f"包含版本信息: {'是' if has_version else '否'}")
            print(f"包含年级信息: {'是' if has_grade else '否'}")
            print(f"包含考试类型信息: {'是' if has_exam_type else '否'}")
            print(f"包含学科信息: {'是' if has_subject else '否'}")
            
            # 统计符合条件的题目数量
            cursor.execute('SELECT COUNT(*) FROM questions WHERE content LIKE ?', ('%[人教版]%',))
            人教版_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions WHERE content LIKE ?', ('%[中考题]%',))
            中考题_count = cursor.fetchone()[0]
            
            print(f"\n数据库统计:")
            print(f"包含'[人教版]'的题目数量: {人教版_count}")
            print(f"包含'[中考题]'的题目数量: {中考题_count}")
            

    except Exception as e:
        print(f"检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================" )
        print("检查完成!")
        print("================================================================================" )

if __name__ == "__main__":
    check_database()

"""