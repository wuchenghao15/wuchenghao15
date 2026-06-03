import React, {createContext, useContext, useState, useEffect} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PlatformAdapter from '../adapters/PlatformAdapter';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({children}) => {
  const [theme, setTheme] = useState('system');

  useEffect(() => {
    const loadTheme = async () => {
      const saved = await AsyncStorage.getItem('app_theme');
      if (saved) {
        setTheme(saved);
      }
    };
    loadTheme();
  }, []);

  const getEffectiveTheme = () => {
    if (theme === 'system') {
      return PlatformAdapter._theme || 'light';
    }
    return theme;
  };

  const toggleTheme = async () => {
    const newTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
    setTheme(newTheme);
    await AsyncStorage.setItem('app_theme', newTheme);
  };

  const setThemeMode = async (newTheme) => {
    setTheme(newTheme);
    await AsyncStorage.setItem('app_theme', newTheme);
  };

  const isDarkMode = () => {
    return getEffectiveTheme() === 'dark';
  };

  const getThemeStyles = () => {
    const effectiveTheme = getEffectiveTheme();
    const isDark = effectiveTheme === 'dark';

    return {
      colors: {
        primary: PlatformAdapter.getPrimaryColor(),
        accent: PlatformAdapter.getAccentColor(),
        background: isDark ? '#1a1a2e' : '#ffffff',
        surface: isDark ? '#16213e' : '#f5f5f5',
        card: isDark ? '#0f0f1a' : '#ffffff',
        text: isDark ? '#ffffff' : '#333333',
        textSecondary: isDark ? '#a0a0a0' : '#666666',
        border: isDark ? 'rgba(255,255,255,0.1)' : '#e0e0e0',
        error: '#ff4444',
        success: '#44ff44',
        warning: '#ffaa00',
      },
      typography: {
        fontFamily: PlatformAdapter.getFontFamily(),
        fontSize: {
          xs: 12,
          sm: 14,
          md: 16,
          lg: 18,
          xl: 24,
          xxl: 32,
        },
      },
      spacing: {
        xs: 4,
        sm: 8,
        md: 16,
        lg: 24,
        xl: 32,
      },
      borderRadius: PlatformAdapter.getCornerRadius(),
      elevation: PlatformAdapter.getElevation(),
    };
  };

  const value = {
    theme,
    effectiveTheme: getEffectiveTheme(),
    isDarkMode: isDarkMode(),
    toggleTheme,
    setThemeMode,
    styles: getThemeStyles(),
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};