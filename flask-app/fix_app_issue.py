#!/usr/bin/env python3
"""
修复app.py中的finally块问题
"""

import sys

# 修复app.py中的问题
try:
    with open('app.py', 'r') as f:
        content = f.read()
    
    # 修复finally块中ai_repair_service可能未定义的问题
    # 先定义旧的和新的代码块
    old_code = '''    finally:
        # 停止AI脑库自动修复服务
        try:
            ai_repair_service.stop()
            logger.info("AI脑库自动修复与自我升级服务已停止")
        except Exception as e:
            logger.error(f"停止AI脑库自动修复服务失败: {str(e)}")
            import traceback
            traceback.print_exc()'''
    
    new_code = '''    finally:
        # 停止AI脑库自动修复服务
        try:
            if 'ai_repair_service' in locals():
                ai_repair_service.stop()
                logger.info("AI脑库自动修复与自我升级服务已停止")
        except Exception as e:
            logger.error(f"停止AI脑库自动修复服务失败: {str(e)}")
            import traceback
            traceback.print_exc()'''
    
    # 执行替换
    new_content = content.replace(old_code, new_code)
    
    with open('app.py', 'w') as f:
        f.write(new_content)
    
    print("成功修复app.py中的finally块问题")
    
except Exception as e:
    print(f"修复app.py失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
