# WeatherWise RAG System Architecture

## System Overview
The WeatherWise RAG (Retrieval-Augmented Generation) system combines vector search with LLM generation to provide intelligent, context-aware disaster risk management analysis.

## Components

### 1. Vector Database (ChromaDB)
- **Storage**: 20 Philippine DRRM documents
- **Chunking**: 400 characters with 50-character overlap
- **Embedding**: Automatic sentence transformers
- **Collections**: drrm_knowledge

### 2. LLM Service (OpenAI)
- **Model**: GPT-3.5-turbo
- **Context**: Philippine DRRM expert persona
- **Input**: Weather conditions + retrieved knowledge
- **Output**: Risk assessment + recommendations

### 3. Document Processing Pipeline
- **Input**: Raw DRRM documents
- **Processing**: Text cleaning, chunking, metadata tagging
- **Output**: Vector-ready chunks with metadata

## Performance Metrics
- Retrieval Success Rate: 100%
- Average Relevance Score: 0.48
- Response Time: <2 seconds
- Knowledge Coverage: 5 disaster types

## API Integration
- Endpoint: `/api/v1/weather/rag/analyze`
- Input: Location + query
- Output: Contextual analysis with sources