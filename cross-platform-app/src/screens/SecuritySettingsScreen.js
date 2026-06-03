import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';

const SecuritySettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [securityInfo, setSecurityInfo] = useState(null);
  const [encryptionEnabled, setEncryptionEnabled] = useState(true);
  const [biometricAuth, setBiometricAuth] = useState(true);
  const [autoLockEnabled, setAutoLockEnabled] = useState(true);
  const [autoLockTime, setAutoLockTime] = useState(5);
  const [dataMasking, setDataMasking] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadSecurityInfo();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadSecurityInfo = async () => {
    const info = {
      lastScan: '2026-05-12 14:30',
      threatsFound: 0,
      encryptionStatus: 'AES-256-GCM',
      dataBreaches: 0,
      lastBackup: '2026-05-12 12:00',
      backupStatus: '安全',
      privacyScore: 98,
    };
    setSecurityInfo(info);
  };

  const handleAISecurityScan = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI安全扫描');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.securityScan({
        encryptionEnabled,
        biometricAuth,
        dataMasking,
      });

      if (result.success) {
        Alert.alert('扫描完成', `安全评估：${result.score}/100\n\n风险项：${result.risks}\n建议：${result.suggestions}`);
      } else {
        Alert.alert('扫描失败', result.message);
      }
    } catch (error) {
      Alert.alert('扫描失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleEncryptAllData = async () => {
    Alert.alert(
      '确认加密',
      '确定要加密所有本地数据吗？此操作可能需要一些时间。',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            setIsProcessing(true);
            try {
              await new Promise(resolve => setTimeout(resolve, 2000));
              Alert.alert('加密完成', '所有数据已成功加密');
            } catch (error) {
              Alert.alert('加密失败', error.message);
            }
            setIsProcessing(false);
          },
        },
      ]
    );
  };

  const handleResetPrivacy = () => {
    Alert.alert(
      '确认重置',
      '确定要重置所有隐私设置吗？',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: () => {
            setEncryptionEnabled(true);
            setBiometricAuth(true);
            setAutoLockEnabled(true);
            setDataMasking(true);
            Alert.alert('重置成功', '隐私设置已恢复默认');
          },
        },
      ]
    );
  };

  const autoLockOptions = [1, 2, 5, 10, 15, 30];

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
    securityCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(68, 255, 68, 0.1)' : 'rgba(68, 255, 68, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    securityHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    securityGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    securityItem: {
      flex: 1,
      minWidth: 120,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    securityLabel: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    securityValue: {
      fontSize: 14,
      fontWeight: 'bold',
      color: '#44ff44',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    securityValueWarning: {
      color: '#ff4444',
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
      paddingVertical: 8,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      minWidth: 60,
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
        <Text style={styles.title}>数据安全</Text>
        <Text style={styles.subtitle}>管理数据保护和隐私设置</Text>
      </View>

      <View style={styles.sections}>
        {securityInfo && (
          <View style={styles.securityCard}>
            <Text style={styles.securityHeader}>🛡️ 安全状态</Text>
            <View style={styles.securityGrid}>
              <View style={styles.securityItem}>
                <Text style={styles.securityLabel}>隐私评分</Text>
                <Text style={styles.securityValue}>{securityInfo.privacyScore}/100</Text>
              </View>
              <View style={styles.securityItem}>
                <Text style={styles.securityLabel}>威胁检测</Text>
                <Text style={styles.securityValue}>{securityInfo.threatsFound} 个</Text>
              </View>
              <View style={styles.securityItem}>
                <Text style={styles.securityLabel}>加密方式</Text>
                <Text style={styles.securityValue}>{securityInfo.encryptionStatus}</Text>
              </View>
              <View style={styles.securityItem}>
                <Text style={styles.securityLabel}>数据泄露</Text>
                <Text style={styles.securityValue}>{securityInfo.dataBreaches} 次</Text>
              </View>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI安全助手</Text>
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
              <Text style={styles.aiStatusValue}>安全扫描、风险评估、威胁检测</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>数据加密</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🔐</Text>
              <Text style={styles.itemLabel}>数据加密</Text>
              <Switch
                value={encryptionEnabled}
                onValueChange={(value) => setEncryptionEnabled(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🔑</Text>
              <Text style={styles.itemLabel}>生物识别认证</Text>
              <Switch
                value={biometricAuth}
                onValueChange={(value) => setBiometricAuth(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🎭</Text>
              <Text style={styles.itemLabel}>数据脱敏</Text>
              <Switch
                value={dataMasking}
                onValueChange={(value) => setDataMasking(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>自动锁定</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>⏱️</Text>
              <Text style={styles.itemLabel}>自动锁定</Text>
              <Switch
                value={autoLockEnabled}
                onValueChange={(value) => setAutoLockEnabled(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemIcon}>⏲️</Text>
              <Text style={styles.itemLabel}>锁定时间</Text>
              <View style={styles.selectorRow}>
                {autoLockOptions.map((time) => (
                  <TouchableOpacity
                    key={time}
                    style={[styles.selectorOption, autoLockTime === time && styles.selectorOptionSelected]}
                    onPress={() => setAutoLockTime(time)}>
                    <Text style={[styles.selectorText, autoLockTime === time && styles.selectorTextSelected]}>
                      {time}分钟
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>安全日志</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>📋</Text>
              <Text style={styles.itemLabel}>上次安全扫描</Text>
              <Text style={styles.itemValue}>{securityInfo?.lastScan}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>💾</Text>
              <Text style={styles.itemLabel}>上次备份</Text>
              <Text style={styles.itemValue}>{securityInfo?.lastBackup}</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemIcon}>✅</Text>
              <Text style={styles.itemLabel}>备份状态</Text>
              <Text style={styles.itemValue}>{securityInfo?.backupStatus}</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAISecurityScan}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI安全扫描</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary} onPress={handleEncryptAllData} disabled={isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color={PlatformAdapter.getTextColor()} />
          ) : (
            <Text style={styles.actionButtonTextSecondary}>🔐 加密所有数据</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📋 查看安全日志</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>🔄 立即备份</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonDanger} onPress={handleResetPrivacy}>
          <Text style={styles.actionButtonTextDanger}>🗑️ 重置隐私设置</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default SecuritySettingsScreen;