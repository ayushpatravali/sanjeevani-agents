# Sanjeevani Agents - Multi-Agent RAG System

A multi-agent RAG system for medicinal plant information using Weaviate vector database.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Start Weaviate: `docker compose up -d`
3. Run setup: `python setup_data.py`
4. Start application: `python src/main.py`

## Architecture

- **Research Agent**: Handles medicinal properties and traditional uses
- **GIS Agent**: Manages geographical and habitat information  
- **IUCN Agent**: Focuses on conservation status and threats
- **Super Agent**: Coordinates all agents and synthesizes responses

## Structure

```
sanjeevani-agents/
├── src/           # Source code
├── data/          # Plant data and processing
├── tests/         # Test suite
└── notebooks/     # Jupyter notebooks for exploration
```
