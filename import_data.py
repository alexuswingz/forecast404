"""Quick import script to load data from Excel"""
import os
from app import create_app, db
from app.data_import import import_excel_data, init_default_settings

app = create_app()

with app.app_context():
    excel_path = 'V2.2 AutoForecast 1000 Bananas 2025.12.21.xlsx'
    if os.path.exists(excel_path):
        print('Importing data from Excel...')
        results = import_excel_data(excel_path)
        init_default_settings()
        print(f"Products: {results['products']}")
        print(f"Sales Records: {results['units_sold_records']}")
        print(f"Inventory Records: {results['inventory_records']}")
        print(f"Vine Claims: {results['vine_claims']}")
        print(f"Seasonality Weeks: {results['seasonality_weeks']}")
        print('Import complete!')
    else:
        print(f'Excel file not found: {excel_path}')

