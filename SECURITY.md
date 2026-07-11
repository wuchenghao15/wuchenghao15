# Security Vulnerability Report

## Overview

This document tracks known security vulnerabilities in the MTSCOS AI Project dependencies.

## Fixed Vulnerabilities (15)

| Package | Old Version | New Version | CVE/Vulnerability ID |
|---------|-------------|-------------|---------------------|
| cryptography | 47.0.0 | 49.0.0 | GHSA-537c-gmf6-5ccf |
| future | 0.18.2 | 1.0.0 | PYSEC-2022-42991 |
| idna | 3.13 | 3.18 | PYSEC-2026-215 |
| wheel | 0.37.0 | 0.47.0 | PYSEC-2022-43017 |
| setuptools | 58.0.4 | 82.0.1 | PYSEC-2022-43012, PYSEC-2025-49, GHSA-cx63-2mw6-8hw5 |
| certifi | 2026.4.22 | 2026.6.17 | CA certificate update |
| six | 1.15.0 | 1.17.0 | Compatibility update |
| Flask | 2.3.3 | 3.1.3 | GHSA-68rp-wp8r-4726 |
| Flask-CORS | 4.0.0 | 6.0.5 | PYSEC-2024-71, PYSEC-2024-271, PYSEC-2026-1383, PYSEC-2026-1384, PYSEC-2026-1385 |
| Jinja2 | 3.1.4 | 3.1.6 | PYSEC-2026-1471, PYSEC-2026-1475, PYSEC-2026-1472 |
| Werkzeug | 2.3.8 | 3.1.8 | PYSEC-2026-2045, PYSEC-2026-2046, PYSEC-2026-2044, PYSEC-2026-2043, GHSA-q34m-jh98-gwm2, GHSA-29vq-49wr-vm6x |
| scikit-learn | 1.3.2 | 1.6.1 | PYSEC-2024-110 |
| SQLAlchemy | 2.0.16 | 2.0.50 | Security patches |
| MarkupSafe | 2.1.5 | 3.0.3 | Security patches |
| protobuf | 4.25.9 | 5.29.6 | Security patches |

## Known Vulnerabilities Requiring Python 3.10+ (28)

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
| pillow | 11.3.0 | 12.2.0 | 6 vulnerabilities |
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
2026-07-11
