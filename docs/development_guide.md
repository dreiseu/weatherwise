# WeatherWise Development Guide

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker Desktop
- Git

### Setup Instructions
1. Clone the repository
2. Set up environment variables (.env)
3. Install dependencies
4. Run database migrations
5. Start development servers

## Development Workflow

### Backend Development
```bash

# Frontend Development:
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Database Setup
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run migrations
python backend/scripts/migrate.py

```
# Project Architecture
## Backend Structure

- app/api/: REST API endpoints
- app/core/: Core business logic
- app/models/: Database models
- app/services/: External service integrations

## Frontend Structure

- src/components/: Reusable UI components
- src/pages/: Page components
- src/utils/: Utility functions

# Testing
```bash
# Backend Tests
cd backend
pytest tests/

# Frontend Tests
cd frontend
npm test
```

# Deployment
## Deployment
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Production
- TBD - Will use Docker containers

# Environment Variables
OPENWEATHER_API_KEY=your_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/weatherwise
DEBUG=True

# Git Workflow
1. Create feature branch: git checkout -b feature/feature-name
2. Make changes and commit
3. Push to GitHub: git push origin feature/feature-name
4. Create Pull Request
5. Merge after review

# Troubleshooting
## Common Issues
- API key not working: Wait 10 minutes for activation
- Database connection error: Check Docker is running
- Port already in use: Change port in config

## Debug Mode
Set DEBUG=True in .env for detailed error messages