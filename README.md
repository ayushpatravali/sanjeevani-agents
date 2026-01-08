# Sanjeevani Plant Assistant

A robust AI-powered application for identifying medicinal plants, their uses, and geographical distribution using advanced Agentic AI.

## Quick Start

### 1. Prerequisites
- Python 3.10+ installed.
- API Keys for Groq and Weaviate Cloud.

### 2. Installation
```bash
git clone https://github.com/ayushpatravali/sanjeevani-agents.git
cd sanjeevani-agents
pip install -r requirements.txt
```

### 3. Setup
Create a .env file in the root folder:
```env
GROQ_API_KEY=your_key
WEAVIATE_URL=your_url
WEAVIATE_API_KEY=your_key
```

### 4. Run
```bash
streamlit run app.py
```
The app will open automatically in your browser.

## Features
- Voice Interaction: Talk to the assistant directly.
- Smart Mapping: Visualizes plant locations on interactive maps.
- Multi-Agent Reasoning: Uses specialized agents (Research, GIS, IUCN) to answer complex queries.

## Folder Structure
- app.py: The main application file.
- src/: Core logic and AI agents.
- data/: Plant database.
- evaluation_metrics/: Performance charts and logs.
