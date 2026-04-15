# API Documentation

## Overview
This document provides detailed information about the MTSCOS AI system API endpoints.

## Authentication
All API endpoints require authentication unless otherwise specified.

## API Endpoints

### Health Check
- **URL**: /health
- **Method**: GET
- **Description**: Check the health status of the system
- **Response**: {
  "status": "ok",
  "timestamp": "2026-02-01T00:00:00Z",
  "version": "1.0.0"
}

## Error Handling
All API endpoints return standard HTTP status codes.

## Rate Limiting
API requests are rate limited to prevent abuse.
