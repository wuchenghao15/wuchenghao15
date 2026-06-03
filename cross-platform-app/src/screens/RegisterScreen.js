import React, {useState} from 'react';
import {View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator} from 'react-native';
import {useAuth} from '../context/AuthContext';
import PlatformAdapter from '../adapters/PlatformAdapter';

const RegisterScreen = ({navigation}) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const {register} = useAuth();

  const handleRegister = async () => {
    if (!username.trim() || !email.trim() || !password || !confirmPassword) {
      Alert.alert('提示', '请填写所有字段');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('提示', '两次输入的密码不一致');
      return;
    }

    if (password.length < 6) {
      Alert.alert('提示', '密码长度至少6位');
      return;
    }

    setLoading(true);
    const result = await register({
      username: username.trim(),
      email: email.trim(),
      password,
    });
    setLoading(false);

    if (result.success) {
      Alert.alert('注册成功', '请登录您的账号', [
        {text: '确定', onPress: () => navigation.navigate('Login')}
      ]);
    } else {
      Alert.alert('注册失败', result.message);
    }
  };

  const handleBack = () => {
    navigation.goBack();
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: PlatformAdapter.getBackgroundColor(),
      padding: 24,
      paddingTop: 48,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 32,
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
      marginTop: 16,
    },
    buttonText: {
      color: '#ffffff',
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    backButton: {
      ...PlatformAdapter.getButtonStyle('outline'),
      alignItems: 'center',
      marginTop: 16,
    },
    backButtonText: {
      color: PlatformAdapter.getTextColor(),
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  return (
    <View style={styles.container}>
      <Text style={styles.title}>注册账号</Text>

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
          placeholder="邮箱"
          placeholderTextColor={PlatformAdapter.getTextColor()}
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
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
        <TextInput
          style={styles.input}
          placeholder="确认密码"
          placeholderTextColor={PlatformAdapter.getTextColor()}
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
        />
        <TouchableOpacity style={styles.button} onPress={handleRegister} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>注册</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Text style={styles.backButtonText}>返回登录</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default RegisterScreen;