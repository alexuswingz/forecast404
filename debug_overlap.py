"""Debug overlap calculation for B0DQ82P4HR"""
from app import create_app, db
from app.models import Product, Inventory, UnitsSold, Seasonality, ForecastSettings
from app.algorithms import (
    calculate_forecast_18m_plus, 
    calculate_weekly_units_needed,
    calculate_units_to_make
)
from datetime import date, timedelta

app = create_app()
with app.app_context():
    asin = 'B0DQ82P4HR'
    today = date(2026, 1, 8)
    
    # Get settings
    settings = {}
    for s in ForecastSettings.query.all():
        settings[s.name] = s.value
    
    lead_time = int(settings.get('amazon_doi_goal', 93) + 
                    settings.get('inbound_lead_time', 30) + 
                    settings.get('manufacture_lead_time', 7))
    lead_time_end = today + timedelta(days=lead_time)
    
    print(f"Today: {today}")
    print(f"Lead time: {lead_time} days")
    print(f"Lead time end: {lead_time_end}")
    
    # Get product and data
    product = Product.query.filter_by(asin=asin).first()
    inv = Inventory.query.filter_by(product_id=product.id).first()
    
    units_sold = UnitsSold.query.filter_by(product_id=product.id).order_by(UnitsSold.week_end).all()
    units_data = [{'week_end': u.week_end, 'units': u.units} for u in units_sold]
    
    print(f"Units sold records: {len(units_data)}")
    if units_data:
        print(f"First: {units_data[0]['week_end']}, Last: {units_data[-1]['week_end']}")
    
    # Run 18m+ forecast
    forecast_result = calculate_forecast_18m_plus(units_data, today, settings)
    
    # Get the final forecasts (Column P)
    forecasts = forecast_result.get('forecasts', [])
    
    print(f"\nTotal forecast entries: {len(forecasts)}")
    print(f"Forecast result keys: {list(forecast_result.keys())}")
    
    # Print first few forecast entries to see structure
    if forecasts:
        print(f"\nFirst forecast entry keys: {list(forecasts[0].keys())}")
        for i, f in enumerate(forecasts[:5]):
            print(f"  {i}: week_end={f.get('week_end')}, final_forecast={f.get('final_forecast')}, adj_forecast={f.get('adj_forecast')}")
    
    # Calculate weekly units needed for each week
    print(f"\n{'Week End':<12} {'P (Forecast)':<14} {'AC (Units Needed)':<14}")
    print("-" * 45)
    
    total_overlap = 0
    weeks_shown = 0
    
    for f in forecasts:
        week_end = f.get('week_end')
        forecast_val = f.get('forecast', 0) or 0
        units_needed = f.get('units_needed', 0) or 0
        
        if not week_end:
            continue
        
        total_overlap += units_needed
        
        if forecast_val > 0 or units_needed > 0:
            print(f"{week_end}   {forecast_val:>12.1f}   {units_needed:>12.1f}")
            weeks_shown += 1
            
            if weeks_shown >= 25:  # Show first 25 weeks in lead time
                break
    
    print("-" * 45)
    print(f"Sum of weekly units needed: {total_overlap:.1f}")
    print(f"Inventory: {inv.total_inventory}")
    print(f"Units to Make: {max(0, total_overlap - inv.total_inventory):.0f}")
    print(f"\nExpected Units to Make: 6729")
    print(f"Difference: {max(0, total_overlap - inv.total_inventory) - 6729:.0f}")
