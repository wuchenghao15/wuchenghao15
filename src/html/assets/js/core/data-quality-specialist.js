/**
 * MTSCOS AI System - 数据质量师AI员工
 * 版本: 4.4.0
 * 描述: 专注于数据质量管理、清洗处理、质量监控和治理策略
 */

class DataQualitySpecialist {
    constructor() {
        this.id = 'data-quality-specialist';
        this.name = '数据质量师';
        this.icon = 'fa-check-circle';
        this.color = '#10b981';
        this.gradient = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        this.role = '数据质量专家';
        this.description = '专注于数据质量管理、数据清洗、质量监控、标准化处理和异常检测';
        this.abilities = [
            '质量管理',
            '数据清洗',
            '质量监控',
            '标准化',
            '异常检测',
            '质量报告'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 96;
        this.qualityRules = this.initQualityRules();
        this.qualityMetrics = new Map();
    }

    // ==================== 质量规则 ====================

    initQualityRules() {
        return {
            completeness: [
                { field: 'required', rule: 'NOT_NULL', threshold: 0.95 },
                { field: 'optional', rule: 'NULL_ALLOWED', threshold: 0 }
            ],
            accuracy: [
                { type: 'email', rule: 'EMAIL_FORMAT', pattern: '^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$' },
                { type: 'phone', rule: 'PHONE_FORMAT', pattern: '^1[3-9]\d{9}$' },
                { type: 'date', rule: 'DATE_FORMAT', pattern: '^\d{4}-\d{2}-\d{2}$' }
            ],
            consistency: [
                { field: 'status', rule: 'ENUM_VALUES', values: ['active', 'inactive', 'pending'] },
                { field: 'gender', rule: 'ENUM_VALUES', values: ['male', 'female', 'other'] }
            ],
            timeliness: [
                { field: 'updated_at', rule: 'RECENCY', maxAge: 86400000 }, // 24小时
                { field: 'created_at', rule: 'NO_FUTURE' }
            ],
            uniqueness: [
                { field: 'email', rule: 'UNIQUE', threshold: 1.0 },
                { field: 'phone', rule: 'UNIQUE', threshold: 1.0 }
            ]
        };
    }

    // ==================== 质量评估 ====================

    // 评估数据质量
    assessDataQuality(config) {
        const assessment = {
            id: `assessment_${Date.now()}`,
            collection: config.collection,
            timestamp: Date.now(),
            dimensions: {},
            overallScore: 0,
            issues: [],
            recommendations: []
        };

        // 评估各维度
        assessment.dimensions = {
            completeness: this.assessCompleteness(config.data),
            accuracy: this.assessAccuracy(config.data),
            consistency: this.assessConsistency(config.data),
            timeliness: this.assessTimeliness(config.data),
            uniqueness: this.assessUniqueness(config.data)
        };

        // 计算综合评分
        assessment.overallScore = this.calculateOverallScore(assessment.dimensions);

        // 生成问题列表
        assessment.issues = this.generateIssueList(assessment.dimensions);

        // 生成建议
        assessment.recommendations = this.generateRecommendations(assessment);

        return assessment;
    }

    // 评估完整性
    assessCompleteness(data) {
        const totalFields = data.length > 0 ? Object.keys(data[0]).length : 0;
        let filledFields = 0;
        let totalRecords = 0;

        data.forEach(record => {
            totalRecords++;
            Object.values(record).forEach(value => {
                if (value !== null && value !== undefined && value !== '') {
                    filledFields++;
                }
            });
        });

        const score = totalRecords > 0 ? filledFields / (totalRecords * totalFields) : 0;

        return {
            score: Math.round(score * 100),
            level: this.getScoreLevel(score),
            filled: filledFields,
            total: totalRecords * totalFields,
            missing: (totalRecords * totalFields) - filledFields
        };
    }

    // 评估准确性
    assessAccuracy(data) {
        let validRecords = 0;
        const totalRecords = data.length;

        data.forEach(record => {
            let isValid = true;

            // 验证邮箱格式
            if (record.email && !/^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(record.email)) {
                isValid = false;
            }

            // 验证手机号格式
            if (record.phone && !/^1[3-9]\d{9}$/.test(record.phone)) {
                isValid = false;
            }

            if (isValid) validRecords++;
        });

        const score = totalRecords > 0 ? validRecords / totalRecords : 0;

        return {
            score: Math.round(score * 100),
            level: this.getScoreLevel(score),
            validRecords,
            invalidRecords: totalRecords - validRecords
        };
    }

    // 评估一致性
    assessConsistency(data) {
        const valueDistribution = {};
        let consistentRecords = 0;
        const totalRecords = data.length;

        data.forEach(record => {
            // 检查枚举值一致性
            if (record.status && ['active', 'inactive', 'pending'].includes(record.status)) {
                valueDistribution[record.status] = (valueDistribution[record.status] || 0) + 1;
                consistentRecords++;
            }
        });

        const score = totalRecords > 0 ? consistentRecords / totalRecords : 0;

        return {
            score: Math.round(score * 100),
            level: this.getScoreLevel(score),
            valueDistribution,
            inconsistencies: totalRecords - consistentRecords
        };
    }

    // 评估时效性
    assessTimeliness(data) {
        const now = Date.now();
        const maxAge = 86400000; // 24小时
        let timelyRecords = 0;
        const totalRecords = data.length;

        data.forEach(record => {
            if (record.updated_at) {
                const age = now - new Date(record.updated_at).getTime();
                if (age <= maxAge) timelyRecords++;
            }
        });

        const score = totalRecords > 0 ? timelyRecords / totalRecords : 0;

        return {
            score: Math.round(score * 100),
            level: this.getScoreLevel(score),
            outdatedRecords: totalRecords - timelyRecords
        };
    }

    // 评估唯一性
    assessUniqueness(data) {
        const uniqueValues = new Set();
        let uniqueRecords = 0;
        const totalRecords = data.length;

        data.forEach(record => {
            const key = record.email || record.phone || record.id;
            if (key && !uniqueValues.has(key)) {
                uniqueValues.add(key);
                uniqueRecords++;
            }
        });

        const score = totalRecords > 0 ? uniqueRecords / totalRecords : 0;

        return {
            score: Math.round(score * 100),
            level: this.getScoreLevel(score),
            uniqueCount: uniqueValues.size,
            duplicates: totalRecords - uniqueRecords
        };
    }

    // 计算综合评分
    calculateOverallScore(dimensions) {
        const weights = {
            completeness: 0.25,
            accuracy: 0.30,
            consistency: 0.20,
            timeliness: 0.10,
            uniqueness: 0.15
        };

        let totalScore = 0;
        Object.entries(dimensions).forEach(([dim, data]) => {
            totalScore += (data.score / 100) * (weights[dim] || 0.2);
        });

        return Math.round(totalScore * 100);
    }

    // 获取评分等级
    getScoreLevel(score) {
        if (score >= 0.95) return 'EXCELLENT';
        if (score >= 0.85) return 'GOOD';
        if (score >= 0.70) return 'FAIR';
        if (score >= 0.50) return 'POOR';
        return 'CRITICAL';
    }

    // 生成问题列表
    generateIssueList(dimensions) {
        const issues = [];

        if (dimensions.completeness.score < 95) {
            issues.push({
                dimension: 'completeness',
                severity: 'HIGH',
                count: dimensions.completeness.missing,
                description: `存在${dimensions.completeness.missing}个缺失值`
            });
        }

        if (dimensions.accuracy.score < 95) {
            issues.push({
                dimension: 'accuracy',
                severity: 'HIGH',
                count: dimensions.accuracy.invalidRecords,
                description: `存在${dimensions.accuracy.invalidRecords}条格式错误的记录`
            });
        }

        if (dimensions.uniqueness.score < 95) {
            issues.push({
                dimension: 'uniqueness',
                severity: 'MEDIUM',
                count: dimensions.uniqueness.duplicates,
                description: `存在${dimensions.uniqueness.duplicates}条重复记录`
            });
        }

        return issues;
    }

    // 生成建议
    generateRecommendations(assessment) {
        const recommendations = [];

        assessment.issues.forEach(issue => {
            switch (issue.dimension) {
                case 'completeness':
                    recommendations.push({
                        action: '数据补全',
                        description: '使用默认值或通过API获取缺失数据',
                        priority: 'HIGH'
                    });
                    break;
                case 'accuracy':
                    recommendations.push({
                        action: '格式校验',
                        description: '对输入数据进行格式验证',
                        priority: 'HIGH'
                    });
                    break;
                case 'uniqueness':
                    recommendations.push({
                        action: '去重处理',
                        description: '执行数据去重操作',
                        priority: 'MEDIUM'
                    });
                    break;
            }
        });

        return recommendations;
    }

    // ==================== 数据清洗 ====================

    // 清洗数据
    cleanData(config) {
        const cleaned = {
            id: `clean_${Date.now()}`,
            originalCount: config.data.length,
            operations: [],
            removed: 0,
            modified: 0,
            result: []
        };

        let data = [...config.data];

        // 去重
        if (config.removeDuplicates) {
            const before = data.length;
            data = this.removeDuplicates(data, config.dedupKey);
            cleaned.removed += before - data.length;
            cleaned.operations.push('removeDuplicates');
        }

        // 填充缺失值
        if (config.fillMissing) {
            const before = data.length;
            data = this.fillMissingValues(data, config.defaults);
            cleaned.modified += data.length;
            cleaned.operations.push('fillMissing');
        }

        // 标准化格式
        if (config.standardize) {
            data = this.standardizeFormats(data);
            cleaned.modified += data.length;
            cleaned.operations.push('standardize');
        }

        // 移除无效记录
        if (config.removeInvalid) {
            const before = data.length;
            data = this.removeInvalidRecords(data);
            cleaned.removed += before - data.length;
            cleaned.operations.push('removeInvalid');
        }

        cleaned.result = data;
        return cleaned;
    }

    // 去重
    removeDuplicates(data, key = 'email') {
        const seen = new Set();
        return data.filter(record => {
            const value = record[key];
            if (seen.has(value)) return false;
            seen.add(value);
            return true;
        });
    }

    // 填充缺失值
    fillMissingValues(data, defaults = {}) {
        return data.map(record => {
            const cleaned = { ...record };
            Object.entries(defaults).forEach(([field, defaultValue]) => {
                if (cleaned[field] === null || cleaned[field] === undefined || cleaned[field] === '') {
                    cleaned[field] = defaultValue;
                }
            });
            return cleaned;
        });
    }

    // 标准化格式
    standardizeFormats(data) {
        return data.map(record => {
            const cleaned = { ...record };
            
            // 标准化邮箱
            if (cleaned.email) {
                cleaned.email = cleaned.email.toLowerCase().trim();
            }

            // 标准化手机号
            if (cleaned.phone) {
                cleaned.phone = cleaned.phone.replace(/\D/g, '');
            }

            // 标准化日期
            if (cleaned.date) {
                const d = new Date(cleaned.date);
                cleaned.date = d.toISOString().split('T')[0];
            }

            return cleaned;
        });
    }

    // 移除无效记录
    removeInvalidRecords(data) {
        return data.filter(record => {
            // 验证邮箱
            if (record.email && !/^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(record.email)) {
                return false;
            }
            return true;
        });
    }

    // ==================== 异常检测 ====================

    // 检测异常
    detectAnomalies(data, config) {
        return {
            outliers: this.detectOutliers(data, config.field),
            inconsistencies: this.detectInconsistencies(data),
            violations: this.detectRuleViolations(data)
        };
    }

    // 检测离群值
    detectOutliers(data, field) {
        const values = data.map(r => r[field]).filter(v => typeof v === 'number');
        if (values.length === 0) return [];

        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const std = Math.sqrt(values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length);
        const threshold = 3;

        const outliers = [];
        data.forEach((record, index) => {
            if (typeof record[field] === 'number') {
                const zScore = Math.abs((record[field] - mean) / std);
                if (zScore > threshold) {
                    outliers.push({
                        index,
                        value: record[field],
                        zScore: zScore.toFixed(2)
                    });
                }
            }
        });

        return outliers;
    }

    // 检测不一致
    detectInconsistencies(data) {
        const inconsistencies = [];

        // 检测命名不一致
        const names = {};
        data.forEach((record, index) => {
            const name = record.name?.toLowerCase().trim();
            if (name) {
                if (!names[name]) names[name] = [];
                names[name].push(index);
            }
        });

        Object.entries(names).forEach(([name, indices]) => {
            if (indices.length > 1) {
                inconsistencies.push({
                    type: 'similar_names',
                    records: indices,
                    value: name
                });
            }
        });

        return inconsistencies;
    }

    // 检测规则违反
    detectRuleViolations(data) {
        const violations = [];

        data.forEach((record, index) => {
            // 检查必填字段
            if (!record.email) {
                violations.push({
                    type: 'missing_required',
                    record: index,
                    field: 'email'
                });
            }

            // 检查未来日期
            if (record.created_at && new Date(record.created_at) > new Date()) {
                violations.push({
                    type: 'future_date',
                    record: index,
                    field: 'created_at'
                });
            }
        });

        return violations;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            rulesCount: Object.values(this.qualityRules).flat().length
        };
    }

    // 生成质量报告
    generateQualityReport(assessment) {
        return {
            summary: {
                overallScore: assessment.overallScore,
                level: this.getScoreLevel(assessment.overallScore / 100),
                issuesCount: assessment.issues.length,
                recommendationsCount: assessment.recommendations.length
            },
            detailedDimensions: assessment.dimensions,
            issues: assessment.issues,
            recommendations: assessment.recommendations,
            generatedAt: new Date().toISOString()
        };
    }
}

// 创建全局实例
window.dataQualitySpecialist = new DataQualitySpecialist();

// 导出
window.MTSCOS_DataQualitySpecialist = DataQualitySpecialist;
