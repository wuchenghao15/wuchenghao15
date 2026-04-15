#!/usr/bin/env python3
"""
测试按钮修复器
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_button_fixer():
    """测试按钮修复器"""
    print("=== 开始测试按钮修复器 ===")
    
    try:
        # 导入按钮修复器
        from app.ai.button_fixer import button_fixer
        
        # 当前按钮的HTML代码
        original_button_html = '''<button id="get-started-btn" class="bg-white text-indigo-600 px-8 py-3 rounded-lg font-bold hover:shadow-xl transition-all transform hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white trae-browser-inspect-draggable" aria-label="立即开始使用系统，点击后将进入登录界面">
                                    <i class="fas fa-rocket mr-2"></i>立即开始
                                </button>'''
        
        button_id = "get-started-btn"
        
        print(f"测试按钮ID: {button_id}")
        print(f"原始按钮HTML: {original_button_html}")
        
        # 调用按钮修复器
        result = button_fixer.fix_button(original_button_html, button_id)
        
        print("\n=== 修复结果 ===")
        print(f"状态: {result['status']}")
        print(f"按钮ID: {result['button_id']}")
        
        print("\n=== 发现的问题 ===")
        for issue in result['issues']:
            print(f"- [{issue['severity']}] {issue['type']}: {issue['description']}")
        
        print("\n=== 修复方案 ===")
        for fix_type, fixes in result['fix_solution'].items():
            if fixes:
                print(f"{fix_type}:")
                for fix in fixes:
                    print(f"  - {fix['action']}: {fix['description']}")
        
        print("\n=== 修复后的HTML ===")
        print(result['fixed_html'])
        
        print("\n=== 修复历史 ===")
        print(f"修复时间: {result['fix_history']['timestamp']}")
        
        print("\n=== 测试成功 ===")
        return True
        
    except Exception as e:
        print(f"\n=== 测试失败 ===")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_button_fixer()
