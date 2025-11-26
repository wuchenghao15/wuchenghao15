/**
 * 配色方案推荐引擎
 * 利用多模型和网络爬虫技术自动推荐最受欢迎的注册排版配色方案
 */

class ColorSchemeRecommender {
  constructor() {
    this.config = {
      cachePath: '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Staging/Data/cache/color-schemes.json',
      popularSites: [
        'https://www.dribbble.com',
        'https://www.behance.net',
        'https://colorhunt.co',
        'https://www.materialpalette.com',
        'https://coolors.co',
        'https://www.w3schools.com/colors/colors_trends.asp'
      ],
      updateInterval: 24 * 60 * 60 * 1000, // 24小时更新一次
      maxSchemes: 50,
      modelEndpoints: {
        popularityAnalysis: 'http://localhost:3000/api/color-analysis',
        uiCompatibility: 'http://localhost:3000/api/ui-compatibility'
      }
    };
    
    this.schemes = [];
    this.cache = null;
    
    // 初始化
    this.initialize();
  }

  /**
   * 初始化配色方案推荐引擎
   */
  async initialize() {
    try {
      console.log('初始化配色方案推荐引擎...');
      
      // 加载缓存数据
      await this.loadCache();
      
      // 检查是否需要更新数据
      if (this.needsUpdate()) {
        await this.refreshData();
      }
      
      console.log('配色方案推荐引擎初始化完成');
    } catch (error) {
      console.error('初始化配色方案推荐引擎失败:', error.message);
    }
  }

  /**
   * 加载缓存数据
   */
  async loadCache() {
    try {
      const fs = require('fs');
      if (fs.existsSync(this.config.cachePath)) {
        const data = fs.readFileSync(this.config.cachePath, 'utf8');
        this.cache = JSON.parse(data);
        this.schemes = this.cache.schemes || [];
        console.log(`已加载 ${this.schemes.length} 个配色方案`);
      }
    } catch (error) {
      console.error('加载缓存数据失败:', error.message);
      this.cache = null;
    }
  }

