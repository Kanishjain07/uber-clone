"""
Main application runner for Uber Clone
"""
import os
from app import create_app

if __name__ == '__main__':
    app, socketio = create_app()

    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '127.0.0.1')
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print("=" * 50)
    print("UBER CLONE API STARTING")
    print("=" * 50)
    print(f"API Server: http://{host}:{port}")
    print(f"WebSocket: ws://{host}:{port}")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"API Docs: http://{host}:{port}/api/v1/docs")
    print("=" * 50)

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )
