// 组件管理器 - 负责页面组件的加载、渲染和层级管理
class ComponentManager {
  constructor() {
    this.componentsConfig = null;
    this.loadedComponents = {};
    this.componentInstances = {};
    this.currentPage = null;
    this.layout = null;
    this.initialized = false;
    
    // 初始化组件管理器
    this.initialize();
  }

  /**
   * 初始化组件管理器
   */
  async initialize() {
    try {
      // 加载组件配置
      await this.loadComponentsConfig();
      
      // 确定当前页面
      this.determineCurrentPage();
      
      // 初始化布局
      this.initializeLayout();
      
      this.initialized = true;
      console.log('组件管理器初始化完成');
    } catch (error) {
      console.error('组件管理器初始化失败:', error);
    }
  }

  /**
   * 加载组件配置文件
   */
  async loadComponentsConfig() {
    try {
      const response = await fetch('config/page-components.json');
      if (!response.ok) {
        throw new Error(`加载配置文件失败: ${response.status}`);
      }
      this.componentsConfig = await response.json();
      console.log('组件配置加载成功');
    } catch (error) {
      console.error('加载组件配置失败:', error);
      // 使用默认配置
      this.componentsConfig = this.getDefaultComponentsConfig();
    }
  }

  /**
   * 获取默认组件配置
   */
  getDefaultComponentsConfig() {
    return {
      components: {
        global: {
          header: { type: 'global', required: true },
          sidebar: { type: 'global', required: true },
          footer: { type: 'global', required: true }
        }
      },
      layouts: {
        default: { components: ['header', 'sidebar', 'content', 'footer'] }
      },
      defaultLayout: 'default'
    };
  }

  /**
   * 确定当前页面
   */
  determineCurrentPage() {
    const pathname = window.location.pathname;
    const filename = pathname.split('/').pop() || 'index.html';
    
    // 在配置中查找当前页面
    const pageSpecific = this.componentsConfig.components['page-specific'] || {};
    
    for (const [pageId, pageConfig] of Object.entries(pageSpecific)) {
      if (pageConfig.path === filename) {
        this.currentPage = { id: pageId, ...pageConfig };
        break;
      }
    }
    
    if (!this.currentPage) {
      // 默认页面配置
      this.currentPage = {
        id: 'default',
        type: 'page',
        path: filename,
        requiresAuth: false,
        children: []
      };
    }
  }

  /**
   * 初始化布局
   */
  initializeLayout() {
    const layoutId = this.currentPage.layout || this.componentsConfig.defaultLayout || 'default';
    this.layout = this.componentsConfig.layouts[layoutId];
    
    if (!this.layout) {
      // 使用默认布局
      this.layout = this.componentsConfig.layouts['default'] || {
        components: ['header', 'sidebar', 'content', 'footer']
      };
    }
  }

  /**
   * 渲染当前页面
   */
  async renderPage() {
    if (!this.initialized) {
      await this.initialize();
    }
    
    try {
      // 检查权限
      if (!this.checkPagePermission()) {
        this.renderPermissionDenied();
        return;
      }
      
      // 创建页面结构
      await this.createPageStructure();
      
      // 加载和渲染全局组件
      await this.loadGlobalComponents();
      
      // 加载和渲染页面特定组件
      await this.loadPageComponents();
      
      // 初始化组件交互
      this.initializeComponents();
      
      console.log('页面渲染完成');
    } catch (error) {
      console.error('页面渲染失败:', error);
    }
  }

  /**
   * 检查页面权限
   */
  checkPagePermission() {
    if (!this.currentPage.requiresAuth) {
      return true;
    }
    
    // 这里可以调用权限检查逻辑
    // 暂时返回true，实际项目中需要实现具体的权限检查
    return true;
  }

  /**
   * 渲染权限被拒绝的页面
   */
  renderPermissionDenied() {
    const contentElement = document.querySelector('.main-content') || document.body;
    contentElement.innerHTML = `
      <div class="permission-denied">
        <h2>没有访问权限</h2>
        <p>您没有权限访问此页面，请联系系统管理员。</p>
        <button onclick="window.history.back()">返回</button>
      </div>
    `;
  }

  /**
   * 创建页面结构
   */
  async createPageStructure() {
    // 创建基本布局容器
    const body = document.body;
    body.classList.add('component-managed');
    
    // 根据布局结构创建容器
    const structure = this.layout.structure || this.layout.components.join(',');
    const components = structure.split(',');
    
    components.forEach(component => {
      component = component.trim();
      if (component === 'content') {
        // 内容区域使用现有的main-content或创建新的
        let contentContainer = document.querySelector('.main-content');
        if (!contentContainer) {
          contentContainer = document.createElement('main');
          contentContainer.className = 'main-content';
          body.appendChild(contentContainer);
        }
      } else if (!document.querySelector(`.${component}-container`)) {
        const container = document.createElement('div');
        container.className = `${component}-container`;
        body.appendChild(container);
      }
    });
  }

