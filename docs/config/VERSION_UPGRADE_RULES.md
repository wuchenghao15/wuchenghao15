# 项目版本升级机制规则文档

## 版本号规则定义

### 一级版本号 (Major)
- **规则**: 手动增加
- **示例**: 1.x.x.x → 2.x.x.x
- **使用场景**: 重大架构变更、破坏性API变更、核心功能重构

### 二级版本号 (Minor)
- **规则**: 当日时间具体到日 (YYYYMMDD)
- **示例**: 1.20260118.x.x
- **使用场景**: 每日构建、日期变更时自动更新

### 三级版本号 (Patch)
- **规则**: 一旦被修复的文件树大于15个或修改代码行超500行，版本号增加
- **示例**: 1.20260118.1.x
- **使用场景**: 批量修复、大型功能更新、代码量较大的修改

### 四级版本号 (Build)
- **规则**: 时间戳后8位 + 修改次数(3位)
- **示例**: 1.20260118.1.12345678041
- **使用场景**: 实时修改、小批量更新、频繁变更

## 版本升级触发条件

| 升级类型 | 触发条件 | 版本号变化 |
|---------|---------|----------|
| 自动升级 | 检测到代码变更 | 根据变更规模自动判断 |
| 每日升级 | 日期变更 | 更新二级版本号 |
| 批量升级 | 文件数>15或行数>500 | 增加三级版本号 |
| 实时升级 | 代码修改 | 更新四级版本号 |
| 手动升级 | 开发者操作 | 增加一级版本号 |

## 版本号格式

```
major.minor.patch+build
```

- **major**: 一级版本号 (手动增加)
- **minor**: 二级版本号 (YYYYMMDD)
- **patch**: 三级版本号 (文件数>15或行数>500时增加)
- **build**: 四级版本号 (时间戳后8位+修改次数3位)

## 示例版本号

| 场景 | 版本号 | 说明 |
|------|--------|------|
| 初始版本 | 1.20260118.0.12345678000 | 2026年1月18日初始版本 |
| 小修改 | 1.20260118.0.12345678005 | 5次小修改 |
| 批量修复 | 1.20260118.1.12345678020 | 超过15个文件修复 |
| 日期变更 | 1.20260119.0.12345678000 | 日期变更到1月19日 |
| 重大更新 | 2.20260119.0.12345678000 | 手动升级一级版本 |

## 版本管理功能

### 1. 代码变更检测
- 自动扫描项目文件
- 检测文件修改时间
- 计算修改文件数量
- 统计修改代码行数
- 记录修改次数

### 2. 版本升级逻辑
- **自动升级**: 根据代码变更自动判断升级类型
- **每日升级**: 检测日期变更自动更新二级版本号
- **批量升级**: 文件数>15或行数>500时增加三级版本号
- **实时升级**: 每次修改自动更新四级版本号
- **手动升级**: 支持手动触发各级版本升级

### 3. 版本文件更新
- 更新 package.json 版本号
- 记录版本升级历史
- 生成版本变更日志
- 支持数据库存储版本信息

## 使用方法

### 自动升级
```javascript
const { getVersionManager } = require('./src/core/version/version-manager');
const versionManager = getVersionManager();

// 自动检测并升级版本
const upgradedVersion = await versionManager.upgradeVersion('auto');
console.log('新版本:', upgradedVersion.versionString);
```

### 手动升级
```javascript
// 升级一级版本
await versionManager.upgradeVersion('major');

// 升级二级版本（当日时间）
await versionManager.upgradeVersion('minor');

// 升级三级版本
await versionManager.upgradeVersion('patch');

// 只更新四级版本
await versionManager.upgradeVersion('build');
```

### 检查版本信息
```javascript
const versionInfo = await versionManager.getVersionInfo();
console.log('当前版本:', versionInfo.currentVersion.versionString);
console.log('版本历史:', versionInfo.versionHistory);
```

### 检查升级需求
```javascript
const requirements = versionManager.checkUpgradeRequirements();
console.log('是否需要升级:', requirements.shouldUpgrade);
console.log('建议升级类型:', requirements.upgradeType);
console.log('升级原因:', requirements.reasons);
```

## 技术实现

### 核心组件
- **VersionManager**: 版本管理核心类
- **代码变更检测**: 扫描文件系统检测修改
- **版本号计算**: 根据规则计算新版本号
- **版本文件更新**: 更新项目版本文件
- **版本历史记录**: 记录版本升级历史

### 依赖项
- Node.js
- fs (文件系统)
- path (路径处理)
- winston (日志记录)
- sqlite3 (数据库存储，可选)

## 配置项

### 配置文件
```javascript
{
    packageJsonFile: path.join(__dirname, '../../package.json'),
    logDir: path.join(__dirname, '../../Logs'),
    srcDir: path.join(__dirname, '../../')
}
```

### 环境变量
- 无特殊环境变量需求，使用默认配置即可

## 故障处理

### 数据库不可用
- 自动切换到文件系统存储
- 版本信息仍可正常更新
- 升级功能不受影响

### 文件系统错误
- 记录错误日志
- 尝试备选路径
- 保持版本管理功能可用

### 版本冲突
- 自动检测版本冲突
- 保留最新版本
- 记录冲突历史

## 性能优化

### 扫描优化
- 跳过不需要检查的目录 (node_modules, .git等)
- 只检查代码文件
- 缓存扫描结果

### 计算优化
- 增量计算修改次数
- 缓存版本信息
- 异步处理文件操作

### 存储优化
- 压缩版本历史
- 限制日志文件大小
- 定期清理旧版本记录

## 总结

本版本升级机制实现了以下功能：
- ✅ 符合要求的四级版本号规则
- ✅ 自动代码变更检测
- ✅ 智能版本升级判断
- ✅ 完整的版本管理功能
- ✅ 健壮的错误处理
- ✅ 良好的性能优化

系统能够根据代码变更自动判断版本升级类型，确保版本号准确反映项目的变更状态，同时提供了灵活的手动升级选项，满足不同场景的需求。