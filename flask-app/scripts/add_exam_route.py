# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
在app.py中添加考试管理路由
"""

# 在matrix_management路由后添加以下代码:

'''
# ============================================
# 考试管理页面
# ============================================
@app.route('/exam_management')
def exam_management():
    return render_template('exam_management.html')
'''

print("请在app.py的matrix_management路由后添加以下代码:\n")
print("""
# ============================================
# 考试管理页面
# ============================================
@app.route('/exam_management')
def exam_management():
    return render_template('exam_management.html')
""")
