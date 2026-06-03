import {Platform} from 'react-native';
import DeviceInfo from 'react-native-device-info';

const PLATFORM_TYPES = {
  ANDROID: 'android',
  HARMONYOS: 'harmonyos',
  HYPEROS: 'hyperos',
  IOS: 'ios',
  UNKNOWN: 'unknown',
};

class PlatformAdapter {
  static _platform = null;
  static _theme = null;

  static async init() {
    const brand = DeviceInfo.getBrand();
    const systemName = await DeviceInfo.getSystemName();
    const systemVersion = await DeviceInfo.getSystemVersion();

    if (systemName.toLowerCase().includes('harmony')) {
      this._platform = PLATFORM_TYPES.HARMONYOS;
    } else if (brand.toLowerCase() === 'xiaomi' && systemVersion >= '15') {
      this._platform = PLATFORM_TYPES.HYPEROS;
    } else if (Platform.OS === 'android') {
      this._platform = PLATFORM_TYPES.ANDROID;
    } else if (Platform.OS === 'ios') {
      this._platform = PLATFORM_TYPES.IOS;
    } else {
      this._platform = PLATFORM_TYPES.UNKNOWN;
    }

    this._theme = this._detectTheme();
  }

  static _detectTheme() {
    if (Platform.OS === 'android') {
      const uiMode = Platform.select({
        android: () => {
          try {
            const {Appearance} = require('react-native-appearance');
            return Appearance.getColorScheme();
          } catch (e) {
            return 'light';
          }
        },
        default: () => 'light',
      })();
      return uiMode;
    }
    return 'light';
  }

  static getPlatform() {
    return this._platform || PLATFORM_TYPES.UNKNOWN;
  }

  static isHyperOS() {
    return this.getPlatform() === PLATFORM_TYPES.HYPEROS;
  }

  static isHarmonyOS() {
    return this.getPlatform() === PLATFORM_TYPES.HARMONYOS;
  }

  static isAndroid() {
    return this.getPlatform() === PLATFORM_TYPES.ANDROID;
  }

  static getPlatformName() {
    const platformNames = {
      [PLATFORM_TYPES.ANDROID]: 'Android',
      [PLATFORM_TYPES.HARMONYOS]: 'HarmonyOS',
      [PLATFORM_TYPES.HYPEROS]: 'HyperOS',
      [PLATFORM_TYPES.IOS]: 'iOS',
      [PLATFORM_TYPES.UNKNOWN]: 'Unknown',
    };
    return platformNames[this.getPlatform()] || 'Unknown';
  }

  static getStatusBarStyle() {
    if (this.isHyperOS()) {
      return 'light-content';
    }
    if (this.isHarmonyOS()) {
      return this._theme === 'dark' ? 'light-content' : 'dark-content';
    }
    return 'dark-content';
  }

  static getStatusBarColor() {
    if (this.isHyperOS()) {
      return '#1a1a2e';
    }
    if (this.isHarmonyOS()) {
      return this._theme === 'dark' ? '#1a1a1a' : '#ffffff';
    }
    return '#ffffff';
  }

  static getBackgroundColor() {
    if (this.isHyperOS()) {
      return '#0d0d1a';
    }
    if (this.isHarmonyOS()) {
      return this._theme === 'dark' ? '#1a1a1a' : '#f5f5f5';
    }
    return '#ffffff';
  }

  static getPrimaryColor() {
    if (this.isHyperOS()) {
      return '#6366f1';
    }
    if (this.isHarmonyOS()) {
      return '#007dff';
    }
    return '#6200ee';
  }

  static getAccentColor() {
    if (this.isHyperOS()) {
      return '#8b5cf6';
    }
    if (this.isHarmonyOS()) {
      return '#00c6ff';
    }
    return '#03dac6';
  }

  static getTextColor() {
    if (this.isHyperOS()) {
      return '#ffffff';
    }
    if (this.isHarmonyOS()) {
      return this._theme === 'dark' ? '#ffffff' : '#333333';
    }
    return '#333333';
  }

