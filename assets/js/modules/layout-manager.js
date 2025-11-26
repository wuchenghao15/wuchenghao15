// 布局管理器 - 负责页面布局的创建、管理和响应式调整
class LayoutManager {
  constructor(componentManager = null) {
    this.componentManager = componentManager || window.componentManager;
    this.currentLayout = null;
    this.layoutHistory = [];
    this.breakpoints = {
      xs: 0,
      sm: 576,
      md: 768,
      lg: 992,
      xl: 1200,
      xxl: 1400
    };
    this.currentBreakpoint = null;
    this.isMobile = false;
    this.sidebarCollapsed = false;
    this.isInitialized = false;
  }

  /**
   * 初始化布局管理器
   */
  initialize() {
    if (this.isInitialized) return;
    
    // 初始化响应式监听
    this.setupResponsiveListeners();
    
    // 初始化布局
    this.initializeCurrentLayout();
    
    // 初始化侧边栏
    this.initializeSidebar();
    
    // 初始化页脚
    this.initializeFooter();
    
    this.isInitialized = true;
    console.log('布局管理器初始化完成');
  }

  /**
   * 设置响应式监听
   */
  setupResponsiveListeners() {
    // 监听窗口大小变化
    window.addEventListener('resize', this.handleResize.bind(this));
    
    // 初始化当前断点
    this.updateBreakpoint();
    
    // 监听设备方向变化
    window.addEventListener('orientationchange', this.handleOrientationChange.bind(this));
  }

  /**
   * 处理窗口大小变化
   */
  handleResize() {
    const previousBreakpoint = this.currentBreakpoint;
    this.updateBreakpoint();
    
    // 断点变化时重新调整布局
    if (previousBreakpoint !== this.currentBreakpoint) {
      this.adjustLayoutForBreakpoint();
      
      // 触发断点变化事件
      window.componentBus?.emit('breakpoint:change', {
        previous: previousBreakpoint,
        current: this.currentBreakpoint
      });
    }
  }

  /**
   * 处理设备方向变化
   */
  handleOrientationChange() {
    // 延迟处理，确保尺寸变化完成
    setTimeout(() => {
      this.updateBreakpoint();
      this.adjustLayoutForBreakpoint();
    }, 100);
  }

  /**
   * 更新当前断点
   */
  updateBreakpoint() {
    const width = window.innerWidth;
    
    if (width < this.breakpoints.sm) {
      this.currentBreakpoint = 'xs';
      this.isMobile = true;
    } else if (width < this.breakpoints.md) {
      this.currentBreakpoint = 'sm';
      this.isMobile = true;
    } else if (width < this.breakpoints.lg) {
      this.currentBreakpoint = 'md';
      this.isMobile = false;
    } else if (width < this.breakpoints.xl) {
      this.currentBreakpoint = 'lg';
      this.isMobile = false;
    } else if (width < this.breakpoints.xxl) {
      this.currentBreakpoint = 'xl';
      this.isMobile = false;
    } else {
      this.currentBreakpoint = 'xxl';
      this.isMobile = false;
    }
    
    // 更新body上的断点类
    document.body.className = document.body.className.replace(/\bbreakpoint-\w+\b/g, '');
    document.body.classList.add(`breakpoint-${this.currentBreakpoint}`);
  }

  /**
   * 根据断点调整布局
   */
  adjustLayoutForBreakpoint() {
    if (this.isMobile) {
      // 移动设备布局调整
      this.collapseSidebar();
      this.adjustForMobile();
    } else {
      // 桌面设备布局调整
      this.expandSidebar();
      this.adjustForDesktop();
    }
    
    // 触发布局调整事件
    window.componentBus?.emit('layout:adjusted', {
      breakpoint: this.currentBreakpoint,
      isMobile: this.isMobile
    });
  }

  /**
   * 初始化当前布局
   */
  initializeCurrentLayout() {
    // 从组件管理器获取布局配置
    if (this.componentManager && this.componentManager.layout) {
      this.currentLayout = this.componentManager.layout;
      this.layoutHistory.push({...this.currentLayout});
    }
    
    // 创建基本布局容器
    this.createLayoutContainers();
  }

  /**
   * 创建布局容器
   */
  createLayoutContainers() {
    const body = document.body;
    
    // 确保有必要的容器
    const containers = ['header', 'sidebar', 'content', 'footer'];
    
    containers.forEach(container => {
      if (!document.querySelector(`.${container}-container`)) {
        const div = document.createElement('div');
        div.className = `${container}-container`;
        
        // 根据容器类型添加特定的ID
        if (container === 'content') {
          div.id = 'page-content';
          div.classList.add('main-content');
        }
        
        // 确定插入位置
        if (container === 'header') {
          body.insertBefore(div, body.firstChild);
        } else if (container === 'footer') {
          body.appendChild(div);
        } else if (container === 'sidebar') {
          // 侧边栏应该在头部之后，内容之前
          const header = document.querySelector('.header-container');
          const content = document.querySelector('.content-container');
          
          if (content) {
            body.insertBefore(div, content);
          } else if (header) {
            header.after(div);
          } else {
            body.appendChild(div);
          }
        } else { // content
          // 内容区域应该在侧边栏之后
          const sidebar = document.querySelector('.sidebar-container');
          const footer = document.querySelector('.footer-container');
          
          if (footer) {
            body.insertBefore(div, footer);
          } else if (sidebar) {
            sidebar.after(div);
          } else {
            body.appendChild(div);
          }
        }
      }
    });
  }

