#!/usr/bin/env node

/**
 * MTSCOS AI 系统 - GitHub备份管理器
 * 实现系统自动备份到GitHub和备份计划功能
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const crypto = require('crypto');
const schedule = require('node-schedule');
const { Octokit } = require('@octokit/rest');

class GitHubBackupManager {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.backupHistory = [];
    this.scheduledJobs = new Map();
    this.isInitialized = false;
    this.octokit = null;
    this.lastBackupTime = null;
    this.currentBackup = null;
    
    // 初始化备份管理器
    this.initialize();
  }

  /**
   * 初始化备份管理器
   */
  initialize() {
    try {
      // 加载配置文件
      this.loadConfig();
      
      // 确保必要目录存在
      this.ensureDirectories();
      
      // 初始化GitHub API客户端
      this.initializeGitHubClient();
      
      // 加载备份历史
      this.loadBackupHistory();
      
      // 设置备份计划
      this.setupBackupSchedule();
      
      this.isInitialized = true;
      console.log('MTSCOS AI 系统 - GitHub备份管理器初始化完成');
      
    } catch (error) {
      console.error('初始化GitHub备份管理器失败:', error.message);
      this.logError('初始化失败', error);
      throw error;
    }
  }

  /**
   * 加载配置文件
   */
  loadConfig() {
    try {
      const configContent = fs.readFileSync(this.configPath, 'utf8');
      const fullConfig = JSON.parse(configContent);
      this.config = fullConfig.stagingEnvironment;
      
      // 验证配置
      this.validateConfig();
      
    } catch (error) {
      throw new Error(`无法加载配置文件: ${error.message}`);
    }
  }

  /**
   * 验证配置
   */
  validateConfig() {
    if (!this.config.backup || !this.config.backup.github) {
      throw new Error('GitHub备份配置缺失');
    }
    
    const githubConfig = this.config.backup.github;
    
    // 检查必要配置项
    const requiredFields = ['token', 'owner', 'repo', 'branch', 'backupDir'];
    for (const field of requiredFields) {
      if (!githubConfig[field]) {
        throw new Error(`GitHub备份配置缺少必要字段: ${field}`);
      }
    }
    
    // 设置默认值
    githubConfig.backupFormat = githubConfig.backupFormat || 'zip';
    githubConfig.backupRetention = githubConfig.backupRetention || 10;
    githubConfig.backupTimeout = githubConfig.backupTimeout || 3600000; // 默认1小时
    githubConfig.backupSchedule = githubConfig.backupSchedule || '0 0 * * *'; // 默认每天午夜
    githubConfig.ignorePatterns = githubConfig.ignorePatterns || [
      'node_modules',
      'logs',
      '.git',
      '.DS_Store',
      '*.tmp',
      '*.temp',
      '*.log'
    ];
    
    // 设置完整的备份目录路径
    if (!path.isAbsolute(githubConfig.backupDir)) {
      githubConfig.backupDir = path.join(this.config.basePath, githubConfig.backupDir);
    }
    
    console.log('GitHub备份配置验证通过');
  }

  /**
   * 确保必要目录存在
   */
  ensureDirectories() {
    try {
      const githubConfig = this.config.backup.github;
      
      // 确保备份工作目录存在
      if (!fs.existsSync(githubConfig.backupDir)) {
        fs.mkdirSync(githubConfig.backupDir, { recursive: true });
        console.log(`创建备份工作目录: ${githubConfig.backupDir}`);
      }
      
      // 确保临时目录存在
      this.tempDir = path.join(githubConfig.backupDir, 'temp');
      if (!fs.existsSync(this.tempDir)) {
        fs.mkdirSync(this.tempDir, { recursive: true });
      }
      
      // 确保日志目录存在
      this.logDir = path.join(this.config.basePath, 'Logs', 'Backup');
      if (!fs.existsSync(this.logDir)) {
        fs.mkdirSync(this.logDir, { recursive: true });
      }
      
    } catch (error) {
      console.error('创建必要目录失败:', error.message);
      throw error;
    }
  }

  /**
   * 初始化GitHub API客户端
   */
  initializeGitHubClient() {
    try {
      const githubConfig = this.config.backup.github;
      
      this.octokit = new Octokit({
        auth: githubConfig.token,
        userAgent: 'MTSCOS-AI-Backup-Manager',
        baseUrl: githubConfig.apiUrl || 'https://api.github.com',
        request: {
          timeout: githubConfig.apiTimeout || 30000
        }
      });
      
      // 测试连接
      this.testGitHubConnection();
      
    } catch (error) {
      console.error('初始化GitHub客户端失败:', error.message);
      throw error;
    }
  }

  /**
   * 测试GitHub连接
   */
  async testGitHubConnection() {
    try {
      const githubConfig = this.config.backup.github;
      
      // 获取仓库信息，测试连接
      const response = await this.octokit.repos.get({
        owner: githubConfig.owner,
        repo: githubConfig.repo
      });
      
      if (response.status === 200) {
        console.log(`成功连接到GitHub仓库: ${githubConfig.owner}/${githubConfig.repo}`);
      } else {
        throw new Error(`GitHub仓库访问失败，状态码: ${response.status}`);
      }
      
    } catch (error) {
      throw new Error(`GitHub连接测试失败: ${error.message}`);
    }
  }

  /**
   * 加载备份历史
   */
  loadBackupHistory() {
    try {
      const historyPath = path.join(this.config.backup.github.backupDir, 'backup-history.json');
      
      if (fs.existsSync(historyPath)) {
        const historyContent = fs.readFileSync(historyPath, 'utf8');
        this.backupHistory = JSON.parse(historyContent);
        
        // 获取最后一次备份时间
        if (this.backupHistory.length > 0) {
          const lastBackup = this.backupHistory[this.backupHistory.length - 1];
          this.lastBackupTime = lastBackup.timestamp;
          console.log(`上次备份时间: ${this.lastBackupTime}`);
        }
        
        console.log(`已加载 ${this.backupHistory.length} 条备份历史记录`);
      }
      
    } catch (error) {
      console.error('加载备份历史失败:', error.message);
      // 使用空历史
      this.backupHistory = [];
    }
  }

  /**
   * 保存备份历史
   */
  saveBackupHistory() {
    try {
      const historyPath = path.join(this.config.backup.github.backupDir, 'backup-history.json');
      
      // 只保留最近的记录，根据配置的保留数量
      const retentionCount = this.config.backup.github.backupRetention;
      if (this.backupHistory.length > retentionCount) {
        this.backupHistory = this.backupHistory.slice(-retentionCount);
      }
      
      fs.writeFileSync(
        historyPath,
        JSON.stringify(this.backupHistory, null, 2),
        'utf8'
      );
      
    } catch (error) {
      console.error('保存备份历史失败:', error.message);
      this.logError('保存备份历史失败', error);
    }
  }

  /**
   * 设置备份计划
   */
  setupBackupSchedule() {
    try {
      const githubConfig = this.config.backup.github;
      
      // 清除已有的定时任务
      this.clearScheduledJobs();
      
      // 添加默认备份计划
      this.addBackupSchedule('daily', githubConfig.backupSchedule, true);
      
      // 添加配置中的其他备份计划
      if (githubConfig.additionalSchedules && Array.isArray(githubConfig.additionalSchedules)) {
        githubConfig.additionalSchedules.forEach(scheduleConfig => {
          this.addBackupSchedule(
            scheduleConfig.name || `schedule_${Date.now()}`,
            scheduleConfig.cronExpression,
            scheduleConfig.enabled !== false
          );
        });
      }
      
    } catch (error) {
      console.error('设置备份计划失败:', error.message);
      this.logError('设置备份计划失败', error);
    }
  }

  /**
   * 添加备份计划
   */
  addBackupSchedule(name, cronExpression, enabled = true) {
    try {
      // 如果已存在同名任务，先移除
      if (this.scheduledJobs.has(name)) {
        this.removeBackupSchedule(name);
      }
      
      if (enabled) {
        const job = schedule.scheduleJob(cronExpression, async () => {
          console.log(`执行定时备份任务: ${name} (${cronExpression})`);
          await this.performBackup(true);
        });
        
        this.scheduledJobs.set(name, {
          job: job,
          cronExpression: cronExpression,
          enabled: true
        });
        
        console.log(`已添加备份计划: ${name} - ${cronExpression}`);
      }
      
      return true;
    } catch (error) {
      console.error(`添加备份计划失败 [${name}]:`, error.message);
      this.logError(`添加备份计划失败 [${name}]`, error);
      return false;
    }
  }

  /**
   * 移除备份计划
   */
  removeBackupSchedule(name) {
    try {
      const scheduleInfo = this.scheduledJobs.get(name);
      if (scheduleInfo) {
        scheduleInfo.job.cancel();
        this.scheduledJobs.delete(name);
        console.log(`已移除备份计划: ${name}`);
        return true;
      }
      return false;
    } catch (error) {
      console.error(`移除备份计划失败 [${name}]:`, error.message);
      this.logError(`移除备份计划失败 [${name}]`, error);
      return false;
    }
  }

  /**
   * 清除所有备份计划
   */
  clearScheduledJobs() {
    try {
      this.scheduledJobs.forEach((scheduleInfo, name) => {
        scheduleInfo.job.cancel();
      });
      this.scheduledJobs.clear();
      console.log('已清除所有备份计划');
    } catch (error) {
      console.error('清除备份计划失败:', error.message);
      this.logError('清除备份计划失败', error);
    }
  }

  /**
   * 执行备份
   */
  async performBackup(isScheduled = false) {
    if (!this.isInitialized) {
      throw new Error('备份管理器未初始化');
    }
    
    // 检查是否已有备份在进行中
    if (this.currentBackup && this.currentBackup.inProgress) {
      console.log('已有备份任务在进行中，跳过此次备份');
      return { status: 'skipped', reason: 'backup_in_progress' };
    }
    
    // 创建备份记录
    const backupId = crypto.randomUUID();
    const timestamp = new Date().toISOString();
    const timestampFormatted = timestamp.replace(/[:.]/g, '-');
    
    this.currentBackup = {
      backupId: backupId,
      timestamp: timestamp,
      isScheduled: isScheduled,
      inProgress: true,
      status: 'started',
      startTime: Date.now(),
      fileSize: 0,
      commitHash: null,
      errors: [],
      warnings: []
    };
    
    console.log(`开始备份任务 [${backupId}] - ${timestamp}`);
    
    try {
      // 1. 准备备份文件
      const backupFile = await this.prepareBackupFile(backupId, timestampFormatted);
      
      // 2. 计算备份文件的哈希值
      const fileHash = this.calculateFileHash(backupFile);
      
      // 3. 上传备份到GitHub
      const commitInfo = await this.uploadToGitHub(backupFile, timestampFormatted, fileHash);
      
      // 4. 更新备份记录
      this.currentBackup.fileSize = fs.statSync(backupFile).size;
      this.currentBackup.commitHash = commitInfo.sha;
      this.currentBackup.status = 'completed';
      this.currentBackup.endTime = Date.now();
      this.currentBackup.duration = this.currentBackup.endTime - this.currentBackup.startTime;
      this.currentBackup.fileHash = fileHash;
      this.currentBackup.backupFile = backupFile;
      
      // 5. 清理临时文件
      this.cleanupTempFiles(backupFile);
      
      // 6. 更新备份历史
      this.backupHistory.push({ ...this.currentBackup });
      this.saveBackupHistory();
      this.lastBackupTime = timestamp;
      
      console.log(`备份任务 [${backupId}] 完成 - 耗时: ${this.formatDuration(this.currentBackup.duration)}`);
      
      // 7. 发送备份完成通知
      this.notifyBackupComplete(this.currentBackup);
      
      return this.currentBackup;
      
    } catch (error) {
      // 更新失败状态
      this.currentBackup.status = 'failed';
      this.currentBackup.endTime = Date.now();
      this.currentBackup.duration = this.currentBackup.endTime - this.currentBackup.startTime;
      this.currentBackup.errors.push(error.message);
      
      console.error(`备份任务 [${backupId}] 失败:`, error.message);
      this.logError(`备份失败 [${backupId}]`, error);
      
      // 发送失败通知
      this.notifyBackupFailed(this.currentBackup);
      
      // 清理临时文件
      if (this.currentBackup.backupFile && fs.existsSync(this.currentBackup.backupFile)) {
        this.cleanupTempFiles(this.currentBackup.backupFile);
      }
      
      // 记录失败的备份尝试
      this.backupHistory.push({ ...this.currentBackup });
      this.saveBackupHistory();
      
      return this.currentBackup;
    } finally {
      // 重置当前备份状态
      this.currentBackup.inProgress = false;
    }
  }

  /**
   * 准备备份文件
   */
  async prepareBackupFile(backupId, timestampFormatted) {
    const githubConfig = this.config.backup.github;
    const projectDir = this.config.basePath;
    
    // 创建临时备份目录
    const tempBackupDir = path.join(this.tempDir, backupId);
    if (fs.existsSync(tempBackupDir)) {
      this.removeDirectory(tempBackupDir);
    }
    fs.mkdirSync(tempBackupDir, { recursive: true });
    
    // 确定备份文件名
    let backupFileName;
    let backupFile;
    
    if (githubConfig.backupFormat === 'zip') {
      backupFileName = `mtscos-backup-${timestampFormatted}.zip`;
      backupFile = path.join(this.tempDir, backupFileName);
      
      // 使用 zip 命令创建压缩包
      await this.createZipArchive(projectDir, backupFile, githubConfig.ignorePatterns);
      
    } else if (githubConfig.backupFormat === 'tar.gz') {
      backupFileName = `mtscos-backup-${timestampFormatted}.tar.gz`;
      backupFile = path.join(this.tempDir, backupFileName);
      
      // 使用 tar 命令创建压缩包
      await this.createTarArchive(projectDir, backupFile, githubConfig.ignorePatterns);
      
    } else {
      throw new Error(`不支持的备份格式: ${githubConfig.backupFormat}`);
    }
    
    console.log(`创建备份文件: ${backupFile}`);
    return backupFile;
  }

  /**
   * 创建ZIP压缩包
   */
  createZipArchive(sourceDir, outputFile, ignorePatterns) {
    return new Promise((resolve, reject) => {
      try {
        // 构建忽略参数
        let ignoreArgs = '';
        if (ignorePatterns && ignorePatterns.length > 0) {
          ignorePatterns.forEach(pattern => {
            ignoreArgs += `-x "${pattern}" `;
          });
        }
        
        // 执行zip命令
        const zipCmd = `cd "${sourceDir}" && zip -r "${outputFile}" . ${ignoreArgs}`;
        console.log(`执行命令: ${zipCmd}`);
        
        execSync(zipCmd, { stdio: 'inherit' });
        resolve();
        
      } catch (error) {
        reject(new Error(`创建ZIP压缩包失败: ${error.message}`));
      }
    });
  }

  /**
   * 创建TAR压缩包
   */
  createTarArchive(sourceDir, outputFile, ignorePatterns) {
    return new Promise((resolve, reject) => {
      try {
        // 构建忽略参数
        let ignoreArgs = '';
        if (ignorePatterns && ignorePatterns.length > 0) {
          ignorePatterns.forEach(pattern => {
            ignoreArgs += `--exclude="${pattern}" `;
          });
        }
        
        // 执行tar命令
        const tarCmd = `cd "${sourceDir}" && tar -czf "${outputFile}" ${ignoreArgs} .`;
        console.log(`执行命令: ${tarCmd}`);
        
        execSync(tarCmd, { stdio: 'inherit' });
        resolve();
        
      } catch (error) {
        reject(new Error(`创建TAR压缩包失败: ${error.message}`));
      }
    });
  }

  /**
   * 计算文件哈希值
   */
  calculateFileHash(filePath) {
    try {
      const fileBuffer = fs.readFileSync(filePath);
      const hash = crypto.createHash('sha256');
      hash.update(fileBuffer);
      return hash.digest('hex');
    } catch (error) {
      console.error(`计算文件哈希值失败: ${error.message}`);
      throw new Error(`计算文件哈希值失败: ${error.message}`);
    }
  }

  /**
   * 上传到GitHub
   */
  async uploadToGitHub(filePath, timestampFormatted, fileHash) {
    const githubConfig = this.config.backup.github;
    
    try {
      // 读取文件内容
      const fileContent = fs.readFileSync(filePath);
      const contentBase64 = fileContent.toString('base64');
      
      // 确定上传路径
      const uploadPath = `${githubConfig.backupPath || 'backups'}/${path.basename(filePath)}`;
      
      // 构建提交信息
      const commitMessage = `自动备份 ${timestampFormatted}\n\n哈希值: ${fileHash}\n备份ID: ${this.currentBackup.backupId}`;
      
      console.log(`上传备份文件到GitHub: ${uploadPath}`);
      console.log(`提交信息: ${commitMessage}`);
      
      // 上传文件（使用API）
      const response = await this.octokit.repos.createOrUpdateFileContents({
        owner: githubConfig.owner,
        repo: githubConfig.repo,
        path: uploadPath,
        message: commitMessage,
        content: contentBase64,
        branch: githubConfig.branch
      });
      
      console.log(`备份文件上传成功: ${response.data.commit.sha}`);
      return response.data.commit;
      
    } catch (error) {
      console.error(`上传到GitHub失败: ${error.message}`);
      // 如果文件太大（GitHub限制），尝试使用git命令
      if (error.status === 422 && error.message.includes('too large')) {
        console.log('文件过大，尝试使用git命令上传...');
        return await this.uploadWithGitCommand(filePath, timestampFormatted, fileHash);
      }
      throw error;
    }
  }

  /**
   * 使用Git命令上传
   */
  async uploadWithGitCommand(filePath, timestampFormatted, fileHash) {
    const githubConfig = this.config.backup.github;
    
    // 创建临时Git工作目录
    const gitWorkDir = path.join(this.tempDir, `git-${this.currentBackup.backupId}`);
    if (fs.existsSync(gitWorkDir)) {
      this.removeDirectory(gitWorkDir);
    }
    fs.mkdirSync(gitWorkDir, { recursive: true });
    
    try {
      const fileName = path.basename(filePath);
      const gitFilePath = path.join(`${githubConfig.backupPath || 'backups'}`, fileName);
      
      // 配置Git
      this.executeGitCommand(gitWorkDir, 'init');
      this.executeGitCommand(gitWorkDir, `config user.name "MTSCOS AI Backup"`);
      this.executeGitCommand(gitWorkDir, `config user.email "backup@mtscos-ai.com"`);
      this.executeGitCommand(gitWorkDir, `remote add origin https://${githubConfig.token}@github.com/${githubConfig.owner}/${githubConfig.repo}.git`);
      
      // 拉取最新代码
      this.executeGitCommand(gitWorkDir, `fetch origin ${githubConfig.branch}`);
      this.executeGitCommand(gitWorkDir, `checkout -b ${githubConfig.branch} origin/${githubConfig.branch}`);
      
      // 确保备份目录存在
      const backupDir = path.join(gitWorkDir, githubConfig.backupPath || 'backups');
      if (!fs.existsSync(backupDir)) {
        fs.mkdirSync(backupDir, { recursive: true });
      }
      
      // 复制备份文件
      fs.copyFileSync(filePath, path.join(backupDir, fileName));
      
      // 提交更改
      this.executeGitCommand(gitWorkDir, `add "${gitFilePath}"`);
      const commitMessage = `自动备份 ${timestampFormatted}\n\n哈希值: ${fileHash}\n备份ID: ${this.currentBackup.backupId}`;
      this.executeGitCommand(gitWorkDir, `commit -m "${commitMessage}"`);
      
      // 推送到GitHub
      this.executeGitCommand(gitWorkDir, `push origin ${githubConfig.branch}`);
      
      // 获取最新提交信息
      const commitHash = this.executeGitCommand(gitWorkDir, `rev-parse HEAD`).trim();
      console.log(`使用Git命令上传成功: ${commitHash}`);
      
      return { sha: commitHash };
      
    } catch (error) {
      console.error(`使用Git命令上传失败: ${error.message}`);
      throw new Error(`使用Git命令上传失败: ${error.message}`);
    } finally {
      // 清理临时Git工作目录
      this.removeDirectory(gitWorkDir);
    }
  }

  /**
   * 执行Git命令
   */
  executeGitCommand(workDir, command) {
    console.log(`执行Git命令 [${workDir}]: git ${command}`);
    return execSync(`git ${command}`, {
      cwd: workDir,
      encoding: 'utf8',
      stdio: 'inherit'
    });
  }

  /**
   * 清理临时文件
   */
  cleanupTempFiles(backupFile) {
    try {
      // 如果配置了保留本地备份，则复制文件到备份目录
      const githubConfig = this.config.backup.github;
      if (githubConfig.keepLocalBackup) {
        const localBackupDir = path.join(githubConfig.backupDir, 'local-backups');
        if (!fs.existsSync(localBackupDir)) {
          fs.mkdirSync(localBackupDir, { recursive: true });
        }
        
        const localBackupPath = path.join(localBackupDir, path.basename(backupFile));
        fs.copyFileSync(backupFile, localBackupPath);
        console.log(`保留本地备份: ${localBackupPath}`);
        
        // 清理旧的本地备份
        this.cleanupLocalBackups(localBackupDir, githubConfig.backupRetention);
      }
      
      // 删除临时文件
      if (fs.existsSync(backupFile)) {
        fs.unlinkSync(backupFile);
        console.log(`删除临时备份文件: ${backupFile}`);
      }
      
    } catch (error) {
      console.error(`清理临时文件失败: ${error.message}`);
      this.logError('清理临时文件失败', error);
    }
  }

  /**
   * 清理旧的本地备份
   */
  cleanupLocalBackups(backupDir, retentionCount) {
    try {
      // 获取所有备份文件并按创建时间排序
      const files = fs.readdirSync(backupDir)
        .map(file => ({
          name: file,
          path: path.join(backupDir, file),
          mtime: fs.statSync(path.join(backupDir, file)).mtime.getTime()
        }))
        .sort((a, b) => b.mtime - a.mtime); // 最新的在前
      
      // 删除超出保留数量的文件
      if (files.length > retentionCount) {
        const filesToDelete = files.slice(retentionCount);
        
        filesToDelete.forEach(file => {
          fs.unlinkSync(file.path);
          console.log(`删除旧的本地备份: ${file.name}`);
        });
      }
      
    } catch (error) {
      console.error(`清理本地备份失败: ${error.message}`);
      this.logError('清理本地备份失败', error);
    }
  }

  /**
   * 从GitHub恢复备份
   */
  async restoreFromBackup(backupId = null, filePath = null) {
    try {
      // 如果指定了备份ID，查找对应的备份记录
      let backupInfo;
      if (backupId) {
        backupInfo = this.backupHistory.find(b => b.backupId === backupId);
        if (!backupInfo) {
          throw new Error(`未找到备份ID: ${backupId}`);
        }
      }
      
      // 如果指定了文件路径，直接使用
      let restoreFilePath = filePath;
      
      // 如果没有指定文件路径，从GitHub下载
      if (!restoreFilePath && backupInfo) {
        restoreFilePath = await this.downloadFromGitHub(backupInfo, this.tempDir);
      }
      
      if (!restoreFilePath || !fs.existsSync(restoreFilePath)) {
        throw new Error('无法获取备份文件进行恢复');
      }
      
      console.log(`开始从备份恢复: ${restoreFilePath}`);
      
      // 确认恢复操作
      const confirmMessage = `确认要从备份恢复吗？这将覆盖当前的项目文件。\n备份ID: ${backupInfo?.backupId || '未知'}\n备份时间: ${backupInfo?.timestamp || '未知'}\n输入 'yes' 确认: `;
      
      // 在交互式环境中获取确认
      const confirmation = await this.getConfirmation(confirmMessage);
      if (confirmation.toLowerCase() !== 'yes') {
        console.log('恢复操作已取消');
        return { status: 'cancelled' };
      }
      
      // 创建恢复前的备份（安全起见）
      const preRestoreBackup = await this.createPreRestoreBackup();
      
      try {
        // 解压备份文件到项目目录
        await this.extractBackup(restoreFilePath, this.config.basePath);
        
        console.log(`恢复完成! 备份ID: ${backupInfo?.backupId || '未知'}`);
        
        // 记录恢复操作
        this.logRestoreOperation(backupInfo, restoreFilePath);
        
        return {
          status: 'completed',
          backupId: backupInfo?.backupId,
          timestamp: backupInfo?.timestamp,
          preRestoreBackupId: preRestoreBackup?.backupId
        };
        
      } catch (restoreError) {
        console.error('恢复操作失败，尝试回滚...', restoreError.message);
        
        // 如果有预恢复备份，尝试回滚
        if (preRestoreBackup && preRestoreBackup.filePath) {
          try {
            await this.extractBackup(preRestoreBackup.filePath, this.config.basePath);
            console.log('已回滚到恢复前状态');
          } catch (rollbackError) {
            console.error('回滚失败:', rollbackError.message);
          }
        }
        
        throw restoreError;
      }
      
    } catch (error) {
      console.error('从备份恢复失败:', error.message);
      this.logError('恢复备份失败', error);
      throw error;
    }
  }

  /**
   * 从GitHub下载备份
   */
  async downloadFromGitHub(backupInfo, downloadDir) {
    const githubConfig = this.config.backup.github;
    
    try {
      // 解析备份文件名
      const backupFileName = path.basename(backupInfo.backupFile || `mtscos-backup-${backupInfo.timestamp.replace(/[:.]/g, '-')}.${githubConfig.backupFormat}`);
      const downloadPath = path.join(githubConfig.backupPath || 'backups', backupFileName);
      const localFilePath = path.join(downloadDir, backupFileName);
      
      console.log(`从GitHub下载备份: ${downloadPath}`);
      
      // 使用API下载
      const response = await this.octokit.repos.getContent({
        owner: githubConfig.owner,
        repo: githubConfig.repo,
        path: downloadPath,
        branch: githubConfig.branch
      });
      
      // 解码并保存文件
      const content = Buffer.from(response.data.content, 'base64');
      fs.writeFileSync(localFilePath, content);
      
      console.log(`备份文件下载成功: ${localFilePath}`);
      
      // 验证文件哈希
      const downloadedHash = this.calculateFileHash(localFilePath);
      if (backupInfo.fileHash && downloadedHash !== backupInfo.fileHash) {
        throw new Error(`文件完整性验证失败，哈希不匹配: ${downloadedHash} != ${backupInfo.fileHash}`);
      }
      
      return localFilePath;
      
    } catch (error) {
      console.error(`从GitHub下载失败: ${error.message}`);
      // 如果API下载失败，尝试使用git命令
      return await this.downloadWithGitCommand(backupInfo, downloadDir);
    }
  }

  /**
   * 使用Git命令下载备份
   */
  downloadWithGitCommand(backupInfo, downloadDir) {
    const githubConfig = this.config.backup.github;
    
    // 创建临时Git工作目录
    const gitWorkDir = path.join(this.tempDir, `git-restore-${Date.now()}`);
    if (fs.existsSync(gitWorkDir)) {
      this.removeDirectory(gitWorkDir);
    }
    fs.mkdirSync(gitWorkDir, { recursive: true });
    
    try {
      // 解析备份文件名
      const backupFileName = path.basename(backupInfo.backupFile || `mtscos-backup-${backupInfo.timestamp.replace(/[:.]/g, '-')}.${githubConfig.backupFormat}`);
      const gitFilePath = path.join(`${githubConfig.backupPath || 'backups'}`, backupFileName);
      const localFilePath = path.join(downloadDir, backupFileName);
      
      console.log(`使用Git命令下载备份: ${gitFilePath}`);
      
      // 配置Git
      this.executeGitCommand(gitWorkDir, 'init');
      this.executeGitCommand(gitWorkDir, `config user.name "MTSCOS AI Backup"`);
      this.executeGitCommand(gitWorkDir, `config user.email "backup@mtscos-ai.com"`);
      
      // 使用深度为1的克隆，只获取最新版本
      this.executeGitCommand(gitWorkDir, `remote add origin https://${githubConfig.token}@github.com/${githubConfig.owner}/${githubConfig.repo}.git`);
      this.executeGitCommand(gitWorkDir, `fetch --depth 1 origin ${githubConfig.branch}`);
      this.executeGitCommand(gitWorkDir, `checkout origin/${githubConfig.branch} -- "${gitFilePath}"`);
      
      // 复制文件到目标位置
      fs.copyFileSync(path.join(gitWorkDir, gitFilePath), localFilePath);
      
      console.log(`Git命令下载成功: ${localFilePath}`);
      return localFilePath;
      
    } catch (error) {
      console.error(`Git命令下载失败: ${error.message}`);
      throw new Error(`Git命令下载失败: ${error.message}`);
    } finally {
      // 清理临时目录
      this.removeDirectory(gitWorkDir);
    }
  }

  /**
   * 创建恢复前的备份
   */
  async createPreRestoreBackup() {
    try {
      const timestamp = new Date().toISOString();
      const timestampFormatted = timestamp.replace(/[:.]/g, '-');
      const backupFileName = `pre-restore-${timestampFormatted}.${this.config.backup.github.backupFormat}`;
      const backupFilePath = path.join(this.tempDir, backupFileName);
      
      console.log('创建恢复前的安全备份...');
      
      // 根据备份格式创建压缩包
      if (this.config.backup.github.backupFormat === 'zip') {
        await this.createZipArchive(this.config.basePath, backupFilePath, this.config.backup.github.ignorePatterns);
      } else {
        await this.createTarArchive(this.config.basePath, backupFilePath, this.config.backup.github.ignorePatterns);
      }
      
      console.log(`恢复前备份已创建: ${backupFilePath}`);
      
      return {
        backupId: `pre_restore_${Date.now()}`,
        timestamp: timestamp,
        filePath: backupFilePath
      };
      
    } catch (error) {
      console.error('创建恢复前备份失败:', error.message);
      this.logError('创建恢复前备份失败', error);
      return null;
    }
  }

  /**
   * 解压备份文件
   */
  async extractBackup(backupFile, targetDir) {
    try {
      const fileExtension = path.extname(backupFile).toLowerCase();
      
      if (fileExtension === '.zip') {
        // 解压ZIP文件
        await this.extractZip(backupFile, targetDir);
      } else if (fileExtension === '.gz' && backupFile.endsWith('.tar.gz')) {
        // 解压TAR.GZ文件
        await this.extractTarGz(backupFile, targetDir);
      } else {
        throw new Error(`不支持的备份文件格式: ${fileExtension}`);
      }
      
    } catch (error) {
      console.error('解压备份文件失败:', error.message);
      throw new Error(`解压备份文件失败: ${error.message}`);
    }
  }

  /**
   * 解压ZIP文件
   */
  extractZip(zipFile, targetDir) {
    return new Promise((resolve, reject) => {
      try {
        console.log(`解压ZIP文件到: ${targetDir}`);
        execSync(`unzip "${zipFile}" -d "${targetDir}"`, { stdio: 'inherit' });
        resolve();
      } catch (error) {
        reject(new Error(`解压ZIP文件失败: ${error.message}`));
      }
    });
  }

  /**
   * 解压TAR.GZ文件
   */
  extractTarGz(tarGzFile, targetDir) {
    return new Promise((resolve, reject) => {
      try {
        console.log(`解压TAR.GZ文件到: ${targetDir}`);
        execSync(`tar -xzf "${tarGzFile}" -C "${targetDir}"`, { stdio: 'inherit' });
        resolve();
      } catch (error) {
        reject(new Error(`解压TAR.GZ文件失败: ${error.message}`));
      }
    });
  }

  /**
   * 获取确认
   */
  getConfirmation(message) {
    return new Promise((resolve) => {
      // 在非交互式环境中，默认拒绝
      if (!process.stdin.isTTY) {
        console.log(message);
        console.log('非交互式环境，自动拒绝操作');
        resolve('no');
        return;
      }
      
      // 在交互式环境中，获取用户输入
      process.stdout.write(message);
      process.stdin.resume();
      process.stdin.once('data', (data) => {
        process.stdin.pause();
        resolve(data.toString().trim());
      });
    });
  }

  /**
   * 记录恢复操作
   */
  logRestoreOperation(backupInfo, restoreFilePath) {
    try {
      const restoreLog = {
        restoreId: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        backupId: backupInfo?.backupId,
        backupTimestamp: backupInfo?.timestamp,
        restoreFilePath: restoreFilePath,
        restoredFiles: [] // 可以在这里添加恢复的文件列表
      };
      
      const logFilePath = path.join(this.logDir, 'restore-operations.log');
      fs.appendFileSync(logFilePath, JSON.stringify(restoreLog) + '\n', 'utf8');
      
      console.log(`恢复操作已记录: ${restoreLog.restoreId}`);
      
    } catch (error) {
      console.error('记录恢复操作失败:', error.message);
    }
  }

  /**
   * 发送备份完成通知
   */
  notifyBackupComplete(backupInfo) {
    try {
      const notification = {
        type: 'backup_complete',
        timestamp: new Date().toISOString(),
        backupId: backupInfo.backupId,
        duration: this.formatDuration(backupInfo.duration),
        fileSize: this.formatFileSize(backupInfo.fileSize),
        commitHash: backupInfo.commitHash
      };
      
      // 这里可以实现不同的通知机制，如邮件、消息等
      console.log('\n📤 备份完成通知:');
      console.log(`  备份ID: ${notification.backupId}`);
      console.log(`  耗时: ${notification.duration}`);
      console.log(`  文件大小: ${notification.fileSize}`);
      console.log(`  提交哈希: ${notification.commitHash}`);
      console.log('\n');
      
      // 写入通知日志
      this.writeNotificationLog(notification);
      
    } catch (error) {
      console.error('发送备份完成通知失败:', error.message);
    }
  }

  /**
   * 发送备份失败通知
   */
  notifyBackupFailed(backupInfo) {
    try {
      const notification = {
        type: 'backup_failed',
        timestamp: new Date().toISOString(),
        backupId: backupInfo.backupId,
        duration: this.formatDuration(backupInfo.duration),
        errors: backupInfo.errors
      };
      
      // 这里可以实现不同的通知机制，如邮件、消息等
      console.error('\n❌ 备份失败通知:');
      console.error(`  备份ID: ${notification.backupId}`);
      console.error(`  耗时: ${notification.duration}`);
      console.error(`  错误: ${notification.errors.join(', ')}`);
      console.error('\n');
      
      // 写入通知日志
      this.writeNotificationLog(notification);
      
    } catch (error) {
      console.error('发送备份失败通知失败:', error.message);
    }
  }

  /**
   * 写入通知日志
   */
  writeNotificationLog(notification) {
    try {
      const logFilePath = path.join(this.logDir, 'backup-notifications.log');
      fs.appendFileSync(logFilePath, JSON.stringify(notification) + '\n', 'utf8');
    } catch (error) {
      console.error('写入通知日志失败:', error.message);
    }
  }

  /**
   * 记录错误日志
   */
  logError(message, error) {
    try {
      const logEntry = {
        timestamp: new Date().toISOString(),
        message: message,
        error: error.message,
        stack: error.stack,
        backupId: this.currentBackup?.backupId
      };
      
      const errorLogPath = path.join(this.logDir, 'backup-errors.log');
      fs.appendFileSync(errorLogPath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (err) {
      console.error('写入错误日志失败:', err.message);
    }
  }

  /**
   * 获取备份状态
   */
  getBackupStatus() {
    return {
      initialized: this.isInitialized,
      lastBackup: this.lastBackupTime,
      currentBackup: this.currentBackup,
      scheduledJobs: Array.from(this.scheduledJobs.keys()),
      backupHistoryCount: this.backupHistory.length,
      githubConfig: {
        repo: this.config.backup.github.repo,
        branch: this.config.backup.github.branch,
        backupFormat: this.config.backup.github.backupFormat
      }
    };
  }

  /**
   * 获取备份历史
   */
  getBackupHistory(limit = 10) {
    return this.backupHistory.slice(-limit).reverse();
  }

  /**
   * 停止所有备份任务
   */
  stop() {
    // 清除定时任务
    this.clearScheduledJobs();
    
    // 如果有正在进行的备份，可以在这里添加逻辑来优雅地停止
    console.log('GitHub备份管理器已停止');
  }

  /**
   * 删除目录
   */
  removeDirectory(dirPath) {
    if (fs.existsSync(dirPath)) {
      fs.readdirSync(dirPath).forEach((file) => {
        const curPath = path.join(dirPath, file);
        if (fs.lstatSync(curPath).isDirectory()) {
          this.removeDirectory(curPath);
        } else {
          fs.unlinkSync(curPath);
        }
      });
      fs.rmdirSync(dirPath);
    }
  }

  /**
   * 格式化持续时间
   */
  formatDuration(ms) {
    const seconds = Math.floor((ms / 1000) % 60);
    const minutes = Math.floor((ms / (1000 * 60)) % 60);
    const hours = Math.floor((ms / (1000 * 60 * 60)) % 24);
    
    if (hours > 0) {
      return `${hours}时${minutes}分${seconds}秒`;
    } else if (minutes > 0) {
      return `${minutes}分${seconds}秒`;
    } else {
      return `${seconds}秒`;
    }
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  try {
    const backupManager = new GitHubBackupManager(configPath);
    
    // 显示帮助信息
    const showHelp = () => {
      console.log('MTSCOS AI GitHub备份管理器');
      console.log('用法: node github-backup-manager.js [命令]');
      console.log('命令:');
      console.log('  backup       立即执行备份');
      console.log('  status       显示备份状态');
      console.log('  history      显示备份历史');
      console.log('  restore <id> 从指定备份ID恢复');
      console.log('  schedule     显示备份计划');
      console.log('  help         显示帮助信息');
    };
    
    // 处理命令行参数
    const args = process.argv.slice(2);
    
    if (args.length === 0 || args[0] === 'help') {
      showHelp();
    } else if (args[0] === 'backup') {
      // 立即执行备份
      console.log('执行手动备份...');
      backupManager.performBackup(false)
        .then(backupInfo => {
          console.log('备份完成:', backupInfo);
          process.exit(0);
        })
        .catch(error => {
          console.error('备份失败:', error);
          process.exit(1);
        });
    } else if (args[0] === 'status') {
      // 显示备份状态
      const status = backupManager.getBackupStatus();
      console.log('备份状态:');
      console.log(JSON.stringify(status, null, 2));
    } else if (args[0] === 'history') {
      // 显示备份历史
      const history = backupManager.getBackupHistory(10);
      console.log('最近10次备份历史:');
      console.log(JSON.stringify(history, null, 2));
    } else if (args[0] === 'restore' && args.length > 1) {
      // 从指定备份ID恢复
      console.log(`从备份ID ${args[1]} 恢复...`);
      backupManager.restoreFromBackup(args[1])
        .then(result => {
          console.log('恢复完成:', result);
          process.exit(0);
        })
        .catch(error => {
          console.error('恢复失败:', error);
          process.exit(1);
        });
    } else if (args[0] === 'schedule') {
      // 显示备份计划
      console.log('备份计划:');
      backupManager.scheduledJobs.forEach((info, name) => {
        console.log(`- ${name}: ${info.cronExpression} (${info.enabled ? '启用' : '禁用'})`);
      });
    } else {
      console.log(`未知命令: ${args[0]}`);
      showHelp();
    }
    
    // 处理信号
    process.on('SIGINT', () => {
      console.log('收到终止信号，正在停止备份管理器...');
      backupManager.stop();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('启动GitHub备份管理器失败:', error.message);
    process.exit(1);
  }
}

module.exports = GitHubBackupManager;