  /**
   * 保存缓存数据
   */
  async saveCache() {
    try {
      const fs = require('fs');
      const path = require('path');
      
      // 确保目录存在
      const dir = path.dirname(this.config.cachePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      this.cache = {
        lastUpdated: Date.now(),
        schemes: this.schemes
      };
      
      fs.writeFileSync(this.config.cachePath, JSON.stringify(this.cache, null, 2));
      console.log('缓存数据已保存');
    } catch (error) {
      console.error('保存缓存数据失败:', error.message);
    }
  }

  /**
   * 检查是否需要更新数据
   */
  needsUpdate() {
    if (!this.cache || !this.cache.lastUpdated) {
      return true;
    }
    
    const now = Date.now();
    const lastUpdate = new Date(this.cache.lastUpdated);
    return now - lastUpdate.getTime() > this.config.updateInterval;
  }

  /**
   * 刷新配色方案数据
   */
  async refreshData() {
    try {
      console.log('正在刷新配色方案数据...');
      
      // 使用爬虫获取数据
      const crawledSchemes = await this.crawlPopularSchemes();
      
      // 使用多模型分析方案
      const analyzedSchemes = await this.analyzeWithModels(crawledSchemes);
      
      // 合并和排序
      this.schemes = this.mergeAndSortSchemes(analyzedSchemes);
      
      // 保存到缓存
      await this.saveCache();
      
      console.log(`已更新 ${this.schemes.length} 个配色方案`);
    } catch (error) {
      console.error('刷新配色方案数据失败:', error.message);
    }
  }

  /**
   * 爬取流行的配色方案
   */
  async crawlPopularSchemes() {
    try {
      console.log('正在爬取流行配色方案...');
      
      // 模拟爬虫功能（实际应用中应使用puppeteer或其他爬虫库）
      const axios = require('axios');
      const schemes = [];
      
      // 模拟从多个来源获取配色方案
      // 1. 预设的流行配色方案
      const presetSchemes = this.getPresetPopularSchemes();
      schemes.push(...presetSchemes);
      
      // 2. 尝试从公开API获取（如果可用）
      try {
        const response = await axios.get('https://www.thecolorapi.com/id?hex=0047AB&format=json');
        const colorData = response.data;
        schemes.push({
          id: `api-${Date.now()}`,
          name: `推荐配色-${colorData.name.value}`,
          colors: [colorData.hex.value],
          popularity: 0.85,
          compatibility: 0.8,
          category: 'api-generated',
          timestamp: Date.now()
        });
      } catch (apiError) {
        console.log('API获取失败，使用预设数据');
      }
      
      return schemes;
    } catch (error) {
      console.error('爬取配色方案失败:', error.message);
      return this.getPresetPopularSchemes(); // 失败时返回预设方案
    }
  }

  /**
   * 获取预设的流行配色方案
   */
  getPresetPopularSchemes() {
    return [
      {
        id: 'scheme-001',
        name: '现代简约',
        colors: ['#165DFF', '#FFFFFF', '#F5F7FA', '#4E5969', '#000000'],
        popularity: 0.95,
        compatibility: 0.92,
        category: 'minimalist',
        description: '简洁明快的现代风格，适合大多数应用场景',
        useCases: ['注册页', '登录页', '仪表盘']
      },
      {
        id: 'scheme-002',
        name: '科技感',
        colors: ['#00D4AA', '#11214A', '#F9F9F9', '#4F5E7B', '#000000'],
        popularity: 0.91,
        compatibility: 0.88,
        category: 'tech',
        description: '充满科技感的配色方案，适合科技产品',
        useCases: ['科技应用', '数据平台']
      },
      {
        id: 'scheme-003',
        name: '商务专业',
        colors: ['#2C3E50', '#3498DB', '#FFFFFF', '#BDC3C7', '#2C3E50'],
        popularity: 0.89,
        compatibility: 0.94,
        category: 'business',
        description: '专业稳重的商务配色，适合企业应用',
        useCases: ['企业官网', '管理系统']
      },
      {
        id: 'scheme-004',
        name: '活力清新',
        colors: ['#FF6B6B', '#4ECDC4', '#FFFFFF', '#F7FFF7', '#FFE66D'],
        popularity: 0.87,
        compatibility: 0.85,
        category: 'creative',
        description: '活力四射的配色方案，适合创意产品',
        useCases: ['社交应用', '创意平台']
      },
      {
        id: 'scheme-005',
        name: '深色主题',
        colors: ['#121212', '#1E1E1E', '#BB86FC', '#03DAC6', '#FFFFFF'],
        popularity: 0.86,
        compatibility: 0.82,
        category: 'dark',
        description: '护眼的深色主题配色',
        useCases: ['代码编辑器', '数据分析工具']
      },
      {
        id: 'scheme-006',
        name: '柔和舒适',
        colors: ['#F8F9FA', '#E9ECEF', '#DEE2E6', '#ADB5BD', '#495057'],
        popularity: 0.84,
        compatibility: 0.96,
        category: 'soft',
        description: '柔和舒适的配色，减少视觉疲劳',
        useCases: ['阅读应用', '长时间使用的工具']
      },
      {
        id: 'scheme-007',
        name: '品牌活力',
        colors: ['#FF5733', '#C70039', '#900C3F', '#581845', '#FFFFFF'],
        popularity: 0.83,
        compatibility: 0.80,
        category: 'brand',
        description: '富有活力和识别度的品牌配色',
        useCases: ['品牌官网', '营销页面']
      },
      {
        id: 'scheme-008',
        name: '自然和谐',
        colors: ['#7CB342', '#C0CA33', '#FDD835', '#FBC02D', '#FFA000'],
        popularity: 0.82,
        compatibility: 0.87,
        category: 'nature',
        description: '自然和谐的配色方案',
        useCases: ['健康应用', '环保平台']
      }
    ];
  }

  /**
   * 使用多模型分析配色方案
   */
  async analyzeWithModels(schemes) {
    try {
      console.log('使用多模型分析配色方案...');
      
      // 模拟多模型分析过程
      // 在实际应用中，这里应该调用真实的AI模型API
      const analyzedSchemes = schemes.map(scheme => {
        // 模拟模型分析结果
        const popularityScore = this.calculatePopularityScore(scheme);
        const compatibilityScore = this.calculateCompatibilityScore(scheme);
        const accessibilityScore = this.calculateAccessibilityScore(scheme);
        const trendScore = this.calculateTrendScore(scheme);
        
        // 综合评分
        const overallScore = (
          popularityScore * 0.3 +
          compatibilityScore * 0.3 +
          accessibilityScore * 0.2 +
          trendScore * 0.2
        );
        
        return {
          ...scheme,
          popularityScore,
          compatibilityScore,
          accessibilityScore,
          trendScore,
          overallScore,
          analysisTime: Date.now()
        };
      });
      
      return analyzedSchemes;
    } catch (error) {
      console.error('模型分析失败:', error.message);
      return schemes; // 失败时返回原始数据
    }
  }

  /**
   * 计算流行度得分
   */
  calculatePopularityScore(scheme) {
    // 简单的流行度计算逻辑
    return scheme.popularity || Math.random() * 0.3 + 0.7; // 随机生成0.7-1.0之间的值
  }

  /**
   * 计算兼容性得分
   */
  calculateCompatibilityScore(scheme) {
    // 简单的兼容性计算逻辑
    return scheme.compatibility || Math.random() * 0.3 + 0.7; // 随机生成0.7-1.0之间的值
  }

  /**
   * 计算可访问性得分
   */
  calculateAccessibilityScore(scheme) {
    // 检查颜色对比度
    // 简单实现，实际应用中应使用专业的对比度计算库
    const colors = scheme.colors || [];
    
    if (colors.length < 2) {
      return 0.5; // 颜色太少，可访问性一般
    }
    
    // 检查是否包含黑色和白色（通常具有良好的对比度）
    const hasBlackOrWhite = colors.some(color => 
      color === '#000000' || color === '#FFFFFF' || 
      color === '#000' || color === '#fff'
    );
    
    return hasBlackOrWhite ? 0.9 : 0.7;
  }

  /**
   * 计算趋势得分
   */
  calculateTrendScore(scheme) {
    // 简单的趋势计算逻辑
    // 深色主题和某些特定颜色组合在当前更流行
    const colors = scheme.colors || [];
    const isDarkTheme = colors.some(color => color === '#121212' || color === '#1E1E1E');
    
    return isDarkTheme ? 0.9 : Math.random() * 0.3 + 0.7;
  }

  /**
   * 合并和排序配色方案
   */
  mergeAndSortSchemes(schemes) {
    // 合并方案，去重
    const uniqueSchemes = [];
    const seenIds = new Set();
    
    for (const scheme of schemes) {
      if (!seenIds.has(scheme.id)) {
        seenIds.add(scheme.id);
        uniqueSchemes.push(scheme);
      }
    }
    
    // 按综合得分排序
    uniqueSchemes.sort((a, b) => (b.overallScore || 0) - (a.overallScore || 0));
    
    // 限制数量
    return uniqueSchemes.slice(0, this.config.maxSchemes);
  }

  /**
   * 获取推荐的配色方案
   */
  getRecommendedSchemes(count = 5, category = null) {
    let filteredSchemes = this.schemes;
    
    // 按类别过滤
    if (category) {
      filteredSchemes = filteredSchemes.filter(scheme => 
        scheme.category === category
      );
    }
    
    // 返回指定数量的推荐方案
    return filteredSchemes.slice(0, count);
  }

  /**
   * 根据用途获取推荐方案
   */
  getSchemesByUse(useCase, count = 3) {
    const filteredSchemes = this.schemes.filter(scheme => 
      scheme.useCases && scheme.useCases.includes(useCase)
    );
    
    return filteredSchemes.slice(0, count);
  }

  /**
   * 获取注册页面专用配色方案推荐
   */
  getRegistrationPageSchemes(count = 3) {
    return this.getSchemesByUse('注册页', count);
  }

  /**
   * 为指定颜色生成配套方案
   */
  generateComplimentaryScheme(baseColor, count = 1) {
    // 简单实现，实际应用中应使用专业的配色算法
    const schemes = [];
    
    for (let i = 0; i < count; i++) {
      const scheme = {
        id: `comp-${Date.now()}-${i}`,
        name: `配套方案-${i + 1}`,
        colors: [
          baseColor,
          this.getComplimentaryColor(baseColor, i),
          '#FFFFFF',
          '#F5F7FA',
          '#4E5969'
        ],
        popularityScore: 0.85,
        compatibilityScore: 0.90,
        accessibilityScore: 0.88,
        trendScore: 0.82,
        overallScore: 0.86,
        generated: true,
        timestamp: Date.now()
      };
      
      schemes.push(scheme);
    }
    
    return schemes;
  }

  /**
   * 获取互补色
   */
  getComplimentaryColor(baseColor, index = 0) {
    // 简单的互补色计算（实际应用中应使用专业的色彩理论）
    const complementColors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ];
    
    return complementColors[index % complementColors.length];
  }

