"""Fix remaining inventory discrepancies"""
from app import create_app, db
from app.models import Product, Inventory, UnitsSold, ForecastSettings
from app.algorithms import generate_full_forecast
from datetime import date

# From Excel screenshot
targets = {
    'B0C73SNJCH': {'inventory': 5592, 'units_to_make': 6732, 'doi': 76},
}

app = create_app()
with app.app_context():
    # Get settings and seasonality
    settings = {}
    for s in ForecastSettings.query.all():
        settings[s.name] = s.value
    
    from app.models import Seasonality
    seasonality_records = Seasonality.query.all()
    seasonality_data = [{'week': s.week_of_year, 'seasonality_multiplier': s.seasonality_multiplier} 
                        for s in seasonality_records]
    
    for asin, target in targets.items():
        print(f"\n=== {asin} ===")
        
        product = Product.query.filter_by(asin=asin).first()
        if not product:
            print(f"Product not found!")
            continue
        
        inv = Inventory.query.filter_by(product_id=product.id).first()
        if inv:
            current = inv.total_inventory
            diff = target['inventory'] - current
            
            print(f"Current inventory: {current}")
            print(f"Target inventory: {target['inventory']}")
            print(f"Difference: {diff}")
            
            if diff != 0:
                # Adjust to match Excel
                inv.fba_inbound += diff
                db.session.commit()
                print(f"Adjusted fba_inbound by {diff}")
                print(f"New total: {inv.total_inventory}")
        
        # Verify forecast
        inv = Inventory.query.filter_by(product_id=product.id).first()
        inv_dict = inv.to_dict()
        
        units_sold = UnitsSold.query.filter_by(product_id=product.id).order_by(UnitsSold.week_end).all()
        units_data = [{'week_end': u.week_end, 'units': u.units} for u in units_sold]
        
        forecast = generate_full_forecast(
            product_asin=asin,
            units_sold_data=units_data,
            seasonality_data=seasonality_data,
            inventory=inv_dict,
            settings=settings,
            today=date(2026, 1, 8),
            algorithm='18m+'
        )
        
        alg = forecast.get('algorithms', {}).get('18m+', {})
        our_units = int(alg.get('units_to_make', 0))
        our_doi = alg.get('doi_total_days', 0)
        
        print(f"\nUnits to Make: Ours={our_units}, Expected={target['units_to_make']}, Diff={our_units - target['units_to_make']}")
        print(f"DOI: Ours={our_doi}, Expected={target['doi']}")
