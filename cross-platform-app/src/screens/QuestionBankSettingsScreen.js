import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert, FlatList} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';
import OfflineStorageService from '../services/OfflineStorageService';

const QuestionBankSettingsScreen = ({navigation}) => {
  const [aiEnabled, setAiEnabled] = useState(true);
  const [aiStatus, setAiStatus] = useState(null);
  const [autoGenerate, setAutoGenerate] = useState(false);
  const [generateCount, setGenerateCount] = useState(10);
  const [generateDifficulty, setGenerateDifficulty] = useState('mixed');
  const [questionStats, setQuestionStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    loadSettings();
    checkAIStatus();
    loadQuestionStats();
    loadCategories();
  }, []);

  const loadSettings = async () => {
    const settings = await AIService.getSettings();
    setAiEnabled(settings.enabled);
  };

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadQuestionStats = async () => {
    try {
      const stats = await OfflineStorageService.getQuestionStats();
      setQuestionStats(stats);
    } catch (error) {
      console.warn('获取题目统计失败:', error);
    }
  };

  const loadCategories = async () => {
    const cats = [
      {id: 'all', name: '全部', icon: '📚', count: 0},
      {id: 'chinese', name: '语文', icon: '📖', count: 0},
      {id: 'math', name: '数学', icon: '📐', count: 0},
      {id: 'english', name: '英语', icon: '🔤', count: 0},
      {id: 'physics', name: '物理', icon: '⚛️', count: 0},
      {id: 'chemistry', name: '化学', icon: '🧪', count: 0},
      {id: 'biology', name: '生物', icon: '🧬', count: 0},
      {id: 'history', name: '历史', icon: '📜', count: 0},
      {id: 'geography', name: '地理', icon: '🌍', count: 0},
      {id: 'politics', name: '政治', icon: '📖', count: 0},
      {id: 'japanese', name: '日语', icon: '🌸', count: 0},
    ];
    setCategories(cats);
  };

  const handleGenerateQuestions = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法生成题目，请确保AI服务在线');
      return;
    }

    setIsGenerating(true);
    try {
      const result = await AIService.generateQuestions({
        count: generateCount,
        difficulty: generateDifficulty,
        category: selectedCategory === 'all' ? undefined : selectedCategory,
      });

      if (result.success) {
        Alert.alert('生成成功', `成功生成 ${result.count} 道题目`);
        loadQuestionStats();
      } else {
        Alert.alert('生成失败', result.message);
      }
    } catch (error) {
      Alert.alert('生成失败', error.message);
    }
    setIsGenerating(false);
  };

  const handleSyncQuestions = async () => {
    try {
      const result = await OfflineStorageService.syncQuestions();
      if (result.success) {
        Alert.alert('同步成功', `${result.syncedCount} 道题目已同步`);
        loadQuestionStats();
      } else {
        Alert.alert('同步失败', result.message);
      }
    } catch (error) {
      Alert.alert('同步失败', error.message);
    }
  };

  const handleClearQuestions = async () => {
    Alert.alert(
      '确认清空',
      '确定要清空所有题目吗？此操作不可恢复！',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: async () => {
            try {
              const result = await OfflineStorageService.clearQuestions();
              if (result.success) {
                Alert.alert('清空成功', '所有题目已删除');
                loadQuestionStats();
              } else {
                Alert.alert('清空失败', result.message);
              }
            } catch (error) {
              Alert.alert('清空失败', error.message);
            }
          },
        },
      ]
    );
  };

  const difficultyOptions = [
    {id: 'easy', name: '简单', desc: '基础题'},
    {id: 'medium', name: '中等', desc: '进阶题'},
    {id: 'hard', name: '困难', desc: '挑战题'},
    {id: 'mixed', name: '混合', desc: '随机难度'},
  ];

  const countOptions = [5, 10, 20, 50, 100];

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
    badgeOnline: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    badgeOffline: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
      color: '#ff4444',
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
    categoryCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    categoryHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    categoryTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    categoryList: {
      padding: 8,
    },
    categoryItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    categoryItemSelected: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
    },
    categoryIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    categoryName: {
      flex: 1,
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    categoryCount: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
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
    actionButtonDisabled: {
      opacity: 0.5,
    },
    dangerButton: {
      backgroundColor: '#ff4444',
      alignItems: 'center',
      padding: 16,
      marginTop: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    dangerButtonText: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>题库设置</Text>
        <Text style={styles.subtitle}>管理题库内容和AI生成设置</Text>
      </View>

      <View style={styles.sections}>
        {questionStats && (
          <View style={styles.statsCard}>
            <Text style={styles.statsHeader}>📊 题库统计</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{questionStats.total || 0}</Text>
                <Text style={styles.statLabel}>总题目数</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{questionStats.categories || 0}</Text>
                <Text style={styles.statLabel}>学科数</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{questionStats.unSynced || 0}</Text>
                <Text style={styles.statLabel}>待同步</Text>
              </View>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI题目生成</Text>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>AI服务</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <View style={[styles.aiStatusIndicator, aiStatus.online ? styles.aiOnline : styles.aiOffline]} />
                <Text style={styles.aiStatusValue}>{aiStatus.online ? '在线' : '离线'}</Text>
              </View>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>今日生成</Text>
              <Text style={styles.aiStatusValue}>{aiStatus.requests_today || 0} 次</Text>
            </View>
            {aiStatus.online && (
              <View style={styles.aiStatusRow}>
                <Text style={styles.aiStatusLabel}>可用模型</Text>
                <Text style={styles.aiStatusValue}>{aiStatus.models?.length || 0} 个</Text>
              </View>
            )}
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI生成设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🤖</Text>
              <Text style={styles.itemLabel}>启用AI生成</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <Switch
                  value={aiEnabled}
                  onValueChange={(value) => setAiEnabled(value)}
                  thumbColor={PlatformAdapter.getPrimaryColor()}
                />
                {aiEnabled && (
                  <Text style={[styles.itemBadge, aiStatus?.online ? styles.badgeOnline : styles.badgeOffline]}>
                    {aiStatus?.online ? 'AI在线' : 'AI离线'}
                  </Text>
                )}
              </View>
            </View>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>⚡</Text>
              <Text style={styles.itemLabel}>自动生成</Text>
              <Switch
                value={autoGenerate}
                onValueChange={(value) => setAutoGenerate(value)}
                thumbColor={PlatformAdapter.getPrimaryColor()}
              />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>选择学科</Text>
          <View style={styles.categoryCard}>
            <View style={styles.categoryHeader}>
              <Text style={styles.categoryTitle}>📚 学科分类</Text>
            </View>
            <View style={styles.categoryList}>
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.id}
                  style={[styles.categoryItem, selectedCategory === category.id && styles.categoryItemSelected]}
                  onPress={() => setSelectedCategory(category.id)}>
                  <Text style={styles.categoryIcon}>{category.icon}</Text>
                  <Text style={styles.categoryName}>{category.name}</Text>
                  <Text style={styles.categoryCount}>{category.count}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>生成数量</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>🔢</Text>
              <Text style={styles.itemLabel}>题目数量</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {countOptions.map((count) => (
                  <TouchableOpacity
                    key={count}
                    style={[styles.selectorOption, generateCount === count && styles.selectorOptionSelected]}
                    onPress={() => setGenerateCount(count)}>
                    <Text style={[styles.selectorText, generateCount === count && styles.selectorTextSelected]}>
                      {count}
                    </Text>
                    <Text style={[styles.selectorDesc, generateCount === count && styles.selectorDescSelected]}>
                      道题
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>难度设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>📊</Text>
              <Text style={styles.itemLabel}>题目难度</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {difficultyOptions.map((option) => (
                  <TouchableOpacity
                    key={option.id}
                    style={[styles.selectorOption, generateDifficulty === option.id && styles.selectorOptionSelected]}
                    onPress={() => setGenerateDifficulty(option.id)}>
                    <Text style={[styles.selectorText, generateDifficulty === option.id && styles.selectorTextSelected]}>
                      {option.name}
                    </Text>
                    <Text style={[styles.selectorDesc, generateDifficulty === option.id && styles.selectorDescSelected]}>
                      {option.desc}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>题库操作</Text>
          <View style={styles.card}>
            <TouchableOpacity 
              style={[styles.cardItem, styles.cardItemLast]} 
              onPress={handleGenerateQuestions} 
              disabled={!aiStatus?.online || isGenerating}>
              <Text style={styles.itemIcon}>✨</Text>
              <Text style={styles.itemLabel}>{isGenerating ? '生成中...' : 'AI生成题目'}</Text>
              {isGenerating && <ActivityIndicator color={PlatformAdapter.getPrimaryColor()} size="small" />}
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <TouchableOpacity style={[styles.cardItem, styles.cardItemLast]} onPress={handleSyncQuestions}>
              <Text style={styles.itemIcon}>☁️</Text>
              <Text style={styles.itemLabel}>同步到云端</Text>
              <Text style={styles.itemValue}>上传本地题目</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.dangerButton} 
          onPress={handleClearQuestions}
          disabled={!questionStats || questionStats.total === 0}>
          <Text style={styles.dangerButtonText}>清空题库</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default QuestionBankSettingsScreen;