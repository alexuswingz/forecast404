"""
TPS AutoForecast - Flask Application Entry Point

Run this file to start the local forecast server.
Usage: python run.py

The application will be available at http://localhost:5000
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.data_import import import_excel_data, init_default_settings

app = create_app()


def init_database():
    """Initialize database with default data if empty"""
    with app.app_context():
        from app.models import Product
        
        # Check if database is empty
        if Product.query.count() == 0:
            print("Database is empty. You can import data from the web interface.")
            print("Navigate to http://localhost:5000/import to upload your Excel file.")
            
            # Check for default Excel file
            default_excel = os.path.join(
                os.path.dirname(__file__),
                'V2.2 AutoForecast 1000 Bananas 2025.12.21.xlsx'
            )
            
            if os.path.exists(default_excel):
                print(f"\nFound default Excel file: {default_excel}")
                response = input("Would you like to import it now? (y/n): ").strip().lower()
                if response == 'y':
                    try:
                        results = import_excel_data(default_excel)
                        init_default_settings()
                        print(f"\nImport successful!")
                        print(f"  Products: {results['products']}")
                        print(f"  Sales Records: {results['units_sold_records']}")
                        print(f"  Inventory Records: {results['inventory_records']}")
                        print(f"  Vine Claims: {results['vine_claims']}")
                        print(f"  Seasonality Weeks: {results['seasonality_weeks']}")
                    except Exception as e:
                        print(f"Import error: {e}")
        else:
            print(f"Database contains {Product.query.count()} products.")


if __name__ == '__main__':
    print("=" * 60)
    print("  TPS AutoForecast - Inventory & Sales Forecasting System")
    print("=" * 60)
    print()
    
    # Initialize database
    init_database()
    
    print()
    print("Starting server...")
    print("Navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print()
    
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)


