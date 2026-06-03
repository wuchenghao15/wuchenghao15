import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';

const SystemConfigScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [networkStatus, setNetworkStatus] = useState('online');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState('system');
  const [language, setLanguage] = useState('zh');
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadSystemInfo();
    checkNetworkStatus();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadSystemInfo = async () => {
    const info = {
      appVersion: '2.0.0',
      buildNumber: '20260512',
      platform: PlatformAdapter.isHyperOS() ? 'HyperOS' : PlatformAdapter.isHarmonyOS() ? 'HarmonyOS' : 'Android',
      deviceName: 'MTSCOS Device',
      storageUsed: '2.4GB',
      storageTotal: '16GB',
      lastUpdate: '2026-05-12',
      dataEncryption: 'AES-256-GCM',
    };
    setSystemInfo(info);
  };

  const checkNetworkStatus = () => {
    setNetworkStatus('online');
  };

  const handleApplyTheme = async (theme) => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', 'AI主题优化不可用');
      setDarkMode(theme);
      return;
    }

    try {
      const result = await AIService.optimizeTheme({theme});
      if (result.success) {
        setDarkMode(theme);
        Alert.alert('主题优化完成', result.message);
      } else {
        setDarkMode(theme);
      }
    } catch (error) {
      setDarkMode(theme);
    }
  };

  const handleApplyLanguage = (lang) => {
    setLanguage(lang);
    Alert.alert('语言已切换', '请重启应用以应用新语言');
  };

  const handleAIConfigure = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI自动配置');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.autoConfigure({
        platform: PlatformAdapter.isHyperOS() ? 'hyperos' : PlatformAdapter.isHarmonyOS() ? 'harmonyos' : 'android',
        deviceType: 'mobile',
      });

      if (result.success) {
        Alert.alert('AI配置完成', `已优化以下设置：\n\n${result.optimizations}`);
      } else {
        Alert.alert('配置失败', result.message);
      }
    } catch (error) {
      Alert.alert('配置失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleResetSettings = () => {
    Alert.alert(
      '确认重置',
      '确定要重置所有系统配置吗？此操作不可恢复！',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: () => {
            setNotificationsEnabled(true);
            setAutoSyncEnabled(true);
            setDarkMode('system');
            setLanguage('zh');
            Alert.alert('重置成功', '所有配置已恢复默认值');
          },
        },
      ]
    );
  };

  const themeOptions = [
    {id: 'light', name: '浅色模式', icon: '☀️'},
    {id: 'dark', name: '深色模式', icon: '🌙'},
    {id: 'system', name: '跟随系统', icon: '🔄'},
  ];

  const languageOptions = [
    {id: 'zh', name: '简体中文', icon: '🇨🇳'},
    {id: 'en', name: 'English', icon: '🇺🇸'},
    {id: 'ja', name: '日本語', icon: '🇯🇵'},
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
    statusBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 12,
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    badgeOnline: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    badgeOffline: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
      color: '#ff4444',
    },
    infoCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    infoHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    infoGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    infoItem: {
      flex: 1,
      minWidth: 120,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    infoLabel: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    infoValue: {
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
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
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      minWidth: 100,
    },
    selectorOptionSelected: {
      backgroundColor: PlatformAdapter.getPrimaryColor(),
    },
    selectorIcon: {
      fontSize: 20,
      marginBottom: 6,
    },
    selectorText: {
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    selectorTextSelected: {
      color: '#ffffff',
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
    actionButtonSecondary: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      padding: 16,
      marginTop: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    actionButtonTextSecondary: {
      color: PlatformAdapter.getTextColor(),
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    actionButtonDanger: {
      backgroundColor: '#ff4444',
      alignItems: 'center',
      padding: 16,
      marginTop: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    actionButtonTextDanger: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    actionButtonDisabled: {
      opacity: 0.5,
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>系统配置</Text>
        <Text style={styles.subtitle}>管理系统设置和AI优化</Text>
      </View>

      <View style={styles.sections}>
        {systemInfo && (
          <View style={styles.infoCard}>
            <Text style={styles.infoHeader}>📱 系统信息</Text>
            <View style={styles.infoGrid}>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>版本</Text>
                <Text style={styles.infoValue}>{systemInfo.appVersion}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>平台</Text>
                <Text style={styles.infoValue}>{systemInfo.platform}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>存储</Text>
                <Text style={styles.infoValue}>{systemInfo.storageUsed}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>加密</Text>
                <Text style={styles.infoValue}>{systemInfo.dataEncryption}</Text>
              </View>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI智能配置</Text>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>AI服务</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <View style={[styles.aiStatusIndicator, aiStatus.online ? styles.aiOnline : styles.aiOffline]} />
                <Text style={styles.aiStatusValue}>{aiStatus.online ? '在线' : '离线'}</Text>
              </View>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>可用功能</Text>
              <Text style={styles.aiStatusValue}>智能优化、自动配置、主题适配</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>网络状态</Text>
          <View style={styles.card}>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemIcon}>📡</Text>
              <Text style={styles.itemLabel}>网络连接</Text>
              <Text style={[styles.statusBadge, networkStatus === 'online' ? styles.badgeOnline : styles.badgeOffline]}>
                {networkStatus === 'online' ? '在线' : '离线'}
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>通用设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🔔</Text>
              <Text style={styles.itemLabel}>通知提醒</Text>
              <Switch
                value={notificationsEnabled}
                onValueChange={(value) => setNotificationsEnabled(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>☁️</Text>
              <Text style={styles.itemLabel}>自动同步</Text>
              <Switch
                value={autoSyncEnabled}
                onValueChange={(value) => setAutoSyncEnabled(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>主题模式</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🎨</Text>
              <Text style={styles.itemLabel}>外观设置</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {themeOptions.map((theme) => (
                  <TouchableOpacity
                    key={theme.id}
                    style={[styles.selectorOption, darkMode === theme.id && styles.selectorOptionSelected]}
                    onPress={() => handleApplyTheme(theme.id)}>
                    <Text style={styles.selectorIcon}>{theme.icon}</Text>
                    <Text style={[styles.selectorText, darkMode === theme.id && styles.selectorTextSelected]}>
                      {theme.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>语言设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🌐</Text>
              <Text style={styles.itemLabel}>应用语言</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {languageOptions.map((lang) => (
                  <TouchableOpacity
                    key={lang.id}
                    style={[styles.selectorOption, language === lang.id && styles.selectorOptionSelected]}
                    onPress={() => handleApplyLanguage(lang.id)}>
                    <Text style={styles.selectorIcon}>{lang.icon}</Text>
                    <Text style={[styles.selectorText, language === lang.id && styles.selectorTextSelected]}>
                      {lang.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIConfigure}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI智能配置</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📤 导出配置</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📥 导入配置</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonDanger} onPress={handleResetSettings}>
          <Text style={styles.actionButtonTextDanger}>🗑️ 重置配置</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default SystemConfigScreen;