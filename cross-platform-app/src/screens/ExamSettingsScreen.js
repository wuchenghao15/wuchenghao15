import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';

const ExamSettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjects, setSelectedSubjects] = useState([]);
  const [examTypes, setExamTypes] = useState([]);
  const [selectedExamType, setSelectedExamType] = useState('practice');
  const [examDuration, setExamDuration] = useState(60);
  const [questionCount, setQuestionCount] = useState(20);
  const [difficulty, setDifficulty] = useState('mixed');
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadStats();
    loadSubjects();
    loadExamTypes();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadStats = async () => {
    const statsData = {
      totalExams: 156,
      completedExams: 142,
      avgScore: 82.3,
      highestScore: 98,
      studyTime: '128小时',
      streak: 15,
      ranking: 12,
      totalStudents: 450,
    };
    setStats(statsData);
  };

  const loadSubjects = async () => {
    const subs = [
      {id: 'chinese', name: '语文', icon: '📖', enabled: true, completed: 15, total: 20},
      {id: 'math', name: '数学', icon: '📐', enabled: true, completed: 12, total: 18},
      {id: 'english', name: '英语', icon: '🔤', enabled: true, completed: 18, total: 20},
      {id: 'physics', name: '物理', icon: '⚛️', enabled: true, completed: 10, total: 15},
      {id: 'chemistry', name: '化学', icon: '🧪', enabled: true, completed: 11, total: 15},
      {id: 'biology', name: '生物', icon: '🧬', enabled: false, completed: 5, total: 10},
      {id: 'history', name: '历史', icon: '📜', enabled: true, completed: 14, total: 16},
      {id: 'geography', name: '地理', icon: '🌍', enabled: true, completed: 13, total: 16},
      {id: 'politics', name: '政治', icon: '📖', enabled: false, completed: 3, total: 10},
      {id: 'japanese', name: '日语', icon: '🌸', enabled: true, completed: 8, total: 12},
    ];
    setSubjects(subs);
    setSelectedSubjects(['chinese', 'math', 'english']);
  };

  const loadExamTypes = async () => {
    const types = [
      {id: 'practice', name: '模拟练习', icon: '📝', desc: '无压力练习，不计入成绩'},
      {id: 'quiz', name: '随堂测验', icon: '📋', desc: '10分钟小测验'},
      {id: 'midterm', name: '期中考试', icon: '📚', desc: '阶段性评估'},
      {id: 'final', name: '期末考试', icon: '🎯', desc: '学期总结评估'},
      {id: 'placement', name: '摸底测试', icon: '🔍', desc: '能力诊断测试'},
    ];
    setExamTypes(types);
  };

  const handleSubjectToggle = (subjectId) => {
    if (selectedSubjects.includes(subjectId)) {
      setSelectedSubjects(prev => prev.filter(id => id !== subjectId));
    } else {
      if (selectedSubjects.length >= 5) {
        Alert.alert('提示', '最多选择5个科目');
        return;
      }
      setSelectedSubjects(prev => [...prev, subjectId]);
    }
  };

  const handleStartExam = async () => {
    if (selectedSubjects.length === 0) {
      Alert.alert('提示', '请至少选择一个科目');
      return;
    }

    navigation.navigate('ExamScreen', {
      subjects: selectedSubjects,
      examType: selectedExamType,
      duration: examDuration,
      questionCount,
      difficulty,
    });
  };

  const handleAIGenerate = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法使用AI出题功能');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.generateExam({
        subjects: selectedSubjects,
        count: questionCount,
        difficulty,
      });

      if (result.success) {
        Alert.alert('AI出题成功', `已生成${result.count}道题目`);
        navigation.navigate('ExamScreen', {
          testId: result.testId,
          isAI: true,
        });
      } else {
        Alert.alert('出题失败', result.message);
      }
    } catch (error) {
      Alert.alert('出题失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleAIAnalysis = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI分析');
      return;
    }

    try {
      const result = await AIService.analyzeExamHistory({
        examCount: stats?.totalExams,
        avgScore: stats?.avgScore,
        subjects: selectedSubjects,
      });

      if (result.success) {
        Alert.alert('分析完成', `学习诊断：\n\n${result.diagnosis}\n\n提升建议：${result.suggestions}`);
      } else {
        Alert.alert('分析失败', result.message);
      }
    } catch (error) {
      Alert.alert('分析失败', error.message);
    }
  };

  const durationOptions = [30, 45, 60, 90, 120];
  const countOptions = [10, 20, 30, 50, 100];
  const difficultyOptions = [
    {id: 'easy', name: '简单'},
    {id: 'medium', name: '中等'},
    {id: 'hard', name: '困难'},
    {id: 'mixed', name: '混合'},
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
      flexWrap: 'wrap',
      gap: 16,
    },
    statItem: {
      flex: 1,
      minWidth: 100,
      alignItems: 'center',
    },
    statValue: {
      fontSize: 20,
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
    subjectCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    subjectHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    subjectTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectList: {
      padding: 8,
    },
    subjectItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    subjectItemSelected: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderWidth: 1,
      borderColor: PlatformAdapter.getPrimaryColor(),
    },
    subjectIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    subjectName: {
      flex: 1,
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectProgress: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
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
    typeCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    typeHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    typeTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    typeList: {
      padding: 8,
    },
    typeItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    typeItemSelected: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderWidth: 1,
      borderColor: PlatformAdapter.getPrimaryColor(),
    },
    typeIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    typeInfo: {
      flex: 1,
    },
    typeName: {
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    typeDesc: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 2,
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
    actionButtonDisabled: {
      opacity: 0.5,
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>考试系统</Text>
        <Text style={styles.subtitle}>管理考试设置和AI出题</Text>
      </View>

      <View style={styles.sections}>
        {stats && (
          <View style={styles.statsCard}>
            <Text style={styles.statsHeader}>📊 考试统计</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.totalExams}</Text>
                <Text style={styles.statLabel}>总考试</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.completedExams}</Text>
                <Text style={styles.statLabel}>已完成</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.avgScore}</Text>
                <Text style={styles.statLabel}>平均分</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>第{stats.ranking}名</Text>
                <Text style={styles.statLabel}>年级排名</Text>
              </View>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI考试助手</Text>
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
              <Text style={styles.aiStatusValue}>智能出题、AI批改、学习诊断</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>选择科目</Text>
          <View style={styles.subjectCard}>
            <View style={styles.subjectHeader}>
              <Text style={styles.subjectTitle}>📚 考试科目</Text>
            </View>
            <View style={styles.subjectList}>
              {subjects.map((subject) => (
                <TouchableOpacity
                  key={subject.id}
                  style={[styles.subjectItem, selectedSubjects.includes(subject.id) && styles.subjectItemSelected]}
                  onPress={() => handleSubjectToggle(subject.id)}>
                  <Text style={styles.subjectIcon}>{subject.icon}</Text>
                  <Text style={styles.subjectName}>{subject.name}</Text>
                  <Text style={styles.subjectProgress}>{subject.completed}/{subject.total}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>考试类型</Text>
          <View style={styles.typeCard}>
            <View style={styles.typeHeader}>
              <Text style={styles.typeTitle}>🎯 选择考试类型</Text>
            </View>
            <View style={styles.typeList}>
              {examTypes.map((examType) => (
                <TouchableOpacity
                  key={examType.id}
                  style={[styles.typeItem, selectedExamType === examType.id && styles.typeItemSelected]}
                  onPress={() => setSelectedExamType(examType.id)}>
                  <Text style={styles.typeIcon}>{examType.icon}</Text>
                  <View style={styles.typeInfo}>
                    <Text style={styles.typeName}>{examType.name}</Text>
                    <Text style={styles.typeDesc}>{examType.desc}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>考试时长</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>⏱️</Text>
              <Text style={styles.itemLabel}>考试时间</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {durationOptions.map((duration) => (
                  <TouchableOpacity
                    key={duration}
                    style={[styles.selectorOption, examDuration === duration && styles.selectorOptionSelected]}
                    onPress={() => setExamDuration(duration)}>
                    <Text style={[styles.selectorText, examDuration === duration && styles.selectorTextSelected]}>
                      {duration}分钟
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>题目数量</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>📝</Text>
              <Text style={styles.itemLabel}>题目数</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {countOptions.map((count) => (
                  <TouchableOpacity
                    key={count}
                    style={[styles.selectorOption, questionCount === count && styles.selectorOptionSelected]}
                    onPress={() => setQuestionCount(count)}>
                    <Text style={[styles.selectorText, questionCount === count && styles.selectorTextSelected]}>
                      {count}题
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
              <Text style={styles.itemLabel}>难度等级</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.selectorRow}>
                {difficultyOptions.map((option) => (
                  <TouchableOpacity
                    key={option.id}
                    style={[styles.selectorOption, difficulty === option.id && styles.selectorOptionSelected]}
                    onPress={() => setDifficulty(option.id)}>
                    <Text style={[styles.selectorText, difficulty === option.id && styles.selectorTextSelected]}>
                      {option.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleStartExam}>
          <Text style={styles.actionButtonText}>🚀 开始考试</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButtonSecondary} 
          onPress={handleAIGenerate}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color={PlatformAdapter.getTextColor()} />
          ) : (
            <Text style={styles.actionButtonTextSecondary}>🤖 AI智能出题</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButtonSecondary} 
          onPress={handleAIAnalysis}
          disabled={!aiStatus?.online}>
          <Text style={styles.actionButtonTextSecondary}>📊 AI学习诊断</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default ExamSettingsScreen;