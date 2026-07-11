/**
 * MTSCOS AI 系统版本管理模块
 * 功能：读取系统版本配置，绑定版本数据到页面元素
 */
class SystemVersionManager {
    constructor() {
        this.versionConfig = null;
        this.versionElement = null;
        this.versionDisplayElement = null;
        this.init();
    }
    async init() {
        this.versionElement = document.getElementById('project-version');
        this.versionDisplayElement = document.getElementById('version-display');
        await this.loadVersionConfig();
        this.bindVersionData();
        this.setupAutoRefresh();
    }
    async loadVersionConfig() {
        try {
            const response = await fetch('/assets/config/system-version.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.versionConfig = await response.json();
            console.log('系统版本配置加载成功:', this.versionConfig);
        } catch (error) {
            console.error('加载版本配置失败:', error);
            this.versionConfig = this.getDefaultConfig();
        }
    }
    getDefaultConfig() {
        return {
            system: {
                name: 'MTSCOS AI 智能管理系统',
                version: '4.3.0',
                build: '2026.06.18',
                codename: '智能教育版'
            },
            features: {
                ai_brain: { enabled: true, version: '2.1.0' },
                auto_upgrade: { enabled: true, version: '1.8.0' },
                cloud_integration: { enabled: true, version: '1.5.0' },
                service_monitor: { enabled: true, version: '2.0.0' },
                teaching_system: { enabled: true, version: '1.0.0' }
            },
            status: {
                stable: true,
                beta: false,
                alpha: false
            }
        };
    }
    bindVersionData() {
        if (!this.versionConfig) {
            console.warn('版本配置未加载');
            return;
        }
        const system = this.versionConfig.system;
        const features = this.versionConfig.features;
        const status = this.versionConfig.status;
        // 绑定版本信息到导航栏元素
        if (this.versionElement) {
            const statusBadge = status.stable ? '稳定版' : (status.beta ? '测试版' : '开发版');
            this.versionElement.textContent = `版本: v${system.version} (${statusBadge})`;
            this.versionElement.setAttribute('data-version', system.version);
            this.versionElement.setAttribute('data-build', system.build);
            this.versionElement.setAttribute('data-codename', system.codename);
        }
        // 绑定版本信息到卡片显示元素
        if (this.versionDisplayElement) {
            const statusBadge = status.stable ? '稳定版' : (status.beta ? '测试版' : '开发版');
            this.versionDisplayElement.textContent = `v${system.version} - ${system.codename}`;
            this.versionDisplayElement.setAttribute('data-version', system.version);
        }
        // 更新页面标题
        document.title = `${system.name} - v${system.version}`;
        // 触发版本加载完成事件
        document.dispatchEvent(new CustomEvent('version-loaded', {
            detail: {
                version: system.version,
                build: system.build,
                codename: system.codename,
                features: features,
                status: status
            }
        }));
        console.log('版本数据绑定完成');
    }
    setupAutoRefresh() {
        // 每5分钟自动刷新版本配置
        setInterval(async () => {
            await this.loadVersionConfig();
            this.bindVersionData();
        }, 5 * 60 * 1000);
    }
    getVersion() {
        return this.versionConfig?.system?.version || '未知';
    }
    getBuild() {
        return this.versionConfig?.system?.build || '未知';
    }
    getCodename() {
        return this.versionConfig?.system?.codename || '未知';
    }
    getFeatures() {
        return this.versionConfig?.features || {};
    }
    getStatus() {
        return this.versionConfig?.status || {};
    }
    getFullVersionInfo() {
        if (!this.versionConfig) return null;
        return {
            version: this.getVersion(),
            build: this.getBuild(),
            codename: this.getCodename(),
            features: this.getFeatures(),
            status: this.getStatus(),
            fullVersion: `v${this.getVersion()} (${this.getCodename()})`
        };
    }
    // 检查是否有新版本
    async checkForUpdates() {
        try {
            const response = await fetch('/assets/config/system-version.json');
            const newConfig = await response.json();
            if (newConfig.system.version !== this.versionConfig.system.version) {
                console.log('发现新版本:', newConfig.system.version);
                document.dispatchEvent(new CustomEvent('version-update-available', {
                    detail: {
                        currentVersion: this.versionConfig.system.version,
                        newVersion: newConfig.system.version,
                        releaseNotes: newConfig.status.release_notes
                    }
                }));
                return true;
            }
            return false;
        } catch (error) {
            console.error('检查更新失败:', error);
            return false;
        }
    }
}
// 初始化版本管理器
document.addEventListener('DOMContentLoaded', () => {
    window.systemVersionManager = new SystemVersionManager();
});
// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemVersionManager;
}