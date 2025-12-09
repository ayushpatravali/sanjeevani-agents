#!/usr/bin/env python3
"""
Setup script for Sanjeevani Agents
This script initializes Weaviate, creates collections, and loads plant data
"""

import logging
import sys
import os
from src.database.weaviate_client import weaviate_manager
from src.database.data_loader import data_processor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main setup function"""
    print("🚀 Setting up Sanjeevani Agents...")
    
    try:
        # Step 1: Connect to Weaviate
        print("\n 1️ Connecting to Weaviate...")
        if not weaviate_manager.connect():
            print(" Failed to connect to Weaviate. Make sure it's running with 'docker compose up -d'")
            return False
        
        # Step 2: Create collections
        print("\n 2️ Creating Weaviate collections...")
        if not weaviate_manager.create_collections():
            print(" Failed to create collections")
            return False
        
        # Step 3: Load plant data
        print("\n 3️ Loading plant data...")
        data_file = "data/detailed_info.json"
        
        if not os.path.exists(data_file):
            print(f" Data file not found: {data_file}")
            print("Please copy your detailed_info.json to the data/ folder")
            return False
        
        if not data_processor.load_json_data(data_file):
            print(" Failed to load JSON data")
            return False
        
        # Step 4: Process and upload to Weaviate
        print("\n 4️ Processing and uploading to Weaviate...")
        if not data_processor.load_data_to_weaviate():
            print(" Failed to upload data to Weaviate")
            return False
        
        print("\n Setup completed successfully!")
        print("\nYour Sanjeevani Agents system is ready!")
        print("\nNext steps:")
        print("- Run 'python test_system.py' to test the system")
        print("- Run 'python src/main.py' to start the application")
        
        return True
    
    finally:
        # Always close the connection properly
        weaviate_manager.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
