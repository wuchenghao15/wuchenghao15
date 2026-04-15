# 检查VERSION文件
with open('VERSION', 'r') as f:
    version = f.read().strip()
print(f'当前版本号: {version}')

# 检查系统配置中的版本号
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute("SELECT config_value FROM system_config WHERE config_key = 'system_version';")
result = cursor.fetchone()
if result:
    print(f'系统配置中的版本号: {result[0]}')
else:
    print('系统配置中未找到版本号')
conn.close()

# 检查CHANGELOG.md
print('\n=== CHANGELOG.md最新版本条目 ===')
with open('CHANGELOG.md', 'r') as f:
    content = f.read()
    # 找到最新版本的位置
    latest_version_start = content.find('## Version 1.0.1')
    if latest_version_start != -1:
        # 找到下一个版本的位置，或者文件末尾
        next_version_start = content.find('## Version', latest_version_start + 1)
        if next_version_start != -1:
            latest_entry = content[latest_version_start:next_version_start]
        else:
            latest_entry = content[latest_version_start:]
        print(latest_entry.strip())
    else:
        print('未找到版本 1.0.1 的更新日志')

print('\n=== 验证完成 ===')
if version == '1.0.1' and result and result[0] == '1.0.1':
    print('✓ 版本升级成功！')
else:
    print('✗ 版本升级失败！')
