import React, {useState} from 'react';
import {View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator} from 'react-native';
import {useAuth} from '../context/AuthContext';
import PlatformAdapter from '../adapters/PlatformAdapter';

const LoginScreen = ({navigation}) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const {login} = useAuth();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('提示', '请输入用户名和密码');
      return;
    }

    setLoading(true);
    const result = await login(username.trim(), password);
    setLoading(false);

    if (!result.success) {
      Alert.alert('登录失败', result.message);
    }
  };

  const handleRegister = () => {
    navigation.navigate('Register');
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: PlatformAdapter.getBackgroundColor(),
      justifyContent: 'center',
      padding: 24,
    },
    logoSection: {
      alignItems: 'center',
      marginBottom: 48,
    },
    logo: {
      width: 120,
      height: 120,
      borderRadius: 24,
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: 16,
    },
    logoText: {
      color: '#ffffff',
      fontSize: 32,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    form: {
      gap: 16,
    },
    input: {
      ...PlatformAdapter.getInputStyle(),
      fontSize: 16,
    },
    button: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      marginTop: 8,
    },
    buttonText: {
      color: '#ffffff',
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    registerLink: {
      alignItems: 'center',
      marginTop: 24,
    },
    registerText: {
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    platformBadge: {
      position: 'absolute',
      bottom: 24,
      left: '50%',
      transform: [{translateX: -75}],
      backgroundColor: PlatformAdapter.isHyperOS() ? '#6366f1' : 
                      PlatformAdapter.isHarmonyOS() ? '#007dff' : '#6200ee',
      paddingVertical: 8,
      paddingHorizontal: 16,
      borderRadius: 20,
    },
    platformText: {
      color: '#ffffff',
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  return (
    <View style={styles.container}>
      <View style={styles.logoSection}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>M</Text>
        </View>
        <Text style={styles.title}>MTSCOS AI Project</Text>
      </View>

      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="用户名"
          placeholderTextColor={PlatformAdapter.getTextColor()}
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="密码"
          placeholderTextColor={PlatformAdapter.getTextColor()}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>登录</Text>
          )}
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.registerLink} onPress={handleRegister}>
        <Text style={styles.registerText}>还没有账号？立即注册</Text>
      </TouchableOpacity>

      <View style={styles.platformBadge}>
        <Text style={styles.platformText}>运行于 {PlatformAdapter.getPlatformName()}</Text>
      </View>
    </View>
  );
};

export default LoginScreen;