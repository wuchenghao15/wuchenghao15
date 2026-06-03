import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PlatformAdapter from '../adapters/PlatformAdapter';

class VersionService {
  constructor() {
    this.currentVersion = '2.0.0';
    this.updateCheckInterval = null;
  }

  getCurrentVersion() {
    return this.currentVersion;
  }

  async checkForUpdates() {
    try {
      const response = await axios.get(
        `${PlatformAdapter.getAPIEndpoint()}/api/version/check`,
        {
          params: {
            current_version: this.currentVersion,
            platform: PlatformAdapter.getPlatform(),
          },
          timeout: 15000,
        }
      );

      if (response.data.success) {
        return {
          hasUpdate: response.data.has_update,
          latestVersion: response.data.latest_version,
          updateUrl: response.data.update_url,
          changelog: response.data.changelog,
          mandatory: response.data.mandatory || false,
        };
      }
      return {hasUpdate: false};
    } catch (error) {
      console.warn('版本检查失败:', error.message);
      return {hasUpdate: false, error: error.message};
    }
  }

  async getVersionHistory() {
    try {
      const response = await axios.get(
        `${PlatformAdapter.getAPIEndpoint()}/api/version/history`,
        {timeout: 15000}
      );

      if (response.data.success) {
        await AsyncStorage.setItem('version_history', JSON.stringify(response.data.history));
        return response.data.history;
      }
      return await this.getCachedHistory();
    } catch (error) {
      console.warn('获取版本历史失败:', error.message);
      return await this.getCachedHistory();
    }
  }

  async getCachedHistory() {
    try {
      const cached = await AsyncStorage.getItem('version_history');
      return cached ? JSON.parse(cached) : this.getDefaultHistory();
    } catch (error) {
      return this.getDefaultHistory();
    }
  }

  getDefaultHistory() {
    return [
      {
        version: '2.0.0',
        date: '2024-01-15',
        type: 'major',
        changes: [
          '深度适配小米HyperOS系统',
          '完美适配华为HarmonyOS系统',
          '新增离线考试功能',
          '优化Android原生体验',
          '支持深色/浅色主题切换',
          '新增多语言支持',
        ],
      },
      {
        version: '1.5.0',
        date: '2024-01-01',
        type: 'minor',
        changes: [
          '新增考试中心模块',
          '优化学习统计展示',
          '修复已知bug',
          '性能优化',
        ],
      },
      {
        version: '1.0.0',
        date: '2023-12-15',
        type: 'initial',
        changes: [
          '初始版本发布',
          '用户登录/注册功能',
          '基础考试功能',
          '个人中心',
        ],
      },
    ];
  }

  async downloadUpdate(url) {
    try {
      const response = await axios.get(url, {
        responseType: 'blob',
        timeout: 300000,
      });
      return response.data;
    } catch (error) {
      throw new Error(`下载更新失败: ${error.message}`);
    }
  }

  async installUpdate(apkPath) {
    try {
      if (Platform.OS === 'android') {
        const RNFS = require('react-native-fs');
        const installResult = await RNFS.installPackage(apkPath);
        return installResult;
      } else {
        throw new Error('仅支持Android平台自动安装');
      }
    } catch (error) {
      throw new Error(`安装失败: ${error.message}`);
    }
  }

  async getUpdateStatus() {
    try {
      const status = await AsyncStorage.getItem('update_status');
      return status ? JSON.parse(status) : null;
    } catch (error) {
      return null;
    }
  }

  async setUpdateStatus(status) {
    try {
      await AsyncStorage.setItem('update_status', JSON.stringify(status));
    } catch (error) {
      console.warn('保存更新状态失败:', error);
    }
  }

  async clearUpdateStatus() {
    try {
      await AsyncStorage.removeItem('update_status');
    } catch (error) {
      console.warn('清除更新状态失败:', error);
    }
  }

  startAutoCheck(intervalMinutes = 60) {
    if (this.updateCheckInterval) {
      clearInterval(this.updateCheckInterval);
    }
    this.updateCheckInterval = setInterval(() => {
      this.checkForUpdates();
    }, intervalMinutes * 60 * 1000);
  }

  stopAutoCheck() {
    if (this.updateCheckInterval) {
      clearInterval(this.updateCheckInterval);
      this.updateCheckInterval = null;
    }
  }

  compareVersions(v1, v2) {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
      const p1 = parts1[i] || 0;
      const p2 = parts2[i] || 0;
      if (p1 > p2) return 1;
      if (p1 < p2) return -1;
    }
    return 0;
  }

  isVersionGreater(newVersion, currentVersion) {
    return this.compareVersions(newVersion, currentVersion) > 0;
  }

  formatVersion(type) {
    const typeLabels = {
      major: '重大更新',
      minor: '功能更新',
      patch: 'Bug修复',
      initial: '初始版本',
      beta: '测试版本',
      dev: '开发版本',
      plc: 'PLC版本',
    };
    return typeLabels[type] || type;
  }
}

export default new VersionService();