  /**
   * 加载全局组件
   */
  async loadGlobalComponents() {
    const globalComponents = this.componentsConfig.components.global || {};
    
    for (const [componentId, componentConfig] of Object.entries(globalComponents)) {
      if (componentConfig.required || this.layout.components.includes(componentId)) {
        await this.loadComponent('global', componentId, componentConfig);
      }
    }
  }

  /**
   * 加载页面特定组件
   */
  async loadPageComponents() {
    if (!this.currentPage.children) return;
    
    for (const childComponentId of this.currentPage.children) {
      await this.loadReusableComponent(childComponentId);
    }
  }

  /**
   * 加载组件
   */
  async loadComponent(type, componentId, componentConfig) {
    try {
      // 如果组件已经加载，直接返回
      if (this.loadedComponents[componentId]) {
        return this.loadedComponents[componentId];
      }
      
      // 加载HTML
      let htmlContent = '';
      if (componentConfig.path) {
        const htmlResponse = await fetch(componentConfig.path);
        if (htmlResponse.ok) {
          htmlContent = await htmlResponse.text();
        }
      }
      
      // 加载CSS
      if (componentConfig.css) {
        await this.loadCSS(componentConfig.css, componentId);
      }
      
      // 加载JavaScript
      let componentScript = null;
      if (componentConfig.js) {
        componentScript = await this.loadJS(componentConfig.js);
      }
      
      // 创建组件实例
      const component = {
        id: componentId,
        type: type,
        config: componentConfig,
        html: htmlContent,
        script: componentScript
      };
      
      this.loadedComponents[componentId] = component;
      
      // 渲染组件
      await this.renderComponent(component);
      
      return component;
    } catch (error) {
      console.error(`加载组件 ${componentId} 失败:`, error);
      return null;
    }
  }

  /**
   * 加载可重用组件
   */
  async loadReusableComponent(componentId) {
    const reusableComponents = this.componentsConfig.components.reusable || {};
    const componentConfig = reusableComponents[componentId];
    
    if (componentConfig) {
      return await this.loadComponent('reusable', componentId, componentConfig);
    }
    
    return null;
  }

