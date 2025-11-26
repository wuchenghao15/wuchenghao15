// 导航管理器 - 处理页面导航、菜单渲染和导航状态
class NavigationManager {
  constructor(options = {}) {
    // 路由系统引用
    this.router = options.router || null;
    
    // 导航配置
    this.config = {
      menuContainer: options.menuContainer || '#sidebar-menu',
      breadcrumbContainer: options.breadcrumbContainer || '#breadcrumb',
      headerContainer: options.headerContainer || '#app-header',
      sidebarContainer: options.sidebarContainer || '#sidebar',
      footerContainer: options.footerContainer || '#app-footer',
      transitionDuration: options.transitionDuration || 300,
      ...options.config
    };
    
    // 导航状态
    this.state = {
      currentRoute: null,
      previousRoute: null,
      sidebarOpen: false,
      mobileMenuOpen: false,
      breadcrumb: [],
      activeMenuItems: [],
      isNavigating: false,
      scrollPosition: { x: 0, y: 0 },
      savedPositions: new Map(),
      deviceType: this.detectDeviceType(),
      isMobile: false,
      lastInteraction: Date.now()
    };
    
    // 菜单配置
    this.menuConfig = options.menuConfig || {};
    
    // 事件监听器
    this.listeners = new Map();
    
    // 动画帧ID
    this.animationId = null;
    
    // 初始化状态
    this.isInitialized = false;
    
    // 导航历史
    this.navigationHistory = [];
    
    // 最大历史记录长度
    this.maxHistoryLength = options.maxHistoryLength || 50;
  }

  /**
   * 初始化导航管理器
   */
  async initialize() {
    if (this.isInitialized) {
      console.warn('导航管理器已经初始化');
      return true;
    }
    
    try {
      console.log('初始化导航管理器...');
      
      // 验证路由系统
      if (!this.router || typeof this.router.getCurrentRoute !== 'function') {
        throw new Error('无效的路由系统引用');
      }
      
      // 设置设备检测
      this.setupDeviceDetection();
      
      // 设置事件监听
      this.setupEventListeners();
      
      // 设置路由监听
      this.setupRouterListeners();
      
      // 初始化导航状态
      this.updateNavigationState();
      
      // 渲染初始菜单
      this.renderMenu();
      
      // 渲染初始面包屑
      this.renderBreadcrumb();
      
      // 初始化布局
      this.initializeLayout();
      
      this.isInitialized = true;
      console.log('导航管理器初始化完成');
      
      return true;
    } catch (error) {
      console.error('初始化导航管理器失败:', error);
      this.emit('error', { error, type: 'initialization' });
      return false;
    }
  }

  /**
   * 设置设备检测
   */
  setupDeviceDetection() {
    // 初始检测
    this.updateDeviceType();
    
    // 监听窗口大小变化
    window.addEventListener('resize', this.debounce(() => {
      this.updateDeviceType();
      this.handleResponsiveLayout();
      this.emit('resize', { deviceType: this.state.deviceType, isMobile: this.state.isMobile });
    }, 200));
  }

  /**
   * 更新设备类型
   */
  updateDeviceType() {
    const deviceType = this.detectDeviceType();
    const isMobile = deviceType === 'mobile' || deviceType === 'tablet';
    
    this.state.deviceType = deviceType;
    this.state.isMobile = isMobile;
    
    // 移动设备自动关闭侧边栏
    if (isMobile && this.state.sidebarOpen) {
      this.closeSidebar();
    }
  }

  /**
   * 检测设备类型
   */
  detectDeviceType() {
    const width = window.innerWidth;
    
    if (width < 768) {
      return 'mobile';
    } else if (width < 1024) {
      return 'tablet';
    } else {
      return 'desktop';
    }
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 点击事件监听
    document.addEventListener('click', (event) => this.handleClick(event));
    
    // 键盘事件监听
    document.addEventListener('keydown', (event) => this.handleKeydown(event));
    
    // 滚动事件监听
    window.addEventListener('scroll', this.throttle(() => this.handleScroll(), 100));
    
    // 触摸事件监听（移动设备）
    if (this.state.isMobile) {
      this.setupTouchEventListeners();
    }
  }

