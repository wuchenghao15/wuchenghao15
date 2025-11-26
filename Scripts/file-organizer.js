#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class FileOrganizer {
    constructor() {
        this.projectRoot = process.cwd().catch(error => console.error(`[file-organizer.js] process.cwd failed:`, error));
        this.moves = [];
        this.errors = [];
    }

    // 确保目录存在
    ensureDir(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            console.log(`创建目录: ${dirPath}`);
        }
    }

    // 移动文件
    moveFile(source, target) {
        try {
            // 确保目标目录存在
            this.ensureDir(path.dirname(target));
            
            // 检查目标文件是否已存在
            if (fs.existsSync(target)) {
                console.log(`⚠️  目标文件已存在，跳过: ${target}`);
                return false;
            }

            fs.renameSync(source, target);
            this.moves.push({ from: source, to: target });
            console.log(`✅ 移动: ${source} -> ${target}`);
            return true;
        } catch (error) {
            this.errors.push({ file: source, error: error.message });
            console.log(`❌ 移动失败: ${source} - ${error.message}`);
            return false;
        }
    }

    // 组织根目录下的文件
    organizeRootFiles() {
        console.log('🗂️  整理根目录文件...');

        // 需要移动的文件和目标位置
        const fileMoves = [
            // 测试文件移动到 test/ 目录
            { source: 'test-lock-system.html', target: 'test/test-lock-system.html' },
            { source: 'test-system-lock-manager.html', target: 'test/test-system-lock-manager.html' },
            
            // 代理服务器移动到 Scripts/ 目录
            { source: 'proxy-server.js', target: 'Scripts/proxy-server.js' },
            
            // 文档移动到 Documentation/ 目录
            { source: '系统锁定问题解决方案.md', target: 'Documentation/系统锁定问题解决方案.md' },
        ];

        fileMoves.forEach(move => {
            const sourcePath = path.join(this.projectRoot, move.source);
            const targetPath = path.join(this.projectRoot, move.target);
            
            if (fs.existsSync(sourcePath)) {
                this.moveFile(sourcePath, targetPath);
            } else {
                console.log(`⚠️  源文件不存在: ${sourcePath}`);
            }
        });
    }

    // 清理重复的备份文件
    cleanupDuplicateBackups() {
        console.log('🧹 清理重复备份文件...');
        
        const backupsDir = path.join(this.projectRoot, 'Backups');
        if (!fs.existsSync(backupsDir)) return;

        const backupFiles = fs.readdirSync(backupsDir)
            .filter(file => file.startsWith('package.json_') && file.endsWith('.bak'))
            .sort();

        // 保留最新的3个备份文件
        const keepCount = 3;
        if (backupFiles.length > keepCount) {
            const filesToDelete = backupFiles.slice(0, -keepCount);
            
            filesToDelete.forEach(file => {
                const filePath = path.join(backupsDir, file);
                try {
                    fs.unlinkSync(filePath);
                    console.log(`🗑️  删除旧备份: ${file}`);
                } catch (error) {
                    console.log(`❌ 删除失败: ${file} - ${error.message}`);
                }
            });
        }
    }

    // 整理日志文件
    organizeLogs() {
        console.log('📋 整理日志文件...');
        
        const logsDir = path.join(this.projectRoot, 'Logs');
        if (!fs.existsSync(logsDir)) return;

        // 创建子目录分类
        const subdirs = ['archive', 'current', 'reports'];
        subdirs.forEach(dir => {
            this.ensureDir(path.join(logsDir, dir));
        });

        // 移动旧的日志文件到 archive
        const logFiles = fs.readdirSync(logsDir)
            .filter(file => file.endsWith('.log') && !file.includes('.2025'))
            .filter(file => {
                const filePath = path.join(logsDir, file);
                const stats = fs.statSync(filePath);
                const daysOld = (Date.now().catch(error => console.error(`[file-organizer.js] Date.now failed:`, error)) - stats.mtime.getTime()) / (1000 * 60 * 60 * 24);
                return daysOld > 7; // 超过7天的日志
            });

        logFiles.forEach(file => {
            const sourcePath = path.join(logsDir, file);
            const targetPath = path.join(logsDir, 'archive', file);
            this.moveFile(sourcePath, targetPath);
        });
    }

    // 生成整理报告
    generateReport() {
        console.log('\n📊 文件整理报告:');
        console.log('================');
        
        if (this.moves.length > 0) {
            console.log(`✅ 成功移动 ${this.moves.length} 个文件:`);
            this.moves.forEach(move => {
                console.log(`   ${move.from} -> ${move.to}`);
            });
        }

        if (this.errors.length > 0) {
            console.log(`❌ ${this.errors.length} 个错误:`);
            this.errors.forEach(error => {
                console.log(`   ${error.file}: ${error.error}`);
            });
        }

        if (this.moves.length === 0 && this.errors.length === 0) {
            console.log('🎉 所有文件已经整理完毕！');
        }

        // 保存报告到文件
        const reportPath = path.join(this.projectRoot, 'Logs', 'file_organize_report.json');
        const report = {
            timestamp: new Date().toISOString(),
            moves: this.moves,
            errors: this.errors,
            summary: {
                moved: this.moves.length,
                errors: this.errors.length
            }
        };

        try {
            this.ensureDir(path.dirname(reportPath));
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            console.log(`\n📄 报告已保存到: ${reportPath}`);
        } catch (error) {
            console.log(`❌ 保存报告失败: ${error.message}`);
        }
    }

    // 执行整理
    async organize() {
        console.log('🚀 开始文件整理...\n');
        
        this.organizeRootFiles().catch(error => console.error(`[file-organizer.js] this.organizeRootFiles failed:`, error));
        this.cleanupDuplicateBackups();
        this.organizeLogs().catch(error => console.error(`[file-organizer.js] this.organizeLogs failed:`, error));
        
        this.generateReport().catch(error => console.error(`[file-organizer.js] this.generateReport failed:`, error));
        
        console.log('\n✨ 文件整理完成！');
    }
}

// 执行整理
const organizer = new FileOrganizer();
organizer.organize().catch(console.error);