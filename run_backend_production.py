"""
Run backend with production settings (no timeout limits)
Use this instead of 'python backend_app.py' for better performance
"""

from backend_app import app, init_db
import os

if __name__ == '__main__':
    print("="*60)
    print("Starting Backend Server (Production Mode)")
    print("="*60)
    print("\nInitializing database...")
    init_db()
    print("✓ Database ready\n")
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Server starting on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"\n⚠️  Using production mode - NO request timeouts")
    print("   This allows long-running scraper operations (like Telegram bot)")
    print("\nPress Ctrl+C to stop\n")
    print("="*60)
    
    # Run with Werkzeug server but with no timeout limits
    from werkzeug.serving import run_simple
    
    run_simple(
        '0.0.0.0', 
        port, 
        app,
        use_reloader=False,
        threaded=True,
        # No timeout limit - same as Telegram bot
    )
