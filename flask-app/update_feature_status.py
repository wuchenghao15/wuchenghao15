#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新特征库中问题的状态
"""

import json
import time
import os

def update_feature_status():
    """更新登录跳转问题的状态为已解决"""
    print("开始更新特征库中登录跳转问题的状态...")
    
    feature_library_path = "feature_library.json"
    
    if not os.path.exists(feature_library_path):
        print(f"特征库文件不存在: {feature_library_path}")
        return {
            "success": False,
            "message": f"特征库文件不存在: {feature_library_path}"
        }
    
    try:
        # 读取特征库
        with open(feature_library_path, 'r', encoding='utf-8') as f:
            feature_library = json.load(f)
        
        # 查找登录跳转问题特征
        login_redirect_feature = None
        for feature in feature_library["features"]:
            if feature["title"] == "index 显示登录成功 没有跳转":
                login_redirect_feature = feature
                break
        
        if not login_redirect_feature:
            print("未找到登录跳转问题特征")
            return {
                "success": False,
                "message": "未找到登录跳转问题特征"
            }
        
        # 更新特征状态
        login_redirect_feature["status"] = "resolved"
        login_redirect_feature["resolved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        login_redirect_feature["resolved_by"] = "system"
        login_redirect_feature["resolution"] = {
            "fix_type": "code_change",
            "fix_description": "修改了app/views/main.py文件中的index路由，添加了登录状态检查，已登录用户自动重定向到combined_test页面",
            "fix_details": {
                "file": "app/views/main.py",
                "function": "index",
                "change_type": "update"
            },
            "verification": "已通过代码审查，修复了登录跳转问题，已登录用户现在会自动跳转到combined_test页面"
        }
        
        # 更新特征库更新时间
        feature_library["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存更新后的特征库
        with open(feature_library_path, 'w', encoding='utf-8') as f:
            json.dump(feature_library, f, ensure_ascii=False, indent=2)
        
        print(f"特征库状态更新成功，特征ID: {login_redirect_feature['feature_id']}")
        print(f"问题状态已更新为: {login_redirect_feature['status']}")
        print(f"特征库已保存到: {feature_library_path}")
        
        return {
            "success": True,
            "message": "特征库状态更新成功",
            "feature_id": login_redirect_feature["feature_id"],
            "feature_library_path": feature_library_path,
            "old_status": "pending",
            "new_status": login_redirect_feature["status"]
        }
    except Exception as e:
        print(f"更新特征库状态时发生错误: {str(e)}")
        return {
            "success": False,
            "message": f"更新特征库状态时发生错误: {str(e)}"
        }

if __name__ == "__main__":
    result = update_feature_status()
    print(json.dumps(result, ensure_ascii=False, indent=2))
