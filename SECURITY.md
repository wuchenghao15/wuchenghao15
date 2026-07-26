# 安全配置指南

## GitHub仓库安全设置

### 1. 仓库可见性
- **生产环境**: 设置为 **Private**（私有）
- **开源项目**: 设置为 Public，但确保不包含敏感信息

### 2. 分支保护规则
前往 Settings → Branches → Branch protection rule

**保护 main/master 分支**:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require signed commits
- ✅ Include administrators
- ✅ Restrict who can push to matching branches

### 3. 安全选项
前往 Settings → Code security and analysis

- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Secret scanning
- ✅ Push protection

### 4. 访问权限管理
前往 Settings → Collaborators and teams

- 只授予必要的权限
- 使用团队（Teams）管理权限
- 定期审查协管员列表

### 5. 双因素认证（2FA）
- 所有协管员必须启用2FA
- 账户设置 → Password and authentication → Two-factor authentication

## 代码安全

### 敏感信息检查清单
**绝对不能提交到Git的文件**:
- ❌ .db / .sqlite3 / .sqlite 数据库文件
- ❌ .env / .env.local 环境变量文件
- ❌ encryption.key 加密密钥
- ❌ *.pem / *.key 私钥文件
- ❌ config.py 中的硬编码密码
- ❌ 包含用户密码的SQL dump

### .gitignore 建议
```
# 数据库
*.db
*.sqlite3
*.db-journal
*.db-shm
*.db-wal

# 环境变量
.env
.env.local
.env.*.local

# 密钥
*.key
*.pem
encryption.key

# 备份
*.bak
backup/
backups/
*.tar.gz
*.zip

# 大文件
*.iso
*.dmg
*.mp4
*.mp3
```

## 数据库备份安全

### 推荐方案
1. **本地备份**: 加密后存储在本地
2. **云存储加密备份**: 使用加密后的文件上传到云存储
3. **定期验证**: 定期验证备份文件的完整性

### 备份工具
使用 `backup_db.py` 工具进行数据库备份:
```bash
# 普通备份
python backup_db.py

# 加密备份
python backup_db.py --encrypt your_password

# 解密
python backup_db.py --decrypt backup.enc --encrypt your_password
```

## 系统安全加固

### 已实施的安全措施
- ✅ 超级管理员唯一性（仅wuchenghao15）
- ✅ CSRF跨站请求伪造防护
- ✅ API权限控制（越权访问防护）
- ✅ 注册速率限制（防暴力注册）
- ✅ SQL注入防护（参数化查询）
- ✅ 密码强度验证
- ✅ Session安全管理

### 建议补充
1. 登录失败次数限制 + 账户锁定
2. IP白名单（管理员接口）
3. 操作审计日志
4. 定期安全扫描
5. 依赖安全检查（pip-audit）

---

**重要提醒**: 安全是一个持续的过程，定期审查和更新安全措施。
