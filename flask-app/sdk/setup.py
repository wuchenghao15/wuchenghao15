# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI SDK Setup
"""

from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mtscos-sdk",
    version="7.2.0",
    author="MTSCOS AI Team",
    author_email="support@mtscos.com",
    description="MTSCOS AI System SDK - 用于集成MTSCOS AI系统的Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mtscos/mtscos-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords=["MTSCOS", "AI", "SDK", "backup", "certificate", "recovery"],
    project_urls={
        "Documentation": "https://docs.mtscos.com/sdk",
        "Source": "https://github.com/mtscos/mtscos-sdk",
        "Tracker": "https://github.com/mtscos/mtscos-sdk/issues",
    },
)