  /**
   * 渲染组件
   */
  async renderComponent(component) {
    try {
      // 确定渲染目标
      let targetElement;
      
      if (component.type === 'global') {
        // 全局组件渲染到对应的容器
        targetElement = document.querySelector(`.${component.id}-container`);
        if (!targetElement) {
          // 如果没有特定容器，根据组件类型选择合适的位置
          if (component.id === 'header') {
            targetElement = document.createElement('header');
            document.body.insertBefore(targetElement, document.body.firstChild);
          } else if (component.id === 'footer') {
            targetElement = document.createElement('footer');
            document.body.appendChild(targetElement);
          } else if (component.id === 'sidebar') {
            targetElement = document.createElement('aside');
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
              document.body.insertBefore(targetElement, mainContent);
            } else {
              document.body.appendChild(targetElement);
            }
          } else {
            targetElement = document.body;
          }
        }
      } else {
        // 页面组件和可重用组件渲染到内容区域
        targetElement = document.querySelector('.main-content');
      }
      
      // 创建组件容器
      const componentContainer = document.createElement('div');
      componentContainer.id = `${component.id}-component`;
      componentContainer.className = `component ${component.id}-component`;
      componentContainer.innerHTML = component.html;
      
      // 添加到目标元素
      if (component.type === 'reusable') {
        // 查找组件占位符或添加到内容区域末尾
        const placeholder = document.querySelector(`[data-component="${component.id}"]`);
        if (placeholder) {
          placeholder.parentNode.replaceChild(componentContainer, placeholder);
        } else if (targetElement) {
          targetElement.appendChild(componentContainer);
        }
      } else {
        // 全局组件和页面组件直接替换容器内容
        if (targetElement) {
          targetElement.innerHTML = '';
          targetElement.appendChild(componentContainer);
        }
      }
      
      // 保存组件实例
      this.componentInstances[component.id] = componentContainer;
      
      console.log(`组件 ${component.id} 渲染完成`);
    } catch (error) {
      console.error(`渲染组件 ${component.id} 失败:`, error);
    }
  }

  /**
   * 加载CSS
   */
  async loadCSS(cssPath, componentId) {
    try {
      // 检查是否已经加载
      if (document.querySelector(`link[data-component="${componentId}"]`)) {
        return;
      }
      
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = cssPath;
      link.dataset.component = componentId;
      document.head.appendChild(link);
      
      // 等待CSS加载完成
      await new Promise((resolve, reject) => {
        link.onload = resolve;
        link.onerror = () => reject(new Error(`加载CSS失败: ${cssPath}`));
      });
    } catch (error) {
      console.error(`加载CSS ${cssPath} 失败:`, error);
    }
  }

  /**
   * 加载JavaScript
   */
  async loadJS(jsPath) {
    try {
      // 检查是否已经加载
      if (document.querySelector(`script[src="${jsPath}"]`)) {
        return null;
      }
      
      const script = document.createElement('script');
      script.src = jsPath;
      document.head.appendChild(script);
      
      // 等待脚本加载完成
      await new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = () => reject(new Error(`加载JavaScript失败: ${jsPath}`));
      });
      
      return script;
    } catch (error) {
      console.error(`加载JavaScript ${jsPath} 失败:`, error);
      return null;
    }
  }

  /**
   * 初始化组件交互
   */
  initializeComponents() {
    // 初始化导航
    this.initializeNavigation();
    
    // 初始化主题
    this.initializeTheme();
    
    // 初始化组件间通信
    this.setupComponentCommunication();
  }

  /**
   * 初始化导航
   */
  initializeNavigation() {
    const navConfig = this.componentsConfig.navigation?.main || [];
    
    // 更新侧边栏导航
    const sidebarNav = document.querySelector('.sidebar-nav');
    if (sidebarNav && navConfig.length > 0) {
      const navMenu = document.createElement('ul');
      navMenu.className = 'nav-menu';
      
      navConfig.forEach(item => {
        if (this.checkPermission(item.permission)) {
          const li = document.createElement('li');
          li.className = 'nav-item' + (this.isActivePage(item.href) ? ' active' : '');
          
          li.innerHTML = `
            <a href="${item.href}" class="nav-link">
              <i class="fas fa-${item.icon}"></i>
              <span>${item.label}</span>
            </a>
          `;
          
          navMenu.appendChild(li);
        }
      });
      
      sidebarNav.innerHTML = '';
      sidebarNav.appendChild(navMenu);
    }
  }

  /**
   * 检查权限
   */
  checkPermission(permission) {
    // 实际项目中需要实现具体的权限检查逻辑
    // 暂时返回true，表示有权限
    return true;
  }

  /**
   * 检查是否是当前活跃页面
   */
  isActivePage(href) {
    const currentPath = window.location.pathname;
    const currentFilename = currentPath.split('/').pop() || 'index.html';
    return href === currentFilename;
  }

  /**
   * 初始化主题
   */
  initializeTheme() {
    // 从本地存储获取主题
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.dataset.theme = savedTheme;
    
    // 初始化主题切换按钮
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        const newTheme = savedTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', newTheme);
        document.body.dataset.theme = newTheme;
      });
    }
  }

  /**
   * 设置组件间通信
   */
  setupComponentCommunication() {
    // 创建自定义事件总线
    window.componentBus = {
      on: (event, callback) => document.addEventListener(event, callback),
      emit: (event, data) => document.dispatchEvent(new CustomEvent(event, { detail: data })),
      off: (event, callback) => document.removeEventListener(event, callback)
    };
  }

  /**
   * 获取组件实例
   */
  getComponent(componentId) {
    return this.componentInstances[componentId];
  }

  /**
   * 更新组件
   */
  async updateComponent(componentId, data) {
    const component = this.loadedComponents[componentId];
    if (!component) {
      console.error(`组件 ${componentId} 未加载`);
      return;
    }
    
    // 触发组件更新事件
    window.componentBus?.emit(`${componentId}:update`, data);
  }

  /**
   * 销毁组件
   */
  destroyComponent(componentId) {
    const componentInstance = this.componentInstances[componentId];
    if (componentInstance) {
      componentInstance.remove();
      delete this.componentInstances[componentId];
    }
    
    const component = this.loadedComponents[componentId];
    if (component && component.config.css) {
      const cssLink = document.querySelector(`link[data-component="${componentId}"]`);
      if (cssLink) {
        cssLink.remove();
      }
    }
    
    delete this.loadedComponents[componentId];
  }

  /**
   * 重新加载页面
   */
  async reloadPage() {
    // 销毁所有组件
    Object.keys(this.componentInstances).forEach(componentId => {
      this.destroyComponent(componentId);
    });
    
    // 重新渲染页面
    await this.renderPage();
  }

  /**
   * 导航到指定页面
   */
  navigateTo(url) {
    window.location.href = url;
  }

  /**
   * 显示模态框
   */
  async showModal(title, content, options = {}) {
    // 确保模态框组件已加载
    let modalComponent = this.loadedComponents['modal'];
    if (!modalComponent) {
      modalComponent = await this.loadReusableComponent('modal');
    }
    
    if (modalComponent) {
      // 触发模态框显示事件
      window.componentBus?.emit('modal:show', { title, content, options });
    }
  }

  /**
   * 显示通知
   */
  showNotification(message, type = 'info', duration = 3000) {
    // 触发通知显示事件
    window.componentBus?.emit('notification:show', { message, type, duration });
  }
}

// 导出组件管理器实例
const componentManager = new ComponentManager();

// 暴露到全局
if (typeof window !== 'undefined') {
  window.ComponentManager = ComponentManager;
  window.componentManager = componentManager;
}

// 导出为模块
export { ComponentManager, componentManager };
