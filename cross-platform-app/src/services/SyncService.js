import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import OfflineStorageService from './OfflineStorageService';
import PlatformAdapter from '../adapters/PlatformAdapter';

class SyncService {
  constructor() {
    this.syncInterval = null;
    this.isSyncing = false;
    this.init();
  }

  async init() {
    NetInfo.addEventListener(this.handleNetworkChange);
    this.startAutoSync();
  }

  handleNetworkChange = async (state) => {
    if (state.isConnected) {
      await this.syncAllData();
    }
  }

  startAutoSync() {
    this.syncInterval = setInterval(() => {
      this.trySync();
    }, 30 * 60 * 1000);
  }

  stopAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  async trySync() {
    const state = await NetInfo.fetch();
    if (state.isConnected && !this.isSyncing) {
      await this.syncAllData();
    }
  }

  async syncAllData() {
    if (this.isSyncing) return;
    
    this.isSyncing = true;
    const results = {};

    try {
      results.records = await this.syncExamRecords();
      results.progress = await this.syncUserProgress();
      results.config = await this.syncConfig();
      results.questions = await this.syncQuestions();
      
      this.onSyncComplete(results);
    } catch (error) {
      console.error('Sync failed:', error);
      this.onSyncError(error);
    } finally {
      this.isSyncing = false;
    }

    return results;
  }

  async syncExamRecords() {
    try {
      const unsyncedRecords = await OfflineStorageService.getUnsyncedRecords();
      
      if (unsyncedRecords.length === 0) {
        return {success: true, message: '没有待同步的考试记录', count: 0};
      }

      const response = await axios.post(
        `${PlatformAdapter.getAPIEndpoint()}/api/sync/records`,
        {records: unsyncedRecords},
        {timeout: 30000}
      );

      if (response.data.success) {
        const syncedIds = unsyncedRecords.map(r => r.record_id);
        await OfflineStorageService.markRecordsAsSynced(syncedIds);
        return {success: true, message: `成功同步 ${unsyncedRecords.length} 条考试记录`, count: unsyncedRecords.length};
      } else {
        return {success: false, message: response.data.message || '同步失败'};
      }
    } catch (error) {
      return {success: false, message: error.message || '网络错误'};
    }
  }

  async syncUserProgress() {
    try {
      const unsyncedProgress = await OfflineStorageService.getUnsyncedProgress();
      
      if (unsyncedProgress.length === 0) {
        return {success: true, message: '没有待同步的学习进度', count: 0};
      }

      const response = await axios.post(
        `${PlatformAdapter.getAPIEndpoint()}/api/sync/progress`,
        {progress: unsyncedProgress},
        {timeout: 30000}
      );

      if (response.data.success) {
        const userId = unsyncedProgress[0]?.user_id;
        if (userId) {
          await OfflineStorageService.markProgressAsSynced(userId);
        }
        return {success: true, message: `成功同步 ${unsyncedProgress.length} 条学习进度`, count: unsyncedProgress.length};
      } else {
        return {success: false, message: response.data.message || '同步失败'};
      }
    } catch (error) {
      return {success: false, message: error.message || '网络错误'};
    }
  }

  async syncConfig() {
    try {
      const response = await axios.get(
        `${PlatformAdapter.getAPIEndpoint()}/api/config/latest`,
        {timeout: 15000}
      );

      if (response.data.success) {
        await OfflineStorageService.saveConfig('server_config', response.data.config);
        return {success: true, message: '配置同步成功'};
      } else {
        return {success: false, message: response.data.message || '配置同步失败'};
      }
    } catch (error) {
      return {success: false, message: error.message || '网络错误'};
    }
  }

  async syncQuestions() {
    try {
      const lastSyncTime = await OfflineStorageService.getConfig('last_question_sync');
      const params = lastSyncTime ? {since: lastSyncTime} : {};

      const response = await axios.get(
        `${PlatformAdapter.getAPIEndpoint()}/api/questions/sync`,
        {params, timeout: 60000}
      );

      if (response.data.success && response.data.questions?.length > 0) {
        await OfflineStorageService.saveQuestions(response.data.questions);
        await OfflineStorageService.saveConfig('last_question_sync', new Date().toISOString());
        return {success: true, message: `成功同步 ${response.data.questions.length} 道题目`, count: response.data.questions.length};
      } else {
        return {success: true, message: '题目已是最新', count: 0};
      }
    } catch (error) {
      return {success: false, message: error.message || '网络错误'};
    }
  }

  async downloadAllQuestions(subject = null) {
    try {
      const params = subject ? {subject} : {};
      const response = await axios.get(
        `${PlatformAdapter.getAPIEndpoint()}/api/questions/download`,
        {params, timeout: 120000}
      );

      if (response.data.success && response.data.questions?.length > 0) {
        await OfflineStorageService.saveQuestions(response.data.questions);
        return {success: true, message: `成功下载 ${response.data.questions.length} 道题目`, count: response.data.questions.length};
      } else {
        return {success: false, message: response.data.message || '下载失败'};
      }
    } catch (error) {
      return {success: false, message: error.message || '网络错误'};
    }
  }

  async getSyncStatus() {
    const stats = await OfflineStorageService.getStorageStats();
    const unsyncedRecords = await OfflineStorageService.getUnsyncedRecords();
    const unsyncedProgress = await OfflineStorageService.getUnsyncedProgress();
    const lastSync = await OfflineStorageService.getConfig('last_sync_time');
    const networkState = await NetInfo.fetch();

    return {
      storage: stats,
      unsynced: {
        records: unsyncedRecords.length,
        progress: unsyncedProgress.length,
      },
      last_sync: lastSync,
      is_online: networkState.isConnected,
      is_syncing: this.isSyncing,
    };
  }

  onSyncComplete(results) {
    const successCount = Object.values(results).filter(r => r.success).length;
    console.log(`Sync completed: ${successCount}/${Object.keys(results).length} operations succeeded`);
    
    OfflineStorageService.saveConfig('last_sync_time', new Date().toISOString());
    OfflineStorageService.saveConfig('sync_results', results);
  }

  onSyncError(error) {
    console.error('Sync error:', error);
  }

  async forceSync() {
    return await this.syncAllData();
  }
}

export default new SyncService();