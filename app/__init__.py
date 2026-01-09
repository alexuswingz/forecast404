"""Flask application factory."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure database - use PostgreSQL if DATABASE_URL is set, otherwise SQLite
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Railway/Heroku PostgreSQL - fix postgres:// to postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local development - use SQLite
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "inventory.db")}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    
    # Import and register blueprints
    from . import routes
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.api_bp, url_prefix='/api')
    
    # Create tables and run migrations
    with app.app_context():
        db.create_all()
        
        # Auto-migrate: Add product_id column to seasonality if missing
        try:
            from sqlalchemy import text
            result = db.session.execute(text("SELECT product_id FROM seasonality LIMIT 1"))
        except Exception:
            try:
                # Column doesn't exist, add it
                db.session.rollback()
                db.session.execute(text("ALTER TABLE seasonality ADD COLUMN product_id INTEGER REFERENCES products(id)"))
                db.session.commit()
                print("Migration: Added product_id column to seasonality table")
            except Exception as e:
                db.session.rollback()
                print(f"Migration warning: {e}")
    
    return app

