// 性能监控和分析工具 - 收集性能数据并提供优化建议
class PerformanceMonitor {
  constructor(options = {}) {
    // 监控配置
    this.config = {
      enablePerformanceAPI: options.enablePerformanceAPI !== false, // 是否启用 Performance API
      enableResourceTiming: options.enableResourceTiming !== false, // 是否监控资源加载时间
      enableNavigationTiming: options.enableNavigationTiming !== false, // 是否监控导航时间
      enableUserTiming: options.enableUserTiming !== false, // 是否启用用户计时
      enablePaintTiming: options.enablePaintTiming !== false, // 是否监控渲染时间
      enableLCPMonitoring: options.enableLCPMonitoring !== false, // 是否监控最大内容绘制
      enableFIDMonitoring: options.enableFIDMonitoring !== false, // 是否监控首次输入延迟
      enableCLSMonitoring: options.enableCLSMonitoring !== false, // 是否监控累积布局偏移
      samplingInterval: options.samplingInterval || 1000, // 采样间隔（毫秒）
      reportInterval: options.reportInterval || 5000, // 报告间隔（毫秒）
      sendToServer: options.sendToServer || false, // 是否发送到服务器
      serverUrl: options.serverUrl || '/api/performance', // 服务器URL
      debug: options.debug || false, // 是否启用调试
      ...options
    };
    
    // 性能数据存储
    this.performanceData = {
      navigation: {}, // 导航性能数据
      resources: [], // 资源性能数据
      marks: [], // 性能标记
      measures: [], // 性能测量
      metrics: {}, // Web Vitals 指标
      paint: {}, // 渲染时间
      frames: [], // 帧数据
      memory: {} // 内存使用情况
    };
    
    // 监控器引用
    this.monitors = new Map();
    
    // 报告定时器
    this.reportTimer = null;
    
    // 采样定时器
    this.samplingTimer = null;
    
    // 资源加载计数器
    this.resourceLoadCount = 0;
    
    // 性能阈值
    this.thresholds = {
      // Web Vitals 推荐阈值
      lcp: 2500, // 最大内容绘制（毫秒）
      fid: 100, // 首次输入延迟（毫秒）
      cls: 0.1, // 累积布局偏移
      
      // 其他性能指标阈值
      fcp: 1800, // 首次内容绘制（毫秒）
      tti: 3000, // 可交互时间（毫秒）
      tbt: 200, // 总阻塞时间（毫秒）
      fmp: 2000 // 首次有效绘制（毫秒）
    };
    
    // 初始化状态
    this.isInitialized = false;
    this.isMonitoring = false;
    
    // 兼容性检查
    this.compatibility = {
      performanceAPI: typeof window.performance !== 'undefined',
      resourceTiming: typeof window.performance.getEntriesByType === 'function',
      navigationTiming: typeof window.performance.timing !== 'undefined',
      userTiming: typeof window.performance.mark === 'function',
      paintTiming: typeof window.performance.getEntriesByType === 'function',
      memoryAPI: typeof window.performance.memory !== 'undefined',
      observerAPI: typeof window.PerformanceObserver === 'function'
    };
  }

  /**
   * 初始化性能监控器
   */
  initialize() {
    if (this.isInitialized) {
      console.warn('性能监控器已经初始化');
      return this;
    }
    
    console.log('初始化性能监控器...');
    
    // 检查浏览器兼容性
    this.checkCompatibility();
    
    // 注册性能监控器
    this.registerMonitors();
    
    // 收集初始性能数据
    this.collectInitialData();
    
    // 设置采样和报告
    this.setupSamplingAndReporting();
    
    // 注册事件监听
    this.setupEventListeners();
    
    // 启用调试
    if (this.config.debug) {
      this.enableDebugging();
    }
    
    this.isInitialized = true;
    
    return this;
  }

  /**
   * 检查浏览器兼容性
   */
  checkCompatibility() {
    console.log('检查浏览器兼容性...');
    
    if (!this.compatibility.performanceAPI) {
      console.warn('浏览器不支持 Performance API，性能监控将受限');
    }
    
    // 输出兼容性信息
    if (this.config.debug) {
      console.log('性能 API 兼容性:', this.compatibility);
    }
  }

  /**
   * 注册性能监控器
   */
  registerMonitors() {
    console.log('注册性能监控器...');
    
    // 注册导航性能监控器
    if (this.config.enableNavigationTiming && this.compatibility.navigationTiming) {
      this.registerNavigationMonitor();
    }
    
    // 注册资源性能监控器
    if (this.config.enableResourceTiming && this.compatibility.resourceTiming) {
      this.registerResourceMonitor();
    }
    
    // 注册渲染性能监控器
    if (this.config.enablePaintTiming && this.compatibility.paintTiming && this.compatibility.observerAPI) {
      this.registerPaintMonitor();
    }
    
    // 注册 Web Vitals 监控器
    this.registerWebVitalsMonitors();
    
    // 注册内存监控器
    if (this.compatibility.memoryAPI) {
      this.registerMemoryMonitor();
    }
  }

  /**
   * 注册导航性能监控器
   */
  registerNavigationMonitor() {
    this.monitors.set('navigation', {
      name: '导航性能',
      collect: this.collectNavigationTiming.bind(this),
      start: () => {},
      stop: () => {}
    });
    
    // 立即收集导航数据
    this.collectNavigationTiming();
  }