  /**
   * 导出配色方案为CSS变量
   */
  exportSchemeToCSS(scheme) {
    if (!scheme || !scheme.colors) {
      return '';
    }
    
    let css = `/* ${scheme.name} 配色方案 */\n`;
    css += ':root {\n';
    
    // 主色调
    if (scheme.colors[0]) css += `  --primary-color: ${scheme.colors[0]};\n`;
    
    // 辅助色
    if (scheme.colors[1]) css += `  --secondary-color: ${scheme.colors[1]};\n`;
    
    // 背景色
    if (scheme.colors[2]) css += `  --background-color: ${scheme.colors[2]};\n`;
    
    // 文本色
    if (scheme.colors[3]) css += `  --text-color: ${scheme.colors[3]};\n`;
    
    // 强调色
    if (scheme.colors[4]) css += `  --accent-color: ${scheme.colors[4]};\n`;
    
    css += '}';
    
    return css;
  }

  /**
   * 导出配色方案为JSON
   */
  exportSchemeToJSON(scheme) {
    return JSON.stringify(scheme, null, 2);
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  console.log('启动配色方案推荐引擎...');
  
  const recommender = new ColorSchemeRecommender();
  
  // 演示推荐功能
  setTimeout(() => {
    console.log('\n推荐的注册页面配色方案:');
    const registrationSchemes = recommender.getRegistrationPageSchemes();
    
    registrationSchemes.forEach(scheme => {
      console.log(`\n方案: ${scheme.name}`);
      console.log(`评分: ${scheme.overallScore.toFixed(2)}`);
      console.log(`颜色: ${scheme.colors.join(', ')}`);
      console.log(`描述: ${scheme.description}`);
    });
    
    // 演示导出功能
    if (registrationSchemes.length > 0) {
      const css = recommender.exportSchemeToCSS(registrationSchemes[0]);
      console.log('\nCSS 变量导出示例:');
      console.log(css);
    }
  }, 1000);
}

// 导出模块
module.exports = {
  ColorSchemeRecommender
};