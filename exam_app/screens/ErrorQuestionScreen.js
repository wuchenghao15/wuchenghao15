import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { errorQuestionService } from '../services/api';

export default function ErrorQuestionScreen({ navigation }) {
  const [errorQuestions, setErrorQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadErrorQuestions();
  }, []);

  const loadErrorQuestions = async () => {
    try {
      const data = await errorQuestionService.getErrorQuestions(1);
      setErrorQuestions(data);
    } catch (error) {
      setErrorQuestions([
        {
          id: 1,
          question: '以下哪个单词的意思是"学习"？',
          userAnswer: 'Play',
          correctAnswer: 'Study',
          knowledgePoint: '基础词汇',
          errorCount: 3,
          lastReviewDate: '2024-04-10',
        },
        {
          id: 2,
          question: '请选择正确的语法：',
          userAnswer: 'I am go to school.',
          correctAnswer: 'I go to school.',
          knowledgePoint: '主谓一致',
          errorCount: 5,
          lastReviewDate: '2024-04-08',
        },
        {
          id: 3,
          question: '"你好"用英语怎么说？',
          userAnswer: 'Goodbye',
          correctAnswer: 'Hello',
          knowledgePoint: '日常用语',
          errorCount: 2,
          lastReviewDate: '2024-04-05',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadErrorQuestions();
    setRefreshing(false);
  };

  const handleReview = (item) => {
    navigation.navigate('AIRecommendation', { question: item });
  };

  const renderErrorQuestion = ({ item }) => (
    <TouchableOpacity style={styles.errorItem} onPress={() => handleReview(item)}>
      <View style={styles.errorHeader}>
        <View style={styles.errorBadge}>
          <Text style={styles.errorBadgeText}>错误 {item.errorCount} 次</Text>
        </View>
        <Text style={styles.knowledgePoint}>{item.knowledgePoint}</Text>
      </View>

      <Text style={styles.questionText}>{item.question}</Text>

      <View style={styles.answerSection}>
        <View style={styles.answerRow}>
          <Text style={styles.answerLabel}>你的答案：</Text>
          <Text style={styles.wrongAnswer}>{item.userAnswer}</Text>
        </View>
        <View style={styles.answerRow}>
          <Text style={styles.answerLabel}>正确答案：</Text>
          <Text style={styles.correctAnswer}>{item.correctAnswer}</Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.reviewDate}>
          上次复习：{item.lastReviewDate}
        </Text>
        <TouchableOpacity style={styles.reviewButton}>
          <Text style={styles.reviewButtonText}>立即复习</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>加载中...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>错题本</Text>
        <Text style={styles.headerSubtitle}>
          共 {errorQuestions.length} 道错题待复习
        </Text>
      </View>

      <FlatList
        data={errorQuestions}
        renderItem={renderErrorQuestion}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🎉</Text>
            <Text style={styles.emptyText}>太棒了！暂无错题</Text>
            <Text style={styles.emptySubtext}>继续保持，再接再厉！</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#FF3B30',
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
  listContent: {
    padding: 20,
  },
  errorItem: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  errorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  errorBadge: {
    backgroundColor: '#FFEBEE',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  errorBadgeText: {
    fontSize: 12,
    color: '#FF3B30',
    fontWeight: '600',
  },
  knowledgePoint: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
  },
  questionText: {
    fontSize: 16,
    color: '#333',
    lineHeight: 24,
    marginBottom: 15,
  },
  answerSection: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
  },
  answerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  answerLabel: {
    fontSize: 14,
    color: '#666',
    width: 80,
  },
  wrongAnswer: {
    fontSize: 14,
    color: '#FF3B30',
    fontWeight: '600',
    flex: 1,
  },
  correctAnswer: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '600',
    flex: 1,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reviewDate: {
    fontSize: 12,
    color: '#999',
  },
  reviewButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  reviewButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 20,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 10,
  },
});
