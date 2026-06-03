import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PlatformAdapter from '../adapters/PlatformAdapter';

class AIService {
  constructor() {
    this.enabled = true;
    this.model = 'gpt-4';
    this.maxTokens = 1024;
    this.temperature = 0.7;
    this.apiEndpoint = PlatformAdapter.getAPIEndpoint();
    this.timeout = 30000;
    this.maxRetries = 3;
    this.retryDelay = 1000;
  }

  async getSettings() {
    try {
      const saved = await AsyncStorage.getItem('ai_settings');
      if (saved) {
        const settings = JSON.parse(saved);
        this.enabled = settings.enabled !== undefined ? settings.enabled : true;
        this.model = settings.model || 'gpt-4';
        this.maxTokens = settings.maxTokens || 1024;
        this.temperature = settings.temperature || 0.7;
        this.timeout = settings.timeout || 30000;
        this.maxRetries = settings.maxRetries || 3;
      }
      return {
        enabled: this.enabled,
        model: this.model,
        maxTokens: this.maxTokens,
        temperature: this.temperature,
        timeout: this.timeout,
        maxRetries: this.maxRetries,
      };
    } catch (error) {
      return this.getDefaultSettings();
    }
  }

  getDefaultSettings() {
    return {
      enabled: true,
      model: 'gpt-4',
      maxTokens: 1024,
      temperature: 0.7,
      timeout: 30000,
      maxRetries: 3,
    };
  }

  async saveSettings(settings) {
    try {
      this.enabled = settings.enabled;
      this.model = settings.model || this.model;
      this.maxTokens = settings.maxTokens || this.maxTokens;
      this.temperature = settings.temperature || this.temperature;
      this.timeout = settings.timeout || this.timeout;
      this.maxRetries = settings.maxRetries || this.maxRetries;
      
      await AsyncStorage.setItem('ai_settings', JSON.stringify({
        enabled: this.enabled,
        model: this.model,
        maxTokens: this.maxTokens,
        temperature: this.temperature,
        timeout: this.timeout,
        maxRetries: this.maxRetries,
      }));
      return true;
    } catch (error) {
      console.warn('保存AI设置失败:', error);
      return false;
    }
  }

