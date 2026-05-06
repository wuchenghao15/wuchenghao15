import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { databaseService, authService } from '../services/api';

export default function DatabaseSyncScreen({ navigation }) {
  const [syncEnabled, setSyncEnabled] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [backupEnabled, setBackupEnabled] = useState(false);
  const [lastBackup, setLastBackup] = useState(null);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 从本地存储加载设置
    loadSettings();
  }, []);

  const loadSettings = () => {
    // 从本地存储加载用户信息
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    
    // 模拟从本地存储加载设置
    setSyncEnabled(true);
    setBackupEnabled(true);
    setLastSync('2026-04-13 10:30');
    setLastBackup('2026-04-12 22:00');
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      // 调用同步API
      const userId = user?.id || 1;
      await databaseService.syncData(userId);
      setLastSync(new Date().toLocaleString());
      Alert.alert('同步成功', '数据已与服务器同步');
    } catch (error) {
      Alert.alert('同步失败', '请检查网络连接后重试');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleBackup = async () => {
    setIsBackingUp(true);
    try {
      // 调用备份API
      const userId = user?.id || 1;
      await databaseService.backupData(userId);
      setLastBackup(new Date().toLocaleString());
      Alert.alert('备份成功', '数据已备份到服务器');
    } catch (error) {
      Alert.alert('备份失败', '请检查网络连接后重试');
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleRestore = () => {
    Alert.alert(
      '恢复数据',
      '确定要从备份恢复数据吗？这将覆盖当前数据。',
      [
        { text: '取消', style: 'cancel' },
        {
          text: '确定',
          style: 'destructive',
          onPress: async () => {
            try {
              // 调用恢复API
              const userId = user?.id || 1;
              await databaseService.restoreData(userId, 1); // 假设使用最近的备份
              Alert.alert('恢复成功', '数据已从备份恢复');
            } catch (error) {
              Alert.alert('恢复失败', '请检查网络连接后重试');
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>数据库同步与备份</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>同步设置</Text>
        <View style={styles.settingItem}>
          <View>
            <Text style={styles.settingLabel}>自动同步</Text>
            <Text style={styles.settingDescription}>定期与服务器同步数据</Text>
          </View>
          <Switch
            value={syncEnabled}
            onValueChange={setSyncEnabled}
            trackColor={{ false: '#767577', true: '#007AFF' }}
            thumbColor={syncEnabled ? '#fff' : '#f4f3f4'}
          />
        </View>

        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleSync}
          disabled={isSyncing}
        >
          {isSyncing ? (
            <ActivityIndicator color="#007AFF" />
          ) : (
            <Text style={styles.actionButtonText}>立即同步</Text>
          )}
        </TouchableOpacity>

        {lastSync && (
          <Text style={styles.lastSyncText}>上次同步：{lastSync}</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>备份设置</Text>
        <View style={styles.settingItem}>
          <View>
            <Text style={styles.settingLabel}>自动备份</Text>
            <Text style={styles.settingDescription}>定期备份数据到服务器</Text>
          </View>
          <Switch
            value={backupEnabled}
            onValueChange={setBackupEnabled}
            trackColor={{ false: '#767577', true: '#34C759' }}
            thumbColor={backupEnabled ? '#fff' : '#f4f3f4'}
          />
        </View>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: '#34C759' }]}
          onPress={handleBackup}
          disabled={isBackingUp}
        >
          {isBackingUp ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={[styles.actionButtonText, { color: '#fff' }]}>立即备份</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: '#FF9500' }]}
          onPress={handleRestore}
        >
          <Text style={[styles.actionButtonText, { color: '#fff' }]}>从备份恢复</Text>
        </TouchableOpacity>

        {lastBackup && (
          <Text style={styles.lastSyncText}>上次备份：{lastBackup}</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>备份信息</Text>
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>• 备份包含考试记录、错题和学习进度</Text>
          <Text style={styles.infoText}>• 自动备份每天凌晨执行</Text>
          <Text style={styles.infoText}>• 备份数据保留30天</Text>
          <Text style={styles.infoText}>• 恢复会覆盖当前数据</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: 20,
    borderRadius: 15,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  settingDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  actionButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  lastSyncText: {
    fontSize: 12,
    color: '#999',
    marginTop: 10,
  },
  infoCard: {
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    padding: 15,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    lineHeight: 20,
  },
});
