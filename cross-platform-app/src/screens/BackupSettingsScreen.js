import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import OfflineStorageService from '../services/OfflineStorageService';
import SyncService from '../services/SyncService';
import AIService from '../services/AIService';

const BackupSettingsScreen = ({navigation}) => {
  const [autoBackup, setAutoBackup] = useState(true);
  const [backupInterval, setBackupInterval] = useState('daily');
  const [cloudBackup, setCloudBackup] = useState(false);
  const [aiOptimization, setAiOptimization] = useState(true);
  const [lastBackup, setLastBackup] = useState(null);
  const [nextBackup, setNextBackup] = useState(null);
  const [backupHistory, setBackupHistory] = useState([]);
  const [backupStats, setBackupStats] = useState(null);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);

  useEffect(() => {
    loadSettings();
    loadBackupHistory();
    loadBackupStats();
    checkAIStatus();
  }, []);

  const loadSettings = async () => {
    const settings = await OfflineStorageService.getBackupSettings();
    setAutoBackup(settings.autoBackup || true);
    setBackupInterval(settings.backupInterval || 'daily');
    setCloudBackup(settings.cloudBackup || false);
    setAiOptimization(settings.aiOptimization || true);
    setLastBackup(settings.lastBackup || '--');
    calculateNextBackup();
  };

  const loadBackupHistory = async () => {
    try {
      const history = await OfflineStorageService.getBackupHistory();
      setBackupHistory(history);
    } catch (error) {
      console.warn('获取备份历史失败:', error);
    }
  };

  const loadBackupStats = async () => {
    try {
      const stats = await OfflineStorageService.getBackupStats();
      setBackupStats(stats);
    } catch (error) {
      console.warn('获取备份统计失败:', error);
    }
  };

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const calculateNextBackup = () => {
    const intervals = {
      hourly: '1小时后',
      daily: '明天同一时间',
      weekly: '下周同一时间',
      monthly: '下月同一时间',
    };
    setNextBackup(intervals[backupInterval] || '未知');
  };

  const handleSaveSettings = async () => {
    const settings = {
      autoBackup,
      backupInterval,
      cloudBackup,
      aiOptimization,
    };
    const success = await OfflineStorageService.saveBackupSettings(settings);
    if (success) {
      Alert.alert('保存成功', '备份设置已保存');
      calculateNextBackup();
    } else {
      Alert.alert('保存失败', '无法保存设置');
    }
  };

  const handleManualBackup = async () => {
    setIsBackingUp(true);
    try {
      const result = await OfflineStorageService.createBackup();
      if (result.success) {
        Alert.alert('备份成功', `备份已保存: ${result.backupId}`);
        loadBackupHistory();
        loadBackupStats();
        setLastBackup(new Date().toLocaleString());
      } else {
        Alert.alert('备份失败', result.message);
      }
    } catch (error) {
      Alert.alert('备份失败', error.message);
    }
    setIsBackingUp(false);
  };

  const handleRestoreBackup = async (backupId) => {
    Alert.alert(
      '确认恢复',
      '恢复备份将覆盖当前数据，确定继续？',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            try {
              const result = await OfflineStorageService.restoreBackup(backupId);
              if (result.success) {
                Alert.alert('恢复成功', '数据已恢复');
                loadBackupHistory();
              } else {
                Alert.alert('恢复失败', result.message);
              }
            } catch (error) {
              Alert.alert('恢复失败', error.message);
            }
          },
        },
      ]
    );
  };

  const handleDeleteBackup = async (backupId) => {
    Alert.alert(
      '确认删除',
      '确定要删除此备份吗？',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '删除',
          onPress: async () => {
            try {
              const result = await OfflineStorageService.deleteBackup(backupId);
              if (result.success) {
                Alert.alert('删除成功', '备份已删除');
                loadBackupHistory();
                loadBackupStats();
              } else {
                Alert.alert('删除失败', result.message);
              }
            } catch (error) {
              Alert.alert('删除失败', error.message);
            }
          },
        },
      ]
    );
  };

  const handleSyncNow = async () => {
    try {
      const result = await SyncService.syncAll();
      if (result.success) {
        Alert.alert('同步成功', `${result.syncedCount} 条数据已同步`);
        loadBackupStats();
      } else {
        Alert.alert('同步失败', result.message);
      }
    } catch (error) {
      Alert.alert('同步失败', error.message);
    }
  };

  const backupIntervalOptions = [
    {id: 'hourly', name: '每小时', desc: '频繁备份'},
    {id: 'daily', name: '每天', desc: '标准备份'},
    {id: 'weekly', name: '每周', desc: '定期备份'},
    {id: 'monthly', name: '每月', desc: '月度备份'},
  ];

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
    subtitle: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 8,
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
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemIcon: {
      fontSize: 18,
      marginRight: 12,
    },
    itemBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 12,
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    badgeSuccess: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    badgeWarning: {
      backgroundColor: 'rgba(255, 215, 0, 0.2)',
      color: '#ffd700',
    },
    statsCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    statsHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    statsGrid: {
      flexDirection: 'row',
      justifyContent: 'space-around',
    },
    statItem: {
      alignItems: 'center',
    },
    statValue: {
      fontSize: 24,
      fontWeight: 'bold',
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 4,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    backupCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(68, 255, 68, 0.05)' : 'rgba(68, 255, 68, 0.05)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    backupHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    backupRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 4,
    },
    backupLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    backupValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    aiCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    aiHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    aiIcon: {
      fontSize: 24,
      marginRight: 12,
    },
    aiTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    aiStatusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 4,
    },
    aiStatusLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    aiStatusValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    aiStatusIndicator: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginRight: 6,
    },
    aiOnline: {
      backgroundColor: '#44ff44',
    },
    aiOffline: {
      backgroundColor: '#ff4444',
    },
    selectorRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
      padding: 8,
    },
    selectorOption: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      minWidth: 80,
    },
    selectorOptionSelected: {
      backgroundColor: PlatformAdapter.getPrimaryColor(),
    },
    selectorText: {
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    selectorTextSelected: {
      color: '#ffffff',
    },
    selectorDesc: {
      fontSize: 11,
      fontFamily: PlatformAdapter.getFontFamily(),
      opacity: 0.6,
      marginTop: 2,
    },
    selectorDescSelected: {
      color: 'rgba(255, 255, 255, 0.7)',
    },
    actionButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      padding: 16,
      marginTop: 16,
    },
    actionButtonText: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    historyCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    historyHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    historyTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    historyList: {
      padding: 8,
    },
    historyItem: {
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    historyItemHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 8,
    },
    historyName: {
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    historyDate: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    historyMeta: {
      flexDirection: 'row',
      gap: 16,
      marginBottom: 8,
    },
    historyMetaItem: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    historyActions: {
      flexDirection: 'row',
      gap: 12,
    },
    historyBtn: {
      paddingHorizontal: 16,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.2)' : 'rgba(0, 125, 255, 0.2)',
    },
    historyBtnText: {
      fontSize: 12,
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    historyBtnDanger: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
    },
    historyBtnTextDanger: {
      color: '#ff4444',
    },
    saveButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      padding: 16,
      marginTop: 16,
    },
    saveButtonText: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>备份设置</Text>
        <Text style={styles.subtitle}>管理数据备份和同步设置</Text>
      </View>

      <View style={styles.sections}>
        {backupStats && (
          <View style={styles.statsCard}>
            <Text style={styles.statsHeader}>📊 备份统计</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{backupStats.totalBackups || 0}</Text>
                <Text style={styles.statLabel}>备份总数</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{backupStats.backupSize || '0'}</Text>
                <Text style={styles.statLabel}>备份大小</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{backupStats.syncedCount || 0}</Text>
                <Text style={styles.statLabel}>已同步</Text>
              </View>
            </View>
          </View>
        )}

        <View style={styles.backupCard}>
          <Text style={styles.backupHeader}>💾 备份状态</Text>
          <View style={styles.backupRow}>
            <Text style={styles.backupLabel}>最后备份</Text>
            <Text style={styles.backupValue}>{lastBackup}</Text>
          </View>
          <View style={styles.backupRow}>
            <Text style={styles.backupLabel}>下次备份</Text>
            <Text style={styles.backupValue}>{nextBackup}</Text>
          </View>
          <View style={styles.backupRow}>
            <Text style={styles.backupLabel}>自动备份</Text>
            <Text style={[styles.backupValue, autoBackup ? {color: '#44ff44'} : {color: '#ff4444'}]}>
              {autoBackup ? '开启' : '关闭'}
            </Text>
          </View>
        </View>

        {aiStatus && aiOptimization && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI智能备份优化</Text>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>AI服务</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <View style={[styles.aiStatusIndicator, aiStatus.online ? styles.aiOnline : styles.aiOffline]} />
                <Text style={styles.aiStatusValue}>{aiStatus.online ? '在线' : '离线'}</Text>
              </View>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>优化状态</Text>
              <Text style={styles.aiStatusValue}>
                {aiStatus.online ? 'AI优化已启用' : 'AI优化不可用'}
              </Text>
            </View>
            {aiStatus.online && (
              <View style={styles.aiStatusRow}>
                <Text style={styles.aiStatusLabel}>优化内容</Text>
                <Text style={styles.aiStatusValue}>智能压缩、增量备份</Text>
              </View>
            )}
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>自动备份设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🔄</Text>
              <Text style={styles.itemLabel}>自动备份</Text>
              <Switch
                value={autoBackup}
                onValueChange={(value) => setAutoBackup(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🕐</Text>
              <Text style={styles.itemLabel}>备份间隔</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {backupIntervalOptions.map((option) => (
                  <TouchableOpacity
                    key={option.id}
                    style={[styles.selectorOption, backupInterval === option.id && styles.selectorOptionSelected]}
                    onPress={() => setBackupInterval(option.id)}>
                    <Text style={[styles.selectorText, backupInterval === option.id && styles.selectorTextSelected]}>
                      {option.name}
                    </Text>
                    <Text style={[styles.selectorDesc, backupInterval === option.id && styles.selectorDescSelected]}>
                      {option.desc}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>高级设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>☁️</Text>
              <Text style={styles.itemLabel}>云端备份</Text>
              <Switch
                value={cloudBackup}
                onValueChange={(value) => setCloudBackup(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🤖</Text>
              <Text style={styles.itemLabel}>AI智能优化</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <Switch
                  value={aiOptimization}
                  onValueChange={(value) => setAiOptimization(value)}
                  thumbColor={PlatformAdapter.getPrimaryColor()}
                />
                {aiOptimization && (
                  <Text style={[styles.itemBadge, aiStatus?.online ? styles.badgeSuccess : styles.badgeWarning]}>
                    {aiStatus?.online ? 'AI优化' : 'AI离线'}
                  </Text>
                )}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>备份操作</Text>
          <View style={styles.card}>
            <TouchableOpacity style={[styles.cardItem, styles.cardItemLast]} onPress={handleManualBackup} disabled={isBackingUp}>
              <Text style={styles.itemIcon}>📤</Text>
              <Text style={styles.itemLabel}>{isBackingUp ? '备份中...' : '立即备份'}</Text>
              {isBackingUp && <ActivityIndicator color={PlatformAdapter.getPrimaryColor()} size="small" />}
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <TouchableOpacity style={[styles.cardItem, styles.cardItemLast]} onPress={handleSyncNow}>
              <Text style={styles.itemIcon}>☁️</Text>
              <Text style={styles.itemLabel}>立即同步到云端</Text>
              <Text style={styles.itemValue}>同步所有本地数据</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.historyCard}>
          <View style={styles.historyHeader}>
            <Text style={styles.historyTitle}>📜 备份历史</Text>
          </View>
          <View style={styles.historyList}>
            {backupHistory.length > 0 ? (
              backupHistory.map((backup) => (
                <View key={backup.id} style={styles.historyItem}>
                  <View style={styles.historyItemHeader}>
                    <Text style={styles.historyName}>{backup.name}</Text>
                    <Text style={styles.historyDate}>{backup.date}</Text>
                  </View>
                  <View style={styles.historyMeta}>
                    <Text style={styles.historyMetaItem}>📝 {backup.questions} 题</Text>
                    <Text style={styles.historyMetaItem}>📋 {backup.records} 记录</Text>
                    <Text style={styles.historyMetaItem}>📈 {backup.progress} 进度</Text>
                  </View>
                  <View style={styles.historyActions}>
                    <TouchableOpacity 
                      style={styles.historyBtn} 
                      onPress={() => handleRestoreBackup(backup.id)}>
                      <Text style={styles.historyBtnText}>恢复</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.historyBtn, styles.historyBtnDanger]} 
                      onPress={() => handleDeleteBackup(backup.id)}>
                      <Text style={[styles.historyBtnText, styles.historyBtnTextDanger]}>删除</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))
            ) : (
              <Text style={{textAlign: 'center', padding: 16, color: PlatformAdapter.getTextColor(), opacity: 0.5}}>
                暂无备份记录
              </Text>
            )}
          </View>
        </View>

        <TouchableOpacity style={styles.saveButton} onPress={handleSaveSettings}>
          <Text style={styles.saveButtonText}>保存设置</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default BackupSettingsScreen;