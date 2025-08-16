# WeatherWise Project Wiki

## Project Overview
**Name:** WeatherWise  
**Description:** DRRM Weather Analytics Platform  
**Tech Stack:** Python, FastAPI, React, PostgreSQL, Vector DB, OpenWeather API, LLM APIs, MCP  
**Timeline:** 11 weeks  

## Quick Links
- [Database Schema](database_schema.md)
- [API Documentation](api_documentation.md)
- [Development Guide](development_guide.md)

## Project Structure
weatherwise/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   └── package.json
├── docs/
├── docker/
└── config/

## Environment Setup
- Python 3.9+
- Node.js 16+
- Docker
- PostgreSQL with TimescaleDB

## API Keys Required
- OpenWeather API
- OpenAI/Claude API (TBD)

## Current Status
- [x] Project setup complete
- [x] Database schema designed
- [ ] Backend API development
- [ ] Frontend development
- [ ] AI/RAG implementation
- [ ] Testing & deployment