  async generateAnswer(prompt, context = '') {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    let retries = 0;
    let lastError = null;

    while (retries < this.maxRetries) {
      try {
        const response = await axios.post(
          `${this.apiEndpoint}/api/ai/chat`,
          {
            prompt,
            context,
            model: this.model,
            max_tokens: this.maxTokens,
            temperature: this.temperature,
          },
          {timeout: this.timeout}
        );

        if (response.data.success) {
          return {
            success: true,
            answer: response.data.answer,
            tokens_used: response.data.tokens_used,
            model: response.data.model,
          };
        }
        return {success: false, message: response.data.message || '请求失败'};
      } catch (error) {
        lastError = error;
        retries++;
        if (retries < this.maxRetries) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * retries));
        }
      }
    }

    console.warn('AI请求失败:', lastError?.message);
    return {success: false, message: `请求失败: ${lastError?.message || '未知错误'}`};
  }

  async analyzeText(text, task = 'summarize') {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/analyze`,
        {
          text,
          task,
          model: this.model,
        },
        {timeout: this.timeout}
      );

      if (response.data.success) {
        return {
          success: true,
          result: response.data.result,
        };
      }
      return {success: false, message: response.data.message || '分析失败'};
    } catch (error) {
      console.warn('AI分析失败:', error.message);
      return {success: false, message: `分析失败: ${error.message}`};
    }
  }

  async generateExamQuestions(subject, count = 10, difficulty = 'medium') {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/generate/questions`,
        {
          subject,
          count,
          difficulty,
          model: this.model,
        },
        {timeout: this.timeout * 2}
      );

      if (response.data.success) {
        return {
          success: true,
          questions: response.data.questions,
        };
      }
      return {success: false, message: response.data.message || '生成失败'};
    } catch (error) {
      console.warn('AI生成题目失败:', error.message);
      return {success: false, message: `生成失败: ${error.message}`};
    }
  }

  async correctAnswer(userAnswer, correctAnswer, subject) {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/correct`,
        {
          user_answer: userAnswer,
          correct_answer: correctAnswer,
          subject,
          model: this.model,
        },
        {timeout: this.timeout}
      );

      if (response.data.success) {
        return {
          success: true,
          score: response.data.score,
          feedback: response.data.feedback,
          explanation: response.data.explanation,
        };
      }
      return {success: false, message: response.data.message || '批改失败'};
    } catch (error) {
      console.warn('AI批改失败:', error.message);
      return {success: false, message: `批改失败: ${error.message}`};
    }
  }

  async getAIStatus() {
    try {
      const response = await axios.get(
        `${this.apiEndpoint}/api/ai/status`,
        {timeout: 10000}
      );

      if (response.data.success) {
        return {
          success: true,
          online: response.data.online,
          models: response.data.models || ['gpt-4', 'gpt-3.5-turbo'],
          uptime: response.data.uptime,
          requests_today: response.data.requests_today,
          version: response.data.version,
        };
      }
      return {success: false, online: false};
    } catch (error) {
      return {success: false, online: false, message: error.message};
    }
  }

  async suggestImprovement(userData) {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/suggest`,
        {
          user_data: userData,
          model: this.model,
        },
        {timeout: this.timeout}
      );

      if (response.data.success) {
        return {
          success: true,
          suggestions: response.data.suggestions,
        };
      }
      return {success: false, message: response.data.message || '建议生成失败'};
    } catch (error) {
      console.warn('AI建议失败:', error.message);
      return {success: false, message: `建议失败: ${error.message}`};
    }
  }

  async summarizeText(text, maxLength = 200) {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/summarize`,
        {
          text,
          max_length: maxLength,
          model: this.model,
        },
        {timeout: this.timeout}
      );

      if (response.data.success) {
        return {
          success: true,
          summary: response.data.summary,
        };
      }
      return {success: false, message: response.data.message || '摘要生成失败'};
    } catch (error) {
      console.warn('AI摘要失败:', error.message);
      return {success: false, message: `摘要失败: ${error.message}`};
    }
  }

  async translateText(text, targetLanguage = 'zh') {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/translate`,
        {
          text,
          target_language: targetLanguage,
          model: this.model,
        },
        {timeout: this.timeout}
      );

      if (response.data.success) {
        return {
          success: true,
          translation: response.data.translation,
          source_language: response.data.source_language,
        };
      }
      return {success: false, message: response.data.message || '翻译失败'};
    } catch (error) {
      console.warn('AI翻译失败:', error.message);
      return {success: false, message: `翻译失败: ${error.message}`};
    }
  }

  async classifyText(text, categories) {
    if (!this.enabled) {
      return {success: false, message: 'AI功能已关闭'};
    }

    try {
      const response = await axios.post(
        `${this.apiEndpoint}/api/ai/classify`,
        {
          text,
          categories,
          model: this.model,
        },
        {timeout: this.timeout}
      );

      if (response.data.success) {
        return {
          success: true,
          category: response.data.category,
          confidence: response.data.confidence,
        };
      }
      return {success: false, message: response.data.message || '分类失败'};
    } catch (error) {
      console.warn('AI分类失败:', error.message);
      return {success: false, message: `分类失败: ${error.message}`};
    }
  }

  getAvailableModels() {
    return [
      {id: 'gpt-4', name: 'GPT-4', description: '最先进的模型，适合复杂任务', maxTokens: 8192},
      {id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: '快速高效，性价比高', maxTokens: 4096},
      {id: 'claude-3', name: 'Claude 3', description: '长上下文支持，适合文档分析', maxTokens: 200000},
      {id: 'llama-3', name: 'Llama 3', description: '开源模型，隐私友好', maxTokens: 8192},
    ];
  }

  getDifficultyLevels() {
    return [
      {id: 'easy', name: '简单', description: '适合入门学习'},
      {id: 'medium', name: '中等', description: '适合巩固练习'},
      {id: 'hard', name: '困难', description: '适合挑战提升'},
      {id: 'expert', name: '专家', description: '适合竞赛备考'},
    ];
  }

  getSystemPrompt() {
    return `你是一个智能教育助手，专门帮助学生学习和备考。
请使用中文回答，保持友好、专业的语气。
对于学习问题，请提供详细的解释和示例。
对于考试相关问题，请给出准确的答案和解题思路。`;
  }
}

export default new AIService();