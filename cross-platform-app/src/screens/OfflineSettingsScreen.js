import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, Alert, ActivityIndicator} from 'react-native';
import OfflineStorageService from '../services/OfflineStorageService';
import SyncService from '../services/SyncService';
import PlatformAdapter from '../adapters/PlatformAdapter';

const OfflineSettingsScreen = ({navigation}) => {
  const [syncStatus, setSyncStatus] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    const status = await SyncService.getSyncStatus();
    setSyncStatus(status);
    const stats = await OfflineStorageService.getStorageStats();
    setStorageStats(stats);
  };

  const handleSync = async () => {
    setIsSyncing(true);
    const result = await SyncService.forceSync();
    setIsSyncing(false);
    await loadStatus();

    let message = '同步完成！\n\n';
    Object.entries(result).forEach(([key, value]) => {
      message += `${value.message}\n`;
    });
    Alert.alert('同步结果', message);
  };

  const handleDownloadQuestions = async () => {
    setIsSyncing(true);
    const result = await SyncService.downloadAllQuestions();
    setIsSyncing(false);
    await loadStatus();

    if (result.success) {
      Alert.alert('下载成功', result.message);
    } else {
      Alert.alert('下载失败', result.message);
    }
  };

  const handleClearData = () => {
    Alert.alert(
      '确认清除',
      '确定要清除所有离线数据吗？此操作不可恢复。',
      [
        {text: '取消', style: 'cancel'},
        {text: '确定', onPress: async () => {
          await OfflineStorageService.clearAllData();
          await loadStatus();
          Alert.alert('已清除', '所有离线数据已清除');
        }}
      ]
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return '从未';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: PlatformAdapter.getBackgroundColor(),
    },
    header: {
      padding: 24,
      paddingTop: 32,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    sections: {
      paddingHorizontal: 24,
    },
    section: {
      marginBottom: 24,
    },
    sectionTitle: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.5,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
      paddingLeft: 8,
    },
    card: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    cardItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    cardItemLast: {
      borderBottomWidth: 0,
    },
    itemLabel: {
      flex: 1,
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statusBadge: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
      backgroundColor: syncStatus?.is_online ? '#44ff44' : '#ff4444',
    },
    statusText: {
      color: '#ffffff',
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    button: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      marginBottom: 12,
    },
    buttonText: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    secondaryButton: {
      ...PlatformAdapter.getButtonStyle('secondary'),
      alignItems: 'center',
      marginBottom: 12,
    },
    secondaryButtonText: {
      color: PlatformAdapter.getPrimaryColor(),
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    dangerButton: {
      backgroundColor: 'rgba(255, 68, 68, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      alignItems: 'center',
    },
    dangerButtonText: {
      color: '#ff4444',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statsGrid: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      padding: 16,
    },
    statItem: {
      alignItems: 'center',
    },
    statValue: {
      fontSize: 24,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    syncIndicator: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>离线设置</Text>
      </View>

      <View style={styles.sections}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>网络状态</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>网络连接</Text>
              <View style={styles.statusBadge}>
                <Text style={styles.statusText}>{syncStatus?.is_online ? '在线' : '离线'}</Text>
              </View>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>上次同步</Text>
              <Text style={styles.itemValue}>{formatDate(syncStatus?.last_sync)}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>自动同步</Text>
              <Switch
                value={autoSyncEnabled}
                onValueChange={setAutoSyncEnabled}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemLabel}>同步状态</Text>
              <Text style={styles.itemValue}>
                {syncStatus?.is_syncing ? '同步中...' : '空闲'}
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>离线数据</Text>
          <View style={styles.card}>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{storageStats?.questions || 0}</Text>
                <Text style={styles.statLabel}>题目数量</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{storageStats?.records || 0}</Text>
                <Text style={styles.statLabel}>考试记录</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{storageStats?.progress || 0}</Text>
                <Text style={styles.statLabel}>学习进度</Text>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>同步操作</Text>
          <TouchableOpacity 
            style={styles.button} 
            onPress={handleSync}
            disabled={isSyncing || !syncStatus?.is_online}>
            <View style={styles.syncIndicator}>
              {isSyncing && <ActivityIndicator color="#ffffff" size="small" />}
              <Text style={styles.buttonText}>{isSyncing ? '同步中...' : '立即同步'}</Text>
            </View>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.secondaryButton} 
            onPress={handleDownloadQuestions}
            disabled={isSyncing || !syncStatus?.is_online}>
            <View style={styles.syncIndicator}>
              {isSyncing && <ActivityIndicator color={PlatformAdapter.getPrimaryColor()} size="small" />}
              <Text style={styles.secondaryButtonText}>{isSyncing ? '下载中...' : '下载题库'}</Text>
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>数据管理</Text>
          <TouchableOpacity style={styles.dangerButton} onPress={handleClearData}>
            <Text style={styles.dangerButtonText}>清除所有离线数据</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>待同步数据</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>考试记录</Text>
              <Text style={styles.itemValue}>{syncStatus?.unsynced?.records || 0} 条</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemLabel}>学习进度</Text>
              <Text style={styles.itemValue}>{syncStatus?.unsynced?.progress || 0} 条</Text>
            </View>
          </View>
        </View>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default OfflineSettingsScreen;