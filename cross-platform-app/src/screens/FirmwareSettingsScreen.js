import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert, ProgressBarAndroid} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';

const FirmwareSettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [firmwareInfo, setFirmwareInfo] = useState(null);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updateProgress, setUpdateProgress] = useState(0);
  const [isUpdating, setIsUpdating] = useState(false);
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(true);
  const [betaChannel, setBetaChannel] = useState(false);
  const [firmwareHistory, setFirmwareHistory] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadFirmwareInfo();
    loadFirmwareHistory();
    checkForUpdates();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadFirmwareInfo = async () => {
    const info = {
      currentVersion: '2.0.0',
      buildNumber: '20260512',
      buildDate: '2026-05-12',
      targetPlatform: PlatformAdapter.isHyperOS() ? 'HyperOS' : PlatformAdapter.isHarmonyOS() ? 'HarmonyOS' : 'Android',
      chipset: 'Snapdragon 8 Gen 3',
      firmwareType: 'userdebug',
      securityPatch: '2026-05-01',
      bootloader: 'AB',
      recovery: 'TWRP 3.7.0',
      vbmeta: 'Disabled',
      dtbo: 'v2.1',
      vendor: 'mtscos',
      region: 'CN',
      language: 'zh-CN',
    };
    setFirmwareInfo(info);
  };

  const loadFirmwareHistory = async () => {
    const history = [
      {version: '2.0.0', date: '2026-05-12', type: 'stable', changelog: 'AI功能增强、性能优化、安全更新'},
      {version: '1.9.5', date: '2026-04-28', type: 'beta', changelog: 'OTA升级优化、Bug修复'},
      {version: '1.9.0', date: '2026-04-15', type: 'stable', changelog: '新增内核优化、UI改进'},
      {version: '1.8.5', date: '2026-03-30', type: 'dev', changelog: '开发版本、新功能测试'},
      {version: '1.8.0', date: '2026-03-15', type: 'stable', changelog: '初始稳定版本'},
    ];
    setFirmwareHistory(history);
  };

  const checkForUpdates = async () => {
    setUpdateAvailable(true);
  };

  const handleCheckUpdate = async () => {
    setIsProcessing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      setUpdateAvailable(true);
      Alert.alert('检查完成', '发现新版本可用！');
    } catch (error) {
      Alert.alert('检查失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleDownloadAndInstall = async () => {
    Alert.alert(
      '确认更新',
      '确定要下载并安装固件更新吗？更新过程中请保持设备连接电源。',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            setIsUpdating(true);
            setUpdateProgress(0);
            
            try {
              for (let i = 0; i <= 100; i += 5) {
                await new Promise(resolve => setTimeout(resolve, 200));
                setUpdateProgress(i);
              }
              
              Alert.alert('更新完成', '固件更新成功！系统将在重启后应用更新。');
            } catch (error) {
              Alert.alert('更新失败', error.message);
            }
            
            setIsUpdating(false);
            setUpdateProgress(0);
          },
        },
      ]
    );
  };

  const handleAIAnalyzeFirmware = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI固件分析');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.analyzeFirmware({
        firmwareInfo,
        platform: PlatformAdapter.isHyperOS() ? 'hyperos' : PlatformAdapter.isHarmonyOS() ? 'harmonyos' : 'android',
      });

      if (result.success) {
        Alert.alert('分析完成', `固件健康评分：${result.healthScore}/100\n\n优化建议：${result.suggestions}`);
      } else {
        Alert.alert('分析失败', result.message);
      }
    } catch (error) {
      Alert.alert('分析失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleAIOptimizeFirmware = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI固件优化');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.optimizeFirmware({
        firmwareInfo,
        betaChannel,
        autoUpdateEnabled,
        platform: PlatformAdapter.isHyperOS() ? 'hyperos' : PlatformAdapter.isHarmonyOS() ? 'harmonyos' : 'android',
      });

      if (result.success) {
        Alert.alert('优化完成', `固件优化成功！\n\n优化项：${result.optimizations}`);
      } else {
        Alert.alert('优化失败', result.message);
      }
    } catch (error) {
      Alert.alert('优化失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleFactoryReset = () => {
    Alert.alert(
      '警告',
      '此操作将清除所有数据并恢复出厂设置！请确保已备份重要数据。',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认重置',
          onPress: () => {
            Alert.alert('已确认', '系统将在重启后恢复出厂设置');
          },
        },
      ]
    );
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
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      opacity: 0.7,
    },
    itemValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    itemIcon: {
      fontSize: 18,
      marginRight: 12,
    },
    updateCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(68, 255, 68, 0.1)' : 'rgba(68, 255, 68, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    updateHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    updateIcon: {
      fontSize: 24,
      marginRight: 12,
    },
    updateTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: '#44ff44',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    updateInfo: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    updateProgress: {
      height: 8,
      borderRadius: 4,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.2)' : '#e0e0e0',
      marginBottom: 12,
      overflow: 'hidden',
    },
    updateProgressBar: {
      height: '100%',
      backgroundColor: '#44ff44',
      transition: 'width 0.3s ease',
    },
    updateProgressText: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
      marginBottom: 12,
    },
    firmwareCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    firmwareHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    firmwareGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    firmwareItem: {
      flex: 1,
      minWidth: 140,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    firmwareLabel: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    firmwareValue: {
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getPrimaryColor(),
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
    historyCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    historyItem: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    historyItemLast: {
      borderBottomWidth: 0,
    },
    historyHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    historyVersion: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    historyType: {
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 4,
      fontSize: 10,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginLeft: 8,
    },
    historyTypeStable: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    historyTypeBeta: {
      backgroundColor: 'rgba(255, 193, 7, 0.2)',
      color: '#ffc107',
    },
    historyTypeDev: {
      backgroundColor: 'rgba(68, 138, 255, 0.2)',
      color: '#448aff',
    },
    historyDate: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 8,
    },
    historyChangelog: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
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
    actionButtonSuccess: {
      backgroundColor: '#44ff44',
      alignItems: 'center',
      padding: 16,
      marginTop: 16,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    actionButtonTextSuccess: {
      color: '#000000',
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
        <Text style={styles.title}>固件设置</Text>
        <Text style={styles.subtitle}>管理系统底层固件和更新设置</Text>
      </View>

      <View style={styles.sections}>
        {firmwareInfo && (
          <View style={styles.firmwareCard}>
            <Text style={styles.firmwareHeader}>📱 固件信息</Text>
            <View style={styles.firmwareGrid}>
              <View style={styles.firmwareItem}>
                <Text style={styles.firmwareLabel}>当前版本</Text>
                <Text style={styles.firmwareValue}>{firmwareInfo.currentVersion}</Text>
              </View>
              <View style={styles.firmwareItem}>
                <Text style={styles.firmwareLabel}>构建号</Text>
                <Text style={styles.firmwareValue}>{firmwareInfo.buildNumber}</Text>
              </View>
              <View style={styles.firmwareItem}>
                <Text style={styles.firmwareLabel}>平台</Text>
                <Text style={styles.firmwareValue}>{firmwareInfo.targetPlatform}</Text>
              </View>
              <View style={styles.firmwareItem}>
                <Text style={styles.firmwareLabel}>芯片</Text>
                <Text style={styles.firmwareValue}>{firmwareInfo.chipset}</Text>
              </View>
            </View>
          </View>
        )}

        {updateAvailable && (
          <View style={styles.updateCard}>
            <View style={styles.updateHeader}>
              <Text style={styles.updateIcon}>🔄</Text>
              <Text style={styles.updateTitle}>发现新版本</Text>
            </View>
            <Text style={styles.updateInfo}>版本 2.1.0 已发布，包含AI功能增强和性能优化</Text>
            
            {isUpdating ? (
              <>
                <View style={styles.updateProgress}>
                  <View style={[styles.updateProgressBar, {width: `${updateProgress}%`}]} />
                </View>
                <Text style={styles.updateProgressText}>{updateProgress}%</Text>
              </>
            ) : (
              <TouchableOpacity style={styles.actionButtonSuccess} onPress={handleDownloadAndInstall}>
                <Text style={styles.actionButtonTextSuccess}>下载并安装</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI固件助手</Text>
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
              <Text style={styles.aiStatusValue}>固件分析、智能优化、OTA预测</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>更新设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🔄</Text>
              <Text style={styles.itemLabel}>自动更新</Text>
              <Switch
                value={autoUpdateEnabled}
                onValueChange={(value) => setAutoUpdateEnabled(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🧪</Text>
              <Text style={styles.itemLabel}>Beta频道</Text>
              <Switch
                value={betaChannel}
                onValueChange={(value) => setBetaChannel(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemIcon}>📅</Text>
              <Text style={styles.itemLabel}>安全补丁</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.securityPatch}</Text>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>固件详情</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>固件类型</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.firmwareType}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>Bootloader</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.bootloader}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>Recovery</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.recovery}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>Vendor</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.vendor}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>Region</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.region}</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemLabel}>Language</Text>
              <Text style={styles.itemValue}>{firmwareInfo?.language}</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleCheckUpdate}
          disabled={isProcessing || isUpdating}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🔍 检查更新</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIAnalyzeFirmware}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI固件分析</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIOptimizeFirmware}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>✨ AI固件优化</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📋 查看更新日志</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>🔧 本地升级</Text>
        </TouchableOpacity>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>更新历史</Text>
          <View style={styles.historyCard}>
            {firmwareHistory.map((item, index) => (
              <View key={item.version} style={[styles.historyItem, index === firmwareHistory.length - 1 && styles.historyItemLast]}>
                <View style={styles.historyHeader}>
                  <Text style={styles.historyVersion}>{item.version}</Text>
                  <Text style={[styles.historyType, 
                    item.type === 'stable' ? styles.historyTypeStable : 
                    item.type === 'beta' ? styles.historyTypeBeta : styles.historyTypeDev]}>
                    {item.type.toUpperCase()}
                  </Text>
                </View>
                <Text style={styles.historyDate}>{item.date}</Text>
                <Text style={styles.historyChangelog}>{item.changelog}</Text>
              </View>
            ))}
          </View>
        </View>

        <TouchableOpacity style={styles.actionButtonDanger} onPress={handleFactoryReset}>
          <Text style={styles.actionButtonTextDanger}>🗑️ 恢复出厂设置</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default FirmwareSettingsScreen;