  /**
   * 初始化侧边栏
   */
  initializeSidebar() {
    const sidebar = document.querySelector('.sidebar-container');
    if (!sidebar) return;
    
    // 添加侧边栏切换按钮
    const toggleButton = document.createElement('button');
    toggleButton.id = 'sidebar-toggle';
    toggleButton.className = 'sidebar-toggle';
    toggleButton.innerHTML = '<i class="fas fa-bars"></i>';
    toggleButton.addEventListener('click', this.toggleSidebar.bind(this));
    
    // 将按钮添加到头部
    const header = document.querySelector('.header-container');
    if (header) {
      header.appendChild(toggleButton);
    }
    
    // 初始化侧边栏状态
    if (this.isMobile) {
      this.collapseSidebar();
    } else {
      this.expandSidebar();
    }
  }

  /**
   * 初始化页脚
   */
  initializeFooter() {
    const footer = document.querySelector('.footer-container');
    if (!footer) return;
    
    // 设置页脚内容
    footer.innerHTML = `
      <div class="footer-content">
        <div class="footer-left">
          <p>&copy; ${new Date().getFullYear()} MTSCOS AI 系统. 保留所有权利.</p>
        </div>
        <div class="footer-right">
          <span class="version">版本: ${this.getAppVersion()}</span>
        </div>
      </div>
    `;
  }

  /**
   * 获取应用版本
   */
  getAppVersion() {
    // 从组件管理器或其他地方获取版本信息
    return '1.0.0';
  }

  /**
   * 切换侧边栏显示状态
   */
  toggleSidebar() {
    if (this.sidebarCollapsed) {
      this.expandSidebar();
    } else {
      this.collapseSidebar();
    }
  }

  /**
   * 展开侧边栏
   */
  expandSidebar() {
    const sidebar = document.querySelector('.sidebar-container');
    const content = document.querySelector('.content-container');
    
    if (sidebar) {
      sidebar.classList.remove('collapsed');
      sidebar.classList.add('expanded');
    }
    
    if (content) {
      content.classList.remove('sidebar-collapsed');
      content.classList.add('sidebar-expanded');
    }
    
    this.sidebarCollapsed = false;
    
    // 保存状态到本地存储
    localStorage.setItem('sidebarCollapsed', 'false');
    
    // 触发侧边栏状态变化事件
    window.componentBus?.emit('sidebar:stateChanged', { collapsed: false });
  }

  /**
   * 折叠侧边栏
   */
  collapseSidebar() {
    const sidebar = document.querySelector('.sidebar-container');
    const content = document.querySelector('.content-container');
    
    if (sidebar) {
      sidebar.classList.remove('expanded');
      sidebar.classList.add('collapsed');
    }
    
    if (content) {
      content.classList.remove('sidebar-expanded');
      content.classList.add('sidebar-collapsed');
    }
    
    this.sidebarCollapsed = true;
    
    // 保存状态到本地存储
    localStorage.setItem('sidebarCollapsed', 'true');
    
    // 触发侧边栏状态变化事件
    window.componentBus?.emit('sidebar:stateChanged', { collapsed: true });
  }

  /**
   * 为移动设备调整布局
   */
  adjustForMobile() {
    document.body.classList.add('mobile-layout');
    document.body.classList.remove('desktop-layout');
    
    // 移动设备上隐藏一些不必要的元素
    const desktopOnlyElements = document.querySelectorAll('.desktop-only');
    desktopOnlyElements.forEach(el => el.classList.add('hidden'));
    
    // 显示移动设备特定元素
    const mobileOnlyElements = document.querySelectorAll('.mobile-only');
    mobileOnlyElements.forEach(el => el.classList.remove('hidden'));
    
    // 调整导航菜单
    this.adjustMobileNavigation();
  }

  /**
   * 为桌面设备调整布局
   */
  adjustForDesktop() {
    document.body.classList.add('desktop-layout');
    document.body.classList.remove('mobile-layout');
    
    // 显示桌面设备特定元素
    const desktopOnlyElements = document.querySelectorAll('.desktop-only');
    desktopOnlyElements.forEach(el => el.classList.remove('hidden'));
    
    // 隐藏移动设备特定元素
    const mobileOnlyElements = document.querySelectorAll('.mobile-only');
    mobileOnlyElements.forEach(el => el.classList.add('hidden'));
  }

