# MTSCOS AI 项目上传指南

## 目标服务器
- **域名**: wuchenghao15.xicp.net
- **IP地址**: 43.137.3.121
- **开放端口**: 80 (HTTP), 443 (HTTPS)
- **FTP端口**: 21 (超时，可能被防火墙阻止)

## FTP凭据
- **用户名**: wuchenghao15
- **密码**: LoginMe.1988
- **主机**: wuchenghao15.xicp.net
- **端口**: 21

## 部署包信息
- **位置**: `deploy-package/`
- **包含文件**: 完整的项目代码、配置、依赖和脚本
- **配置状态**: 已配置为使用目标服务器域名和端口

## 上传方法

### 方法1: 使用FileZilla (推荐)
1. **下载FileZilla**: https://filezilla-project.org/
2. **安装并打开FileZilla**
3. **输入连接信息**:
   - 主机: wuchenghao15.xicp.net
   - 端口: 21
   - 用户名: wuchenghao15
   - 密码: LoginMe.1988
4. **点击快速连接**
5. **上传文件**:
   - 左侧: 导航到 `deploy-package` 目录
   - 右侧: 导航到远程服务器根目录 `/`
   - 选择左侧所有文件，拖拽到右侧
6. **等待上传完成**
7. **在服务器上启动服务**:
   ```bash
   cd /
   npm install
   npm start
   ```

### 方法2: 使用WinSCP
1. **下载WinSCP**: https://winscp.net/
2. **安装并打开WinSCP**
3. **输入连接信息**:
   - 文件协议: FTP
   - 主机名: wuchenghao15.xicp.net
   - 端口号: 21
   - 用户名: wuchenghao15
   - 密码: LoginMe.1988
4. **点击登录**
5. **上传文件**: 拖拽 `deploy-package` 目录中的所有文件到远程服务器

### 方法3: 使用浏览器上传 (如果服务器支持)
1. **访问服务器**: http://wuchenghao15.xicp.net
2. **寻找上传区域**或文件管理界面
3. **使用提供的FTP凭据登录**
4. **上传 `deploy-package` 目录中的文件**
5. **按照界面提示完成部署**

### 方法4: 使用其他FTP客户端
- **CoreFTP**: https://www.coreftp.com/
- **Cyberduck**: https://cyberduck.io/
- **SmartFTP**: https://www.smartftp.com/
- **Transmit** (Mac): https://panic.com/transmit/

## 故障排除

### FTP连接失败
1. **检查网络连接**: 确保您的网络连接正常
2. **尝试不同端口**: 尝试端口 22 (SFTP) 或 2121
3. **检查防火墙**: 临时禁用防火墙试试
4. **使用被动模式**: 在FTP客户端中启用被动模式
5. **尝试HTTPS上传**: 访问 https://wuchenghao15.xicp.net/upload

### 上传速度慢
1. **压缩文件**: 先压缩再上传
2. **分批上传**: 分批次上传大文件
3. **使用更快的网络**: 尝试使用有线网络或更快的连接

### 服务无法启动
1. **检查端口**: 确保端口80未被占用
2. **安装依赖**: 运行 `npm install` 安装所有依赖
3. **检查权限**: 确保文件权限正确
4. **查看日志**: 检查服务器日志了解错误原因

## 部署后验证

部署完成后，验证服务是否正常运行:

1. **访问主页**: http://wuchenghao15.xicp.net
2. **检查健康状态**: http://wuchenghao15.xicp.net/api/health
3. **测试AI接口**: http://wuchenghao15.xicp.net/api/ai/models
4. **验证防火墙**: http://wuchenghao15.xicp.net/api/health

## 技术支持

如果遇到问题，请尝试:

1. **检查服务器状态**: ping wuchenghao15.xicp.net
2. **检查端口开放**: 使用在线端口检查工具
3. **尝试不同网络**: 切换网络环境
4. **联系服务器管理员**: 确认FTP服务状态
5. **使用HTTP替代方案**: 如果FTP持续失败，考虑使用HTTP上传

## 备用方案

如果FTP上传持续失败，考虑:

1. **使用云存储**: 上传到百度网盘、阿里云盘等，然后从服务器下载
2. **使用Git**: 初始化Git仓库，推送到GitHub，然后从服务器克隆
3. **使用文件传输服务**: WeTransfer、SendGB等
4. **联系服务器托管商**: 寻求技术支持

## 服务器信息

- **服务器类型**: 可能是虚拟主机或云服务器
- **操作系统**: 可能是Linux或Windows
- **Web服务器**: 可能运行Apache或Nginx
- **Node.js**: 需要Node.js环境

## 项目配置

项目已配置为:
- **端口**: 80
- **主机**: wuchenghao15.xicp.net
- **环境**: production
- **AI引擎**: 10个本地AI引擎已配置
- **安全措施**: 防火墙保护已启用

**请按照上述方法完成项目上传，上传完成后服务器将自动开始运行！**