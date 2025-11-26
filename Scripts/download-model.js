#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const https = require('https');
const { createWriteStream } = require('fs');

class ModelDownloader {
    constructor() {
        this.modelsDir = path.join(__dirname, '../models');
        this.downloads = {
            'deepseek-coder-6.7b-base.Q4_K_M.gguf': {
                url: 'https://huggingface.co/TheBloke/deepseek-coder-6.7B-base-GGUF/resolve/main/deepseek-coder-6.7b-base.Q4_K_M.gguf',
                description: 'DeepSeek Coder 6.7B Base (量化版，约3.8GB)',
                size: '3.8GB'
            },
            'deepseek-coder-1.3b-base.Q4_K_M.gguf': {
                url: 'https://huggingface.co/TheBloke/deepseek-coder-1.3B-base-GGUF/resolve/main/deepseek-coder-1.3b-base.Q4_K_M.gguf',
                description: 'DeepSeek Coder 1.3B Base (量化版，约770MB)',
                size: '770MB'
            }
        };
    }

    async init() {
        try {
            await fs.mkdir(this.modelsDir, { recursive: true });
            console.log('📁 模型目录已创建:', this.modelsDir);
        } catch (error) {
            console.error(`[download-model.js] 创建模型目录失败:, error`);
        }
    }

    async listModels() {
        console.log('\n🤖 可用的DeepSeek模型:');
        console.log('================================');
        
        for (const [filename, info] of Object.entries(this.downloads)) {
            const exists = await this.checkModelExists(filename);
            const status = exists ? '✅ 已下载' : '⬇️ 待下载';
            console.log(`\n📦 ${filename}`);
            console.log(`   ${info.description}`);
            console.log(`   大小: ${info.size}`);
            console.log(`   状态: ${status}`);
            console.log(`   下载链接: ${info.url}`);
        }
    }

    async checkModelExists(filename) {
        try {
            await fs.access(path.join(this.modelsDir, filename));
            return true;
        } catch {
            return false;
        }
    }

    async downloadModel(filename) {
        const modelInfo = this.downloads[filename];
        if (!modelInfo) {
            console.error(`[download-model.js] ❌ 未找到模型:, filename`);
            return false;
        }

        const filePath = path.join(this.modelsDir, filename);
        
        // 检查是否已存在
        if (await this.checkModelExists(filename)) {
            console.log('✅ 模型已存在:', filePath);
            return true;
        }

        console.log(`\n🚀 开始下载: ${filename}`);
        console.log(`📝 描述: ${modelInfo.description}`);
        console.log(`📊 大小: ${modelInfo.size}`);
        console.log(`🔗 链接: ${modelInfo.url}`);
        console.log('\n⏳ 下载中，请耐心等待...');

        try {
            await this.downloadFile(modelInfo.url, filePath);
            console.log('\n✅ 下载完成!');
            console.log('📁 保存位置:', filePath);
            return true;
        } catch (error) {
            console.error(`[download-model.js] \n❌ 下载失败:, error.message`);
            return false;
        }
    }

    async downloadFile(url, filePath) {
        return new Promise((resolve, reject) => {
            const file = createWriteStream(filePath);
            let downloadedBytes = 0;
            let totalBytes = 0;

            const request = https.get(url, (response) => {
                if (response.statusCode !== 200) {
                    reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
                    return;
                }

                totalBytes = parseInt(response.headers['content-length'] || '0');
                
                response.on('data', (chunk) => {
                    downloadedBytes += chunk.length;
                    if (totalBytes > 0) {
                        const progress = ((downloadedBytes / totalBytes) * 100).toFixed(1);
                        process.stdout.write(`\r📊 进度: ${progress}% (${this.formatBytes(downloadedBytes)}/${this.formatBytes(totalBytes)})`);
                    }
                });

                response.pipe(file);
            });

            file.on('finish', () => {
                file.close().catch(error => console.error(`[download-model.js] file.close failed:`, error));
                console.log(); // 换行
                resolve();
            });

            file.on('error', (error) => {
                fs.unlink(filePath).catch(() => {}); // 删除部分下载的文件
                reject(error);
            });

            request.on('error', (error) => {
                fs.unlink(filePath).catch(() => {});
                reject(error);
            });

            request.setTimeout(300000, () => { // 5分钟超时
                request.destroy().catch(error => console.error(`[download-model.js] request.destroy failed:`, error));
                reject(new Error('下载超时'));
            });
        });
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async updateConfig(filename) {
        const configPath = path.join(__dirname, '../Configs/deepseek_config.json');
        
        try {
            const configData = await fs.readFile(configPath, 'utf8');
            const config = JSON.parse(configData);
            
            config.localModel.modelPath = `./models/${filename}`;
            config.localModel.enabled = true;
            
            await fs.writeFile(configPath, JSON.stringify(config, null, 2));
            console.log('✅ 配置文件已更新');
            console.log('📝 模型路径:', config.localModel.modelPath);
        } catch (error) {
            console.error(`[download-model.js] ❌ 更新配置文件失败:, error`);
        }
    }
}

// 命令行接口
async function main() {
    const downloader = new ModelDownloader();
    await downloader.init();

    const args = process.argv.slice(2);
    const command = args[0];

    switch (command) {
        case 'list':
            await downloader.listModels();
            break;
            
        case 'download':
            const modelName = args[1];
            if (!modelName) {
                console.error(`[download-model.js] ❌ 请指定要下载的模型名称`);
                console.log('💡 使用 "list" 查看可用模型');
                process.exit(1);
            }
            
            const success = await downloader.downloadModel(modelName);
            if (success) {
                await downloader.updateConfig(modelName);
            }
            break;
            
        case 'setup':
            console.log('🚀 DeepSeek 本地模型设置向导');
            console.log('================================');
            await downloader.listModels();
            console.log('\n💡 推荐下载 "deepseek-coder-1.3b-base.Q4_K_M.gguf" 开始使用');
            console.log('🔧 使用命令: node scripts/download-model.js download <模型名>');
            break;
            
        default:
            console.log('🤖 DeepSeek 模型下载工具');
            console.log('============================');
            console.log('用法:');
            console.log('  node scripts/download-model.js list              # 列出可用模型');
            console.log('  node scripts/download-model.js download <模型名>   # 下载指定模型');
            console.log('  node scripts/download-model.js setup              # 运行设置向导');
            break;
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = ModelDownloader;