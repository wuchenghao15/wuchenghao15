// 测试动画功能是否正常工作
function testAnimations() {
    console.log('=== 开始测试动画功能 ===');
    
    // 检查DOM元素是否存在
    const testElements = [
        { id: 'transition-overlay', name: '过渡动画容器' },
        { id: 'transition-text', name: '过渡文本' },
        { selector: '.spinner-ring', name: '加载动画' },
        { selector: '.dashboard-header', name: '顶部导航栏' },
        { selector: '.sidebar', name: '侧边栏' },
        { selector: '.content-header', name: '内容标题' },
        { selector: '.dashboard-stats', name: '统计卡片' },
        { selector: '.feature-grid', name: '功能卡片' }
    ];
    
    let allElementsFound = true;
    testElements.forEach(element => {
        let found;
        if (element.id) {
            found = document.getElementById(element.id);
        } else {
            found = document.querySelector(element.selector);
        }
        
        if (found) {
            console.log(`✅ ${element.name}: 元素存在`);
        } else {
            console.log(`❌ ${element.name}: 元素不存在`);
            allElementsFound = false;
        }
    });
    
    // 检查CSS动画是否已添加
    const styleSheets = document.styleSheets;
    let animationsFound = false;
    
    for (let i = 0; i < styleSheets.length; i++) {
        const rules = styleSheets[i].cssRules || styleSheets[i].rules;
        if (rules) {
            for (let j = 0; j < rules.length; j++) {
                const rule = rules[j];
                if (rule.type === CSSRule.KEYFRAMES_RULE || rule.type === CSSRule.WEBKIT_KEYFRAMES_RULE) {
                    animationsFound = true;
                    break;
                }
            }
        }
        if (animationsFound) break;
    }
    
    if (animationsFound) {
        console.log('✅ CSS动画关键帧: 已添加');
    } else {
        console.log('❌ CSS动画关键帧: 未找到');
    }
    
    // 检查JavaScript函数是否已定义
    const functionsToCheck = [
        'initDashboard',
        'initTransitionAnimation',
        'initElementRevealAnimations',
        'initMenuInteractions',
        'initStatCardAnimations',
        'initFeatureCardInteractions',
        'initSmoothScroll',
        'initPageLoadComplete',
        'createRippleEffect',
        'createConfettiEffect',
        'addAnimationKeyframes'
    ];
    
    let allFunctionsDefined = true;
    functionsToCheck.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ 函数 ${funcName}: 已定义`);
        } else {
            console.log(`❌ 函数 ${funcName}: 未定义`);
            allFunctionsDefined = false;
        }
    });
    
    console.log('=== 动画功能测试完成 ===');
    
    if (allElementsFound && animationsFound && allFunctionsDefined) {
        console.log('🎉 所有动画功能测试通过！');
        return true;
    } else {
        console.log('⚠️  部分动画功能测试未通过');
        return false;
    }
}

// 页面加载完成后运行测试
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', testAnimations);
} else {
    testAnimations();
}