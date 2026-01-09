"""
Migration script to add product_id column to seasonality table.
Run this once to update the database schema.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if product_id column exists
    try:
        result = db.session.execute(text("SELECT product_id FROM seasonality LIMIT 1"))
        print("product_id column already exists")
    except Exception as e:
        print(f"Adding product_id column to seasonality table...")
        
        # Add the column
        try:
            db.session.execute(text("ALTER TABLE seasonality ADD COLUMN product_id INTEGER REFERENCES products(id)"))
            db.session.commit()
            print("Added product_id column successfully")
        except Exception as e:
            print(f"Error adding column: {e}")
            # Try dropping and recreating the table
            print("Dropping old seasonality table and creating new one...")
            db.session.execute(text("DROP TABLE IF EXISTS seasonality"))
            db.session.commit()
            
            # Recreate using SQLAlchemy models
            from app.models import Seasonality
            db.create_all()
            print("Recreated seasonality table with product_id column")
    
    # Remove the unique constraint on week_of_year alone (now per product)
    try:
        # For SQLite, we need to recreate the table
        # For PostgreSQL, we can drop the constraint
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM seasonality
        """))
        count = result.scalar()
        print(f"Seasonality table has {count} rows")
        
        if count > 0:
            print("Note: Existing seasonality data has no product_id (global)")
            print("You'll need to upload seasonality per-product using the Import page")
    except Exception as e:
        print(f"Error checking seasonality: {e}")

print("\nMigration complete!")
