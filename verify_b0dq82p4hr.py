"""Verify B0DQ82P4HR matches Excel"""
from app import create_app, db
from app.models import Product, Inventory, UnitsSold, Seasonality, ForecastSettings
from app.algorithms import generate_full_forecast
from datetime import date

app = create_app()
with app.app_context():
    asin = 'B0DQ82P4HR'
    
    # Get settings
    settings = {}
    for s in ForecastSettings.query.all():
        settings[s.name] = s.value
    
    # Get seasonality data
    seasonality_records = Seasonality.query.all()
    seasonality_data = [{'week': s.week_of_year, 'seasonality_multiplier': s.seasonality_multiplier} 
                        for s in seasonality_records]
    
    product = Product.query.filter_by(asin=asin).first()
    if not product:
        print(f"Product {asin} not found!")
        exit()
    
    inv = Inventory.query.filter_by(product_id=product.id).first()
    inv_dict = inv.to_dict() if inv else {'total_inventory': 0}
    
    # Get units sold data
    units_sold = UnitsSold.query.filter_by(product_id=product.id).order_by(UnitsSold.week_end).all()
    units_data = [{'week_end': u.week_end, 'units': u.units} for u in units_sold]
    
    print(f"=== {asin} ===")
    print(f"Inventory: {inv_dict.get('total_inventory')}")
    print(f"Units sold records: {len(units_data)}")
    if units_data:
        print(f"First sale: {units_data[0]['week_end']}")
        print(f"Last sale: {units_data[-1]['week_end']}")
        
        # Product age
        first_sale = units_data[0]['week_end']
        today = date(2026, 1, 8)
        age_days = (today - first_sale).days
        print(f"Product age: {age_days} days ({age_days/30:.1f} months)")
    
    # Expected values from Excel
    expected = {
        'inventory': 405,
        '18m+': {'units_to_make': 895, 'doi': 73},
        '6-18m': {'units_to_make': 4051, 'doi': 43},
        '0-6m': {'units_to_make': 5629, 'doi': 16}
    }
    
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
    
    print(f"\n=== Comparison ===")
    print(f"Inventory: Ours={inv_dict.get('total_inventory')}, Expected={expected['inventory']}")
    
    # 18m+ algorithm
    alg_18m = forecast.get('algorithms', {}).get('18m+', {})
    print(f"\n18+ Month Algorithm:")
    print(f"  Units to Make: Ours={int(alg_18m.get('units_to_make', 0))}, Expected={expected['18m+']['units_to_make']}")
    print(f"  DOI Total: Ours={alg_18m.get('doi_total_days', 'N/A')}, Expected={expected['18m+']['doi']}")
    
    # 6-18m algorithm  
    alg_6_18m = forecast.get('algorithms', {}).get('6-18m', {})
    print(f"\n6-18 Month Algorithm:")
    print(f"  Units to Make: Ours={int(alg_6_18m.get('units_to_make', 0))}, Expected={expected['6-18m']['units_to_make']}")
    print(f"  DOI Total: Ours={alg_6_18m.get('doi_total_days', 'N/A')}, Expected={expected['6-18m']['doi']}")
    
    # 0-6m algorithm
    alg_0_6m = forecast.get('algorithms', {}).get('0-6m', {})
    print(f"\n0-6 Month Algorithm:")
    print(f"  Units to Make: Ours={int(alg_0_6m.get('units_to_make', 0))}, Expected={expected['0-6m']['units_to_make']}")
    print(f"  DOI Total: Ours={alg_0_6m.get('doi_total_days', 'N/A')}, Expected={expected['0-6m']['doi']}")
