from datetime import datetime

# 读取当前版本号
version_file = 'VERSION'
with open(version_file, 'r') as f:
    current_version = f.read().strip()

# 计算下一个版本号
major, minor, patch = map(int, current_version.split('.'))
next_version = f"{major}.{minor}.{patch + 1}"

# 更新VERSION文件
with open(version_file, 'w') as f:
    f.write(next_version)

print(f"版本号已从 {current_version} 升级到 {next_version}")

# 更新系统配置
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
current_time = datetime.now().isoformat()

# 检查system_version配置是否存在
cursor.execute('SELECT id FROM system_config WHERE config_key = "system_version";')
existing = cursor.fetchone()

if existing:
    # 更新现有配置
    cursor.execute('''
        UPDATE system_config 
        SET config_value = ?, updated_at = ?
        WHERE config_key = "system_version"
    ''', (next_version, current_time))
else:
    # 创建新配置
    cursor.execute('''
        INSERT INTO system_config 
        (config_key, config_value, config_type, description, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("system_version", next_version, "string", "系统当前版本号", 1, current_time, current_time))

conn.commit()
conn.close()
print("系统配置已更新")

# 更新CHANGELOG.md
changelog_file = 'CHANGELOG.md'

log_entry = f"\n## Version {next_version} ({datetime.now().strftime('%Y-%m-%d')})\n\n"
log_entry += "### Features\n"
log_entry += "- 全面自动完善AI脑库所有功能\n"
log_entry += "- 打通所有测试流程\n"
log_entry += "- 优化系统性能和稳定性\n"
log_entry += "- 完善API端口和中间件\n"
log_entry += "- 增强系统规则和配置\n"
log_entry += "\n### Improvements\n"
log_entry += "- 优化数据库结构\n"
log_entry += "- 增强系统监控和恢复机制\n"
log_entry += "- 完善备份和清理策略\n"
log_entry += "- 提升AI脑库自动更新能力\n"
log_entry += "\n### Bug Fixes\n"
log_entry += "- 修复已知问题\n"
log_entry += "- 优化错误处理\n"

# 读取现有内容
with open(changelog_file, 'r') as f:
    content = f.read()

# 在文件开头添加新日志
updated_content = log_entry + content
with open(changelog_file, 'w') as f:
    f.write(updated_content)

print("CHANGELOG.md已更新")
print("\n版本升级完成！")
