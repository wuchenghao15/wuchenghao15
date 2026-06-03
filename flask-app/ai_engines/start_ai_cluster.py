# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Startup script for MTSCOS AI Cluster System
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('ai_cluster_startup.log'),
                              logging.StreamHandler()])
logger = logging.getLogger('AI_Cluster_Startup')

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def startup():
    """Startup the AI Cluster System"""
    logger.info("=== Starting MTSCOS AI Cluster System ===")

    # Step 0: Initialize Database
    logger.info("0. Initializing Database...")
    from app import init_db
    init_db()

    # Step 1: Initialize AI Cluster Manager
    logger.info("1. Initializing AI Cluster Manager...")

    # Step 2: Initialize AI Service Manager
    logger.info("2. Initializing AI Service Manager...")
    from ai_service import ai_service_manager

    # Step 3: Initialize AI Learning System
    logger.info("3. Initializing AI Learning System...")
    from ai_learning_system import AILearningSystem
    ai_learning_system = AILearningSystem(ai_service_manager)

    # Step 4: Create Flask app
    logger.info("4. Creating Flask application...")
    from app import app

    # Step 5: Start the server
    logger.info("5. Starting Flask server on port 8888...")
    print("\n == MTSCOS AI Cluster System ===")
    print(f"Access API endpoints at: http://localhost:8888/api")
    print(f"- Clusters: http://localhost:8888/api/clusters")
    print(f"- Employees: http://localhost:8888/api/employees")
    print(f"- Global Upgrade: http://localhost:8888/api/ai/global-upgrade")
    print("\nPress Ctrl+C to stop the server\n")

    # Start the Flask server
    try:
        app.run(host='0.0.0.0', port=8888, debug=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal - stopping server...")
        print("\n == Shutting down MTSCOS AI Cluster System ===")
        return
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        logger.error(f"Error starting server: {str(e)}")
        raise

if __name__ == '__main__':
    startup()
