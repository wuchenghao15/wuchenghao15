#!/usr/bin/env python3
"""
AI Color Learning System

This script learns from successful color schemes found on the web and stores the knowledge points in a database.
Then it uses the learned color schemes to update the project's front-end layout and theme color schemes.
"""

import os
import sys
import sqlite3
import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_color_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/mtscos.db'

# Define color scheme table schema
COLOR_SCHEME_TABLE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS ai_color_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    primary_color TEXT NOT NULL,
    secondary_color TEXT NOT NULL,
    accent_color TEXT,
    background_color TEXT NOT NULL,
    text_color TEXT NOT NULL,
    success_color TEXT,
    warning_color TEXT,
    error_color TEXT,
    info_color TEXT,
    color_palette TEXT,
    usage_context TEXT,
    source_url TEXT,
    popularity_score REAL DEFAULT 0.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
'''

# Define AI learning log table schema
AI_LEARNING_LOG_TABLE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS ai_learning_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_topic TEXT NOT NULL,
    source TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    data_acquired INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
'''

class AIColorLearningSystem:
    """
    AI Color Learning System that learns from web color schemes and updates project styling
    """
    
    def __init__(self):
        """Initialize the AI Color Learning System"""
        self.conn = None
        self.cursor = None
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize the database and create necessary tables"""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            self.cursor.execute(COLOR_SCHEME_TABLE_SCHEMA)
            self.cursor.execute(AI_LEARNING_LOG_TABLE_SCHEMA)
            
            self.conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def close_database(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def learn_from_web(self):
        """
        Learn color schemes from web sources
        """
        logger.info("Starting AI color scheme learning from web sources...")
        
        # List of web sources to learn from
        sources = [
            {
                'name': 'Color Hunt',
                'url': 'https://colorhunt.co/popular',
                'parser': self._parse_colorhunt
            },
            {
                'name': 'Coolors',
                'url': 'https://coolors.co/palettes/trending',
                'parser': self._parse_coolors
            }
        ]
        
        total_schemes = 0
        
        for source in sources:
            try:
                logger.info(f"Learning from {source['name']}...")
                schemes = source['parser'](source['url'])
                total_schemes += len(schemes)
                
                # Store learned color schemes
                for scheme in schemes:
                    self._store_color_scheme(scheme, source['name'])
                
                # Log successful learning
                self._log_learning_activity(
                    topic='color_schemes',
                    source=source['name'],
                    success=True,
                    data_acquired=len(schemes)
                )
                
            except Exception as e:
                logger.error(f"Error learning from {source['name']}: {e}")
                # Log failed learning
                self._log_learning_activity(
                    topic='color_schemes',
                    source=source['name'],
                    success=False,
                    error_message=str(e)
                )
            
            # Add delay between requests to avoid rate limiting
            time.sleep(2)
        
        logger.info(f"AI color scheme learning completed. Total schemes learned: {total_schemes}")
        return total_schemes
    
    def _parse_colorhunt(self, url):
        """Parse color schemes from Color Hunt"""
        schemes = []
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find color scheme cards
            color_cards = soup.find_all('div', class_='palette')
            
            for card in color_cards:
                # Extract color codes
                color_divs = card.find_all('div', class_='color')
                colors = [color_div['style'].split(':')[-1].strip() for color_div in color_divs]
                
                if len(colors) >= 4:
                    # Create color scheme
                    scheme = {
                        'name': f'Color Hunt Scheme {len(schemes) + 1}',
                        'description': 'Color scheme from Color Hunt',
                        'primary_color': colors[0],
                        'secondary_color': colors[1],
                        'accent_color': colors[2],
                        'background_color': colors[3],
                        'text_color': '#ffffff' if self._is_dark_color(colors[0]) else '#000000',
                        'color_palette': json.dumps(colors),
                        'usage_context': 'general',
                        'source_url': url
                    }
                    schemes.append(scheme)
                    
        except Exception as e:
            logger.error(f"Error parsing Color Hunt: {e}")
            raise
        
        return schemes
    
    def _parse_coolors(self, url):
        """Parse color schemes from Coolors"""
        schemes = []
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find color scheme containers
            scheme_containers = soup.find_all('div', class_='palette-container')
            
            for container in scheme_containers:
                # Extract color codes
                color_elements = container.find_all('span', class_='color-value')
                colors = [color.text.strip() for color in color_elements if color.text.strip().startswith('#')]
                
                if len(colors) >= 4:
                    # Create color scheme
                    scheme = {
                        'name': f'Coolors Scheme {len(schemes) + 1}',
                        'description': 'Color scheme from Coolors',
                        'primary_color': colors[0],
                        'secondary_color': colors[1],
                        'accent_color': colors[2],
                        'background_color': colors[3],
                        'text_color': '#ffffff' if self._is_dark_color(colors[0]) else '#000000',
                        'color_palette': json.dumps(colors),
                        'usage_context': 'general',
                        'source_url': url
                    }
                    schemes.append(scheme)
                    
        except Exception as e:
            logger.error(f"Error parsing Coolors: {e}")
            raise
        
        return schemes
    
    def _is_dark_color(self, color):
        """Determine if a color is dark (for text color contrast)"""
        # Remove # if present
        color = color.lstrip('#')
        
        # Convert hex to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Calculate luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return True if dark (luminance < 0.5)
        return luminance < 0.5
    
    def _store_color_scheme(self, scheme, source_name):
        """Store a color scheme in the database"""
        try:
            # Check if scheme already exists (based on primary and secondary colors)
            self.cursor.execute(
                "SELECT id FROM ai_color_schemes WHERE primary_color = ? AND secondary_color = ?",
                (scheme['primary_color'], scheme['secondary_color'])
            )
            existing_scheme = self.cursor.fetchone()
            
            if existing_scheme:
                logger.info(f"Color scheme already exists: {scheme['name']}")
                return
            
            # Insert new color scheme
            self.cursor.execute(
                '''
                INSERT INTO ai_color_schemes (
                    name, description, primary_color, secondary_color, accent_color,
                    background_color, text_color, color_palette, usage_context, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    scheme['name'],
                    scheme['description'],
                    scheme['primary_color'],
                    scheme['secondary_color'],
                    scheme.get('accent_color'),
                    scheme['background_color'],
                    scheme['text_color'],
                    scheme['color_palette'],
                    scheme['usage_context'],
                    scheme['source_url']
                )
            )
            
            self.conn.commit()
            logger.info(f"Stored color scheme: {scheme['name']}")
            
        except Exception as e:
            logger.error(f"Error storing color scheme: {e}")
            self.conn.rollback()
            raise
    
    def _log_learning_activity(self, topic, source, success, data_acquired=0, error_message=None):
        """Log AI learning activity"""
        try:
            self.cursor.execute(
                '''
                INSERT INTO ai_learning_logs (
                    learning_topic, source, success, data_acquired, error_message
                ) VALUES (?, ?, ?, ?, ?)
                ''',
                (topic, source, 1 if success else 0, data_acquired, error_message)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error logging learning activity: {e}")
            self.conn.rollback()
    
    def generate_theme_from_learned_schemes(self):
        """Generate a new theme based on learned color schemes"""
        try:
            # Get the most recent color schemes
            self.cursor.execute(
                "SELECT * FROM ai_color_schemes ORDER BY created_at DESC LIMIT 10"
            )
            recent_schemes = self.cursor.fetchall()
            
            if not recent_schemes:
                logger.warning("No color schemes found. Using default theme.")
                return self._get_default_theme()
            
            # Select the first scheme as the base theme
            base_scheme = recent_schemes[0]
            
            # Generate theme from the base scheme
            theme = {
                'primary': base_scheme[3],
                'secondary': base_scheme[4],
                'accent': base_scheme[5] or base_scheme[3],
                'background': base_scheme[6],
                'text': base_scheme[7],
                'success': '#10b981',  # Default success color
                'warning': '#f59e0b',  # Default warning color
                'error': '#ef4444',    # Default error color
                'info': '#3b82f6',     # Default info color
                'palette': json.loads(base_scheme[11]) if base_scheme[11] else []
            }
            
            logger.info(f"Generated theme from learned scheme: {base_scheme[1]}")
            return theme
            
        except Exception as e:
            logger.error(f"Error generating theme: {e}")
            return self._get_default_theme()
    
    def _get_default_theme(self):
        """Return default theme if no learned schemes are available"""
        return {
            'primary': '#06b6d4',
            'secondary': '#10b981',
            'accent': '#8b5cf6',
            'background': '#ffffff',
            'text': '#374151',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'info': '#3b82f6',
            'palette': ['#06b6d4', '#10b981', '#8b5cf6', '#ffffff', '#374151']
        }
    
    def update_project_theme(self):
        """Update the project's front-end theme with learned color schemes"""
        try:
            logger.info("Updating project theme with learned color schemes...")
            
            # Generate new theme
            theme = self.generate_theme_from_learned_schemes()
            
            # Update the index.html file with the new theme
            self._update_index_html_theme(theme)
            
            logger.info("Project theme updated successfully")
            return theme
            
        except Exception as e:
            logger.error(f"Error updating project theme: {e}")
            raise
    
    def _update_index_html_theme(self, theme):
        """Update the index.html file with the new theme"""
        # Read the current index.html file
        index_html_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates/index.html'
        
        try:
            with open(index_html_path, 'r') as f:
                content = f.read()
            
            # Update gradient colors
            content = content.replace(
                'background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%)',
                f'background: linear-gradient(135deg, {theme["primary"]} 0%, {theme["secondary"]} 100%)'
            )
            
            # Update button colors
            content = content.replace(
                'background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%)',
                f'background: linear-gradient(135deg, {theme["primary"]} 0%, {theme["secondary"]} 100%)',
                1  # Only replace the first occurrence (button background)
            )
            
            # Update checkbox colors
            content = content.replace(
                'border-color: #06b6d4',
                f'border-color: {theme["primary"]}'
            )
            
            content = content.replace(
                'box-shadow: 0 4px 12px rgba(6, 182, 212, 0.15)',
                f'box-shadow: 0 4px 12px rgba({self._hex_to_rgb(theme["primary"])}, 0.15)'
            )
            
            content = content.replace(
                'background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%)',
                f'background: linear-gradient(135deg, {theme["primary"]} 0%, {theme["secondary"]} 100%)',
                1  # Only replace the first occurrence (checkbox background)
            )
            
            content = content.replace(
                'box-shadow: 0 4px 16px rgba(6, 182, 212, 0.3)',
                f'box-shadow: 0 4px 16px rgba({self._hex_to_rgb(theme["primary"])}, 0.3)'
            )
            
            # Update input focus colors
            content = content.replace(
                'background: linear-gradient(white, white) padding-box, linear-gradient(135deg, #06b6d4, #10b981) border-box',
                f'background: linear-gradient(white, white) padding-box, linear-gradient(135deg, {theme["primary"]}, {theme["secondary"]}) border-box'
            )
            
            content = content.replace(
                'box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.1), 0 0 0 2px rgba(6, 182, 212, 0.6), 0 8px 24px rgba(6, 182, 212, 0.2)',
                f'box-shadow: 0 0 0 4px rgba({self._hex_to_rgb(theme["primary"])}, 0.1), 0 0 0 2px rgba({self._hex_to_rgb(theme["primary"])}, 0.6), 0 8px 24px rgba({self._hex_to_rgb(theme["primary"])}, 0.2)'
            )
            
            # Update input icon focus color
            content = content.replace(
                'color: #06b6d4',
                f'color: {theme["primary"]}'
            )
            
            # Update password toggle hover color
            content = content.replace(
                'color: #06b6d4',
                f'color: {theme["primary"]}',
                1  # Only replace the first occurrence (password toggle)
            )
            
            content = content.replace(
                'background: rgba(6, 182, 212, 0.1)',
                f'background: rgba({self._hex_to_rgb(theme["primary"])}, 0.1)'
            )
            
            # Update button hover shadow
            content = content.replace(
                'box-shadow: 0 20px 40px rgba(6, 182, 212, 0.4)',
                f'box-shadow: 0 20px 40px rgba({self._hex_to_rgb(theme["primary"])}, 0.4)'
            )
            
            # Update footer link hover color
            content = content.replace(
                'hover:text-teal-500',
                f'hover:text-{theme["primary"].lstrip("#")}'
            )
            
            # Update forgot password link color
            content = content.replace(
                'text-teal-500 hover:text-teal-700',
                f'text-{theme["primary"].lstrip("#")} hover:text-{theme["secondary"].lstrip("#")}'
            )
            
            # Update remember me hover color
            content = content.replace(
                'hover:text-teal-500',
                f'hover:text-{theme["primary"].lstrip("#")}'
            )
            
            # Update register link color
            content = content.replace(
                'text-teal-500 hover:text-teal-700',
                f'text-{theme["primary"].lstrip("#")} hover:text-{theme["secondary"].lstrip("#")}'
            )
            
            # Write the updated content back to the file
            with open(index_html_path, 'w') as f:
                f.write(content)
            
            logger.info("Updated index.html with new theme colors")
            
        except Exception as e:
            logger.error(f"Error updating index.html: {e}")
            raise
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'{r}, {g}, {b}'
    
    def run(self):
        """Run the complete AI color learning and theme generation process"""
        try:
            logger.info("Starting AI Color Learning System...")
            
            # Step 1: Learn color schemes from web
            schemes_learned = self.learn_from_web()
            
            # Step 2: Generate new theme from learned schemes
            theme = self.generate_theme_from_learned_schemes()
            
            # Step 3: Update project theme
            self.update_project_theme()
            
            logger.info("AI Color Learning System completed successfully!")
            return {
                'status': 'success',
                'schemes_learned': schemes_learned,
                'generated_theme': theme
            }
            
        except Exception as e:
            logger.error(f"AI Color Learning System failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            self.close_database()

if __name__ == "__main__":
    ai_system = AIColorLearningSystem()
    result = ai_system.run()
    print(json.dumps(result, indent=2))