  /**
   * 设置触摸事件监听
   */
  setupTouchEventListeners() {
    // 侧边栏滑动
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', (event) => {
      touchStartX = event.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', (event) => {
      touchEndX = event.changedTouches[0].screenX;
      this.handleSwipe(touchStartX, touchEndX);
    }, false);
  }

  /**
   * 处理滑动事件
   */
  handleSwipe(startX, endX) {
    const threshold = 50;
    const diff = startX - endX;
    
    // 从左向右滑动
    if (diff < -threshold && !this.state.sidebarOpen) {
      this.openSidebar();
    }
    // 从右向左滑动
    else if (diff > threshold && this.state.sidebarOpen) {
      this.closeSidebar();
    }
  }

  /**
   * 设置路由监听
   */
  setupRouterListeners() {
    // 监听路由变化
    this.router.on('routeChanged', ({ from, to }) => {
      this.handleRouteChange(from, to);
    });
    
    // 监听路由错误
    this.router.on('error', (error) => {
      this.handleRouteError(error);
    });
    
    // 监听路由未找到
    this.router.on('notFound', ({ path }) => {
      this.handleRouteNotFound(path);
    });
  }

  /**
   * 处理路由变化
   */
  async handleRouteChange(from, to) {
    try {
      // 保存滚动位置
      this.saveScrollPosition(from?.path);
      
      // 更新导航状态
      this.state.previousRoute = from;
      this.state.currentRoute = to;
      
      // 记录导航历史
      this.recordNavigationHistory(to);
      
      // 更新活动菜单项
      this.updateActiveMenuItems();
      
      // 生成面包屑
      this.generateBreadcrumb();
      
      // 应用页面过渡
      await this.applyPageTransition();
      
      // 恢复滚动位置
      this.restoreScrollPosition(to.path);
      
      // 更新页面标题
      this.updatePageTitle(to);
      
      // 更新布局状态
      this.updateLayoutState(to);
      
      // 触发导航完成事件
      this.emit('navigationCompleted', { from, to });
    } catch (error) {
      console.error('处理路由变化失败:', error);
      this.emit('error', { error, type: 'route_change' });
    }
  }

  /**
   * 处理路由错误
   */
  handleRouteError(error) {
    console.error('路由错误:', error);
    this.emit('error', { error, type: 'route_error' });
  }

  /**
   * 处理路由未找到
   */
  handleRouteNotFound(path) {
    console.warn(`未找到路由: ${path}`);
    this.emit('routeNotFound', { path });
  }

  /**
   * 记录导航历史
   */
  recordNavigationHistory(route) {
    // 避免重复记录
    const lastRecord = this.navigationHistory[this.navigationHistory.length - 1];
    if (lastRecord && lastRecord.path === route.path) {
      return;
    }
    
    // 添加到历史记录
    this.navigationHistory.push({
      path: route.path,
      name: route.name,
      title: route.meta?.title || '',
      timestamp: Date.now()
    });
    
    // 限制历史记录长度
    if (this.navigationHistory.length > this.maxHistoryLength) {
      this.navigationHistory.shift();
    }
  }

  /**
   * 更新导航状态
   */
  updateNavigationState() {
    const currentRoute = this.router.getCurrentRoute();
    if (currentRoute) {
      this.state.currentRoute = currentRoute;
      this.updateActiveMenuItems();
      this.generateBreadcrumb();
    }
  }

  /**
   * 渲染菜单
   */
  renderMenu() {
    const menuContainer = document.querySelector(this.config.menuContainer);
    if (!menuContainer) {
      console.warn(`菜单容器不存在: ${this.config.menuContainer}`);
      return false;
    }
    
    try {
      // 获取路由配置
      const routes = this.router.getRoutes();
      
      // 生成菜单项
      const menuItems = this.generateMenuItems(routes);
      
      // 渲染菜单 HTML
      menuContainer.innerHTML = this.createMenuHTML(menuItems);
      
      // 绑定菜单项事件
      this.bindMenuEvents();
      
      // 更新活动菜单项样式
      this.updateActiveMenuStyles();
      
      console.log('菜单渲染完成');
      
      return true;
    } catch (error) {
      console.error('渲染菜单失败:', error);
      this.emit('error', { error, type: 'menu_render' });
      return false;
    }
  }

  /**
   * 生成菜单项
   */
  generateMenuItems(routes) {
    const menuItems = [];
    
    routes.forEach(route => {
      // 跳过不显示在菜单中的路由
      if (route.meta && route.meta.showInMenu === false) {
        return;
      }
      
      // 生成菜单项
      const menuItem = this.createMenuItem(route);
      
      // 处理子菜单
      if (route.children && route.children.length > 0) {
        const visibleChildren = route.children.filter(
          child => !child.meta || child.meta.showInMenu !== false
        );
        
        if (visibleChildren.length > 0) {
          menuItem.children = visibleChildren.map(child => this.createMenuItem(child));
        }
      }
      
      menuItems.push(menuItem);
    });
    
    // 按照顺序排序
    return this.sortMenuItems(menuItems);
  }

  /**
   * 创建菜单项
   */
  createMenuItem(route) {
    return {
      id: route.name || `route-${route.path}`,
      name: route.name || '',
      path: route.path,
      title: route.meta?.title || '',
      description: route.meta?.description || '',
      icon: route.meta?.icon || 'default',
      badge: route.meta?.badge || null,
      external: route.meta?.external || false,
      target: route.meta?.target || '_self',
      requiresAuth: route.meta?.requiresAuth || false,
      order: route.meta?.order || 0,
      children: []
    };
  }

  /**
   * 排序菜单项
   */
  sortMenuItems(menuItems) {
    return menuItems.sort((a, b) => a.order - b.order);
  }

  /**
   * 创建菜单HTML
   */
  createMenuHTML(menuItems) {
    let html = '<ul class="menu-items">';
    
    menuItems.forEach(item => {
      html += this.createMenuItemHTML(item);
    });
    
    html += '</ul>';
    
    return html;
  }

  /**
   * 创建菜单项HTML
   */
  createMenuItemHTML(item) {
    const isActive = this.state.activeMenuItems.includes(item.id);
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = hasChildren && this.isMenuItemExpanded(item.id);
    
    let html = `<li class="menu-item ${isActive ? 'active' : ''} ${hasChildren ? 'has-children' : ''} ${isExpanded ? 'expanded' : ''}" data-menu-id="${item.id}" data-path="${item.path}">`;
    
    // 菜单项内容
    html += `<a href="${item.path}" class="menu-link" target="${item.target}">`;
    
    // 图标
    html += `<span class="menu-icon ${item.icon ? `icon-${item.icon}` : 'icon-default'}"></span>`;
    
    // 文本
    html += `<span class="menu-text">${item.title}</span>`;
    
    // 徽章
    if (item.badge) {
      html += `<span class="menu-badge ${item.badge.type || 'default'}">${item.badge.text || ''}</span>`;
    }
    
    // 子菜单箭头
    if (hasChildren) {
      html += `<span class="menu-arrow ${isExpanded ? 'expanded' : ''}"></span>`;
    }
    
    html += '</a>';
    
    // 子菜单
    if (hasChildren) {
      html += '<ul class="sub-menu">';
      
      item.children.forEach(child => {
        html += this.createMenuItemHTML(child);
      });
      
      html += '</ul>';
    }
    
    html += '</li>';
    
    return html;
  }

  /**
   * 检查菜单项是否展开
   */
  isMenuItemExpanded(menuId) {
    const activeItem = this.state.activeMenuItems.find(id => id === menuId || id.startsWith(`${menuId}-`));
    return !!activeItem;
  }

  /**
   * 绑定菜单事件
   */
  bindMenuEvents() {
    // 查找所有菜单项
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
      const link = item.querySelector('.menu-link');
      const hasChildren = item.classList.contains('has-children');
      
      // 点击事件
      link.addEventListener('click', (event) => {
        // 如果有子菜单，阻止默认行为并切换展开状态
        if (hasChildren) {
          event.preventDefault();
          this.toggleSubMenu(item);
        } else {
          // 记录交互时间
          this.state.lastInteraction = Date.now();
        }
      });
      
      // 悬停事件
      link.addEventListener('mouseenter', () => {
        if (this.state.deviceType === 'desktop') {
          // 桌面设备自动展开子菜单
          if (hasChildren && !item.classList.contains('expanded')) {
            this.expandSubMenu(item);
          }
        }
      });
      
      // 离开事件
      link.addEventListener('mouseleave', () => {
        // 可以添加延迟关闭逻辑
      });
    });
  }

  /**
   * 切换子菜单
   */
  toggleSubMenu(menuItem) {
    const isExpanded = menuItem.classList.contains('expanded');
    
    if (isExpanded) {
      this.collapseSubMenu(menuItem);
    } else {
      this.expandSubMenu(menuItem);
    }
  }

  /**
   * 展开子菜单
   */
  expandSubMenu(menuItem) {
    // 先关闭其他同级子菜单
    const parent = menuItem.parentElement;
    if (parent) {
      parent.querySelectorAll('.menu-item.expanded').forEach(item => {
        if (item !== menuItem) {
          this.collapseSubMenu(item);
        }
      });
    }
    
    // 展开当前子菜单
    menuItem.classList.add('expanded');
    
    const subMenu = menuItem.querySelector('.sub-menu');
    if (subMenu) {
      subMenu.style.maxHeight = subMenu.scrollHeight + 'px';
    }
  }

  /**
   * 折叠子菜单
   */
  collapseSubMenu(menuItem) {
    menuItem.classList.remove('expanded');
    
    const subMenu = menuItem.querySelector('.sub-menu');
    if (subMenu) {
      subMenu.style.maxHeight = '0';
    }
  }

  /**
   * 更新活动菜单项
   */
  updateActiveMenuItems() {
    const activeItems = [];
    const currentRoute = this.state.currentRoute;
    
    if (currentRoute) {
      // 添加当前路由
      activeItems.push(currentRoute.name || `route-${currentRoute.path}`);
      
      // 查找父路由
      const parentRoutes = this.findParentRoutes(currentRoute.path);
      parentRoutes.forEach(route => {
        activeItems.push(route.name || `route-${route.path}`);
      });
    }
    
    this.state.activeMenuItems = activeItems;
  }

  /**
   * 查找父路由
   */
  findParentRoutes(currentPath) {
    const parentRoutes = [];
    const routes = this.router.getRoutes();
    
    // 分割路径段
    const pathSegments = currentPath.split('/').filter(Boolean);
    
    // 构建父路径
    for (let i = 1; i < pathSegments.length; i++) {
      const parentPath = '/' + pathSegments.slice(0, i).join('/');
      const parentRoute = routes.find(route => route.path === parentPath);
      
      if (parentRoute) {
        parentRoutes.push(parentRoute);
      }
    }
    
    return parentRoutes.reverse();
  }

  /**
   * 更新活动菜单项样式
   */
  updateActiveMenuStyles() {
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
      const menuId = item.getAttribute('data-menu-id');
      
      if (this.state.activeMenuItems.includes(menuId)) {
        item.classList.add('active');
        
        // 展开父菜单
        let parent = item.parentElement;
        while (parent && parent.classList.contains('sub-menu')) {
          const menuItem = parent.closest('.menu-item');
          if (menuItem) {
            this.expandSubMenu(menuItem);
          }
          parent = parent.parentElement.parentElement;
        }
      } else {
        item.classList.remove('active');
      }
    });
  }

  /**
   * 生成面包屑
   */
  generateBreadcrumb() {
    const breadcrumb = [];
    const currentRoute = this.state.currentRoute;
    
    if (currentRoute) {
      // 添加首页
      breadcrumb.push({
        id: 'home',
        name: 'home',
        path: '/',
        title: '首页',
        icon: 'home'
      });
      
      // 查找父路由
      const parentRoutes = this.findParentRoutes(currentRoute.path);
      
      // 添加父路由
      parentRoutes.forEach(route => {
        breadcrumb.push({
          id: route.name || `route-${route.path}`,
          name: route.name,
          path: route.path,
          title: route.meta?.title || route.name || route.path,
          icon: route.meta?.icon
        });
      });
      
      // 添加当前路由
      breadcrumb.push({
        id: currentRoute.name || `route-${currentRoute.path}`,
        name: currentRoute.name,
        path: currentRoute.path,
        title: currentRoute.meta?.title || currentRoute.name || currentRoute.path,
        icon: currentRoute.meta?.icon,
        isActive: true
      });
    }
    
    this.state.breadcrumb = breadcrumb;
  }

  /**
   * 渲染面包屑
   */
  renderBreadcrumb() {
    const container = document.querySelector(this.config.breadcrumbContainer);
    if (!container) {
      console.warn(`面包屑容器不存在: ${this.config.breadcrumbContainer}`);
      return false;
    }
    
    try {
      const breadcrumb = this.state.breadcrumb;
      
      if (breadcrumb.length === 0) {
        container.innerHTML = '';
        return;
      }
      
      let html = '<ol class="breadcrumb">';
      
      breadcrumb.forEach((item, index) => {
        const isLast = index === breadcrumb.length - 1;
        
        if (isLast || item.isActive) {
          // 最后一项或活动项
          html += `<li class="breadcrumb-item active">`;
          
          if (item.icon) {
            html += `<span class="breadcrumb-icon ${item.icon ? `icon-${item.icon}` : ''}"></span>`;
          }
          
          html += `<span class="breadcrumb-text">${item.title}</span>`;
          html += `</li>`;
        } else {
          // 普通项
          html += `<li class="breadcrumb-item">`;
          html += `<a href="${item.path}" class="breadcrumb-link">`;
          
          if (item.icon) {
            html += `<span class="breadcrumb-icon ${item.icon ? `icon-${item.icon}` : ''}"></span>`;
          }
          
          html += `<span class="breadcrumb-text">${item.title}</span>`;
          html += `</a>`;
          html += `</li>`;
          html += `<li class="breadcrumb-separator">/</li>`;
        }
      });
      
      html += '</ol>';
      
      container.innerHTML = html;
      
      console.log('面包屑渲染完成');
      
      return true;
    } catch (error) {
      console.error('渲染面包屑失败:', error);
      this.emit('error', { error, type: 'breadcrumb_render' });
      return false;
    }
  }

  /**
   * 应用页面过渡
   */
  async applyPageTransition() {
    try {
      this.state.isNavigating = true;
      
      // 获取过渡配置
      const transitionConfig = this.getTransitionConfig();
      
      // 添加过渡类
      const appContainer = document.querySelector('#app') || document.body;
      appContainer.classList.add('transitioning');
      appContainer.classList.add(transitionConfig.leaveActiveClass);
      
      // 等待过渡完成
      await new Promise(resolve => {
        setTimeout(() => {
          // 移除离开过渡类
          appContainer.classList.remove(transitionConfig.leaveActiveClass);
          
          // 添加进入过渡类
          appContainer.classList.add(transitionConfig.enterActiveClass);
          
          setTimeout(() => {
            // 移除所有过渡类
            appContainer.classList.remove('transitioning');
            appContainer.classList.remove(transitionConfig.enterActiveClass);
            
            this.state.isNavigating = false;
            resolve();
          }, transitionConfig.duration);
        }, transitionConfig.duration);
      });
      
      return true;
    } catch (error) {
      console.error('应用页面过渡失败:', error);
      this.state.isNavigating = false;
      return false;
    }
  }

  /**
   * 获取过渡配置
   */
  getTransitionConfig() {
    // 从路由元数据获取配置
    const currentRoute = this.state.currentRoute;
    
    if (currentRoute && currentRoute.meta && currentRoute.meta.transition) {
      return { ...this.getDefaultTransitionConfig(), ...currentRoute.meta.transition };
    }
    
    return this.getDefaultTransitionConfig();
  }

  /**
   * 获取默认过渡配置
   */
  getDefaultTransitionConfig() {
    return {
      enterActiveClass: 'fade-in',
      leaveActiveClass: 'fade-out',
      duration: this.config.transitionDuration || 300
    };
  }

  /**
   * 保存滚动位置
   */
  saveScrollPosition(path) {
    if (!path) return;
    
    this.state.scrollPosition = {
      x: window.scrollX,
      y: window.scrollY
    };
    
    this.state.savedPositions.set(path, this.state.scrollPosition);
  }

  /**
   * 恢复滚动位置
   */
  restoreScrollPosition(path) {
    if (!path) return;
    
    const savedPosition = this.state.savedPositions.get(path);
    
    if (savedPosition) {
      window.scrollTo(savedPosition.x, savedPosition.y);
    } else {
      // 默认滚动到顶部
      window.scrollTo(0, 0);
    }
  }

  /**
   * 更新页面标题
   */
  updatePageTitle(route) {
    if (!route || !route.meta || !route.meta.title) return;
    
    const baseTitle = this.config.baseTitle || '智能优化规划系统';
    const pageTitle = route.meta.title;
    
    document.title = `${pageTitle} - ${baseTitle}`;
  }

  /**
   * 初始化布局
   */
  initializeLayout() {
    // 设置初始布局类
    this.updateLayoutClasses();
    
    // 初始化响应式布局
    this.handleResponsiveLayout();
  }

  /**
   * 更新布局状态
   */
  updateLayoutState(route) {
    // 根据路由元数据更新布局
    if (route && route.meta) {
      // 处理侧边栏显示
      if (route.meta.hideSidebar) {
        this.hideSidebar();
      } else if (!this.state.isMobile) {
        this.showSidebar();
      }
      
      // 处理头部显示
      if (route.meta.hideHeader) {
        this.hideHeader();
      } else {
        this.showHeader();
      }
      
      // 处理底部显示
      if (route.meta.hideFooter) {
        this.hideFooter();
      } else {
        this.showFooter();
      }
    }
    
    // 更新布局类
    this.updateLayoutClasses();
  }

  /**
   * 更新布局类
   */
  updateLayoutClasses() {
    const body = document.body;
    
    // 更新设备类型类
    body.classList.remove('device-mobile', 'device-tablet', 'device-desktop');
    body.classList.add(`device-${this.state.deviceType}`);
    
    // 更新侧边栏状态类
    body.classList.toggle('sidebar-open', this.state.sidebarOpen);
    body.classList.toggle('sidebar-closed', !this.state.sidebarOpen);
    
    // 更新移动端菜单状态类
    body.classList.toggle('mobile-menu-open', this.state.mobileMenuOpen);
    
    // 更新导航状态类
    body.classList.toggle('is-navigating', this.state.isNavigating);
  }

  /**
   * 处理响应式布局
   */
  handleResponsiveLayout() {
    // 根据设备类型调整布局
    if (this.state.isMobile) {
      this.closeSidebar();
      this.adjustForMobile();
    } else {
      this.adjustForDesktop();
    }
  }

  /**
   * 调整移动端布局
   */
  adjustForMobile() {
    // 移动设备特定逻辑
    const sidebar = document.querySelector(this.config.sidebarContainer);
    const header = document.querySelector(this.config.headerContainer);
    
    if (sidebar) {
      sidebar.style.transform = this.state.sidebarOpen ? 'translateX(0)' : 'translateX(-100%)';
    }
    
    if (header) {
      header.classList.add('mobile-header');
    }
  }

  /**
   * 调整桌面端布局
   */
  adjustForDesktop() {
    // 桌面设备特定逻辑
    const sidebar = document.querySelector(this.config.sidebarContainer);
    const header = document.querySelector(this.config.headerContainer);
    
    if (sidebar) {
      sidebar.style.transform = '';
      sidebar.style.width = this.state.sidebarOpen ? '250px' : '0';
    }
    
    if (header) {
      header.classList.remove('mobile-header');
    }
  }

  /**
   * 切换侧边栏
   */
  toggleSidebar() {
    if (this.state.sidebarOpen) {
      this.closeSidebar();
    } else {
      this.openSidebar();
    }
  }

  /**
   * 打开侧边栏
   */
  openSidebar() {
    this.state.sidebarOpen = true;
    this.updateLayoutClasses();
    this.handleResponsiveLayout();
    this.emit('sidebarOpened');
  }

  /**
   * 关闭侧边栏
   */
  closeSidebar() {
    this.state.sidebarOpen = false;
    this.updateLayoutClasses();
    this.handleResponsiveLayout();
    this.emit('sidebarClosed');
  }

  /**
   * 显示侧边栏
   */
  showSidebar() {
    const sidebar = document.querySelector(this.config.sidebarContainer);
    if (sidebar) {
      sidebar.classList.remove('hidden');
    }
  }

  /**
   * 隐藏侧边栏
   */
  hideSidebar() {
    const sidebar = document.querySelector(this.config.sidebarContainer);
    if (sidebar) {
      sidebar.classList.add('hidden');
    }
  }

  /**
   * 显示头部
   */
  showHeader() {
    const header = document.querySelector(this.config.headerContainer);
    if (header) {
      header.classList.remove('hidden');
    }
  }

  /**
   * 隐藏头部
   */
  hideHeader() {
    const header = document.querySelector(this.config.headerContainer);
    if (header) {
      header.classList.add('hidden');
    }
  }

  /**
   * 显示底部
   */
  showFooter() {
    const footer = document.querySelector(this.config.footerContainer);
    if (footer) {
      footer.classList.remove('hidden');
    }
  }

  /**
   * 隐藏底部
   */
  hideFooter() {
    const footer = document.querySelector(this.config.footerContainer);
    if (footer) {
      footer.classList.add('hidden');
    }
  }

  /**
   * 处理点击事件
   */
  handleClick(event) {
    // 记录交互时间
    this.state.lastInteraction = Date.now();
    
    // 处理遮罩点击
    if (event.target.classList.contains('sidebar-overlay')) {
      this.closeSidebar();
    }
    
    // 处理菜单切换按钮
    if (event.target.closest('.menu-toggle')) {
      this.toggleSidebar();
    }
    
    // 处理移动端菜单切换
    if (event.target.closest('.mobile-menu-toggle')) {
      this.toggleMobileMenu();
    }
  }

  /**
   * 处理键盘事件
   */
  handleKeydown(event) {
    // ESC键关闭侧边栏
    if (event.key === 'Escape' && this.state.sidebarOpen) {
      this.closeSidebar();
    }
    
    // 左右箭头导航
    if (event.key === 'ArrowLeft') {
      this.router.back();
    } else if (event.key === 'ArrowRight') {
      this.router.forward();
    }
  }

  /**
   * 处理滚动事件
   */
  handleScroll() {
    const scrollPosition = window.scrollY;
    
    // 更新滚动状态
    this.state.scrollPosition = {
      x: window.scrollX,
      y: scrollPosition
    };
    
    // 处理滚动事件
    if (scrollPosition > 100) {
      document.body.classList.add('scrolled');
    } else {
      document.body.classList.remove('scrolled');
    }
    
    // 触发滚动事件
    this.emit('scroll', { position: this.state.scrollPosition });
  }

  /**
   * 切换移动菜单
   */
  toggleMobileMenu() {
    this.state.mobileMenuOpen = !this.state.mobileMenuOpen;
    this.updateLayoutClasses();
    
    if (this.state.mobileMenuOpen) {
      this.emit('mobileMenuOpened');
    } else {
      this.emit('mobileMenuClosed');
    }
  }

  /**
   * 导航到指定路径
   */
  navigate(path, options = {}) {
    const { replace = false, params = {}, query = {} } = options;
    
    try {
      // 生成URL
      let url = path;
      
      // 添加查询参数
      if (Object.keys(query).length > 0) {
        const queryString = new URLSearchParams(query).toString();
        url += `?${queryString}`;
      }
      
      // 执行导航
      return this.router[replace ? 'replace' : 'push'](url);
    } catch (error) {
      console.error('导航失败:', error);
      this.emit('error', { error, type: 'navigation' });
      return false;
    }
  }

  /**
   * 获取导航状态
   */
  getState() {
    return {
      ...this.state,
      navigationHistoryLength: this.navigationHistory.length,
      activeRoutes: this.state.activeMenuItems
    };
  }

  /**
   * 获取导航历史
   */
  getNavigationHistory() {
    return [...this.navigationHistory];
  }

  /**
   * 清空导航历史
   */
  clearNavigationHistory() {
    this.navigationHistory = [];
    console.log('导航历史已清空');
  }

  /**
   * 事件监听
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    
    this.listeners.get(event).push(callback);
    return true;
  }

  /**
   * 移除事件监听
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      
      if (index !== -1) {
        callbacks.splice(index, 1);
        return true;
      }
    }
    
    return false;
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`事件监听器执行失败: ${event}`, error);
        }
      });
    }
  }

  /**
   * 防抖函数
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * 节流函数
   */
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * 销毁导航管理器
   */
  destroy() {
    try {
      // 清除事件监听器
      this.listeners.clear();
      
      // 清除定时器
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
      }
      
      // 重置状态
      this.state = {
        currentRoute: null,
        previousRoute: null,
        sidebarOpen: false,
        mobileMenuOpen: false,
        breadcrumb: [],
        activeMenuItems: [],
        isNavigating: false,
        scrollPosition: { x: 0, y: 0 },
        savedPositions: new Map(),
        deviceType: 'desktop',
        isMobile: false,
        lastInteraction: Date.now()
      };
      
      // 清空历史
      this.navigationHistory = [];
      
      this.isInitialized = false;
      
      console.log('导航管理器已销毁');
      
      return true;
    } catch (error) {
      console.error('销毁导航管理器失败:', error);
      return false;
    }
  }
}

// 创建导航管理器实例
const navigationManager = new NavigationManager({
  menuContainer: '#sidebar-menu',
  breadcrumbContainer: '#breadcrumb',
  transitionDuration: 300,
  config: {
    baseTitle: '智能优化规划系统'
  }
});

// 导出
if (typeof window !== 'undefined') {
  window.NavigationManager = NavigationManager;
  window.navigationManager = navigationManager;
}

export { NavigationManager, navigationManager };