  /**
   * 调整移动设备导航
   */
  adjustMobileNavigation() {
    // 创建汉堡菜单按钮（如果不存在）
    if (!document.querySelector('.mobile-menu-button')) {
      const menuButton = document.createElement('button');
      menuButton.className = 'mobile-menu-button mobile-only';
      menuButton.innerHTML = '<i class="fas fa-bars"></i>';
      menuButton.addEventListener('click', this.toggleMobileMenu.bind(this));
      
      const header = document.querySelector('.header-container');
      if (header) {
        header.appendChild(menuButton);
      }
    }
  }

  /**
   * 切换移动菜单
   */
  toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar-container');
    
    if (sidebar) {
      sidebar.classList.toggle('mobile-open');
      
      // 切换背景遮罩
      this.toggleMobileOverlay();
    }
  }

  /**
   * 切换移动设备背景遮罩
   */
  toggleMobileOverlay() {
    let overlay = document.querySelector('.mobile-overlay');
    
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'mobile-overlay';
      overlay.addEventListener('click', () => {
        const sidebar = document.querySelector('.sidebar-container');
        if (sidebar) {
          sidebar.classList.remove('mobile-open');
          overlay.remove();
        }
      });
      document.body.appendChild(overlay);
    } else {
      overlay.remove();
    }
  }

  /**
   * 设置布局
   */
  setLayout(layoutId) {
    // 从组件配置中获取布局
    const layoutConfig = this.componentManager?.componentsConfig?.layouts[layoutId];
    
    if (layoutConfig) {
      // 保存当前布局到历史记录
      if (this.currentLayout) {
        this.layoutHistory.push({...this.currentLayout});
      }
      
      // 更新当前布局
      this.currentLayout = layoutConfig;
      
      // 应用新布局
      this.applyLayout(this.currentLayout);
      
      // 触发布局变化事件
      window.componentBus?.emit('layout:changed', { layoutId, layout: layoutConfig });
    }
  }

  /**
   * 应用布局
   */
  applyLayout(layout) {
    const containers = ['header', 'sidebar', 'content', 'footer'];
    
    // 显示或隐藏容器
    containers.forEach(container => {
      const element = document.querySelector(`.${container}-container`);
      if (element) {
        if (layout.components.includes(container)) {
          element.classList.remove('hidden');
        } else {
          element.classList.add('hidden');
        }
      }
    });
    
    // 根据布局结构调整顺序
    if (layout.structure) {
      this.reorderContainers(layout.structure);
    }
  }

  /**
   * 重新排序容器
   */
  reorderContainers(structure) {
    const components = structure.split(',');
    const body = document.body;
    let lastElement = null;
    
    components.forEach(component => {
      component = component.trim();
      const container = document.querySelector(`.${component}-container`);
      
      if (container) {
        if (lastElement) {
          lastElement.after(container);
        } else {
          body.insertBefore(container, body.firstChild);
        }
        lastElement = container;
      }
    });
  }

  /**
   * 恢复上一个布局
   */
  restorePreviousLayout() {
    if (this.layoutHistory.length > 0) {
      const previousLayout = this.layoutHistory.pop();
      this.currentLayout = previousLayout;
      this.applyLayout(previousLayout);
      
      return true;
    }
    
    return false;
  }

  /**
   * 获取当前布局信息
   */
  getCurrentLayoutInfo() {
    return {
      layout: this.currentLayout,
      breakpoint: this.currentBreakpoint,
      isMobile: this.isMobile,
      sidebarCollapsed: this.sidebarCollapsed
    };
  }

  /**
   * 锁定布局（禁止响应式变化）
   */
  lockLayout() {
    this.layoutLocked = true;
    window.removeEventListener('resize', this.handleResize.bind(this));
  }

  /**
   * 解锁布局（恢复响应式变化）
   */
  unlockLayout() {
    this.layoutLocked = false;
    window.addEventListener('resize', this.handleResize.bind(this));
    this.handleResize(); // 立即调整一次
  }

  /**
   * 销毁布局管理器
   */
  destroy() {
    window.removeEventListener('resize', this.handleResize.bind(this));
    window.removeEventListener('orientationchange', this.handleOrientationChange.bind(this));
    
    // 清理事件监听器
    const toggleButton = document.getElementById('sidebar-toggle');
    if (toggleButton) {
      toggleButton.removeEventListener('click', this.toggleSidebar.bind(this));
    }
    
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    if (mobileMenuButton) {
      mobileMenuButton.removeEventListener('click', this.toggleMobileMenu.bind(this));
    }
    
    this.isInitialized = false;
  }
}

// 导出布局管理器实例
const layoutManager = new LayoutManager();

// 暴露到全局
if (typeof window !== 'undefined') {
  window.LayoutManager = LayoutManager;
  window.layoutManager = layoutManager;
}

// 导出为模块
export { LayoutManager, layoutManager };