  static getFontFamily() {
    if (this.isHyperOS()) {
      return 'MiSans';
    }
    if (this.isHarmonyOS()) {
      return 'HarmonyOS Sans SC';
    }
    return Platform.select({
      android: 'Roboto',
      ios: 'San Francisco',
      default: 'System',
    });
  }

  static getCornerRadius() {
    if (this.isHyperOS()) {
      return 16;
    }
    if (this.isHarmonyOS()) {
      return 12;
    }
    return 8;
  }

  static getElevation() {
    if (this.isHyperOS()) {
      return {
        shadowColor: 'rgba(99, 102, 241, 0.3)',
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4,
      };
    }
    if (this.isHarmonyOS()) {
      return {
        shadowColor: 'rgba(0, 125, 255, 0.2)',
        shadowOffset: {width: 0, height: 2},
        shadowOpacity: 0.2,
        shadowRadius: 4,
        elevation: 2,
      };
    }
    return {
      shadowColor: 'rgba(0, 0, 0, 0.1)',
      shadowOffset: {width: 0, height: 2},
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    };
  }

  static getAnimationDuration() {
    if (this.isHyperOS()) {
      return 300;
    }
    if (this.isHarmonyOS()) {
      return 250;
    }
    return 200;
  }

  static getToastStyle() {
    if (this.isHyperOS()) {
      return {
        backgroundColor: 'rgba(30, 30, 50, 0.95)',
        textColor: '#ffffff',
        cornerRadius: 16,
        padding: 16,
      };
    }
    if (this.isHarmonyOS()) {
      return {
        backgroundColor: this._theme === 'dark' ? 'rgba(50, 50, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
        textColor: this._theme === 'dark' ? '#ffffff' : '#333333',
        cornerRadius: 12,
        padding: 12,
      };
    }
    return {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textColor: '#ffffff',
      cornerRadius: 8,
      padding: 12,
    };
  }

  static getButtonStyle(variant = 'primary') {
    const styles = {
      primary: {
        backgroundColor: this.getPrimaryColor(),
        borderRadius: this.getCornerRadius(),
        paddingVertical: 12,
        paddingHorizontal: 24,
        ...this.getElevation(),
      },
      secondary: {
        backgroundColor: 'transparent',
        borderColor: this.getPrimaryColor(),
        borderWidth: 1,
        borderRadius: this.getCornerRadius(),
        paddingVertical: 12,
        paddingHorizontal: 24,
      },
      outline: {
        backgroundColor: 'transparent',
        borderColor: this.getTextColor(),
        borderWidth: 1,
        borderRadius: this.getCornerRadius(),
        paddingVertical: 12,
        paddingHorizontal: 24,
      },
    };
    return styles[variant] || styles.primary;
  }

  static getInputStyle() {
    return {
      backgroundColor: this.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : 
                      this.isHarmonyOS() && this._theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderColor: this.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : 
                   this.isHarmonyOS() ? 'rgba(0, 125, 255, 0.3)' : '#e0e0e0',
      borderWidth: 1,
      borderRadius: this.getCornerRadius(),
      padding: 12,
      color: this.getTextColor(),
      fontFamily: this.getFontFamily(),
    };
  }

  static getPlatformSpecificCode() {
    return {
      hyperos: () => {
        try {
          const HyperOSAPI = require('./HyperOSAPI');
          return new HyperOSAPI();
        } catch (e) {
          return null;
        }
      },
      harmonyos: () => {
        try {
          const HarmonyOSAPI = require('./HarmonyOSAPI');
          return new HarmonyOSAPI();
        } catch (e) {
          return null;
        }
      },
    }[this.getPlatform()]?.() || null;
  }

  static getAPIEndpoint() {
    const endpoints = {
      [PLATFORM_TYPES.ANDROID]: 'https://api.mtscos.com/android',
      [PLATFORM_TYPES.HARMONYOS]: 'https://api.mtscos.com/harmonyos',
      [PLATFORM_TYPES.HYPEROS]: 'https://api.mtscos.com/hyperos',
      [PLATFORM_TYPES.IOS]: 'https://api.mtscos.com/ios',
    };
    return endpoints[this.getPlatform()] || 'https://api.mtscos.com';
  }
}

export default PlatformAdapter;
export {PLATFORM_TYPES};