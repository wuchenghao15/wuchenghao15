const path = require('path');
const fs = require('fs').promises;

// 动态导入 node-llama-cpp
let LlamaModel, LlamaChatSession;

class LocalDeepSeekModel {
    constructor(config) {
        this.config = config;
        this.model = null;
        this.session = null;
        this.isInitialized = false;
        this.modelPath = config.localModel?.modelPath || './models/deepseek-coder-6.7b-base.Q4_K_M.gguf';
        this.dependenciesLoaded = false;
    }

    async loadDependencies() {
        if (this.dependenciesLoaded) return true;
        
        try {
            // 使用动态导入来解决ESM问题
            const llamaCpp = await import('node-llama-cpp');
            LlamaModel = llamaCpp.LlamaModel;
            LlamaChatSession = llamaCpp.LlamaChatSession;
            this.dependenciesLoaded = true;
            return true;
        } catch (error) {
            console.warn('node-llama-cpp 依赖加载失败:', error.message);
            return false;
        }
    }

    async initialize() {
        try {
            console.log('正在初始化本地DeepSeek模型...');
            
            // 加载依赖
            const depsLoaded = await this.loadDependencies();
            if (!depsLoaded) {
                throw new Error('无法加载 node-llama-cpp 依赖，请确保已正确安装');
            }
            
            // 检查模型文件是否存在
            const modelExists = await this.checkModelFile();
            if (!modelExists) {
                console.warn(`模型文件不存在: ${this.modelPath}`);
                console.log('提示: 请下载模型文件到指定位置，或使用云端API模式');
                this.isInitialized = false;
                return false;
            }

            // 创建模型目录
            const modelDir = path.dirname(this.modelPath);
            await fs.mkdir(modelDir, { recursive: true });

            // 初始化模型
            this.model = new LlamaModel({
                modelPath: this.modelPath,
                contextLength: this.config.localModel?.contextLength || 4096,
                gpuLayers: this.config.localModel?.gpuLayers || 0,
                threads: this.config.localModel?.threads || 4
            });

            // 创建聊天会话
            this.session = new LlamaChatSession({
                model: this.model,
                systemPrompt: '你是一个专业的AI助手，擅长编程、分析和解答问题。'
            });

            this.isInitialized = true;
            console.log('本地DeepSeek模型初始化成功');
            return true;

        } catch (error) {
            console.error(`[local-deepseek-model.js] 本地模型初始化失败:, error`);
            this.isInitialized = false;
            return false;
        }
    }

    async checkModelFile() {
        try {
            await fs.access(this.modelPath);
            return true;
        } catch {
            return false;
        }
    }

    async downloadModel() {
        console.log('开始下载DeepSeek模型...');
        console.log('注意: 模型文件较大(约3.8GB)，请耐心等待...');
        
        // 这里可以添加模型下载逻辑
        // 由于模型文件较大，建议用户手动下载
        console.log('请手动下载模型文件到:', this.modelPath);
        console.log('下载地址: https://huggingface.co/TheBloke/deepseek-coder-6.7B-base-GGUF');
        
        return false;
    }

    async generateResponse(prompt, options = {}) {
        if (!this.isInitialized) {
            throw new Error('模型未初始化');
        }

        try {
            const maxTokens = options.maxTokens || this.config.deepseek?.maxTokens || 2048;
            const temperature = options.temperature || this.config.deepseek?.temperature || 0.7;

            const response = await this.session.prompt(prompt, {
                maxTokens: maxTokens,
                temperature: temperature
            });

            return {
                response: response,
                model: 'deepseek-coder-6.7b-local',
                usage: {
                    prompt_tokens: prompt.length,
                    completion_tokens: response.length,
                    total_tokens: prompt.length + response.length
                }
            };

        } catch (error) {
            console.error(`[local-deepseek-model.js] 生成响应失败:, error`);
            throw error;
        }
    }

    async isReady() {
        return this.isInitialized && await this.checkModelFile();
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            modelPath: this.modelPath,
            modelExists: false, // 需要异步检查
            config: this.config.localModel
        };
    }

    async cleanup() {
        if (this.session) {
            // 清理会话资源
            this.session = null;
        }
        if (this.model) {
            // 清理模型资源
            this.model = null;
        }
        this.isInitialized = false;
        console.log('本地模型资源已清理');
    }
}

module.exports = LocalDeepSeekModel;