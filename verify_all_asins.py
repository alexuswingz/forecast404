"""Verify all ASINs against Excel"""
from app import create_app, db
from app.models import Product, Inventory, UnitsSold, Seasonality, ForecastSettings
from app.algorithms import generate_full_forecast
from datetime import date

app = create_app()
with app.app_context():
    # Expected values from Excel screenshots
    expected = {
        'B0C73TDZCQ': {'inventory': 7769, 'units_to_make': 6729, 'doi': 104},
        'B073ZNW8MX': {'inventory': 6638, 'units_to_make': 5700, 'doi': 90},
        'B0CPGR5T5W': {'inventory': 1843, 'units_to_make': 4005, 'doi': 77},
    }
    
    # Get settings
    settings = {}
    for s in ForecastSettings.query.all():
        settings[s.name] = s.value
    
    # Get seasonality data
    seasonality_records = Seasonality.query.all()
    seasonality_data = [{'week': s.week_of_year, 'seasonality_multiplier': s.seasonality_multiplier} 
                        for s in seasonality_records]
    
    print("=== Verification ===\n")
    
    for asin, exp in expected.items():
        product = Product.query.filter_by(asin=asin).first()
        if not product:
            print(f"{asin}: NOT FOUND IN DATABASE")
            continue
        
        inv = Inventory.query.filter_by(product_id=product.id).first()
        inv_dict = inv.to_dict() if inv else {'total_inventory': 0}
        
        # Get units sold data
        units_sold = UnitsSold.query.filter_by(product_id=product.id).order_by(UnitsSold.week_end).all()
        units_data = [{'week_end': u.week_end, 'units': u.units} for u in units_sold]
        
        # Get forecast
        forecast = generate_full_forecast(
            product_asin=asin,
            units_sold_data=units_data,
            seasonality_data=seasonality_data,
            inventory=inv_dict,
            settings=settings,
            today=date(2026, 1, 8),
            algorithm='18m+'
        )
        
        alg_18m = forecast.get('algorithms', {}).get('18m+', {})
        our_units = int(alg_18m.get('units_to_make', 0))
        our_doi = alg_18m.get('doi_total_days', 0)
        our_inv = inv_dict.get('total_inventory', 0)
        
        inv_match = "OK" if our_inv == exp['inventory'] else "DIFF"
        units_match = "OK" if abs(our_units - exp['units_to_make']) < 50 else "DIFF"
        doi_match = "OK" if abs(our_doi - exp['doi']) < 5 else "DIFF"
        
        print(f"{asin}:")
        print(f"  Inventory: Ours={our_inv}, Expected={exp['inventory']} {inv_match}")
        print(f"  Units to Make: Ours={our_units}, Expected={exp['units_to_make']} {units_match} (diff={our_units - exp['units_to_make']})")
        print(f"  DOI: Ours={our_doi}, Expected={exp['doi']} {doi_match}")
        print(f"  Sales records: {len(units_data)}")
        if units_data:
            print(f"  First sale: {units_data[0]['week_end']}, Last sale: {units_data[-1]['week_end']}")
        print()
