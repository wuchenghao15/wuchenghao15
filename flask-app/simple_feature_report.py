#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的特征库上报脚本，避免初始化整个Flask应用
"""

import json
import time
import os

def report_feature():
    """上报登录跳转问题特征到特征库"""
    print("开始上报登录跳转问题特征到特征库...")
    
    # 准备特征数据
    feature_data = {
        "feature_id": f"feature_{int(time.time())}_{hash('login_redirect_feature')}",
        "type": "bug",
        "title": "index 显示登录成功 没有跳转",
        "description": "用户登录成功后，停留在首页(index)，没有自动跳转到预期页面",
        "severity": "medium",
        "feature_category": "authentication",
        "affected_functionality": "login_redirect",
        "location": {
            "file": "app/views/main.py",
            "function": "index",
            "line": 20
        },
        "issue_details": {
            "expected_behavior": "用户登录成功后，应该自动跳转到combined_test页面",
            "actual_behavior": "用户登录成功后，停留在首页",
            "environment": {
                "app_version": "1.0.0",
                "python_version": "3.8+",
                "flask_version": "2.0+",
                "database": "SQLite"
            }
        },
        "reported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "analysis": {
            "root_cause": "index路由没有检查用户登录状态，导致已登录用户仍停留在首页",
            "suggested_fix": "修改index路由，添加登录状态检查，已登录用户自动重定向到combined_test页面",
            "expected_impact": "提高用户体验，确保登录流程完整性"
        }
    }
    
    print(f"收集到的特征信息: {json.dumps(feature_data, ensure_ascii=False, indent=2)}")
    
    # 将特征数据保存到本地特征库文件
    feature_library_path = "feature_library.json"
    
    try:
        # 读取现有特征库
        if os.path.exists(feature_library_path):
            with open(feature_library_path, 'r', encoding='utf-8') as f:
                feature_library = json.load(f)
        else:
            feature_library = {
                "version": "1.0.0",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "features": []
            }
        
        # 添加新特征
        feature_library["features"].append(feature_data)
        feature_library["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存更新后的特征库
        with open(feature_library_path, 'w', encoding='utf-8') as f:
            json.dump(feature_library, f, ensure_ascii=False, indent=2)
        
        print(f"特征库上报成功，特征ID: {feature_data['feature_id']}")
        print(f"特征库已保存到: {feature_library_path}")
        print(f"当前特征库中共有 {len(feature_library['features'])} 个特征")
        
        return {
            "success": True,
            "message": "特征库上报成功",
            "feature_id": feature_data["feature_id"],
            "feature_library_path": feature_library_path,
            "feature_count": len(feature_library['features'])
        }
    except Exception as e:
        print(f"上报特征库时发生错误: {str(e)}")
        return {
            "success": False,
            "message": f"上报特征库时发生错误: {str(e)}"
        }

if __name__ == "__main__":
    result = report_feature()
    print(json.dumps(result, ensure_ascii=False, indent=2))
