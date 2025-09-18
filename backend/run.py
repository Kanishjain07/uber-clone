#!/usr/bin/env python3
"""
Uber Clone Backend Runner Script
Simple script to start the backend with proper error handling
"""

import os
import sys
from dotenv import load_dotenv

def main():
    """Main entry point"""
    print("Starting Uber Clone Backend...")
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required variables.")
        print("See README.md for setup instructions.")
        sys.exit(1)
    
    # Check MongoDB connection
    try:
        from pymongo import MongoClient
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            print("MONGO_URI not found in environment variables")
            print("Please set MONGO_URI in your .env file")
            sys.exit(1)

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("MongoDB connection successful")
        client.close()
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print("Please ensure MongoDB is running and accessible.")
        sys.exit(1)
    
    # Import and run app
    try:
        from app import app, socketio
        
        print("Backend initialized successfully")
        print("API: http://localhost:5000")
        print("WebSocket: ws://localhost:5000")
        print("Health Check: http://localhost:5000/health")
        print("Starting server...")
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Startup error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
