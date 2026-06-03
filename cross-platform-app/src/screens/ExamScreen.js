import React, {useState} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';

const ExamScreen = ({navigation}) => {
  const [loading, setLoading] = useState(false);

  const examCategories = [
    {id: 'chinese', name: '语文', icon: '📖', count: 156, color: '#ff6b6b'},
    {id: 'math', name: '数学', icon: '🧮', count: 234, color: '#4ecdc4'},
    {id: 'english', name: '英语', icon: '🔤', count: 189, color: '#45b7d1'},
    {id: 'physics', name: '物理', icon: '⚛️', count: 145, color: '#96ceb4'},
    {id: 'chemistry', name: '化学', icon: '🧪', count: 123, color: '#ffeaa7'},
    {id: 'biology', name: '生物', icon: '🧬', count: 98, color: '#dfe6e9'},
    {id: 'history', name: '历史', icon: '📜', count: 87, color: '#fd79a8'},
    {id: 'geography', name: '地理', icon: '🌍', count: 112, color: '#a29bfe'},
    {id: 'politics', name: '政治', icon: '⚖️', count: 76, color: '#00b894'},
    {id: 'japanese', name: '日语', icon: '🇯🇵', count: 54, color: '#e17055'},
  ];

  const recentExams = [
    {id: 1, name: '高一数学期中测试', date: '2024-01-15', score: 92, total: 100},
    {id: 2, name: '英语摸底测试', date: '2024-01-14', score: 85, total: 100},
    {id: 3, name: '物理单元检测', date: '2024-01-12', score: 78, total: 100},
    {id: 4, name: '语文古诗词默写', date: '2024-01-10', score: 95, total: 100},
  ];

  const handleStartExam = (category) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
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
      marginBottom: 8,
    },
    subtitle: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    categoriesSection: {
      paddingHorizontal: 24,
      marginBottom: 24,
    },
    categoriesGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    categoryCard: {
      width: '31%',
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      alignItems: 'center',
      ...PlatformAdapter.getElevation(),
    },
    categoryIcon: {
      fontSize: 28,
      marginBottom: 8,
    },
    categoryName: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    categoryCount: {
      fontSize: 10,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.5,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    recentSection: {
      paddingHorizontal: 24,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 16,
    },
    recentList: {
      gap: 12,
    },
    recentCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      ...PlatformAdapter.getElevation(),
    },
    recentInfo: {
      flex: 1,
    },
    recentName: {
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 4,
    },
    recentDate: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.5,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    recentScore: {
      backgroundColor: '#44ff44',
      padding: 8,
      borderRadius: 8,
      minWidth: 60,
      alignItems: 'center',
    },
    scoreText: {
      fontSize: 16,
      fontWeight: 'bold',
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    startButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      margin: 24,
    },
    buttonText: {
      color: '#ffffff',
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>考试中心</Text>
        <Text style={styles.subtitle}>选择科目开始你的学习之旅</Text>
      </View>

      <View style={styles.categoriesSection}>
        <Text style={styles.sectionTitle}>科目分类</Text>
        <View style={styles.categoriesGrid}>
          {examCategories.map((category) => (
            <TouchableOpacity
              key={category.id}
              style={styles.categoryCard}
              onPress={() => handleStartExam(category)}>
              <Text style={styles.categoryIcon}>{category.icon}</Text>
              <Text style={styles.categoryName}>{category.name}</Text>
              <Text style={styles.categoryCount}>{category.count}题</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.recentSection}>
        <Text style={styles.sectionTitle}>最近考试</Text>
        <View style={styles.recentList}>
          {recentExams.map((exam) => (
            <View key={exam.id} style={styles.recentCard}>
              <View style={styles.recentInfo}>
                <Text style={styles.recentName}>{exam.name}</Text>
                <Text style={styles.recentDate}>{exam.date}</Text>
              </View>
              <View style={styles.recentScore}>
                <Text style={styles.scoreText}>{exam.score}/{exam.total}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      <TouchableOpacity style={styles.startButton} onPress={() => {}} disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <Text style={styles.buttonText}>开始随机测试</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
};

export default ExamScreen;