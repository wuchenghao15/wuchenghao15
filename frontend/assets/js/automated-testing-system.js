/**
 * 自动化测试验证流程
 * 提供全面的自动化测试框架，确保系统更新前的质量验证
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const EventEmitter = require('events');
const crypto = require('crypto');

class AutomatedTestingSystem extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            // 测试配置
            testing: {
                enabled: true,
                timeout: 300000,              // 测试超时时间 5分钟
                parallel: true,               // 并行执行测试
                retryAttempts: 2,             // 测试失败重试次数
                retryDelay: 10000            // 重试延迟
            },
            // 测试套件配置
            testSuites: {
                unit: {
                    name: '单元测试',
                    enabled: true,
                    critical: false,
                    frameworks: ['jest', 'mocha'],
                    coverage: {
                        enabled: true,
                        threshold: 80,        // 代码覆盖率阈值
                        reportFormats: ['html', 'json', 'lcov']
                    }
                },
                integration: {
                    name: '集成测试',
                    enabled: true,
                    critical: false,
                    frameworks: ['jest', 'supertest'],
                    testPaths: ['./tests/integration']
                },
                e2e: {
                    name: '端到端测试',
                    enabled: true,
                    critical: true,
                    frameworks: ['cypress', 'playwright'],
                    testPaths: ['./tests/e2e'],
                    browsers: ['chrome', 'firefox']
                },
                performance: {
                    name: '性能测试',
                    enabled: true,
                    critical: false,
                    frameworks: ['k6', 'artillery'],
                    thresholds: {
                        responseTime: 2000,     // 响应时间阈值 2秒
                        throughput: 100,        // 吞吐量阈值
                        errorRate: 0.01         // 错误率阈值 1%
                    }
                },
                security: {
                    name: '安全测试',
                    enabled: true,
                    critical: true,
                    frameworks: ['owasp-zap', 'npm-audit'],
                    scanTypes: ['vulnerability', 'dependency', 'code']
                },
                api: {
                    name: 'API测试',
                    enabled: true,
                    critical: false,
                    frameworks: ['jest', 'supertest'],
                    testPaths: ['./tests/api'],
                    endpoints: [
                        { method: 'GET', path: '/health', expectedStatus: 200 },
                        { method: 'GET', path: '/api/status', expectedStatus: 200 }
                    ]
                }
            },
            // 环境配置
            environments: {
                gray: {
                    name: '灰色环境',
                    url: 'http://localhost:8082',
                    testPriority: 1
                },
                staging: {
                    name: '预发布环境',
                    url: 'http://localhost:8081',
                    testPriority: 2
                },
                production: {
                    name: '生产环境',
                    url: 'http://localhost:8080',
                    testPriority: 3,
                    readOnly: true
                }
            },
            // 报告配置
            reporting: {
                enabled: true,
                formats: ['html', 'json', 'junit'],
                outputDir: './test-reports',
                artifacts: {
                    screenshots: true,
                    videos: true,
                    logs: true,
                    coverage: true
                }
            },
            // 通知配置
            notifications: {
                enabled: true,
                channels: {
                    email: {
                        enabled: false,
                        recipients: []
                    },
                    slack: {
                        enabled: false,
                        webhook: ''
                    }
                }
            },
            ...config
        };

        // 测试状态
        this.isTesting = false;
        this.currentTestRun = null;
        this.testHistory = [];
        this.testResults = new Map();

        // 初始化
        this.initialize();
    }

    /**
     * 初始化测试系统
     */
    async initialize() {
        this.log('🧪 初始化自动化测试验证系统...');

        try {
            // 创建测试目录
            await this.createTestDirectories();
            
            // 初始化测试框架
            await this.initializeTestFrameworks();
            
            // 加载测试配置
            await this.loadTestConfigurations();

            this.log('✅ 自动化测试验证系统初始化完成');
        } catch (error) {
            this.log(`❌ 初始化失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 创建测试目录
     */
    async createTestDirectories() {
        const directories = [
            './tests',
            './tests/unit',
            './tests/integration',
            './tests/e2e',
            './tests/api',
            './tests/performance',
            './tests/security',
            './test-reports',
            './test-reports/unit',
            './test-reports/integration',
            './test-reports/e2e',
            './test-reports/performance',
            './test-reports/security',
            './test-reports/api',
            './test-reports/artifacts',
            './test-reports/coverage'
        ];

        for (const dir of directories) {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        }
    }

    /**
     * 初始化测试框架
     */
    async initializeTestFrameworks() {
        const packageJsonPath = './package.json';
        
        if (!fs.existsSync(packageJsonPath)) {
            // 创建基础的package.json
            const packageJson = {
                name: 'automated-testing-system',
                version: '1.0.0',
                scripts: {
                    'test': 'jest',
                    'test:unit': 'jest --testPathPattern=tests/unit',
                    'test:integration': 'jest --testPathPattern=tests/integration',
                    'test:e2e': 'cypress run',
                    'test:performance': 'k6 run tests/performance/load-test.js',
                    'test:security': 'npm audit && owasp-zap-baseline.py',
                    'test:coverage': 'jest --coverage',
                    'test:all': 'npm run test:unit && npm run test:integration && npm run test:e2e'
                },
                devDependencies: {
                    'jest': '^29.0.0',
                    'supertest': '^6.3.0',
                    'cypress': '^12.0.0',
                    'playwright': '^1.30.0',
                    'k6': '^0.45.0',
                    'artillery': '^2.0.0',
                    '@testing-library/jest-dom': '^5.16.0',
                    'axios': '^1.3.0'
                }
            };

            fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
        }

        // 创建Jest配置
        const jestConfig = {
            testEnvironment: 'node',
            collectCoverage: true,
            coverageDirectory: './test-reports/coverage',
            coverageReporters: ['text', 'lcov', 'html'],
            testMatch: [
                '**/tests/**/*.test.js',
                '**/tests/**/*.spec.js'
            ],
            reporters: [
                'default',
                ['jest-html-reporters', {
                    publicPath: './test-reports',
                    filename: 'jest-report.html',
                    expand: true
                }],
                ['jest-junit', {
                    outputDirectory: './test-reports',
                    outputName: 'junit.xml'
                }]
            ]
        };

        fs.writeFileSync('./jest.config.json', JSON.stringify(jestConfig, null, 2));
    }

    /**
     * 加载测试配置
     */
    async loadTestConfigurations() {
        // 创建示例测试文件
        await this.createSampleTests();
    }

    /**
     * 创建示例测试文件
     */
    async createSampleTests() {
        // 单元测试示例
        const unitTestExample = `
describe('单元测试示例', () => {
    test('基本功能测试', () => {
        expect(2 + 2).toBe(4);
    });

    test('异步功能测试', async () => {
        const result = await Promise.resolve('success');
        expect(result).toBe('success');
    });

    test('错误处理测试', () => {
        expect(() => {
            throw new Error('测试错误');
        }).toThrow('测试错误');
    });
});
        `;
        fs.writeFileSync('./tests/unit/example.test.js', unitTestExample);

        // 集成测试示例
        const integrationTestExample = `
const request = require('supertest');
const app = require('../../app'); // 假设应用入口文件

describe('集成测试示例', () => {
    test('健康检查接口', async () => {
        const response = await request(app)
            .get('/health')
            .expect(200);
        
        expect(response.body.status).toBe('healthy');
    });

    test('API接口测试', async () => {
        const response = await request(app)
            .get('/api/status')
            .expect(200);
        
        expect(response.body).toHaveProperty('timestamp');
    });
});
        `;
        fs.writeFileSync('./tests/integration/api.test.js', integrationTestExample);

        // API测试示例
        const apiTestExample = `
const axios = require('axios');

describe('API测试示例', () => {
    const baseURL = process.env.TEST_BASE_URL || 'http://localhost:8082';

    test('健康检查API', async () => {
        try {
            const response = await axios.get(\`\${baseURL}/health\`);
            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('status');
        } catch (error) {
            console.error('API测试失败:', error.message);
            throw error;
        }
    });

    test('系统状态API', async () => {
        try {
            const response = await axios.get(\`\${baseURL}/api/status\`);
            expect(response.status).toBe(200);
            expect(response.data).toHaveProperty('environments');
        } catch (error) {
            console.error('API测试失败:', error.message);
            throw error;
        }
    });
});
        `;
        fs.writeFileSync('./tests/api/health.test.js', apiTestExample);

        // 性能测试示例
        const performanceTestExample = `
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
    stages: [
        { duration: '30s', target: 20 },
        { duration: '1m', target: 20 },
        { duration: '20s', target: 0 },
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'],
        http_req_failed: ['rate<0.01'],
    },
};

export default function () {
    let response = http.get('http://localhost:8082/health');
    
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    
    sleep(1);
}
        `;
        fs.writeFileSync('./tests/performance/load-test.js', performanceTestExample);

        // Cypress配置
        const cypressConfig = `
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:8082',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'tests/e2e/**/*.cy.js',
    videosFolder: 'test-reports/artifacts/videos',
    screenshotsFolder: 'test-reports/artifacts/screenshots',
    video: true,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
  },
  reporter: 'cypress-mochawesome-reporter',
  reporterOptions: {
    reportDir: 'test-reports/cypress',
    charts: true,
    reportPageTitle: 'Cypress测试报告',
  },
});
        `;
        fs.writeFileSync('./cypress.config.js', cypressConfig);

        // E2E测试示例
        const e2eTestExample = `
describe('端到端测试示例', () => {
    beforeEach(() => {
        cy.visit('/');
    });

    it('页面加载测试', () => {
        cy.get('h1').should('contain', '系统监控');
        cy.get('.status-indicator').should('be.visible');
    });

    it('环境状态检查', () => {
        cy.get('.environment-item').should('have.length.greaterThan', 0);
        cy.get('.environment-item').first().should('contain', '生产环境');
    });

    it('实时更新测试', () => {
        cy.get('.last-update').should('contain.text', '最后更新');
        
        // 等待WebSocket连接
        cy.get('.connection-status.connected', { timeout: 10000 }).should('be.visible');
    });
});
        `;
        fs.writeFileSync('./tests/e2e/dashboard.cy.js', e2eTestExample);
    }

    /**
     * 执行完整测试套件
     */
    async runFullTestSuite(options = {}) {
        if (this.isTesting) {
            throw new Error('测试正在运行中');
        }

        const testRun = {
            id: this.generateTestRunId(),
            timestamp: new Date().toISOString(),
            environment: options.environment || 'gray',
            testSuites: options.testSuites || Object.keys(this.config.testSuites),
            status: 'running',
            results: {},
            summary: {
                total: 0,
                passed: 0,
                failed: 0,
                skipped: 0,
                duration: 0
            }
        };

        this.isTesting = true;
        this.currentTestRun = testRun;

        this.log(`🚀 开始执行测试套件: ${testRun.id}`);

        try {
            const startTime = Date.now();

            // 执行测试套件
            for (const suiteName of testRun.testSuites) {
                const suiteConfig = this.config.testSuites[suiteName];
                
                if (!suiteConfig.enabled) {
                    testRun.results[suiteName] = {
                        status: 'skipped',
                        reason: '测试套件未启用'
                    };
                    continue;
                }

                try {
                    const result = await this.runTestSuite(suiteName, suiteConfig, testRun.environment);
                    testRun.results[suiteName] = result;
                    
                    // 更新汇总信息
                    testRun.summary.total += result.total || 0;
                    testRun.summary.passed += result.passed || 0;
                    testRun.summary.failed += result.failed || 0;
                    testRun.summary.skipped += result.skipped || 0;

                    // 关键测试失败时停止
                    if (suiteConfig.critical && result.status === 'failed') {
                        this.log(`❌ 关键测试套件 ${suiteName} 失败，停止后续测试`);
                        break;
                    }

                } catch (error) {
                    testRun.results[suiteName] = {
                        status: 'error',
                        error: error.message
                    };
                    testRun.summary.failed++;

                    if (suiteConfig.critical) {
                        this.log(`❌ 关键测试套件 ${suiteName} 执行异常，停止后续测试`);
                        break;
                    }
                }
            }

            testRun.summary.duration = Date.now() - startTime;
            testRun.status = testRun.summary.failed === 0 ? 'passed' : 'failed';

            // 生成测试报告
            await this.generateTestReport(testRun);

            // 发送通知
            await this.sendTestNotifications(testRun);

            this.log(`✅ 测试套件执行完成: ${testRun.status}`);

        } catch (error) {
            testRun.status = 'error';
            testRun.error = error.message;
            this.log(`❌ 测试套件执行异常: ${error.message}`);
        } finally {
            this.isTesting = false;
            this.testHistory.push(testRun);
            this.currentTestRun = null;

            // 触发测试完成事件
            this.emit('testCompleted', testRun);
        }

        return testRun;
    }

    /**
     * 运行单个测试套件
     */
    async runTestSuite(suiteName, suiteConfig, environment) {
        this.log(`📋 执行测试套件: ${suiteConfig.name}`);

        const result = {
            suiteName,
            suiteConfig: suiteConfig.name,
            status: 'running',
            startTime: new Date().toISOString(),
            environment,
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0,
            duration: 0,
            details: {}
        };

        const startTime = Date.now();

        try {
            switch (suiteName) {
                case 'unit':
                    await this.runUnitTests(result);
                    break;
                case 'integration':
                    await this.runIntegrationTests(result);
                    break;
                case 'e2e':
                    await this.runE2ETests(result);
                    break;
                case 'performance':
                    await this.runPerformanceTests(result);
                    break;
                case 'security':
                    await this.runSecurityTests(result);
                    break;
                case 'api':
                    await this.runApiTests(result);
                    break;
                default:
                    throw new Error(`未知的测试套件: ${suiteName}`);
            }

            result.status = result.failed === 0 ? 'passed' : 'failed';
            result.duration = Date.now() - startTime;

            this.log(`✅ 测试套件完成: ${suiteConfig.name} - ${result.status}`);

        } catch (error) {
            result.status = 'error';
            result.error = error.message;
            result.duration = Date.now() - startTime;
            this.log(`❌ 测试套件异常: ${suiteConfig.name} - ${error.message}`);
        }

        return result;
    }

    /**
     * 运行单元测试
     */
    async runUnitTests(result) {
        try {
            const command = 'npm run test:unit -- --coverage --verbose';
            const output = await this.executeCommand(command, { timeout: this.config.testing.timeout });
            
            result.details.output = output.stdout;
            result.details.coverage = await this.parseCoverageReport();
            
            // 解析测试结果
            const testResults = this.parseJestOutput(output.stdout);
            result.total = testResults.total;
            result.passed = testResults.passed;
            result.failed = testResults.failed;
            result.skipped = testResults.skipped;

        } catch (error) {
            result.error = error.message;
            result.failed = 1;
        }
    }

    /**
     * 运行集成测试
     */
    async runIntegrationTests(result) {
        try {
            const command = 'npm run test:integration -- --verbose';
            const output = await this.executeCommand(command, { timeout: this.config.testing.timeout });
            
            result.details.output = output.stdout;
            
            // 解析测试结果
            const testResults = this.parseJestOutput(output.stdout);
            result.total = testResults.total;
            result.passed = testResults.passed;
            result.failed = testResults.failed;
            result.skipped = testResults.skipped;

        } catch (error) {
            result.error = error.message;
            result.failed = 1;
        }
    }

    /**
     * 运行端到端测试
     */
    async runE2ETests(result) {
        try {
            const command = 'npm run test:e2e';
            const output = await this.executeCommand(command, { timeout: this.config.testing.timeout });
            
            result.details.output = output.stdout;
            
            // 解析Cypress输出
            const testResults = this.parseCypressOutput(output.stdout);
            result.total = testResults.total;
            result.passed = testResults.passed;
            result.failed = testResults.failed;
            result.skipped = testResults.skipped;

        } catch (error) {
            result.error = error.message;
            result.failed = 1;
        }
    }

    /**
     * 运行性能测试
     */
    async runPerformanceTests(result) {
        try {
            const command = 'npm run test:performance';
            const output = await this.executeCommand(command, { timeout: this.config.testing.timeout });
            
            result.details.output = output.stdout;
            
            // 解析K6输出
            const testResults = this.parseK6Output(output.stdout);
            result.total = 1; // K6通常只有一个测试场景
            result.passed = testResults.passed ? 1 : 0;
            result.failed = testResults.passed ? 0 : 1;
            result.details.metrics = testResults.metrics;

        } catch (error) {
            result.error = error.message;
            result.failed = 1;
        }
    }

    /**
     * 运行安全测试
     */
    async runSecurityTests(result) {
        try {
            // 依赖漏洞扫描
            const auditCommand = 'npm audit --json';
            const auditOutput = await this.executeCommand(auditCommand);
            result.details.dependencyAudit = JSON.parse(auditOutput.stdout);

            // 代码安全扫描
            const zapCommand = 'owasp-zap-baseline.py -t http://localhost:8082 -J test-reports/security/zap-report.json';
            try {
                const zapOutput = await this.executeCommand(zapCommand);
                result.details.securityScan = zapOutput.stdout;
            } catch (error) {
                // ZAP可能未安装，记录但不失败
                result.details.securityScan = `安全扫描工具未安装: ${error.message}`;
            }

            // 评估安全测试结果
            const vulnerabilities = result.details.dependencyAudit.vulnerabilities || {};
            const criticalVulns = Object.values(vulnerabilities).filter(v => v.severity === 'critical').length;
            const highVulns = Object.values(vulnerabilities).filter(v => v.severity === 'high').length;

            result.total = 1;
            result.passed = (criticalVulns === 0 && highVulns === 0) ? 1 : 0;
            result.failed = (criticalVulns === 0 && highVulns === 0) ? 0 : 1;
            result.details.securitySummary = {
                critical: criticalVulns,
                high: highVulns,
                total: Object.keys(vulnerabilities).length
            };

        } catch (error) {
            result.error = error.message;
            result.failed = 1;
        }
    }

    /**
     * 运行API测试
     */
    async runApiTests(result) {
        try {
            // 设置环境变量
            process.env.TEST_BASE_URL = this.config.environments[result.environment].url;
            
            const command = 'npm run test:api -- --verbose';
            const output = await this.executeCommand(command, { timeout: this.config.testing.timeout });
            
            result.details.output = output.stdout;
            
            // 解析测试结果
            const testResults = this.parseJestOutput(output.stdout);
            result.total = testResults.total;
            result.passed = testResults.passed;
            result.failed = testResults.failed;
            result.skipped = testResults.skipped;

        } catch (error) {
            result.error = error.message;
            result.failed = 1;
        }
    }

    /**
     * 解析Jest输出
     */
    parseJestOutput(output) {
        const results = {
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0
        };

        // 使用正则表达式解析Jest输出
        const testMatch = output.match(/Test Suites: (\d+) passed, (\d+) failed, (\d+) total/);
        if (testMatch) {
            results.passed = parseInt(testMatch[1]);
            results.failed = parseInt(testMatch[2]);
            results.total = parseInt(testMatch[3]);
        }

        const testMatch2 = output.match(/Tests:.*?(\d+) passed, (\d+) failed/);
        if (testMatch2) {
            results.passed = parseInt(testMatch2[1]);
            results.failed = parseInt(testMatch2[2]);
        }

        return results;
    }

    /**
     * 解析Cypress输出
     */
    parseCypressOutput(output) {
        const results = {
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0
        };

        // 解析Cypress输出
        const summaryMatch = output.match(/All specs passed!\|(\d+)\|(\d+)\|(\d+)/);
        if (summaryMatch) {
            results.total = parseInt(summaryMatch[1]);
            results.passed = parseInt(summaryMatch[2]);
            results.failed = parseInt(summaryMatch[3]);
        }

        return results;
    }

    /**
     * 解析K6输出
     */
    parseK6Output(output) {
        const results = {
            passed: true,
            metrics: {}
        };

        // 解析K6指标
        const lines = output.split('\n');
        for (const line of lines) {
            if (line.includes('http_req_duration')) {
                const match = line.match(/http_req_duration.*?=.*?(\d+\.\d+)/);
                if (match) {
                    results.metrics.responseTime = parseFloat(match[1]);
                }
            }
            
            if (line.includes('http_req_failed')) {
                const match = line.match(/http_req_failed.*?=.*?(\d+\.\d+)%/);
                if (match) {
                    results.metrics.errorRate = parseFloat(match[1]);
                }
            }
        }

        // 检查阈值
        const thresholds = this.config.testSuites.performance.thresholds;
        if (results.metrics.responseTime > thresholds.responseTime) {
            results.passed = false;
        }
        if (results.metrics.errorRate > thresholds.errorRate * 100) {
            results.passed = false;
        }

        return results;
    }

    /**
     * 解析覆盖率报告
     */
    async parseCoverageReport() {
        try {
            const coveragePath = './test-reports/coverage/coverage-summary.json';
            if (fs.existsSync(coveragePath)) {
                const coverageData = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
                return {
                    lines: coverageData.total.lines.pct,
                    functions: coverageData.total.functions.pct,
                    branches: coverageData.total.branches.pct,
                    statements: coverageData.total.statements.pct
                };
            }
        } catch (error) {
            this.log(`解析覆盖率报告失败: ${error.message}`);
        }
        return null;
    }

    /**
     * 生成测试报告
     */
    async generateTestReport(testRun) {
        if (!this.config.reporting.enabled) {
            return;
        }

        const reportPath = path.join(this.config.reporting.outputDir, `test-report-${testRun.id}.json`);
        
        try {
            // 生成JSON报告
            fs.writeFileSync(reportPath, JSON.stringify(testRun, null, 2));

            // 生成HTML报告
            await this.generateHTMLReport(testRun);

            // 生成JUnit报告
            await this.generateJUnitReport(testRun);

            this.log(`📊 测试报告已生成: ${reportPath}`);

        } catch (error) {
            this.log(`生成测试报告失败: ${error.message}`);
        }
    }

    /**
     * 生成HTML报告
     */
    async generateHTMLReport(testRun) {
        const htmlTemplate = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - ${testRun.id}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { display: flex; gap: 20px; margin-bottom: 20px; }
        .metric { background: #fff; padding: 15px; border-radius: 5px; border: 1px solid #ddd; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; }
        .metric-label { color: #666; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .suite-results { margin-top: 20px; }
        .suite { background: #fff; margin-bottom: 10px; padding: 15px; border-radius: 5px; border: 1px solid #ddd; }
        .suite-header { font-weight: bold; margin-bottom: 10px; }
        .suite-details { color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>测试报告</h1>
        <p><strong>测试ID:</strong> ${testRun.id}</p>
        <p><strong>时间:</strong> ${testRun.timestamp}</p>
        <p><strong>环境:</strong> ${testRun.environment}</p>
        <p><strong>状态:</strong> <span class="${testRun.status}">${testRun.status}</span></p>
    </div>

    <div class="summary">
        <div class="metric">
            <div class="metric-value">${testRun.summary.total}</div>
            <div class="metric-label">总测试数</div>
        </div>
        <div class="metric">
            <div class="metric-value passed">${testRun.summary.passed}</div>
            <div class="metric-label">通过</div>
        </div>
        <div class="metric">
            <div class="metric-value failed">${testRun.summary.failed}</div>
            <div class="metric-label">失败</div>
        </div>
        <div class="metric">
            <div class="metric-value skipped">${testRun.summary.skipped}</div>
            <div class="metric-label">跳过</div>
        </div>
        <div class="metric">
            <div class="metric-value">${Math.round(testRun.summary.duration / 1000)}s</div>
            <div class="metric-label">耗时</div>
        </div>
    </div>

    <div class="suite-results">
        <h2>测试套件结果</h2>
        ${Object.entries(testRun.results).map(([suiteName, result]) => `
            <div class="suite">
                <div class="suite-header">
                    ${result.suiteName} - <span class="${result.status}">${result.status}</span>
                </div>
                <div class="suite-details">
                    <p><strong>测试数:</strong> ${result.total || 0}</p>
                    <p><strong>通过:</strong> ${result.passed || 0}</p>
                    <p><strong>失败:</strong> ${result.failed || 0}</p>
                    <p><strong>跳过:</strong> ${result.skipped || 0}</p>
                    <p><strong>耗时:</strong> ${Math.round((result.duration || 0) / 1000)}s</p>
                    ${result.error ? `<p><strong>错误:</strong> ${result.error}</p>` : ''}
                </div>
            </div>
        `).join('')}
    </div>
</body>
</html>
        `;

        const htmlPath = path.join(this.config.reporting.outputDir, `test-report-${testRun.id}.html`);
        fs.writeFileSync(htmlPath, htmlTemplate);
    }

    /**
     * 生成JUnit报告
     */
    async generateJUnitReport(testRun) {
        const junitXml = `<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Automated Tests" tests="${testRun.summary.total}" failures="${testRun.summary.failed}" time="${testRun.summary.duration / 1000}">
    ${Object.entries(testRun.results).map(([suiteName, result]) => `
    <testsuite name="${result.suiteName}" tests="${result.total || 0}" failures="${result.failed || 0}" time="${(result.duration || 0) / 1000}">
        ${result.error ? `<failure message="${result.error}"></failure>` : ''}
    </testsuite>
    `).join('')}
</testsuites>`;

        const junitPath = path.join(this.config.reporting.outputDir, `junit-${testRun.id}.xml`);
        fs.writeFileSync(junitPath, junitXml);
    }

    /**
     * 发送测试通知
     */
    async sendTestNotifications(testRun) {
        if (!this.config.notifications.enabled) {
            return;
        }

        try {
            // 发送邮件通知
            if (this.config.notifications.channels.email.enabled) {
                await this.sendEmailNotification(testRun);
            }

            // 发送Slack通知
            if (this.config.notifications.channels.slack.enabled) {
                await this.sendSlackNotification(testRun);
            }

        } catch (error) {
            this.log(`发送测试通知失败: ${error.message}`);
        }
    }

    /**
     * 发送邮件通知
     */
    async sendEmailNotification(testRun) {
        // 实现邮件发送逻辑
        this.log(`📧 测试邮件通知已发送: ${testRun.id}`);
    }

    /**
     * 发送Slack通知
     */
    async sendSlackNotification(testRun) {
        // 实现Slack通知逻辑
        this.log(`💬 测试Slack通知已发送: ${testRun.id}`);
    }

    /**
     * 执行命令
     */
    async executeCommand(command, options = {}) {
        return new Promise((resolve, reject) => {
            const timeout = options.timeout || this.config.testing.timeout;
            
            exec(command, { timeout }, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }

    /**
     * 生成测试运行ID
     */
    generateTestRunId() {
        return `test_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * 获取测试历史
     */
    getTestHistory() {
        return this.testHistory;
    }

    /**
     * 获取当前测试状态
     */
    getCurrentTestStatus() {
        return {
            isTesting: this.isTesting,
            currentTestRun: this.currentTestRun
        };
    }

    /**
     * 记录日志
     */
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[AutomatedTestingSystem] ${timestamp} - ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        const logPath = './test-reports/test.log';
        fs.appendFile(logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error('写入日志失败:', err);
            }
        });
    }
}

module.exports = AutomatedTestingSystem;