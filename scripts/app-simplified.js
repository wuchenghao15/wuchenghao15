/**
 * Simplified app.js for debugging
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');

// Import config
const config = require('./src/config/app.config');

// Initialize app
const app = express();
const PORT = config.server.port || 8080;

// Middleware
app.use(cors(config.cors));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Static files
app.use('/html', express.static(__dirname + '/src/html'));

// Routes
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: config.app.version,
        message: 'Server is running'
    });
});

// Root path
app.get('/', (req, res) => {
    res.redirect('/html/index.html');
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        message: 'Route not found'
    });
});

// Start server
console.log('Starting simplified server...');
try {
    const server = app.listen(PORT, () => {
        console.log(`✅ Server started on http://localhost:${PORT}`);
        console.log(`✅ Static files: http://localhost:${PORT}/html`);
        console.log(`✅ Health check: http://localhost:${PORT}/api/health`);
    });
    
    server.on('error', (error) => {
        console.error('❌ Server error:', error);
        process.exit(1);
    });
} catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
}