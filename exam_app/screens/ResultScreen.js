import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
} from 'react-native';

export default function ResultScreen({ route, navigation }) {
  const { exam, result } = route.params;

  const correctCount = 3;
  const totalCount = result.totalQuestions || 5;
  const score = Math.round((correctCount / totalCount) * 100);
  const passed = score >= 60;

  const getScoreColor = () => {
    if (score >= 90) return '#34C759';
    if (score >= 70) return '#FF9500';
    return '#FF3B30';
  };

  const handleReviewQuestions = () => {
    navigation.navigate('Main', { screen: '错题' });
  };

  const handleBackToExamList = () => {
    navigation.navigate('Main', { screen: '考试' });
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.resultCard}>
          <View style={styles.scoreCircle}>
            <View style={[styles.scoreInner, { borderColor: getScoreColor() }]}>
              <Text style={[styles.scoreText, { color: getScoreColor() }]}>
                {score}
              </Text>
              <Text style={styles.scoreLabel}>分</Text>
            </View>
          </View>

          <Text style={[styles.resultStatus, { color: passed ? '#34C759' : '#FF3B30' }]}>
            {passed ? '🎉 考试通过' : '😢 未通过'}
          </Text>

          <Text style={styles.examTitle}>{exam.title}</Text>
        </View>

        <View style={styles.statsCard}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{totalCount}</Text>
            <Text style={styles.statLabel}>总题数</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: '#34C759' }]}>{correctCount}</Text>
            <Text style={styles.statLabel}>正确</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: '#FF3B30' }]}>{totalCount - correctCount}</Text>
            <Text style={styles.statLabel}>错误</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{exam.duration || 30}</Text>
            <Text style={styles.statLabel}>分钟</Text>
          </View>
        </View>

        <View style={styles.aiSection}>
          <View style={styles.aiHeader}>
            <Text style={styles.aiTitle}>🤖 AI分析</Text>
          </View>
          <View style={styles.aiContent}>
            <Text style={styles.aiText}>
              你在本次考试中表现{' '}
              {score >= 90 ? '非常优秀' : score >= 70 ? '不错' : '需要继续努力'}。
            </Text>
            <Text style={styles.aiText}>
              {score >= 90
                ? '你已经掌握了大部分知识点，建议挑战更高难度的题目。'
                : score >= 70
                ? '你需要加强薄弱环节的练习，推荐你复习相关知识点。'
                : '建议你先巩固基础知识，再进行进一步的练习。'}
            </Text>
            <View style={styles.aiRecommendation}>
              <Text style={styles.aiRecommendationTitle}>推荐学习内容：</Text>
              <Text style={styles.aiRecommendationText}>
                • 词汇语法基础{'n'}• 阅读理解技巧{'n'}• 写作表达训练
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={handleBackToExamList}
          >
            <Text style={styles.primaryButtonText}>返回考试列表</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={handleReviewQuestions}
          >
            <Text style={styles.secondaryButtonText}>查看错题</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    padding: 20,
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 30,
    alignItems: 'center',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 15,
    elevation: 8,
  },
  scoreCircle: {
    marginBottom: 20,
  },
  scoreInner: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 48,
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: 18,
    color: '#999',
  },
  resultStatus: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  examTitle: {
    fontSize: 16,
    color: '#666',
  },
  statsCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
  },
  statDivider: {
    width: 1,
    backgroundColor: '#F0F0F0',
  },
  aiSection: {
    backgroundColor: '#fff',
    borderRadius: 15,
    marginBottom: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  aiHeader: {
    backgroundColor: '#5856D6',
    padding: 15,
  },
  aiTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  aiContent: {
    padding: 15,
  },
  aiText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 22,
    marginBottom: 10,
  },
  aiRecommendation: {
    backgroundColor: '#F5F5F5',
    padding: 15,
    borderRadius: 10,
    marginTop: 10,
  },
  aiRecommendationTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  aiRecommendationText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  actions: {
    marginTop: 10,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    borderRadius: 25,
    paddingVertical: 15,
    alignItems: 'center',
    marginBottom: 12,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderRadius: 25,
    paddingVertical: 15,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
