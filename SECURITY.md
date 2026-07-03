# Security Vulnerability Report

## Overview

This document tracks known security vulnerabilities in the MTSCOS AI Project dependencies.

## Fixed Vulnerabilities (7)

| Package | Old Version | New Version | CVE/Vulnerability ID |
|---------|-------------|-------------|---------------------|
| cryptography | 47.0.0 | 49.0.0 | GHSA-537c-gmf6-5ccf |
| future | 0.18.2 | 1.0.0 | PYSEC-2022-42991 |
| idna | 3.13 | 3.18 | PYSEC-2026-215 |
| wheel | 0.37.0 | 0.47.0 | PYSEC-2022-43017 |
| setuptools | 58.0.4 | 82.0.1 | PYSEC-2022-43012, PYSEC-2025-49, GHSA-cx63-2mw6-8hw5 |
| certifi | 2026.4.22 | 2026.6.17 | CA certificate update |
| six | 1.15.0 | 1.17.0 | Compatibility update |

## Known Vulnerabilities Requiring Python 3.10+ (22)

These vulnerabilities **cannot be fixed** in the current Python 3.9.6 environment. Upgrade to Python 3.10+ to resolve them.

### High Severity

| Package | Current | Fix Version | Vulnerabilities |
|---------|---------|-------------|-----------------|
| aiohttp | 3.13.5 | 3.14.1 | 11 vulnerabilities |

### Medium Severity

| Package | Current | Fix Version | Vulnerabilities |
|---------|---------|-------------|-----------------|
| filelock | 3.19.1 | 3.20.3 | 2 vulnerabilities |
| msgpack | 1.1.2 | 1.2.1 | 1 vulnerability |
| pip | 26.0.1 | 26.1.2 | 3 vulnerabilities |
| pytest | 8.4.2 | 9.0.3 | 1 vulnerability |
| python-dotenv | 1.2.1 | 1.2.2 | 1 vulnerability |
| requests | 2.32.5 | 2.33.0 | 1 vulnerability |
| urllib3 | 2.6.3 | 2.7.0 | 2 vulnerabilities |

## Risk Assessment

### Core Dependencies (Used Directly)

- **requests/urllib3**: Used for HTTP requests — medium risk
- **python-dotenv**: Used for configuration — low risk

### Transitive Dependencies (Not Used Directly)

- **aiohttp/filelock/msgpack/pytest**: Not directly imported in core app code — lower risk

## Remediation Plan

### Short Term (Current Environment)
- ✅ Already upgraded all Python 3.9-compatible packages
- Monitor for security patches that support Python 3.9

### Long Term (Recommended)
1. **Upgrade Python to 3.10+** (minimum requirement)
2. Run `pip install --upgrade aiohttp filelock msgpack pip pytest python-dotenv requests urllib3`
3. Re-run `pip-audit` to verify all vulnerabilities are resolved

## Verification

```bash
# Run vulnerability scan
python -m pip_audit

# Check Python version
python --version
```

## Last Updated
2026-07-03
