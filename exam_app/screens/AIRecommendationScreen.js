import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { aiService } from '../services/api';

export default function AIRecommendationScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState({
    personalizedContent: [
      { id: 1, title: '高频词汇强化训练', description: '根据你的学习记录，推荐重点记忆高频词汇', progress: 60 },
      { id: 2, title: '语法薄弱点突破', description: '针对你的语法弱项进行专项训练', progress: 40 },
      { id: 3, title: '阅读理解技巧', description: '提升阅读理解能力和速度', progress: 25 },
    ],
    studyPlan: {
      today: ['复习昨天学习的词汇', '完成一套模拟题', '整理错题本'],
      thisWeek: ['完成日语N3语法学习', '进行词汇测试', '准备下周考试'],
    },
    learningAnalysis: {
      strength: ['词汇记忆', '阅读理解'],
      weakness: ['听力训练', '写作表达'],
      suggestion: '建议每天花费30分钟进行听力训练，同时加强写作练习。',
    },
  });

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      const data = await aiService.getPersonalizedRecommendations(1);
      setRecommendations(data);
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };

  const handleStartLearning = (item) => {
    navigation.navigate('Main', { screen: '考试' });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#5856D6" />
        <Text style={styles.loadingText}>AI分析中...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🤖 AI学习助手</Text>
          <Text style={styles.headerSubtitle}>智能分析，个性化推荐</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📚 个性化推荐</Text>
          {recommendations.personalizedContent.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={styles.recommendItem}
              onPress={() => handleStartLearning(item)}
            >
              <View style={styles.recommendHeader}>
                <Text style={styles.recommendTitle}>{item.title}</Text>
                <View style={styles.progressBadge}>
                  <Text style={styles.progressText}>{item.progress}%</Text>
                </View>
              </View>
              <Text style={styles.recommendDesc}>{item.description}</Text>
              <View style={styles.progressBar}>
                <View
                  style={[styles.progressFill, { width: `${item.progress}%` }]}
                />
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📅 学习计划</Text>
          <View style={styles.planCard}>
            <View style={styles.planHeader}>
              <Text style={styles.planTitle}>今日计划</Text>
            </View>
            {recommendations.studyPlan.today.map((item, index) => (
              <View key={index} style={styles.planItem}>
                <View style={styles.planDot} />
                <Text style={styles.planText}>{item}</Text>
              </View>
            ))}
          </View>

          <View style={styles.planCard}>
            <View style={[styles.planHeader, { backgroundColor: '#5856D6' }]}>
              <Text style={styles.planTitle}>本周目标</Text>
            </View>
            {recommendations.studyPlan.thisWeek.map((item, index) => (
              <View key={index} style={styles.planItem}>
                <View style={[styles.planDot, { backgroundColor: '#5856D6' }]} />
                <Text style={styles.planText}>{item}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📊 学习分析</Text>
          <View style={styles.analysisCard}>
            <View style={styles.analysisRow}>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisLabel}>优势领域</Text>
                <View style={styles.tagContainer}>
                  {recommendations.learningAnalysis.strength.map((item, index) => (
                    <View key={index} style={[styles.tag, { backgroundColor: '#34C759' }]}>
                      <Text style={styles.tagText}>{item}</Text>
                    </View>
                  ))}
                </View>
              </View>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisLabel}>薄弱领域</Text>
                <View style={styles.tagContainer}>
                  {recommendations.learningAnalysis.weakness.map((item, index) => (
                    <View key={index} style={[styles.tag, { backgroundColor: '#FF3B30' }]}>
                      <Text style={styles.tagText}>{item}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>
            <View style={styles.suggestionSection}>
              <Text style={styles.suggestionTitle}>💡 AI建议</Text>
              <Text style={styles.suggestionText}>
                {recommendations.learningAnalysis.suggestion}
              </Text>
            </View>
          </View>
        </View>

        <TouchableOpacity
          style={styles.chatButton}
          onPress={() => navigation.navigate('Main')}
        >
          <Text style={styles.chatButtonText}>与AI助手对话</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#5856D6',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 30,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 5,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#5856D6',
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  recommendItem: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  recommendHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  recommendTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  progressBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
  },
  progressText: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
  },
  recommendDesc: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 15,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#F0F0F0',
    borderRadius: 3,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 3,
  },
  planCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    marginBottom: 15,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  planHeader: {
    backgroundColor: '#007AFF',
    padding: 15,
  },
  planTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  planItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  planDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#007AFF',
    marginRight: 12,
  },
  planText: {
    fontSize: 14,
    color: '#333',
  },
  analysisCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  analysisRow: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  analysisItem: {
    flex: 1,
  },
  analysisLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    marginRight: 8,
    marginBottom: 8,
  },
  tagText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  suggestionSection: {
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    padding: 15,
  },
  suggestionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  suggestionText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  chatButton: {
    backgroundColor: '#5856D6',
    marginHorizontal: 20,
    marginBottom: 30,
    borderRadius: 25,
    paddingVertical: 15,
    alignItems: 'center',
  },
  chatButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