  /**
   * 注册资源性能监控器
   */
  registerResourceMonitor() {
    // 设置资源计时缓冲区
    if (typeof window.performance.setResourceTimingBufferSize === 'function') {
      window.performance.setResourceTimingBufferSize(100);
    }
    
    // 创建资源计时观察者
    let resourceObserver = null;
    
    const monitor = {
      name: '资源性能',
      collect: this.collectResourceTiming.bind(this),
      start: () => {
        if (this.compatibility.observerAPI && this.config.enableResourceTiming) {
          resourceObserver = new PerformanceObserver((list) => {
            this.handleResourceEntries(list.getEntries());
          });
          
          resourceObserver.observe({ type: 'resource', buffered: true });
        }
      },
      stop: () => {
        if (resourceObserver) {
          resourceObserver.disconnect();
        }
      }
    };
    
    this.monitors.set('resource', monitor);
  }

  /**
   * 注册渲染性能监控器
   */
  registerPaintMonitor() {
    let paintObserver = null;
    
    const monitor = {
      name: '渲染性能',
      collect: this.collectPaintTiming.bind(this),
      start: () => {
        if (this.compatibility.observerAPI && this.config.enablePaintTiming) {
          paintObserver = new PerformanceObserver((list) => {
            this.handlePaintEntries(list.getEntries());
          });
          
          paintObserver.observe({ type: 'paint', buffered: true });
        }
      },
      stop: () => {
        if (paintObserver) {
          paintObserver.disconnect();
        }
      }
    };
    
    this.monitors.set('paint', monitor);
  }

  /**
   * 注册 Web Vitals 监控器
   */
  registerWebVitalsMonitors() {
    // LCP 监控
    if (this.config.enableLCPMonitoring && this.compatibility.observerAPI) {
      this.registerLCPMonitor();
    }
    
    // FID 监控
    if (this.config.enableFIDMonitoring) {
      this.registerFIDMonitor();
    }
    
    // CLS 监控
    if (this.config.enableCLSMonitoring && this.compatibility.observerAPI) {
      this.registerCLSMonitor();
    }
  }

