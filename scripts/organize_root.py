# -*- coding: utf-8 -*-
"""
MTSCOS AI 系统根目录智能整理脚本
自动分类归档散乱文件，精简系统根目录
"""
import os
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 目录映射规则
DIR_MAPPINGS = {
    'scripts/': [
        'main.py', 'setup.py', 'launch_system.py', 'start_full_system.py',
        'start_json_sync.py', 'system_init_restart_manager.py',
        'system_manager.py', 'system_config_manager.py',
        'integrated_system_manager.py', 'system_adaptation_manager.py',
        'system_auto_adapter.py', 'system_upgrader.py',
        'system_upgrade_optimizer.py', 'start_server.sh', 'start.sh',
        'start-all.sh', 'start_all.sh', 'start_complete_system.sh',
        'start_root_server.sh', 'stop-all.sh', 'init_system.sh',
        'demo.sh', 'monitor-system.sh', 'recover-system.sh',
        'deploy.sh', 'create-deploy-package.sh', 'build_app.sh',
        'verify_optimization.sh', 'temp_http_function.sh',
        'cluster_manager.sh', 'git_upload_backup.sh',
    ],
    'scripts/ai/': [
        'ai_employee_api.py', 'ai_employee_manager.py',
        'auto_fix_employee.py', 'comprehensive_fix_employee.py',
        'add_more_employees.py', 'ai_adaptive_learning_rules.py',
        'ai_highdim_adaptation_rules.py', 'ai_optimizer_analyzer.py',
        'ai_rule_optimizer.py', 'fix_font_awesome.py',
        'fix_partition_tables.py', 'optimization_report_generator.py',
        'test_mtscos_web.py', 'py_optimizer.py',
        'simple_course_expander.py', 'course_expander.py',
    ],
    'scripts/database/': [
        'database_manager.py', 'database_sharding.py',
        'database_upgrade.py', 'data_integrator.py', 'data_security.py',
        'json_to_db_uploader.py', 'json_auto_sync_system.py',
        'learning_system_db.py', 'learning_system_ai_init.py',
        'learning_api.py', 'nine_year_api.py',
        'nine_year_upgrade_system.py', 'question_increment_rules.py',
    ],
    'scripts/security/': [
        'security_rules.py', 'ip_security.py',
        'permission_priority_rules.py', 'permission_enhancement.py',
        'user_behavior.py',
    ],
    'scripts/api/': [
        'api_server.py', 'enhanced_api_server.py', 'config_api.py',
        'auto_sync.sh',
    ],
    'scripts/git/': [
        'git_manager.py', 'git_sync.py', 'github_cli.py',
        'auto-backup.sh', 'backup-script.sh', 'backup-system.sh',
    ],
    'scripts/backup/': [
        'backup_manager.py', 'rollback_manager.py',
        'shadow_node.py', 'sandbox_manager.py',
    ],
    'docs/reports/': [
        'API错误完整诊断报告.md',
        'ERR_ABORTED错误修复报告.md',
        'AI员工批量修复系统执行报告.md',
        '前端AI员工修复报告.md',
        '最终问题分析.md',
        '错误修复报告.md',
        '任务完成报告.md',
        '路由重复问题修复报告.md',
        'super_admin_dashboard优化报告.md',
        'SYSTEM_EXTENSION_REPORT.md',
        'SYSTEM_OPTIMIZATION_REPORT.md',
        'PROJECT_ORGANIZATION_SUMMARY.md',
        'FINAL_FIX_SOLUTION.md',
        '系统升级计划.md',
        'system_upgrade_plan.md',
    ],
    'docs/': [
        'CODE_WIKI.md',
        'AI_CAPABILITIES.md',
        'ai_learning_system_doc.md',
    ],
}

def organize_files():
    """执行文件整理"""
    print("=" * 60)
    print("MTSCOS AI 系统根目录智能整理")
    print("=" * 60)
    
    moved_count = 0
    skipped_count = 0
    errors = []
    
    # 创建目标目录
    for dir_path in DIR_MAPPINGS.keys():
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        os.makedirs(full_path, exist_ok=True)
    
    # 处理每个文件
    for dir_path, filenames in DIR_MAPPINGS.items():
        target_dir = os.path.join(PROJECT_ROOT, dir_path)
        
        for filename in filenames:
            src = os.path.join(PROJECT_ROOT, filename)
            dst = os.path.join(target_dir, filename)
            
            if not os.path.exists(src):
                skipped_count += 1
                continue
            
            try:
                # 如果目标已存在，先备份
                if os.path.exists(dst):
                    backup_name = f"{filename}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_dst = os.path.join(target_dir, backup_name)
                    shutil.move(dst, backup_dst)
                    print(f"  备份已存在文件: {filename} -> {backup_name}")
                
                shutil.move(src, dst)
                moved_count += 1
                print(f"  ✓ {filename} -> {dir_path}")
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
                print(f"  ✗ {filename}: {e}")
    
    # 统计剩余根目录文件
    root_files = [f for f in os.listdir(PROJECT_ROOT) 
                  if os.path.isfile(os.path.join(PROJECT_ROOT, f))]
    
    print("\n" + "=" * 60)
    print("整理完成!")
    print("=" * 60)
    print(f"  移动文件数: {moved_count}")
    print(f"  跳过文件数: {skipped_count}")
    print(f"  错误数: {len(errors)}")
    print(f"  根目录剩余文件数: {len(root_files)}")
    
    if errors:
        print("\n错误详情:")
        for err in errors:
            print(f"  - {err}")
    
    print("\n根目录核心文件:")
    important = ['README.md', 'CHANGELOG.md', 'VERSION', 'LICENSE', 
                 'Makefile', 'Dockerfile', 'docker-compose.yml',
                 '.gitignore', '.gitattributes', '.env.example',
                 'app.py', 'requirements.txt']
    for f in sorted(root_files):
        if f in important or f.startswith('.'):
            print(f"  📄 {f}")
    
    return moved_count, skipped_count, errors

if __name__ == '__main__':
    organize_files()
