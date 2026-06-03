import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';

const KernelSettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [kernelInfo, setKernelInfo] = useState(null);
  const [performanceMode, setPerformanceMode] = useState('balanced');
  const [memoryOptimization, setMemoryOptimization] = useState(true);
  const [backgroundSync, setBackgroundSync] = useState(true);
  const [aiOptimization, setAiOptimization] = useState(true);
  const [gpuAcceleration, setGpuAcceleration] = useState(true);
  const [jitCompiler, setJitCompiler] = useState(true);
  const [zramEnabled, setZramEnabled] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);

  useEffect(() => {
    checkAIStatus();
    loadKernelInfo();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadKernelInfo = async () => {
    const info = {
      version: '5.15.0-mtscos',
      buildDate: '2026-05-12',
      architecture: 'arm64-v8a',
      memoryUsage: '2.4GB / 8GB',
      cpuUsage: '15%',
      uptime: '4小时32分',
      processes: 45,
      threads: 128,
      gpuInfo: 'Mali-G78',
      aiAcceleration: 'Enabled',
      cacheSize: '512MB',
      swapSize: '2GB',
      filesystem: 'ext4',
      kernelCompiler: 'GCC 11.2',
      securityPatch: '2026-05-01',
      thermalStatus: 'Normal',
      batteryTemp: '38°C',
    };
    setKernelInfo(info);
  };

  const handleAIKernelOptimize = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI内核优化');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.optimizeKernel({
        performanceMode,
        memoryOptimization,
        aiAcceleration: aiOptimization,
        gpuAcceleration,
        jitCompiler,
        zramEnabled,
        platform: PlatformAdapter.isHyperOS() ? 'hyperos' : PlatformAdapter.isHarmonyOS() ? 'harmonyos' : 'android',
      });

      if (result.success) {
        Alert.alert('优化完成', `内核优化成功！\n\n优化项：${result.optimizations}\n性能提升：${result.performanceGain}%`);
      } else {
        Alert.alert('优化失败', result.message);
      }
    } catch (error) {
      Alert.alert('优化失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleAIDiagnosis = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI诊断');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.diagnoseKernel({
        kernelInfo,
        performanceMode,
        memoryOptimization,
        backgroundSync,
        aiOptimization,
      });

      if (result.success) {
        setDiagnosisResult(result);
        Alert.alert('诊断完成', `健康评分：${result.healthScore}/100\n\n问题：${result.issues.length}个\n建议：${result.suggestions}`);
      } else {
        Alert.alert('诊断失败', result.message);
      }
    } catch (error) {
      Alert.alert('诊断失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleClearCache = () => {
    Alert.alert(
      '确认清除',
      '确定要清除内核缓存吗？这可能会提高性能。',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            setIsProcessing(true);
            try {
              await new Promise(resolve => setTimeout(resolve, 1500));
              Alert.alert('清除完成', '内核缓存已清除');
            } catch (error) {
              Alert.alert('清除失败', error.message);
            }
            setIsProcessing(false);
          },
        },
      ]
    );
  };

  const handleRestartServices = () => {
    Alert.alert(
      '确认重启',
      '确定要重启核心服务吗？这将暂时中断应用。',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            setIsProcessing(true);
            try {
              await new Promise(resolve => setTimeout(resolve, 2000));
              Alert.alert('重启完成', '核心服务已重启');
            } catch (error) {
              Alert.alert('重启失败', error.message);
            }
            setIsProcessing(false);
          },
        },
      ]
    );
  };

  const handleHotRestart = () => {
    Alert.alert(
      '确认热重启',
      '确定要进行热重启吗？应用将在不重启系统的情况下重新加载核心模块。',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            setIsProcessing(true);
            try {
              await new Promise(resolve => setTimeout(resolve, 1000));
              Alert.alert('热重启完成', '核心模块已重新加载');
            } catch (error) {
              Alert.alert('热重启失败', error.message);
            }
            setIsProcessing(false);
          },
        },
      ]
    );
  };

  const performanceOptions = [
    {id: 'power_saving', name: '省电模式', icon: '🔋', desc: '优先省电', color: '#4ade80'},
    {id: 'balanced', name: '平衡模式', icon: '⚖️', desc: '性能与续航平衡', color: '#60a5fa'},
    {id: 'performance', name: '性能模式', icon: '🚀', desc: '最佳性能', color: '#f472b6'},
    {id: 'turbo', name: '极速模式', icon: '⚡', desc: '极限性能', color: '#fbbf24'},
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
    kernelCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    kernelHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    kernelGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    kernelItem: {
      flex: 1,
      minWidth: 120,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    kernelLabel: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    kernelValue: {
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
    statsCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(68, 255, 68, 0.1)' : 'rgba(68, 255, 68, 0.1)',
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
    statsRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 8,
    },
    statsLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statsValue: {
      fontSize: 14,
      color: '#44ff44',
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    thermalCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 193, 7, 0.1)' : 'rgba(255, 193, 7, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    thermalHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    thermalRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 8,
    },
    thermalLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    thermalValue: {
      fontSize: 14,
      color: '#ffc107',
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    selectorRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
      padding: 8,
    },
    selectorOption: {
      paddingHorizontal: 12,
      paddingVertical: 12,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      minWidth: 90,
    },
    selectorOptionSelected: {
      backgroundColor: PlatformAdapter.getPrimaryColor(),
    },
    selectorIcon: {
      fontSize: 20,
      marginBottom: 4,
    },
    selectorText: {
      fontSize: 13,
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    selectorDesc: {
      fontSize: 11,
      fontFamily: PlatformAdapter.getFontFamily(),
      opacity: 0.6,
      marginTop: 2,
    },
    selectorTextSelected: {
      color: '#ffffff',
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
    actionButtonWarning: {
      backgroundColor: '#ffc107',
      alignItems: 'center',
      padding: 16,
      marginTop: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    actionButtonTextWarning: {
      color: '#000000',
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
        <Text style={styles.title}>内核系统</Text>
        <Text style={styles.subtitle}>管理系统内核和性能设置</Text>
      </View>

      <View style={styles.sections}>
        {kernelInfo && (
          <View style={styles.kernelCard}>
            <Text style={styles.kernelHeader}>⚙️ 内核信息</Text>
            <View style={styles.kernelGrid}>
              <View style={styles.kernelItem}>
                <Text style={styles.kernelLabel}>版本</Text>
                <Text style={styles.kernelValue}>{kernelInfo.version}</Text>
              </View>
              <View style={styles.kernelItem}>
                <Text style={styles.kernelLabel}>架构</Text>
                <Text style={styles.kernelValue}>{kernelInfo.architecture}</Text>
              </View>
              <View style={styles.kernelItem}>
                <Text style={styles.kernelLabel}>GPU</Text>
                <Text style={styles.kernelValue}>{kernelInfo.gpuInfo}</Text>
              </View>
              <View style={styles.kernelItem}>
                <Text style={styles.kernelLabel}>运行时间</Text>
                <Text style={styles.kernelValue}>{kernelInfo.uptime}</Text>
              </View>
              <View style={styles.kernelItem}>
                <Text style={styles.kernelLabel}>缓存</Text>
                <Text style={styles.kernelValue}>{kernelInfo.cacheSize}</Text>
              </View>
              <View style={styles.kernelItem}>
                <Text style={styles.kernelLabel}>交换分区</Text>
                <Text style={styles.kernelValue}>{kernelInfo.swapSize}</Text>
              </View>
            </View>
          </View>
        )}

        {kernelInfo && (
          <View style={styles.statsCard}>
            <Text style={styles.statsHeader}>📊 系统状态</Text>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>内存使用</Text>
              <Text style={styles.statsValue}>{kernelInfo.memoryUsage}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>CPU使用率</Text>
              <Text style={styles.statsValue}>{kernelInfo.cpuUsage}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>进程数</Text>
              <Text style={styles.statsValue}>{kernelInfo.processes}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statsLabel}>AI加速</Text>
              <Text style={styles.statsValue}>{kernelInfo.aiAcceleration}</Text>
            </View>
          </View>
        )}

        {kernelInfo && (
          <View style={styles.thermalCard}>
            <Text style={styles.thermalHeader}>🌡️ 温度状态</Text>
            <View style={styles.thermalRow}>
              <Text style={styles.thermalLabel}>热状态</Text>
              <Text style={styles.thermalValue}>{kernelInfo.thermalStatus}</Text>
            </View>
            <View style={styles.thermalRow}>
              <Text style={styles.thermalLabel}>电池温度</Text>
              <Text style={styles.thermalValue}>{kernelInfo.batteryTemp}</Text>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI内核助手</Text>
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
              <Text style={styles.aiStatusValue}>智能优化、性能诊断、资源调度</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>性能模式</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>⚡</Text>
              <Text style={styles.itemLabel}>性能模式</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {performanceOptions.map((option) => (
                  <TouchableOpacity
                    key={option.id}
                    style={[styles.selectorOption, performanceMode === option.id && styles.selectorOptionSelected]}
                    onPress={() => setPerformanceMode(option.id)}>
                    <Text style={styles.selectorIcon}>{option.icon}</Text>
                    <Text style={[styles.selectorText, performanceMode === option.id && styles.selectorTextSelected]}>
                      {option.name}
                    </Text>
                    <Text style={[styles.selectorDesc, performanceMode === option.id && styles.selectorDescSelected]}>
                      {option.desc}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>内核优化</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>💾</Text>
              <Text style={styles.itemLabel}>内存优化</Text>
              <Switch
                value={memoryOptimization}
                onValueChange={(value) => setMemoryOptimization(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>☁️</Text>
              <Text style={styles.itemLabel}>后台同步</Text>
              <Switch
                value={backgroundSync}
                onValueChange={(value) => setBackgroundSync(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🤖</Text>
              <Text style={styles.itemLabel}>AI加速</Text>
              <Switch
                value={aiOptimization}
                onValueChange={(value) => setAiOptimization(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🎮</Text>
              <Text style={styles.itemLabel}>GPU加速</Text>
              <Switch
                value={gpuAcceleration}
                onValueChange={(value) => setGpuAcceleration(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>⚙️</Text>
              <Text style={styles.itemLabel}>JIT编译</Text>
              <Switch
                value={jitCompiler}
                onValueChange={(value) => setJitCompiler(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <Text style={styles.itemIcon}>🔄</Text>
              <Text style={styles.itemLabel}>ZRAM压缩</Text>
              <Switch
                value={zramEnabled}
                onValueChange={(value) => setZramEnabled(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIKernelOptimize}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI内核优化</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIDiagnosis}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🔍 AI性能诊断</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonWarning} onPress={handleHotRestart} disabled={isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#000000" />
          ) : (
            <Text style={styles.actionButtonTextWarning}>🔥 热重启核心模块</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary} onPress={handleClearCache} disabled={isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color={PlatformAdapter.getTextColor()} />
          ) : (
            <Text style={styles.actionButtonTextSecondary}>🗑️ 清除内核缓存</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary} onPress={handleRestartServices} disabled={isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color={PlatformAdapter.getTextColor()} />
          ) : (
            <Text style={styles.actionButtonTextSecondary}>🔄 重启核心服务</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📋 查看系统日志</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📊 性能监控</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>🔧 内核模块管理</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default KernelSettingsScreen;