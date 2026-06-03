# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for MTSCOS AI Project
"""

from setuptools import setup, find_packages
import os

setup(
    name="mtscos-core",
    version="3.1.0",
    description="MTSCOS AI Project Core Module v3.1 - Enhanced AI and System Monitoring",
    author="MTSCOS AI Team",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0",
        "flask-cors>=4.0",
        "psutil>=5.8",
        "openai>=1.0",
        "ollama>=0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-flask>=1.2",
            "flake8>=6.0",
            "black>=23.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mtscos=main:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
