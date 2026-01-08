# Sanjeevani Plant Assistant 🌿

A robust AI-powered application for identifying medicinal plants, their uses, and geographical distribution using advanced Agentic AI.

## Quick Start

### 1. Prerequisites
- Python 3.10+ installed.
- API Keys for **Groq** and **Weaviate Cloud**.

### 2. Installation
```bash
git clone https://github.com/ayushpatravali/sanjeevani-agents.git
cd sanjeevani-agents
pip install -r requirements.txt
```

### 3. Setup
Create a `.env` file in the root folder:
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
- **Voice Interaction**: Talk to the assistant directly.
- **Smart Mapping**: Visualizes plant locations on interactive maps.
- **Multi-Agent Reasoning**: Uses specialized agents (Research, GIS, IUCN) to answer complex queries.

## Folder Structure
- `app.py`: The main application file.
- `src/`: Core logic and AI agents.
- `data/`: Plant database.
- `evaluation_metrics/`: Performance charts and logs.
- `DEVELOPER_MANUAL.md`: Detailed technical guide for developers (Internal Use).

Before running the application, ensure you have the following installed:

- Python 3.10 or higher
- Git

You also need API keys for:
- **Groq API**: For the Large Language Model.
- **Weaviate Cloud (WCS)**: For the vector database.

## Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/ayushpatravali/sanjeevani-agents.git
    cd sanjeevani-agents
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    python -m venv venv
    # Activate on Windows
    .\venv\Scripts\activate
    # Activate on Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a file named `.env` in the root directory.
2.  Add your API credentials to the file as shown below:

    ```env
    GROQ_API_KEY=your_groq_api_key_here
    WEAVIATE_URL=your_weaviate_cloud_url_here
    WEAVIATE_API_KEY=your_weaviate_api_key_here
    ```

## Data Setup

To populate the database with plant information:

1.  Run the ingestion script:
    ```bash
    python src/scripts/ingest_to_cloud.py
    ```
    This will connect to your Weaviate instance and upload the data from the `data/` folder.

## Running the Application

Start the application using Streamlit:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## File Structure

- `app.py`: Main entry point for the Streamlit application.
- `src/`: Contains the source code for agents and tools.
    - `agents/`: Logic for Research, GIS, and other agents.
    - `database/`: Weaviate client and data loading scripts.
    - `scripts/`: Utilities for data ingestion.
- `data/`: JSON files containing plant and location data.
- `requirements.txt`: List of Python libraries required.
- `.env`: Configuration file for API keys (do not commit this file).

## Deployment

Refer to `DEPLOYMENT_GUIDE.md` and `PROJECT_MASTER_GUIDE.md` for detailed deployment instructions and architectural overview.
