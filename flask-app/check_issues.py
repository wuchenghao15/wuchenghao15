#!/usr/bin/env python3
"""
查看系统检测到的具体问题
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.instances import ai_instance_manager


def check_detailed_issues():
    """查看详细的系统问题"""
    print("=== 系统问题详细报告 ===")
    
    try:
        if hasattr(ai_instance_manager, 'self_healing_system'):
            # 获取系统健康状况
            health = ai_instance_manager.self_healing_system.get_system_health()
            
            print(f"系统健康分数: {health['health_score']}")
            print(f"检测到的问题数: {len(health['detected_issues'])}")
            print(f"活跃实例数: {health['instance_stats']['active_instances']}")
            print(f"总实例数: {health['instance_stats']['total_instances']}")
            print(f"最后检查时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(health['last_check_time']))}")
            
            # 输出检测到的具体问题
            if health['detected_issues']:
                print("\n详细问题列表:")
                for i, issue in enumerate(health['detected_issues'], 1):
                    print(f"\n{i}. 类型: {issue['type']}")
                    print(f"   严重程度: {issue['severity']}")
                    print(f"   描述: {issue['description']}")
                    if 'instance_id' in issue:
                        print(f"   影响实例: {issue['instance_id']}")
                    if 'details' in issue:
                        print(f"   详细信息: {issue['details']}")
            else:
                print("\n✓ 未检测到问题")
            
            # 输出修复历史
            history = ai_instance_manager.self_healing_system.get_fix_history(limit=10)
            if history:
                print("\n最近10条修复记录:")
                for i, record in enumerate(history, 1):
                    print(f"\n{i}. 结果: {record['result']}")
                    print(f"   问题: {record['issue']['description']}")
                    print(f"   时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record['fixed_at']))}")
                    if 'error' in record:
                        print(f"   错误信息: {record['error']}")
            
            return True
        else:
            print("✗ 自我修复系统未初始化")
            return False
    except Exception as e:
        print(f"检查系统问题失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_auto_upgrade():
    """运行自动升级"""
    print("\n=== 运行自动升级 ===")
    try:
        result = ai_instance_manager.auto_upgrade()
        print(f"升级结果: {result}")
        print(f"成功升级了 {result['upgraded_instances']} 个AI实例")
        print(f"成功升级了 {result['upgraded_collections']} 个AI集")
        print(f"检测到 {result['detected_issues']} 个问题")
        return True
    except Exception as e:
        print(f"自动升级失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    check_detailed_issues()
    run_auto_upgrade()
    print("\n=== 升级后再次检查问题 ===")
    check_detailed_issues()


if __name__ == "__main__":
    main()
