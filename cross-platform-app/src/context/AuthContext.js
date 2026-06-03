import React, {createContext, useContext, useState, useEffect} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PlatformAdapter from '../adapters/PlatformAdapter';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({children}) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        const storedToken = await AsyncStorage.getItem('auth_token');
        const storedUser = await AsyncStorage.getItem('user_data');
        
        if (storedToken && storedUser) {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        }
      } catch (e) {
        console.error('Failed to load auth data:', e);
      } finally {
        setLoading(false);
      }
    };
    bootstrapAsync();
  }, []);

  const login = async (username, password) => {
    try {
      const response = await axios.post(
        `${PlatformAdapter.getAPIEndpoint()}/api/auth/login`,
        {username, password},
        {headers: {'Content-Type': 'application/json'}}
      );

      const {token: newToken, user: userData} = response.data;
      
      await AsyncStorage.setItem('auth_token', newToken);
      await AsyncStorage.setItem('user_data', JSON.stringify(userData));
      
      setToken(newToken);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

      return {success: true, user: userData};
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || '登录失败，请重试'
      };
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${PlatformAdapter.getAPIEndpoint()}/api/auth/logout`);
    } catch (e) {
      console.warn('Logout API failed, clearing local data anyway');
    } finally {
      await AsyncStorage.removeItem('auth_token');
      await AsyncStorage.removeItem('user_data');
      setToken(null);
      setUser(null);
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(
        `${PlatformAdapter.getAPIEndpoint()}/api/auth/register`,
        userData,
        {headers: {'Content-Type': 'application/json'}}
      );
      return {success: true, ...response.data};
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || '注册失败，请重试'
      };
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await axios.put(
        `${PlatformAdapter.getAPIEndpoint()}/api/user/profile`,
        profileData
      );
      
      const updatedUser = {...user, ...response.data.user};
      setUser(updatedUser);
      await AsyncStorage.setItem('user_data', JSON.stringify(updatedUser));
      
      return {success: true, user: updatedUser};
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || '更新失败，请重试'
      };
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    register,
    updateProfile,
    isAuthenticated: !!token && !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};