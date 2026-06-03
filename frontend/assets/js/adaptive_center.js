/**
 * MTSCOS 系统自适应管理中心
 * 实现系统的自我适应、自我拓展和自适应升级功能
 */

class AdaptiveSystemManager {
    constructor() {
        this.core = {
            name: "MTSCOS 自适应核心",
            version: "1.0.0",
            status: "运行中",
            tier: 1,
            experience: 0
        };
        
        this.capabilities = {
            nlp: { name: "自然语言处理", level: 3, experience: 250 },
            vision: { name: "图像识别", level: 2, experience: 150 },
            data: { name: "数据分析", level: 4, experience: 380 },
            optimize: { name: "系统优化", level: 2, experience: 180 }
        };
        
        this.modules = {
            compute: { nodes: 3, status: "active" },
            storage: { nodes: 2, status: "active" },
            network: { nodes: 2, status: "active" },
            security: { nodes: 1, status: "active" }
        };
        
        this.metrics = {
            cpu: 45,
            memory: 62,
            responseTime: 125,
            accuracy: 87
        };
        
        this.adaptationProgress = 0;
        this.logs = [];
        this.learningHistory = [];
        
        this.init();
    }
    
    init() {
        this.addLog("系统自适应管理中心已初始化");
        this.updateDisplay();
        this.startMonitoring();
        this.simulateLearning();
        
        document.getElementById('upgradeBtn').addEventListener('click', () => this.performUpgrade());
        document.getElementById('expandBtn').addEventListener('click', () => this.performExpansion());
    }
    
    addLog(message) {
        const timestamp = new Date().toLocaleString('zh-CN');
        this.logs.unshift({ timestamp, message });
        if (this.logs.length > 50) this.logs.pop();
        this.updateLogDisplay();
    }
    
    updateLogDisplay() {
        const container = document.getElementById('logContainer');
        container.innerHTML = this.logs.map(log => `
            <div class="log-item">
                <div class="log-timestamp">${log.timestamp}</div>
                <div>${log.message}</div>
            </div>
        `).join('');
    }
    
    updateDisplay() {
        // 更新能力等级
        document.getElementById('nlpLevel').textContent = this.capabilities.nlp.level;
        document.getElementById('visionLevel').textContent = this.capabilities.vision.level;
        document.getElementById('dataLevel').textContent = this.capabilities.data.level;
        document.getElementById('optimizeLevel').textContent = this.capabilities.optimize.level;
        
        // 更新性能指标
        document.getElementById('cpuUsage').textContent = this.metrics.cpu + '%';
        document.getElementById('memoryUsage').textContent = this.metrics.memory + '%';
        document.getElementById('responseTime').textContent = this.metrics.responseTime + 'ms';
        document.getElementById('accuracy').textContent = this.metrics.accuracy + '%';
        
        // 更新适应度
        document.getElementById('adaptationProgress').textContent = this.adaptationProgress + '%';
        document.getElementById('adaptationBar').style.width = this.adaptationProgress + '%';
    }
    
    performUpgrade() {
        this.addLog("开始执行AI能力升级...");
        
        // 随机选择一个能力进行升级
        const capabilityKeys = Object.keys(this.capabilities);
        const randomKey = capabilityKeys[Math.floor(Math.random() * capabilityKeys.length)];
        const capability = this.capabilities[randomKey];
        
        capability.level += 1;
        capability.experience += 50;
        
        this.addLog(`${capability.name} 已升级到等级 ${capability.level}`);
        
        // 更新AI状态
        document.getElementById('aiStatus').textContent = `${capability.name}已升级`;
        
        // 增加适应度
        this.adaptationProgress = Math.min(100, this.adaptationProgress + 10);
        this.updateDisplay();
        
        // 添加学习历史
        this.addLearningHistory(`${capability.name} 能力提升`);
        
        // 模拟优化性能
        this.metrics.accuracy = Math.min(99, this.metrics.accuracy + 2);
        this.updateDisplay();
    }
    
    performExpansion() {
        this.addLog("开始执行系统自我拓展...");
        
        // 添加新的计算节点
        const moduleTypes = ['compute', 'storage', 'network', 'security'];
        const randomModule = moduleTypes[Math.floor(Math.random() * moduleTypes.length)];
        
        this.modules[randomModule].nodes += 1;
        
        this.addLog(`已添加新的${randomModule}节点`);
        
        // 增加适应度
        this.adaptationProgress = Math.min(100, this.adaptationProgress + 15);
        this.updateDisplay();
        
        // 添加学习历史
        this.addLearningHistory(`系统${randomModule}模块已扩展`);
        
        // 模拟性能提升
        this.metrics.responseTime = Math.max(50, this.metrics.responseTime - 10);
        this.updateDisplay();
    }
    
    addLearningHistory(action) {
        const timestamp = new Date().toLocaleString('zh-CN');
        this.learningHistory.unshift({ timestamp, action });
        if (this.learningHistory.length > 20) this.learningHistory.pop();
        this.updateLearningDisplay();
    }
    
    updateLearningDisplay() {
        const container = document.getElementById('learningHistory');
        container.innerHTML = this.learningHistory.map(item => `
            <div class="log-item">
                <div class="log-timestamp">${item.timestamp}</div>
                <div>${item.action}</div>
            </div>
        `).join('');
    }
    
    startMonitoring() {
        // 定期更新性能指标
        setInterval(() => {
            this.metrics.cpu = Math.max(20, Math.min(80, this.metrics.cpu + (Math.random() - 0.5) * 10));
            this.metrics.memory = Math.max(30, Math.min(85, this.metrics.memory + (Math.random() - 0.5) * 5));
            this.updateDisplay();
        }, 5000);
        
        // 定期增加适应度
        setInterval(() => {
            if (this.adaptationProgress < 100) {
                this.adaptationProgress = Math.min(100, this.adaptationProgress + 1);
                this.updateDisplay();
            }
        }, 10000);
    }
    
    simulateLearning() {
        // 模拟AI学习
        setInterval(() => {
            const learningTopics = [
                "完成模式识别训练",
                "优化决策算法",
                "更新知识图谱",
                "强化学习完成",
                "数据分析模型已更新"
            ];
            
            const randomTopic = learningTopics[Math.floor(Math.random() * learningTopics.length)];
            this.addLearningHistory(randomTopic);
            this.addLog(randomTopic);
            
            // 增加经验
            this.core.experience += 10;
            
            // 检查是否升级
            if (this.core.experience >= this.core.tier * 100) {
                this.core.tier += 1;
                this.addLog(`AI核心已升级到 tier ${this.core.tier}`);
            }
        }, 15000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.adaptiveManager = new AdaptiveSystemManager();
});