  /**
   * 注册 LCP 监控器
   */
  registerLCPMonitor() {
    let lcpObserver = null;
    let lcpEntry = null;
    let lcpStartTime = 0;
    
    const monitor = {
      name: 'LCP 监控',
      collect: () => {
        return { lcp: lcpEntry };
      },
      start: () => {
        lcpStartTime = performance.now();
        
        lcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const lastEntry = entries[entries.length - 1];
          
          // 只记录最大的 LCP 条目
          if (!lcpEntry || lastEntry.startTime > lcpEntry.startTime) {
            lcpEntry = lastEntry;
            
            // 更新性能数据
            this.performanceData.metrics.lcp = {
              value: lastEntry.startTime,
              element: lastEntry.element,
              timing: performance.now() - lcpStartTime,
              score: this.calculateLCPMetric(lastEntry.startTime)
            };
            
            // 触发 LCP 更新事件
            this.emit('lcpUpdated', this.performanceData.metrics.lcp);
          }
        });
        
        lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
      },
      stop: () => {
        if (lcpObserver) {
          lcpObserver.disconnect();
        }
      }
    };
    
    this.monitors.set('lcp', monitor);
  }

  /**
   * 注册 FID 监控器
   */
  registerFIDMonitor() {
    let fidTimeout = null;
    let hasFired = false;
    
    const monitor = {
      name: 'FID 监控',
      collect: () => {
        return { fid: this.performanceData.metrics.fid };
      },
      start: () => {
        const handleFirstInput = (entry) => {
          if (hasFired) return;
          hasFired = true;
          
          // 清除超时
          clearTimeout(fidTimeout);
          
          // 计算 FID
          const fid = entry.processingStart - entry.startTime;
          
          // 更新性能数据
          this.performanceData.metrics.fid = {
            value: fid,
            entry,
            score: this.calculateFIDMetric(fid)
          };
          
          // 触发 FID 更新事件
          this.emit('fidUpdated', this.performanceData.metrics.fid);
          
          // 移除事件监听
          window.removeEventListener('mousedown', handleFirstInput, { passive: true, capture: true });
          window.removeEventListener('keydown', handleFirstInput, { passive: true, capture: true });
          window.removeEventListener('touchstart', handleFirstInput, { passive: true, capture: true });
        };
        
        // 添加事件监听
        window.addEventListener('mousedown', handleFirstInput, { passive: true, capture: true });
        window.addEventListener('keydown', handleFirstInput, { passive: true, capture: true });
        window.addEventListener('touchstart', handleFirstInput, { passive: true, capture: true });
        
        // 设置超时，防止没有用户输入
        fidTimeout = setTimeout(() => {
          hasFired = true;
          // 移除事件监听
          window.removeEventListener('mousedown', handleFirstInput, { passive: true, capture: true });
          window.removeEventListener('keydown', handleFirstInput, { passive: true, capture: true });
          window.removeEventListener('touchstart', handleFirstInput, { passive: true, capture: true });
        }, 10000);
      },
      stop: () => {
        clearTimeout(fidTimeout);
      }
    };
    
    this.monitors.set('fid', monitor);
  }

  /**
   * 注册 CLS 监控器
   */
  registerCLSMonitor() {
    let clsObserver = null;
    let clsValue = 0;
    let clsEntries = [];
    let lastEntries = [];
    
    const monitor = {
      name: 'CLS 监控',
      collect: () => {
        return { cls: { value: clsValue, entries: clsEntries } };
      },
      start: () => {
        clsObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          
          entries.forEach(entry => {
            // 忽略不影响布局稳定性的动画
            if (!entry.hadRecentInput) {
              const lastEntry = lastEntries[lastEntries.length - 1];
              const lastTime = lastEntry ? lastEntry.startTime : 0;
              
              // 将同一渲染帧中的偏移合并
              if (entry.startTime - lastTime < 1000) {
                clsValue += entry.value;
                clsEntries.push(entry);
              } else {
                // 新的渲染帧，重置
                lastEntries = [entry];
                clsValue = entry.value;
                clsEntries = [entry];
              }
              
              // 更新性能数据
              this.performanceData.metrics.cls = {
                value: clsValue,
                entries: clsEntries,
                score: this.calculateCLSMetric(clsValue)
              };
              
              // 触发 CLS 更新事件
              this.emit('clsUpdated', this.performanceData.metrics.cls);
            }
          });
        });
        
        clsObserver.observe({ type: 'layout-shift', buffered: true });
      },
      stop: () => {
        if (clsObserver) {
          clsObserver.disconnect();
        }
      }
    };
    
    this.monitors.set('cls', monitor);
  }

  /**
   * 注册内存监控器
   */
  registerMemoryMonitor() {
    const monitor = {
      name: '内存监控',
      collect: this.collectMemoryInfo.bind(this),
      start: () => {},
      stop: () => {}
    };
    
    this.monitors.set('memory', monitor);
  }

  /**
   * 收集初始性能数据
   */
  collectInitialData() {
    console.log('收集初始性能数据...');
    
    // 收集导航数据
    if (this.monitors.has('navigation')) {
      this.monitors.get('navigation').collect();
    }
    
    // 收集资源数据
    if (this.monitors.has('resource')) {
      this.monitors.get('resource').collect();
    }
    
    // 收集内存数据
    if (this.monitors.has('memory')) {
      this.monitors.get('memory').collect();
    }
  }

  /**
   * 设置采样和报告
   */
  setupSamplingAndReporting() {
    // 设置采样定时器
    if (this.config.samplingInterval > 0) {
      this.samplingTimer = setInterval(() => {
        this.collectSample();
      }, this.config.samplingInterval);
    }
    
    // 设置报告定时器
    if (this.config.reportInterval > 0) {
      this.reportTimer = setInterval(() => {
        this.generateReport();
      }, this.config.reportInterval);
    }
  }

  /**
   * 设置事件监听
   */
  setupEventListeners() {
    // 监听页面卸载事件，清理资源
    window.addEventListener('beforeunload', () => {
      this.cleanup();
    });
    
    // 监听资源加载完成事件
    window.addEventListener('load', () => {
      this.onPageLoaded();
    });
    
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        // 页面隐藏时生成最终报告
        this.generateFinalReport();
      }
    });
  }

  /**
   * 页面加载完成
   */
  onPageLoaded() {
    console.log('页面加载完成，收集最终性能数据...');
    
    // 收集最终的导航和资源数据
    this.collectNavigationTiming();
    this.collectResourceTiming();
    
    // 生成初始报告
    this.generateReport();
    
    // 触发页面加载完成事件
    this.emit('pageLoaded', this.performanceData);
  }

  /**
   * 收集采样数据
   */
  collectSample() {
    try {
      // 收集内存数据
      if (this.monitors.has('memory')) {
        this.monitors.get('memory').collect();
      }
      
      // 收集帧数据
      this.collectFrameData();
      
      // 收集资源数据
      if (this.monitors.has('resource')) {
        this.monitors.get('resource').collect();
      }
    } catch (error) {
      console.error('收集采样数据失败:', error);
    }
  }

  /**
   * 收集导航计时数据
   */
  collectNavigationTiming() {
    if (!this.compatibility.navigationTiming) return;
    
    const timing = window.performance.timing;
    const navigation = window.performance.navigation;
    
    // 计算各种性能指标
    const navigationData = {
      // 网络连接阶段
      redirectTime: timing.redirectEnd - timing.redirectStart,
      appCacheTime: timing.domainLookupStart - timing.fetchStart,
      dnsLookupTime: timing.domainLookupEnd - timing.domainLookupStart,
      tcpConnectTime: timing.connectEnd - timing.connectStart,
      sslHandshakeTime: timing.secureConnectionStart > 0 ? timing.connectEnd - timing.secureConnectionStart : 0,
      
      // 请求阶段
      requestTime: timing.responseStart - timing.requestStart,
      responseTime: timing.responseEnd - timing.responseStart,
      
      // 渲染阶段
      processingTime: timing.domComplete - timing.responseEnd,
      domInteractiveTime: timing.domInteractive - timing.fetchStart,
      domContentLoadedTime: timing.domContentLoadedEventEnd - timing.fetchStart,
      loadTime: timing.loadEventEnd - timing.loadEventStart,
      
      // 总时间
      totalLoadTime: timing.loadEventEnd - timing.navigationStart,
      timeToInteractive: timing.domInteractive - timing.navigationStart,
      
      // 导航信息
      navigationType: navigation.type,
      redirectCount: navigation.redirectCount
    };
    
    // 更新性能数据
    this.performanceData.navigation = navigationData;
    
    // 触发导航数据更新事件
    this.emit('navigationDataUpdated', navigationData);
    
    return navigationData;
  }

  /**
   * 收集资源计时数据
   */
  collectResourceTiming() {
    if (!this.compatibility.resourceTiming) return;
    
    try {
      const resources = window.performance.getEntriesByType('resource');
      
      // 筛选新增的资源
      const newResources = resources.filter(resource => {
        return !this.performanceData.resources.some(r => r.name === resource.name);
      });
      
      // 添加新资源
      if (newResources.length > 0) {
        // 处理新资源
        newResources.forEach(resource => {
          this.processResourceEntry(resource);
        });
        
        // 更新资源加载计数
        this.resourceLoadCount += newResources.length;
        
        // 触发资源数据更新事件
        this.emit('resourcesUpdated', newResources);
      }
    } catch (error) {
      console.error('收集资源计时数据失败:', error);
    }
  }

  /**
   * 处理资源条目
   */
  processResourceEntry(entry) {
    // 计算资源加载的各个阶段时间
    const resourceData = {
      name: entry.name,
      type: entry.initiatorType || this.detectResourceType(entry.name),
      startTime: entry.startTime,
      duration: entry.duration,
      
      // 阶段时间
      redirectTime: entry.redirectEnd - entry.redirectStart,
      dnsLookupTime: entry.domainLookupEnd - entry.domainLookupStart,
      tcpConnectTime: entry.connectEnd - entry.connectStart,
      sslHandshakeTime: entry.secureConnectionStart > 0 ? entry.connectEnd - entry.secureConnectionStart : 0,
      requestTime: entry.responseStart - entry.requestStart,
      responseTime: entry.responseEnd - entry.responseStart,
      
      // 其他信息
      transferSize: entry.transferSize || 0,
      encodedBodySize: entry.encodedBodySize || 0,
      decodedBodySize: entry.decodedBodySize || 0,
      nextHopProtocol: entry.nextHopProtocol || '',
      
      // 加载状态
      status: 'loaded',
      timestamp: Date.now()
    };
    
    // 添加到资源列表
    this.performanceData.resources.push(resourceData);
    
    return resourceData;
  }

  /**
   * 检测资源类型
   */
  detectResourceType(url) {
    const extensions = {
      '.js': 'script',
      '.css': 'css',
      '.jpg': 'image',
      '.jpeg': 'image',
      '.png': 'image',
      '.gif': 'image',
      '.webp': 'image',
      '.svg': 'image',
      '.ico': 'image',
      '.woff': 'font',
      '.woff2': 'font',
      '.ttf': 'font',
      '.otf': 'font',
      '.eot': 'font',
      '.mp3': 'audio',
      '.wav': 'audio',
      '.ogg': 'audio',
      '.mp4': 'video',
      '.webm': 'video',
      '.json': 'fetch',
      '.xml': 'fetch',
      '.html': 'document'
    };
    
    // 获取扩展名
    const lastDotIndex = url.lastIndexOf('.');
    if (lastDotIndex !== -1) {
      const extension = url.slice(lastDotIndex).toLowerCase();
      return extensions[extension] || 'other';
    }
    
    return 'other';
  }

  /**
   * 处理资源条目列表
   */
  handleResourceEntries(entries) {
    entries.forEach(entry => {
      this.processResourceEntry(entry);
    });
    
    // 更新资源加载计数
    this.resourceLoadCount += entries.length;
    
    // 触发资源更新事件
    this.emit('resourcesUpdated', entries);
  }

  /**
   * 收集渲染计时数据
   */
  collectPaintTiming() {
    if (!this.compatibility.paintTiming) return;
    
    try {
      const paintEntries = window.performance.getEntriesByType('paint');
      
      paintEntries.forEach(entry => {
        if (entry.name === 'first-paint') {
          this.performanceData.paint.firstPaint = entry.startTime;
        } else if (entry.name === 'first-contentful-paint') {
          this.performanceData.paint.firstContentfulPaint = entry.startTime;
        }
      });
      
      // 触发渲染数据更新事件
      this.emit('paintDataUpdated', this.performanceData.paint);
    } catch (error) {
      console.error('收集渲染计时数据失败:', error);
    }
  }

  /**
   * 处理渲染条目
   */
  handlePaintEntries(entries) {
    entries.forEach(entry => {
      if (entry.name === 'first-paint') {
        this.performanceData.paint.firstPaint = entry.startTime;
      } else if (entry.name === 'first-contentful-paint') {
        this.performanceData.paint.firstContentfulPaint = entry.startTime;
      }
    });
    
    // 触发渲染数据更新事件
    this.emit('paintDataUpdated', this.performanceData.paint);
  }

  /**
   * 收集内存信息
   */
  collectMemoryInfo() {
    if (!this.compatibility.memoryAPI) return;
    
    const memory = window.performance.memory;
    
    const memoryData = {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit,
      
      // 计算使用百分比
      usagePercentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
      timestamp: Date.now()
    };
    
    // 更新性能数据
    this.performanceData.memory = memoryData;
    
    // 触发内存数据更新事件
    this.emit('memoryUpdated', memoryData);
    
    return memoryData;
  }

  /**
   * 收集帧数据
   */
  collectFrameData() {
    // 使用 requestAnimationFrame 收集帧率数据
    requestAnimationFrame(() => {
      const now = performance.now();
      
      // 计算帧率
      if (this.lastFrameTime) {
        const frameDuration = now - this.lastFrameTime;
        const fps = Math.round(1000 / frameDuration);
        
        // 添加到帧数据列表
        this.performanceData.frames.push({
          timestamp: now,
          fps: fps,
          duration: frameDuration
        });
        
        // 限制帧数据列表长度
        if (this.performanceData.frames.length > 100) {
          this.performanceData.frames.shift();
        }
        
        // 触发帧数据更新事件
        this.emit('frameUpdated', { fps, duration: frameDuration });
      }
      
      this.lastFrameTime = now;
    });
  }

  /**
   * 开始监控
   */
  start() {
    if (this.isMonitoring) {
      console.warn('性能监控已经开始');
      return this;
    }
    
    console.log('开始性能监控...');
    
    // 如果未初始化，先初始化
    if (!this.isInitialized) {
      this.initialize();
    }
    
    // 启动所有监控器
    this.monitors.forEach(monitor => {
      if (monitor.start && typeof monitor.start === 'function') {
        try {
          monitor.start();
        } catch (error) {
          console.error(`启动监控器 ${monitor.name} 失败:`, error);
        }
      }
    });
    
    // 设置监控状态
    this.isMonitoring = true;
    
    // 触发监控开始事件
    this.emit('monitoringStarted');
    
    return this;
  }

  /**
   * 停止监控
   */
  stop() {
    if (!this.isMonitoring) {
      console.warn('性能监控未开始');
      return this;
    }
    
    console.log('停止性能监控...');
    
    // 停止所有监控器
    this.monitors.forEach(monitor => {
      if (monitor.stop && typeof monitor.stop === 'function') {
        try {
          monitor.stop();
        } catch (error) {
          console.error(`停止监控器 ${monitor.name} 失败:`, error);
        }
      }
    });
    
    // 清除定时器
    if (this.samplingTimer) {
      clearInterval(this.samplingTimer);
    }
    
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
    }
    
    // 设置监控状态
    this.isMonitoring = false;
    
    // 触发监控停止事件
    this.emit('monitoringStopped');
    
    return this;
  }

  /**
   * 生成性能报告
   */
  generateReport() {
    try {
      // 收集最新数据
      this.collectLatestData();
      
      // 生成综合报告
      const report = this.createComprehensiveReport();
      
      // 分析性能问题
      const analysis = this.analyzePerformance(report);
      
      // 生成优化建议
      const recommendations = this.generateRecommendations(analysis);
      
      // 完整报告
      const fullReport = {
        timestamp: Date.now(),
        report,
        analysis,
        recommendations
      };
      
      // 触发报告生成事件
      this.emit('reportGenerated', fullReport);
      
      // 发送到服务器（如果配置了）
      if (this.config.sendToServer) {
        this.sendReportToServer(fullReport);
      }
      
      return fullReport;
    } catch (error) {
      console.error('生成性能报告失败:', error);
      return null;
    }
  }

  /**
   * 收集最新数据
   */
  collectLatestData() {
    // 收集所有监控器的数据
    this.monitors.forEach(monitor => {
      if (monitor.collect && typeof monitor.collect === 'function') {
        try {
          monitor.collect();
        } catch (error) {
          console.error(`收集 ${monitor.name} 数据失败:`, error);
        }
      }
    });
  }

  /**
   * 创建综合报告
   */
  createComprehensiveReport() {
    return {
      // 基本信息
      page: {
        url: window.location.href,
        title: document.title,
        userAgent: navigator.userAgent,
        screenSize: `${window.innerWidth}x${window.innerHeight}`
      },
      
      // 导航性能
      navigation: this.performanceData.navigation,
      
      // Web Vitals 指标
      metrics: this.performanceData.metrics,
      
      // 渲染时间
      paint: this.performanceData.paint,
      
      // 资源统计
      resourceStats: this.calculateResourceStats(),
      
      // 内存使用
      memory: this.performanceData.memory,
      
      // 帧率统计
      frameStats: this.calculateFrameStats()
    };
  }

  /**
   * 计算资源统计
   */
  calculateResourceStats() {
    const resources = this.performanceData.resources;
    const stats = {
      total: resources.length,
      byType: {},
      totalSize: 0,
      averageLoadTime: 0,
      largestResources: [],
      slowestResources: []
    };
    
    // 按类型统计
    resources.forEach(resource => {
      // 初始化类型计数
      if (!stats.byType[resource.type]) {
        stats.byType[resource.type] = {
          count: 0,
          totalSize: 0,
          totalTime: 0
        };
      }
      
      // 更新类型统计
      stats.byType[resource.type].count++;
      stats.byType[resource.type].totalSize += resource.transferSize;
      stats.byType[resource.type].totalTime += resource.duration;
      
      // 更新总体统计
      stats.totalSize += resource.transferSize;
    });
    
    // 计算平均加载时间
    if (resources.length > 0) {
      const totalTime = resources.reduce((sum, resource) => sum + resource.duration, 0);
      stats.averageLoadTime = totalTime / resources.length;
    }
    
    // 找出最大的资源
    stats.largestResources = [...resources]
      .sort((a, b) => b.transferSize - a.transferSize)
      .slice(0, 5)
      .map(r => ({ name: r.name, size: r.transferSize, type: r.type }));
    
    // 找出最慢的资源
    stats.slowestResources = [...resources]
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 5)
      .map(r => ({ name: r.name, duration: r.duration, type: r.type }));
    
    return stats;
  }

  /**
   * 计算帧率统计
   */
  calculateFrameStats() {
    const frames = this.performanceData.frames;
    
    if (frames.length === 0) {
      return {
        averageFPS: 0,
        minFPS: 0,
        maxFPS: 0,
        frameDrops: 0
      };
    }
    
    const fpsValues = frames.map(frame => frame.fps);
    const frameDrops = fpsValues.filter(fps => fps < 30).length;
    
    return {
      averageFPS: fpsValues.reduce((sum, fps) => sum + fps, 0) / fpsValues.length,
      minFPS: Math.min(...fpsValues),
      maxFPS: Math.max(...fpsValues),
      frameDrops: frameDrops
    };
  }

  /**
   * 分析性能
   */
  analyzePerformance(report) {
    const issues = [];
    const scores = {};
    
    // 分析 Web Vitals 指标
    this.analyzeWebVitals(report, issues, scores);
    
    // 分析资源加载
    this.analyzeResourceLoading(report, issues);
    
    // 分析导航性能
    this.analyzeNavigationPerformance(report, issues);
    
    // 分析内存使用
    this.analyzeMemoryUsage(report, issues);
    
    // 分析帧率
    this.analyzeFrameRate(report, issues);
    
    return {
      overallScore: this.calculateOverallScore(scores),
      issues,
      scores
    };
  }

  /**
   * 分析 Web Vitals 指标
   */
  analyzeWebVitals(report, issues, scores) {
    const metrics = report.metrics;
    
    // 分析 LCP
    if (metrics.lcp) {
      const score = this.calculateLCPMetric(metrics.lcp.value);
      scores.lcp = score;
      
      if (metrics.lcp.value > this.thresholds.lcp) {
        issues.push({
          type: 'performance',
          severity: 'high',
          metric: 'LCP',
          value: metrics.lcp.value,
          threshold: this.thresholds.lcp,
          description: `最大内容绘制时间过长: ${metrics.lcp.value.toFixed(2)}ms (阈值: ${this.thresholds.lcp}ms)`,
          element: metrics.lcp.element ? metrics.lcp.element.tagName : 'unknown'
        });
      }
    }
    
    // 分析 FID
    if (metrics.fid) {
      const score = this.calculateFIDMetric(metrics.fid.value);
      scores.fid = score;
      
      if (metrics.fid.value > this.thresholds.fid) {
        issues.push({
          type: 'performance',
          severity: 'medium',
          metric: 'FID',
          value: metrics.fid.value,
          threshold: this.thresholds.fid,
          description: `首次输入延迟过长: ${metrics.fid.value.toFixed(2)}ms (阈值: ${this.thresholds.fid}ms)`
        });
      }
    }
    
    // 分析 CLS
    if (metrics.cls) {
      const score = this.calculateCLSMetric(metrics.cls.value);
      scores.cls = score;
      
      if (metrics.cls.value > this.thresholds.cls) {
        issues.push({
          type: 'performance',
          severity: 'medium',
          metric: 'CLS',
          value: metrics.cls.value,
          threshold: this.thresholds.cls,
          description: `累积布局偏移过大: ${metrics.cls.value.toFixed(3)} (阈值: ${this.thresholds.cls})`
        });
      }
    }
  }

  /**
   * 计算 LCP 指标分数
   */
  calculateLCPMetric(value) {
    if (value <= 2500) return 100;
    if (value <= 4000) return 75;
    if (value <= 6000) return 50;
    return 25;
  }

  /**
   * 计算 FID 指标分数
   */
  calculateFIDMetric(value) {
    if (value <= 100) return 100;
    if (value <= 300) return 75;
    if (value <= 500) return 50;
    return 25;
  }

  /**
   * 计算 CLS 指标分数
   */
  calculateCLSMetric(value) {
    if (value <= 0.1) return 100;
    if (value <= 0.25) return 75;
    if (value <= 0.5) return 50;
    return 25;
  }

  /**
   * 分析资源加载
   */
  analyzeResourceLoading(report, issues) {
    const resourceStats = report.resourceStats;
    
    // 检查资源数量
    if (resourceStats.total > 100) {
      issues.push({
        type: 'resource',
        severity: 'medium',
        description: `页面资源数量过多: ${resourceStats.total} 个资源`,
        suggestion: '考虑减少资源数量，合并或压缩文件'
      });
    }
    
    // 检查大资源
    resourceStats.largestResources.forEach(resource => {
      if (resource.size > 1024 * 1024) { // 1MB
        issues.push({
          type: 'resource',
          severity: 'high',
          description: `发现大资源: ${resource.name} (${(resource.size / 1024 / 1024).toFixed(2)}MB)`,
          suggestion: '考虑压缩或优化此资源'
        });
      }
    });
    
    // 检查慢资源
    resourceStats.slowestResources.forEach(resource => {
      if (resource.duration > 2000) { // 2秒
        issues.push({
          type: 'resource',
          severity: 'high',
          description: `资源加载缓慢: ${resource.name} (${resource.duration.toFixed(2)}ms)`,
          suggestion: '考虑使用 CDN 或优化此资源'
        });
      }
    });
  }

  /**
   * 分析导航性能
   */
  analyzeNavigationPerformance(report, issues) {
    const navigation = report.navigation;
    
    if (!navigation) return;
    
    // 检查总加载时间
    if (navigation.totalLoadTime > 5000) { // 5秒
      issues.push({
        type: 'navigation',
        severity: 'high',
        description: `页面加载时间过长: ${(navigation.totalLoadTime / 1000).toFixed(2)}秒`,
        suggestion: '优化关键路径渲染，减少阻塞资源'
      });
    }
    
    // 检查 DNS 查找时间
    if (navigation.dnsLookupTime > 200) { // 200ms
      issues.push({
        type: 'navigation',
        severity: 'medium',
        description: `DNS 查找时间过长: ${navigation.dnsLookupTime.toFixed(2)}ms`,
        suggestion: '考虑使用 DNS 预解析'
      });
    }
    
    // 检查 TCP 连接时间
    if (navigation.tcpConnectTime > 300) { // 300ms
      issues.push({
        type: 'navigation',
        severity: 'medium',
        description: `TCP 连接时间过长: ${navigation.tcpConnectTime.toFixed(2)}ms`,
        suggestion: '确保使用持久连接'
      });
    }
  }

  /**
   * 分析内存使用
   */
  analyzeMemoryUsage(report, issues) {
    const memory = report.memory;
    
    if (!memory) return;
    
    // 检查内存使用百分比
    if (memory.usagePercentage > 80) {
      issues.push({
        type: 'memory',
        severity: 'high',
        description: `内存使用过高: ${memory.usagePercentage.toFixed(2)}%`,
        suggestion: '检查内存泄漏，优化大型对象处理'
      });
    }
  }

  /**
   * 分析帧率
   */
  analyzeFrameRate(report, issues) {
    const frameStats = report.frameStats;
    
    if (!frameStats) return;
    
    // 检查平均帧率
    if (frameStats.averageFPS < 30) {
      issues.push({
        type: 'render',
        severity: 'high',
        description: `平均帧率过低: ${frameStats.averageFPS.toFixed(2)}fps`,
        suggestion: '优化动画性能，使用硬件加速'
      });
    }
    
    // 检查帧丢失
    if (frameStats.frameDrops > 10) {
      issues.push({
        type: 'render',
        severity: 'medium',
        description: `帧丢失过多: ${frameStats.frameDrops}次`,
        suggestion: '减少主线程阻塞，优化动画'
      });
    }
  }

  /**
   * 计算总体分数
   */
  calculateOverallScore(scores) {
    const scoreValues = Object.values(scores);
    
    if (scoreValues.length === 0) return 0;
    
    // 计算平均分
    const averageScore = scoreValues.reduce((sum, score) => sum + score, 0) / scoreValues.length;
    
    return Math.round(averageScore);
  }

  /**
   * 生成优化建议
   */
  generateRecommendations(analysis) {
    const recommendations = [];
    const issues = analysis.issues;
    
    // 基于问题生成建议
    issues.forEach(issue => {
      switch (issue.type) {
        case 'performance':
          this.generatePerformanceRecommendations(issue, recommendations);
          break;
        case 'resource':
          this.generateResourceRecommendations(issue, recommendations);
          break;
        case 'navigation':
          this.generateNavigationRecommendations(issue, recommendations);
          break;
        case 'memory':
          this.generateMemoryRecommendations(issue, recommendations);
          break;
        case 'render':
          this.generateRenderRecommendations(issue, recommendations);
          break;
      }
    });
    
    // 去重
    return this.deduplicateRecommendations(recommendations);
  }

  /**
   * 生成性能优化建议
   */
  generatePerformanceRecommendations(issue, recommendations) {
    switch (issue.metric) {
      case 'LCP':
        recommendations.push({
          type: 'optimize',
          target: 'LCP',
          description: '优化最大内容绘制 (LCP)',
          actions: [
            '优化关键图片，使用适当的格式和尺寸',
            '减少阻塞渲染的 CSS/JS',
            '使用浏览器缓存',
            '考虑使用 CDN'
          ],
          priority: 'high'
        });
        break;
      case 'FID':
        recommendations.push({
          type: 'optimize',
          target: 'FID',
          description: '优化首次输入延迟 (FID)',
          actions: [
            '延迟加载非关键 JavaScript',
            '减少主线程工作',
            '使用 Web Workers 处理复杂计算',
            '优化长任务'
          ],
          priority: 'medium'
        });
        break;
      case 'CLS':
        recommendations.push({
          type: 'optimize',
          target: 'CLS',
          description: '优化累积布局偏移 (CLS)',
          actions: [
            '为图片和视频元素设置固定尺寸',
            '避免动态注入内容',
            '使用 CSS 变换代替位置偏移',
            '预加载字体并设置回退字体'
          ],
          priority: 'medium'
        });
        break;
    }
  }

  /**
   * 生成资源优化建议
   */
  generateResourceRecommendations(issue, recommendations) {
    recommendations.push({
      type: 'optimize',
      target: 'resources',
      description: '优化资源加载',
      actions: [
        '压缩和合并 CSS/JS 文件',
        '使用适当的图片格式 (WebP, AVIF)',
        '实施资源预加载',
        '使用延迟加载非关键资源',
        '优化字体加载'
      ],
      priority: issue.severity === 'high' ? 'high' : 'medium'
    });
  }

  /**
   * 生成导航优化建议
   */
  generateNavigationRecommendations(issue, recommendations) {
    recommendations.push({
      type: 'optimize',
      target: 'navigation',
      description: '优化导航性能',
      actions: [
        '减少重定向',
        '启用 DNS 预解析',
        '使用 HTTP/2 或 HTTP/3',
        '优化服务器响应时间',
        '实施关键渲染路径优化'
      ],
      priority: 'high'
    });
  }

  /**
   * 生成内存优化建议
   */
  generateMemoryRecommendations(issue, recommendations) {
    recommendations.push({
      type: 'optimize',
      target: 'memory',
      description: '优化内存使用',
      actions: [
        '移除不再使用的事件监听器',
        '避免内存泄漏',
        '优化大型数据结构',
        '使用适当的缓存策略',
        '考虑使用虚拟滚动处理大型列表'
      ],
      priority: 'high'
    });
  }

  /**
   * 生成渲染优化建议
   */
  generateRenderRecommendations(issue, recommendations) {
    recommendations.push({
      type: 'optimize',
      target: 'render',
      description: '优化渲染性能',
      actions: [
        '使用 CSS transform 和 opacity 进行动画',
        '避免频繁的布局计算',
        '使用 CSS will-change 属性',
        '优化动画帧率',
        '减少重绘和回流'
      ],
      priority: 'high'
    });
  }

  /**
   * 去重建议
   */
  deduplicateRecommendations(recommendations) {
    const unique = new Map();
    
    recommendations.forEach(rec => {
      const key = `${rec.type}-${rec.target}`;
      if (!unique.has(key)) {
        unique.set(key, rec);
      }
    });
    
    return Array.from(unique.values());
  }

  /**
   * 发送报告到服务器
   */
  sendReportToServer(report) {
    try {
      fetch(this.config.serverUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(report)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`服务器响应失败: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (this.config.debug) {
          console.log('性能报告已发送到服务器');
        }
      })
      .catch(error => {
        console.error('发送性能报告失败:', error);
      });
    } catch (error) {
      console.error('发送性能报告异常:', error);
    }
  }

  /**
   * 生成最终报告
   */
  generateFinalReport() {
    const report = this.generateReport();
    
    if (report) {
      // 触发最终报告事件
      this.emit('finalReportGenerated', report);
    }
    
    return report;
  }

  /**
   * 事件系统
   */
  on(event, listener) {
    if (!this.listeners) {
      this.listeners = new Map();
    }
    
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    
    this.listeners.get(event).push(listener);
    return this;
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (!this.listeners || !this.listeners.has(event)) return this;
    
    const listeners = this.listeners.get(event);
    listeners.forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error(`事件处理器错误: ${event}`, error);
      }
    });
    
    return this;
  }

  /**
   * 移除事件监听
   */
  off(event, listener) {
    if (!this.listeners || !this.listeners.has(event)) return this;
    
    const listeners = this.listeners.get(event);
    const index = listeners.indexOf(listener);
    
    if (index !== -1) {
      listeners.splice(index, 1);
    }
    
    return this;
  }

  /**
   * 启用调试
   */
  enableDebugging() {
    console.log('启用性能监控调试模式');
    
    // 监听关键事件
    this.on('reportGenerated', report => {
      console.log('性能报告:', report);
    });
    
    this.on('performanceWarning', warning => {
      console.warn('性能警告:', warning);
    });
    
    // 定期输出性能概览
    setInterval(() => {
      console.log('性能概览:', this.getPerformanceOverview());
    }, 10000);
  }

  /**
   * 获取性能概览
   */
  getPerformanceOverview() {
    return {
      webVitals: this.performanceData.metrics,
      resourceCount: this.performanceData.resources.length,
      memoryUsage: this.performanceData.memory.usagePercentage || 0,
      monitoring: this.isMonitoring
    };
  }

  /**
   * 获取完整性能数据
   */
  getPerformanceData() {
    return { ...this.performanceData };
  }

  /**
   * 获取状态
   */
  getState() {
    return {
      initialized: this.isInitialized,
      monitoring: this.isMonitoring,
      resourceCount: this.performanceData.resources.length,
      monitorsCount: this.monitors.size,
      compatibility: this.compatibility
    };
  }

  /**
   * 清理资源
   */
  cleanup() {
    // 停止监控
    if (this.isMonitoring) {
      this.stop();
    }
    
    // 清除定时器
    if (this.samplingTimer) {
      clearInterval(this.samplingTimer);
      this.samplingTimer = null;
    }
    
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = null;
    }
    
    // 清除数据
    this.performanceData = {
      navigation: {},
      resources: [],
      marks: [],
      measures: [],
      metrics: {},
      paint: {},
      frames: [],
      memory: {}
    };
    
    console.log('性能监控器资源已清理');
  }

  /**
   * 销毁性能监控器
   */
  destroy() {
    this.cleanup();
    
    // 清除所有引用
    this.monitors.clear();
    
    if (this.listeners) {
      this.listeners.clear();
    }
    
    // 重置状态
    this.isInitialized = false;
    this.isMonitoring = false;
    
    console.log('性能监控器已销毁');
  }
}

// 创建性能监控器实例
const performanceMonitor = new PerformanceMonitor({
  enablePerformanceAPI: true,
  enableResourceTiming: true,
  enableNavigationTiming: true,
  enableUserTiming: true,
  enablePaintTiming: true,
  enableLCPMonitoring: true,
  enableFIDMonitoring: true,
  enableCLSMonitoring: true,
  samplingInterval: 1000,
  reportInterval: 10000,
  sendToServer: false,
  debug: false
});

// 导出
if (typeof window !== 'undefined') {
  window.PerformanceMonitor = PerformanceMonitor;
  window.performanceMonitor = performanceMonitor;
}

export { PerformanceMonitor, performanceMonitor };