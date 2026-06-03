import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import AIService from '../services/AIService';
import PlatformAdapter from '../adapters/PlatformAdapter';

const AISettingsScreen = ({navigation}) => {
  const [settings, setSettings] = useState({});
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [quickAction, setQuickAction] = useState(null);

  useEffect(() => {
    loadSettings();
    checkAIStatus();
  }, []);

  const loadSettings = async () => {
    const saved = await AIService.getSettings();
    setSettings(saved);
    setLoading(false);
  };

  const checkAIStatus = async () => {
    const result = await AIService.getAIStatus();
    setStatus(result);
  };

  const handleSave = async () => {
    setSaving(true);
    const success = await AIService.saveSettings(settings);
    setSaving(false);
    
    if (success) {
      Alert.alert('保存成功', 'AI设置已保存');
    } else {
      Alert.alert('保存失败', '无法保存设置，请重试');
    }
  };

  const handleModelChange = (modelId) => {
    setSettings(prev => ({...prev, model: modelId}));
  };

  const handleMaxTokensChange = (value) => {
    setSettings(prev => ({...prev, maxTokens: value}));
  };

  const handleTemperatureChange = (value) => {
    setSettings(prev => ({...prev, temperature: value}));
  };

  const handleTimeoutChange = (value) => {
    setSettings(prev => ({...prev, timeout: value}));
  };

  const handleMaxRetriesChange = (value) => {
    setSettings(prev => ({...prev, maxRetries: value}));
  };

  const applyPreset = (preset) => {
    const presets = {
      balanced: {temperature: 0.5, maxTokens: 1024},
      creative: {temperature: 0.9, maxTokens: 2048},
      precise: {temperature: 0.1, maxTokens: 512},
      efficient: {temperature: 0.3, maxTokens: 256},
    };
    setSettings(prev => ({...prev, ...presets[preset]}));
    setQuickAction(`已应用「${preset === 'balanced' ? '平衡' : preset === 'creative' ? '创意' : preset === 'precise' ? '精确' : '高效'}」预设`);
    setTimeout(() => setQuickAction(null), 3000);
  };

  const models = AIService.getAvailableModels();

  const tokenOptions = [
    {value: 256, label: '256', desc: '简短回复'},
    {value: 512, label: '512', desc: '标准回复'},
    {value: 1024, label: '1024', desc: '详细回复'},
    {value: 2048, label: '2048', desc: '长篇回复'},
    {value: 4096, label: '4096', desc: '超长回复'},
  ];

  const tempOptions = [
    {value: 0.1, label: '0.1', desc: '精确'},
    {value: 0.3, label: '0.3', desc: '严谨'},
    {value: 0.5, label: '0.5', desc: '平衡'},
    {value: 0.7, label: '0.7', desc: '灵活'},
    {value: 0.9, label: '0.9', desc: '创意'},
  ];

  const timeoutOptions = [
    {value: 10000, label: '10秒'},
    {value: 20000, label: '20秒'},
    {value: 30000, label: '30秒'},
    {value: 60000, label: '60秒'},
  ];

  const retryOptions = [
    {value: 1, label: '1次'},
    {value: 2, label: '2次'},
    {value: 3, label: '3次'},
    {value: 5, label: '5次'},
  ];

  const presetOptions = [
    {id: 'balanced', name: '平衡', desc: '适合日常使用'},
    {id: 'creative', name: '创意', desc: '适合创作场景'},
    {id: 'precise', name: '精确', desc: '适合学术场景'},
    {id: 'efficient', name: '高效', desc: '节省资源'},
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
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemDesc: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.5,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    statusCard: {
      padding: 16,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    statusOnline: {
      backgroundColor: 'rgba(68, 255, 68, 0.1)',
    },
    statusOffline: {
      backgroundColor: 'rgba(255, 68, 68, 0.1)',
    },
    statusHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    statusIndicator: {
      width: 10,
      height: 10,
      borderRadius: 5,
      marginRight: 8,
    },
    statusIndicatorOnline: {
      backgroundColor: '#44ff44',
    },
    statusIndicatorOffline: {
      backgroundColor: '#ff4444',
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
    modelCard: {
      padding: 16,
      borderRadius: PlatformAdapter.getCornerRadius(),
      borderWidth: 2,
      marginBottom: 8,
    },
    modelCardSelected: {
      borderColor: PlatformAdapter.getPrimaryColor(),
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
    },
    modelCardUnselected: {
      borderColor: 'transparent',
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#f8f8f8',
    },
    modelName: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 4,
    },
    modelDesc: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    modelMaxTokens: {
      fontSize: 11,
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    selectorRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
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
    aiBadge: {
      marginTop: 24,
      padding: 16,
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      alignItems: 'center',
    },
    aiIcon: {
      fontSize: 48,
      marginBottom: 12,
    },
    aiTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 4,
    },
    aiDesc: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    presetCard: {
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      borderWidth: 1,
      borderColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#e0e0e0',
    },
    presetCardSelected: {
      borderColor: PlatformAdapter.getPrimaryColor(),
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.05)' : 'rgba(0, 125, 255, 0.05)',
    },
    presetName: {
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    presetDesc: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 2,
    },
    quickActionToast: {
      position: 'absolute',
      top: 100,
      left: '10%',
      right: '10%',
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      padding: 16,
      borderRadius: PlatformAdapter.getCornerRadius(),
      alignItems: 'center',
      zIndex: 100,
      ...PlatformAdapter.getElevation(),
    },
    quickActionText: {
      color: '#ffffff',
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    featureCard: {
      padding: 16,
      borderRadius: PlatformAdapter.getCornerRadius(),
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      ...PlatformAdapter.getElevation(),
    },
    featureHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    featureItem: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 8,
    },
    featureLabel: {
      flex: 1,
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    featureIcon: {
      fontSize: 16,
      marginRight: 12,
    },
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>AI设置</Text>
        </View>
        <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
          <ActivityIndicator color={PlatformAdapter.getPrimaryColor()} />
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>AI助手设置</Text>
        <Text style={styles.subtitle}>配置智能学习助手的各项功能</Text>
      </View>

      {quickAction && (
        <View style={styles.quickActionToast}>
          <Text style={styles.quickActionText}>{quickAction}</Text>
        </View>
      )}

      <View style={styles.sections}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>服务状态</Text>
          <View style={[styles.statusCard, status?.online ? styles.statusOnline : styles.statusOffline]}>
            <View style={styles.statusHeader}>
              <View style={[styles.statusIndicator, status?.online ? styles.statusIndicatorOnline : styles.statusIndicatorOffline]} />
              <Text style={styles.statusTitle}>
                {status?.online ? 'AI服务在线' : 'AI服务离线'}
              </Text>
            </View>
            {status?.online && (
              <>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>在线时长</Text>
                  <Text style={styles.statusValue}>{status?.uptime || '--'}</Text>
                </View>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>今日请求</Text>
                  <Text style={styles.statusValue}>{status?.requests_today || '0'} 次</Text>
                </View>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>可用模型</Text>
                  <Text style={styles.statusValue}>{status?.models?.length || 0} 个</Text>
                </View>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>API版本</Text>
                  <Text style={styles.statusValue}>{status?.version || '--'}</Text>
                </View>
              </>
            )}
            {!status?.online && (
              <Text style={{...styles.statusLabel, marginTop: 8}}>
                {status?.message || '无法连接到AI服务，请检查网络连接'}
              </Text>
            )}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI功能总开关</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>启用AI助手</Text>
              <Switch
                value={settings.enabled}
                onValueChange={(value) => setSettings(prev => ({...prev, enabled: value}))}
                thumbColor={PlatformAdapter.getPrimaryColor()}
                trackColor={{
                  true: PlatformAdapter.getPrimaryColor(),
                  false: 'rgba(0,0,0,0.2)',
                }}
              />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>预设配置</Text>
          <View style={styles.selectorRow}>
            {presetOptions.map((preset) => (
              <TouchableOpacity
                key={preset.id}
                style={[styles.presetCard, settings.temperature === (preset.id === 'balanced' ? 0.5 : preset.id === 'creative' ? 0.9 : preset.id === 'precise' ? 0.1 : 0.3) && styles.presetCardSelected]}
                onPress={() => applyPreset(preset.id)}>
                <Text style={styles.presetName}>{preset.name}</Text>
                <Text style={styles.presetDesc}>{preset.desc}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>选择AI模型</Text>
          {models.map((model) => (
            <TouchableOpacity
              key={model.id}
              style={[styles.modelCard, settings.model === model.id ? styles.modelCardSelected : styles.modelCardUnselected]}
              onPress={() => handleModelChange(model.id)}>
              <Text style={styles.modelName}>{model.name}</Text>
              <Text style={styles.modelDesc}>{model.description}</Text>
              {model.maxTokens && (
                <Text style={styles.modelMaxTokens}>最大Token: {model.maxTokens.toLocaleString()}</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>响应长度</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>Token数量</Text>
              <Text style={styles.itemValue}>{settings.maxTokens} tokens</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {tokenOptions.map((option) => (
                  <TouchableOpacity
                    key={option.value}
                    style={[styles.selectorOption, settings.maxTokens === option.value && styles.selectorOptionSelected]}
                    onPress={() => handleMaxTokensChange(option.value)}>
                    <Text style={[styles.selectorText, settings.maxTokens === option.value && styles.selectorTextSelected]}>
                      {option.label}
                    </Text>
                    <Text style={[styles.selectorDesc, settings.maxTokens === option.value && styles.selectorDescSelected]}>
                      {option.desc}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>创意程度</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>Temperature</Text>
              <Text style={styles.itemValue}>{settings.temperature}</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {tempOptions.map((option) => (
                  <TouchableOpacity
                    key={option.value}
                    style={[styles.selectorOption, settings.temperature === option.value && styles.selectorOptionSelected]}
                    onPress={() => handleTemperatureChange(option.value)}>
                    <Text style={[styles.selectorText, settings.temperature === option.value && styles.selectorTextSelected]}>
                      {option.label}
                    </Text>
                    <Text style={[styles.selectorDesc, settings.temperature === option.value && styles.selectorDescSelected]}>
                      {option.desc}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>网络设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>请求超时</Text>
              <Text style={styles.itemValue}>{timeoutOptions.find(o => o.value === settings.timeout)?.label || '30秒'}</Text>
            </View>
            <View style={styles.cardItem}>
              <View style={styles.selectorRow}>
                {timeoutOptions.map((option) => (
                  <TouchableOpacity
                    key={option.value}
                    style={[styles.selectorOption, settings.timeout === option.value && styles.selectorOptionSelected]}
                    onPress={() => handleTimeoutChange(option.value)}>
                    <Text style={[styles.selectorText, settings.timeout === option.value && styles.selectorTextSelected]}>
                      {option.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemLabel}>最大重试次数</Text>
              <Text style={styles.itemValue}>{settings.maxRetries} 次</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {retryOptions.map((option) => (
                  <TouchableOpacity
                    key={option.value}
                    style={[styles.selectorOption, settings.maxRetries === option.value && styles.selectorOptionSelected]}
                    onPress={() => handleMaxRetriesChange(option.value)}>
                    <Text style={[styles.selectorText, settings.maxRetries === option.value && styles.selectorTextSelected]}>
                      {option.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI功能模块</Text>
          <View style={styles.featureCard}>
            <Text style={styles.featureHeader}>可用功能</Text>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>✓</Text>
              <Text style={styles.featureLabel}>智能问答</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>✓</Text>
              <Text style={styles.featureLabel}>题目生成</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>✓</Text>
              <Text style={styles.featureLabel}>作业批改</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>✓</Text>
              <Text style={styles.featureLabel}>学习建议</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>✓</Text>
              <Text style={styles.featureLabel}>文本摘要</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>✓</Text>
              <Text style={styles.featureLabel}>多语言翻译</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity style={styles.saveButton} onPress={handleSave} disabled={saving}>
          {saving ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.saveButtonText}>保存设置</Text>
          )}
        </TouchableOpacity>
      </View>

      <View style={[styles.sections, styles.aiBadge]}>
        <Text style={styles.aiIcon}>🤖</Text>
        <Text style={styles.aiTitle}>智能学习助手</Text>
        <Text style={styles.aiDesc}>
          利用先进的AI技术，为您提供智能问答、题目生成、作业批改、学习建议等功能。
          根据您的学习需求，选择合适的模型和参数，获得最佳的学习体验。
        </Text>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default AISettingsScreen;