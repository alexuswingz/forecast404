"""Test 6-18m algorithm against Excel targets."""

from datetime import date
from app import create_app, db
from app.models import Product, UnitsSold, Inventory, Seasonality
from app.algorithms import calculate_forecast_6_18m

# Excel targets for 6-18m algorithm
ASIN = "B0DQ82P4HR"
EXCEL_UNITS_TO_MAKE = 1146
EXCEL_DOI_TOTAL = 45
EXCEL_DOI_FBA = 43
TODAY = date(2026, 1, 8)

print("="*70)
print(f"Testing 6-18m Algorithm for {ASIN}")
print(f"Today: {TODAY}")
print("="*70)

app = create_app()
with app.app_context():
    # Get product data
    product = Product.query.filter_by(asin=ASIN).first()
    if not product:
        print(f"Product {ASIN} not found!")
        exit(1)
    
    # Get inventory
    inventory = Inventory.query.filter_by(product_id=product.id).first()
    total_inv = inventory.total_inventory if inventory else 0
    fba_inv = inventory.fba_available if inventory else 0
    print(f"\nInventory: Total={total_inv}, FBA={fba_inv}")
    
    # Get units sold
    units_sold = UnitsSold.query.filter_by(product_id=product.id).order_by(UnitsSold.week_end).all()
    units_data = [{'week_end': u.week_end, 'units': u.units, 'week_number': u.week_number} for u in units_sold]
    print(f"Units sold records: {len(units_data)}")
    
    # Get seasonality data (including search_volume for 6-18m algorithm)
    seasonality = Seasonality.query.order_by(Seasonality.week_of_year).all()
    seasonality_data = [
        {
            'week_of_year': s.week_of_year,
            'search_volume': s.search_volume or 100,  # sv_smooth_env for 6-18m
            'seasonality_index': s.seasonality_index or 1.0,
            'seasonality_multiplier': s.seasonality_multiplier or 1.0
        }
        for s in seasonality
    ]
    print(f"Seasonality records: {len(seasonality_data)}")
    if seasonality_data:
        print(f"Sample: week 1 search_volume={seasonality_data[0].get('search_volume', 'N/A')}")
    
    if not seasonality_data:
        print("\nWARNING: No seasonality data found! Using defaults.")
        # Create default seasonality (flat)
        seasonality_data = [{'week_of_year': i, 'seasonality_index': 1.0, 'seasonality_multiplier': 1.0} for i in range(1, 53)]
    
    # Settings
    settings = {
        'amazon_doi_goal': 93,
        'inbound_lead_time': 30,
        'manufacture_lead_time': 7,
        'total_inventory': total_inv,
        'fba_available': fba_inv
    }
    
    # Calculate 6-18m forecast
    result = calculate_forecast_6_18m(
        units_data=units_data,
        seasonality_data=seasonality_data,
        today=TODAY,
        settings=settings
    )
    
    # Show results
    print(f"\nF constant (max deseasonalized avg): {result.get('F_constant', 0):.2f}")
    print(f"Lead time: {result['lead_time_days']} days")
    
    print("\nFirst 10 forecast weeks:")
    for f in result['forecasts'][:10]:
        print(f"  {f['week_end']}: forecast={f['forecast']:.2f}, needed={f['units_needed']:.2f}")
    
    print(f"\nTotal units needed: {result['total_units_needed']:.2f}")
    
    # Compare results
    our_units = result['units_to_make']
    our_doi_total = result['doi_total_days']
    our_doi_fba = result['doi_fba_days']
    
    print("\n" + "="*70)
    print("RESULTS COMPARISON (6-18m Algorithm)")
    print("="*70)
    print(f"{'Metric':<20} {'Ours':>12} {'Excel':>12} {'Diff':>10} {'Match':>8}")
    print("-"*62)
    
    units_diff = our_units - EXCEL_UNITS_TO_MAKE
    doi_total_diff = our_doi_total - EXCEL_DOI_TOTAL
    doi_fba_diff = our_doi_fba - EXCEL_DOI_FBA
    
    print(f"{'Units to Make':<20} {our_units:>12} {EXCEL_UNITS_TO_MAKE:>12} {units_diff:>10} {'OK' if abs(units_diff) < 50 else 'DIFF':>8}")
    print(f"{'DOI Total':<20} {our_doi_total:>12} {EXCEL_DOI_TOTAL:>12} {doi_total_diff:>10} {'OK' if abs(doi_total_diff) < 5 else 'DIFF':>8}")
    print(f"{'DOI FBA':<20} {our_doi_fba:>12} {EXCEL_DOI_FBA:>12} {doi_fba_diff:>10} {'OK' if abs(doi_fba_diff) < 5 else 'DIFF':>8}")
    
    all_match = abs(units_diff) < 50 and abs(doi_total_diff) < 5 and abs(doi_fba_diff) < 5
    print("\n" + "="*70)
    if all_match:
        print("SUCCESS! All metrics match Excel within tolerance!")
    else:
        print("SOME METRICS DO NOT MATCH - investigation needed")

