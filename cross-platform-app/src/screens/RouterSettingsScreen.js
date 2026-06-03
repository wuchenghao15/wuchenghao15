import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert, FlatList} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';

const RouterSettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [protectedRoutes, setProtectedRoutes] = useState([]);
  const [aiOptimization, setAiOptimization] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadRoutes();
    loadProtectedRoutes();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadRoutes = async () => {
    const routeList = [
      {id: 'Home', name: '首页', icon: '🏠', enabled: true, visits: 156},
      {id: 'Exam', name: '考试中心', icon: '📝', enabled: true, visits: 89},
      {id: 'Study', name: '学习中心', icon: '📚', enabled: true, visits: 142},
      {id: 'Profile', name: '个人中心', icon: '👤', enabled: true, visits: 67},
      {id: 'Settings', name: '设置', icon: '⚙️', enabled: true, visits: 34},
      {id: 'AISettings', name: 'AI设置', icon: '🤖', enabled: true, visits: 28},
      {id: 'Backup', name: '备份', icon: '💾', enabled: true, visits: 15},
      {id: 'QuestionBank', name: '题库', icon: '📖', enabled: true, visits: 45},
      {id: 'Teacher', name: '教师系统', icon: '👨‍🏫', enabled: true, visits: 12},
      {id: 'Student', name: '学生信息', icon: '👨‍🎓', enabled: true, visits: 23},
    ];
    setRoutes(routeList);
  };

  const loadProtectedRoutes = async () => {
    const protectedList = [
      {id: 'Admin', name: '管理员后台', role: 'admin', icon: '🔐'},
      {id: 'ExamAdmin', name: '考试管理', role: 'teacher', icon: '📋'},
      {id: 'QuestionAdmin', name: '题库管理', role: 'professor', icon: '📚'},
      {id: 'GradeAdmin', name: '成绩管理', role: 'teacher', icon: '📊'},
      {id: 'UserAdmin', name: '用户管理', role: 'admin', icon: '👥'},
    ];
    setProtectedRoutes(protectedList);
  };

  const handleRouteToggle = (routeId) => {
    setRoutes(prev => prev.map(route => 
      route.id === routeId ? {...route, enabled: !route.enabled} : route
    ));
  };

  const handleAIRecommendRoutes = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法获取AI路由建议');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.optimizeRoutes({
        routes: routes.filter(r => r.enabled),
        platform: PlatformAdapter.isHyperOS() ? 'hyperos' : PlatformAdapter.isHarmonyOS() ? 'harmonyos' : 'android',
      });

      if (result.success) {
        Alert.alert('AI优化完成', `推荐的路由优化方案：\n\n${result.recommendations}`);
      } else {
        Alert.alert('优化失败', result.message);
      }
    } catch (error) {
      Alert.alert('优化失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleResetRoutes = () => {
    Alert.alert(
      '确认重置',
      '确定要重置所有路由设置吗？',
      [
        {text: '取消', style: 'cancel'},
        {
          text: '确认',
          onPress: () => {
            loadRoutes();
            Alert.alert('重置成功', '路由设置已恢复默认');
          },
        },
      ]
    );
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
    cardHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    cardTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
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
    itemIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    itemInfo: {
      flex: 1,
    },
    itemName: {
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemVisits: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 4,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemRole: {
      fontSize: 12,
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    itemBadge: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    badgeEnabled: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    badgeDisabled: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
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
        <Text style={styles.title}>路由系统</Text>
        <Text style={styles.subtitle}>管理应用路由和导航配置</Text>
      </View>

      <View style={styles.sections}>
        <View style={styles.statsCard}>
          <Text style={styles.statsHeader}>📊 路由统计</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{routes.length}</Text>
              <Text style={styles.statLabel}>总路由数</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{routes.filter(r => r.enabled).length}</Text>
              <Text style={styles.statLabel}>已启用</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{protectedRoutes.length}</Text>
              <Text style={styles.statLabel}>保护路由</Text>
            </View>
          </View>
        </View>

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI路由优化</Text>
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
              <Text style={styles.aiStatusValue}>智能路由推荐、导航优化</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>路由列表</Text>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>📱 公共路由</Text>
            </View>
            {routes.map((route, index) => (
              <TouchableOpacity
                key={route.id}
                style={[styles.cardItem, index === routes.length - 1 && styles.cardItemLast]}
                onPress={() => handleRouteToggle(route.id)}>
                <Text style={styles.itemIcon}>{route.icon}</Text>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{route.name}</Text>
                  <Text style={styles.itemVisits}>访问次数: {route.visits}</Text>
                </View>
                <Text style={[styles.itemBadge, route.enabled ? styles.badgeEnabled : styles.badgeDisabled]}>
                  {route.enabled ? '启用' : '禁用'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>保护路由</Text>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>🔐 需要权限的路由</Text>
            </View>
            {protectedRoutes.map((route, index) => (
              <View
                key={route.id}
                style={[styles.cardItem, index === protectedRoutes.length - 1 && styles.cardItemLast]}>
                <Text style={styles.itemIcon}>{route.icon}</Text>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{route.name}</Text>
                  <Text style={styles.itemRole}>需要角色: {route.role}</Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIRecommendRoutes}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI路由优化建议</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📋 导出路由配置</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary}>
          <Text style={styles.actionButtonTextSecondary}>📥 导入路由配置</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButtonSecondary} onPress={handleResetRoutes}>
          <Text style={styles.actionButtonTextSecondary}>🔄 重置路由设置</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default RouterSettingsScreen;