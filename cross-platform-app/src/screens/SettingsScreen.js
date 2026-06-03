import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import {useTheme} from '../context/ThemeContext';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';
import OfflineStorageService from '../services/OfflineStorageService';
import SyncService from '../services/SyncService';

const SettingsScreen = ({navigation}) => {
  const {theme, toggleTheme} = useTheme();
  const [notifications, setNotifications] = useState(true);
  const [sound, setSound] = useState(true);
  const [autoSync, setAutoSync] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [aiStatus, setAiStatus] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [syncStatus, setSyncStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
    checkAIStatus();
    getStorageStats();
    checkSyncStatus();
  }, []);

  const loadSettings = async () => {
    const aiSettings = await AIService.getSettings();
    setAiEnabled(aiSettings.enabled);
    setLoading(false);
  };

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const getStorageStats = async () => {
    try {
      const stats = await OfflineStorageService.getStorageStats();
      setStorageStats(stats);
    } catch (error) {
      console.warn('获取存储统计失败:', error);
    }
  };

  const checkSyncStatus = async () => {
    const status = await SyncService.getSyncStatus();
    setSyncStatus(status);
  };

  const handleAction = (actionId) => {
    switch (actionId) {
      case 'theme':
        toggleTheme();
        break;
      case 'clearCache':
        clearCache();
        break;
      case 'exportData':
        exportData();
        break;
      case 'importData':
        importData();
        break;
      case 'aiSettings':
        navigation.navigate('AISettings');
        break;
      case 'updateSettings':
        navigation.navigate('UpdateSettings');
        break;
      case 'backupSettings':
        navigation.navigate('BackupSettings');
        break;
      case 'securitySettings':
        navigation.navigate('SecuritySettings');
        break;
      case 'systemConfig':
        navigation.navigate('SystemConfig');
        break;
      case 'firmwareSettings':
        navigation.navigate('FirmwareSettings');
        break;
      case 'examSettings':
        navigation.navigate('ExamSettings');
        break;
      case 'teacherSettings':
        navigation.navigate('TeacherSettings');
        break;
      case 'studentSettings':
        navigation.navigate('StudentSettings');
        break;
      case 'questionBankSettings':
        navigation.navigate('QuestionBankSettings');
        break;
      case 'routerSettings':
        navigation.navigate('RouterSettings');
        break;
      case 'kernelSettings':
        navigation.navigate('KernelSettings');
        break;
      case 'versionHistory':
        navigation.navigate('VersionHistory');
        break;
    }
  };

  const clearCache = async () => {
    try {
      await OfflineStorageService.clearCache();
      Alert.alert('缓存已清除', '本地缓存已清空');
      getStorageStats();
    } catch (error) {
      Alert.alert('清除失败', error.message);
    }
  };

  const exportData = async () => {
    try {
      const result = await OfflineStorageService.exportData();
      if (result.success) {
        Alert.alert('导出成功', `数据已导出`);
      } else {
        Alert.alert('导出失败', result.message);
      }
    } catch (error) {
      Alert.alert('导出失败', error.message);
    }
  };

  const importData = async () => {
    Alert.alert('导入数据', '请选择要导入的文件');
  };

  const handleAIEnabledChange = async (value) => {
    setAiEnabled(value);
    await AIService.saveSettings({enabled: value});
  };

  const mainCategories = [
    {
      id: 'personal',
      title: '个性化',
      icon: '🎨',
      items: [
        {id: 'theme', icon: '🌙', label: '主题模式', value: theme === 'dark' ? '深色' : theme === 'light' ? '浅色' : '跟随系统'},
        {id: 'notifications', icon: '🔔', label: '通知提醒', toggle: true, value: notifications, onChange: (v) => setNotifications(v)},
        {id: 'sound', icon: '🔊', label: '音效', toggle: true, value: sound, onChange: (v) => setSound(v)},
      ],
    },
    {
      id: 'ai',
      title: 'AI助手',
      icon: '🤖',
      items: [
        {id: 'aiToggle', icon: '⚡', label: 'AI功能', toggle: true, value: aiEnabled, onChange: handleAIEnabledChange},
        {id: 'aiSettings', icon: '⚙️', label: 'AI配置', badge: aiStatus?.online ? {text: '在线', color: 'green'} : {text: '离线', color: 'red'}},
        {id: 'updateSettings', icon: '🔄', label: '检查更新'},
      ],
    },
    {
      id: 'data',
      title: '数据管理',
      icon: '📊',
      items: [
        {id: 'backupSettings', icon: '💾', label: '备份设置'},
        {id: 'clearCache', icon: '🗑️', label: '清除缓存'},
        {id: 'exportData', icon: '📤', label: '导出数据'},
        {id: 'importData', icon: '📥', label: '导入数据'},
      ],
    },
    {
      id: 'security',
      title: '安全隐私',
      icon: '🛡️',
      items: [
        {id: 'securitySettings', icon: '🔐', label: '数据安全'},
        {id: 'autoSync', icon: '☁️', label: '自动同步', toggle: true, value: autoSync, onChange: (v) => setAutoSync(v)},
      ],
    },
    {
      id: 'education',
      title: '教育系统',
      icon: '📚',
      items: [
        {id: 'examSettings', icon: '📝', label: '考试系统'},
        {id: 'questionBankSettings', icon: '📖', label: '题库管理'},
        {id: 'teacherSettings', icon: '👨‍🏫', label: '教师系统'},
        {id: 'studentSettings', icon: '👨‍🎓', label: '学生信息'},
      ],
    },
    {
      id: 'system',
      title: '系统配置',
      icon: '⚙️',
      items: [
        {id: 'systemConfig', icon: '🔧', label: '系统配置'},
        {id: 'routerSettings', icon: '🔗', label: '路由系统'},
        {id: 'kernelSettings', icon: '🖥️', label: '内核系统'},
        {id: 'firmwareSettings', icon: '🔩', label: '固件设置'},
        {id: 'versionHistory', icon: '📜', label: '版本历史'},
      ],
    },
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
    statusCards: {
      paddingHorizontal: 24,
      marginBottom: 24,
    },
    statusCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 12,
    },
    statusCardHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    statusIcon: {
      fontSize: 24,
      marginRight: 12,
    },
    statusTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 4,
    },
    statusLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statusValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    statusIndicator: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginRight: 6,
    },
    statusOnline: {
      backgroundColor: '#44ff44',
    },
    statusOffline: {
      backgroundColor: '#ff4444',
    },
    storageCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(68, 255, 68, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      ...PlatformAdapter.getElevation(),
    },
    storageHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    storageGrid: {
      flexDirection: 'row',
      justifyContent: 'space-around',
    },
    storageItem: {
      alignItems: 'center',
    },
    storageValue: {
      fontSize: 24,
      fontWeight: 'bold',
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    storageLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 4,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    sections: {
      paddingHorizontal: 24,
    },
    section: {
      marginBottom: 24,
    },
    sectionHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    sectionIcon: {
      fontSize: 20,
      marginRight: 8,
    },
    sectionTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemList: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    item: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    itemLast: {
      borderBottomWidth: 0,
    },
    itemIcon: {
      fontSize: 18,
      marginRight: 12,
    },
    itemContent: {
      flex: 1,
    },
    itemLabel: {
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 2,
    },
    itemBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 12,
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginRight: 8,
    },
    badgeGreen: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    badgeRed: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
      color: '#ff4444',
    },
    itemArrow: {
      fontSize: 20,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.4,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
  });

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={PlatformAdapter.getPrimaryColor()} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>系统设置</Text>
        <Text style={styles.subtitle}>管理您的学习体验和系统配置</Text>
      </View>

      <View style={styles.statusCards}>
        {aiStatus && (
          <View style={styles.statusCard}>
            <View style={styles.statusCardHeader}>
              <Text style={styles.statusIcon}>🤖</Text>
              <Text style={styles.statusTitle}>AI助手</Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>服务状态</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <View style={[styles.statusIndicator, aiStatus.online ? styles.statusOnline : styles.statusOffline]} />
                <Text style={styles.statusValue}>{aiStatus.online ? '在线' : '离线'}</Text>
              </View>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>今日请求</Text>
              <Text style={styles.statusValue}>{aiStatus.todayRequests || 0} 次</Text>
            </View>
          </View>
        )}

        {storageStats && (
          <View style={styles.storageCard}>
            <Text style={styles.storageHeader}>📊 本地数据</Text>
            <View style={styles.storageGrid}>
              <View style={styles.storageItem}>
                <Text style={styles.storageValue}>{storageStats.questions || 0}</Text>
                <Text style={styles.storageLabel}>题目</Text>
              </View>
              <View style={styles.storageItem}>
                <Text style={styles.storageValue}>{storageStats.records || 0}</Text>
                <Text style={styles.storageLabel}>记录</Text>
              </View>
              <View style={styles.storageItem}>
                <Text style={styles.storageValue}>{storageStats.progress || 0}</Text>
                <Text style={styles.storageLabel}>进度</Text>
              </View>
            </View>
          </View>
        )}

        {syncStatus && (
          <View style={styles.statusCard}>
            <View style={styles.statusCardHeader}>
              <Text style={styles.statusIcon}>📡</Text>
              <Text style={styles.statusTitle}>同步状态</Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>状态</Text>
              <Text style={styles.statusValue}>{syncStatus.status || '未知'}</Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>最后同步</Text>
              <Text style={styles.statusValue}>{syncStatus.lastSync || '--'}</Text>
            </View>
          </View>
        )}
      </View>

      <View style={styles.sections}>
        {mainCategories.map((category) => (
          <View key={category.id} style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionIcon}>{category.icon}</Text>
              <Text style={styles.sectionTitle}>{category.title}</Text>
            </View>
            <View style={styles.itemList}>
              {category.items.map((item, index) => (
                <TouchableOpacity
                  key={item.id}
                  style={[styles.item, index === category.items.length - 1 && styles.itemLast]}
                  onPress={() => item.toggle ? item.onChange(!item.value) : handleAction(item.id)}>
                  <Text style={styles.itemIcon}>{item.icon}</Text>
                  <View style={styles.itemContent}>
                    <Text style={styles.itemLabel}>{item.label}</Text>
                    {item.value && typeof item.value === 'string' && (
                      <Text style={styles.itemValue}>{item.value}</Text>
                    )}
                  </View>
                  {item.badge && (
                    <Text style={[styles.itemBadge, item.badge.color === 'green' ? styles.badgeGreen : styles.badgeRed]}>
                      {item.badge.text}
                    </Text>
                  )}
                  {item.toggle ? (
                    <Switch
                      value={item.value}
                      onValueChange={item.onChange}
                      thumbColor={PlatformAdapter.getPrimaryColor()}
                    />
                  ) : (
                    <Text style={styles.itemArrow}>›</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionIcon}>ℹ️</Text>
            <Text style={styles.sectionTitle}>关于</Text>
          </View>
          <View style={styles.itemList}>
            <TouchableOpacity style={styles.item} onPress={() => {}}>
              <Text style={styles.itemIcon}>📱</Text>
              <Text style={styles.itemLabel}>关于应用</Text>
              <Text style={styles.itemArrow}>›</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.item}>
              <Text style={styles.itemIcon}>🔒</Text>
              <Text style={styles.itemLabel}>隐私政策</Text>
              <Text style={styles.itemArrow}>›</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.item}>
              <Text style={styles.itemIcon}>📋</Text>
              <Text style={styles.itemLabel}>用户协议</Text>
              <Text style={styles.itemArrow}>›</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.item, styles.itemLast]}>
              <Text style={styles.itemIcon}>💬</Text>
              <Text style={styles.itemLabel}>意见反馈</Text>
              <Text style={styles.itemArrow}>›</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default SettingsScreen;