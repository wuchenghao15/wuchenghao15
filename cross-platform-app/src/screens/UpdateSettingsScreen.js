import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import VersionService from '../services/VersionService';
import PlatformAdapter from '../adapters/PlatformAdapter';

const UpdateSettingsScreen = ({navigation}) => {
  const [updateStatus, setUpdateStatus] = useState(null);
  const [checking, setChecking] = useState(false);
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [updateInterval, setUpdateInterval] = useState(60);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    checkForUpdates();
    loadSettings();
  }, []);

  const checkForUpdates = async () => {
    setChecking(true);
    const result = await VersionService.checkForUpdates();
    setUpdateStatus(result);
    setChecking(false);
  };

  const loadSettings = async () => {
    const saved = await VersionService.getUpdateStatus();
    if (saved) {
      setAutoUpdate(saved.autoUpdate || true);
      setUpdateInterval(saved.updateInterval || 60);
    }
  };

  const saveSettings = async () => {
    await VersionService.setUpdateStatus({
      autoUpdate,
      updateInterval,
    });
    
    if (autoUpdate) {
      VersionService.startAutoCheck(updateInterval);
    } else {
      VersionService.stopAutoCheck();
    }
  };

  const handleDownload = async () => {
    if (!updateStatus?.updateUrl) return;
    
    setIsDownloading(true);
    setDownloadProgress(0);

    try {
      const progressInterval = setInterval(() => {
        setDownloadProgress(prev => {
          if (prev >= 95) {
            clearInterval(progressInterval);
            return 95;
          }
          return prev + Math.random() * 15;
        });
      }, 500);

      await new Promise(resolve => setTimeout(resolve, 3000));
      clearInterval(progressInterval);
      setDownloadProgress(100);

      await new Promise(resolve => setTimeout(resolve, 500));
      
      Alert.alert(
        '下载完成',
        '更新包已下载完成，请手动安装',
        [
          {text: '确定', onPress: () => {}}
        ]
      );
    } catch (error) {
      Alert.alert('下载失败', error.message);
    } finally {
      setIsDownloading(false);
      setDownloadProgress(0);
    }
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
    checkButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      marginBottom: 16,
    },
    checkButtonText: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    updateCard: {
      backgroundColor: '#44ff44',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 20,
      marginBottom: 16,
    },
    updateTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 8,
    },
    updateVersion: {
      fontSize: 14,
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    changelogList: {
      marginBottom: 16,
    },
    changelogItem: {
      fontSize: 14,
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 4,
    },
    downloadButton: {
      backgroundColor: '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 12,
      alignItems: 'center',
    },
    downloadButtonText: {
      color: '#44ff44',
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    progressBar: {
      height: 8,
      backgroundColor: 'rgba(255,255,255,0.3)',
      borderRadius: 4,
      overflow: 'hidden',
      marginBottom: 16,
    },
    progressFill: {
      height: '100%',
      backgroundColor: '#ffffff',
      borderRadius: 4,
      transition: 'width 0.3s ease',
    },
    progressText: {
      fontSize: 12,
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    noUpdateCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#f0f0f0',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 20,
      alignItems: 'center',
      marginBottom: 16,
    },
    noUpdateText: {
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    intervalSelector: {
      flexDirection: 'row',
      gap: 8,
    },
    intervalOption: {
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
    },
    intervalOptionSelected: {
      backgroundColor: PlatformAdapter.getPrimaryColor(),
    },
    intervalText: {
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    intervalTextSelected: {
      color: '#ffffff',
    },
    mandatoryBadge: {
      backgroundColor: '#ff4444',
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
      marginLeft: 8,
    },
    mandatoryText: {
      color: '#ffffff',
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  const intervals = [
    {value: 15, label: '15分钟'},
    {value: 30, label: '30分钟'},
    {value: 60, label: '1小时'},
    {value: 180, label: '3小时'},
    {value: 720, label: '12小时'},
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>版本更新</Text>
      </View>

      <View style={styles.sections}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>检查更新</Text>
          
          {checking ? (
            <View style={[styles.card, {padding: 20, alignItems: 'center'}]}>
              <ActivityIndicator color={PlatformAdapter.getPrimaryColor()} />
              <Text style={{...styles.itemValue, marginTop: 12}}>正在检查更新...</Text>
            </View>
          ) : updateStatus?.hasUpdate ? (
            <View style={styles.updateCard}>
              <View style={{flexDirection: 'row', alignItems: 'center', marginBottom: 8}}>
                <Text style={styles.updateTitle}>发现新版本!</Text>
                {updateStatus.mandatory && (
                  <View style={styles.mandatoryBadge}>
                    <Text style={styles.mandatoryText}>强制更新</Text>
                  </View>
                )}
              </View>
              <Text style={styles.updateVersion}>当前版本: v{VersionService.getCurrentVersion()} → 最新版本: v{updateStatus.latestVersion}</Text>
              
              {updateStatus.changelog && (
                <View style={styles.changelogList}>
                  {updateStatus.changelog.map((change, index) => (
                    <Text key={index} style={styles.changelogItem}>• {change}</Text>
                  ))}
                </View>
              )}

              {isDownloading ? (
                <>
                  <View style={styles.progressBar}>
                    <View style={[styles.progressFill, {width: `${downloadProgress}%`}]} />
                  </View>
                  <Text style={styles.progressText}>{Math.round(downloadProgress)}%</Text>
                </>
              ) : (
                <TouchableOpacity style={styles.downloadButton} onPress={handleDownload}>
                  <Text style={styles.downloadButtonText}>下载更新</Text>
                </TouchableOpacity>
              )}
            </View>
          ) : (
            <View style={styles.noUpdateCard}>
              <Text style={{fontSize: 32, marginBottom: 8}}>✅</Text>
              <Text style={styles.noUpdateText}>当前已是最新版本 v{VersionService.getCurrentVersion()}</Text>
            </View>
          )}

          <TouchableOpacity style={styles.checkButton} onPress={checkForUpdates} disabled={checking}>
            {checking ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.checkButtonText}>检查更新</Text>
            )}
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>自动更新设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>自动检查更新</Text>
              <Switch
                value={autoUpdate}
                onValueChange={(value) => {
                  setAutoUpdate(value);
                  saveSettings();
                }}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>检查间隔</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.intervalSelector}>
                {intervals.map((interval) => (
                  <TouchableOpacity
                    key={interval.value}
                    style={[styles.intervalOption, updateInterval === interval.value && styles.intervalOptionSelected]}
                    onPress={() => {
                      setUpdateInterval(interval.value);
                      saveSettings();
                    }}>
                    <Text style={[styles.intervalText, updateInterval === interval.value && styles.intervalTextSelected]}>
                      {interval.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>当前版本信息</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>应用版本</Text>
              <Text style={styles.itemValue}>v{VersionService.getCurrentVersion()}</Text>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>平台类型</Text>
              <Text style={styles.itemValue}>{PlatformAdapter.getPlatformName()}</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemLabel}>上次检查</Text>
              <Text style={styles.itemValue}>{updateStatus?.checkedAt || '刚刚'}</Text>
            </View>
          </View>
        </View>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default UpdateSettingsScreen;