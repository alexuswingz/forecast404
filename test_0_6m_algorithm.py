"""Test 0-6m algorithm against Excel targets."""

from datetime import date
from app import create_app, db
from app.models import Product, UnitsSold, Inventory, Seasonality, VineClaim
from app.algorithms import calculate_forecast_0_6m_exact

# Test parameters - UPDATE THESE WITH EXCEL VALUES
ASIN = "B0DQ82P4HR"
TODAY = date(2026, 1, 8)

# Excel targets for 0-6m algorithm
EXCEL_UNITS_TO_MAKE = 4051
EXCEL_DOI_TOTAL = 13  # 12.63 rounded
EXCEL_DOI_FBA = 12

print("="*70)
print(f"Testing 0-6m Algorithm for {ASIN}")
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
    
    # Get seasonality data
    seasonality = Seasonality.query.order_by(Seasonality.week_of_year).all()
    seasonality_data = [
        {
            'week_of_year': s.week_of_year,
            'search_volume': s.search_volume or 100,
            'seasonality_index': s.seasonality_index or 1.0,
            'seasonality_multiplier': s.seasonality_multiplier or 1.0
        }
        for s in seasonality
    ]
    print(f"Seasonality records: {len(seasonality_data)}")
    
    # Get vine claims (if any)
    vine_claims = VineClaim.query.filter_by(product_id=product.id).all()
    vine_data = [{'claim_date': v.claim_date, 'units_claimed': v.units_claimed} for v in vine_claims]
    print(f"Vine claims: {len(vine_data)}")
    
    # Settings
    settings = {
        'amazon_doi_goal': 93,
        'inbound_lead_time': 30,
        'manufacture_lead_time': 7,
        'total_inventory': total_inv,
        'fba_available': fba_inv
    }
    
    # Calculate 0-6m forecast
    result = calculate_forecast_0_6m_exact(
        units_data=units_data,
        seasonality_data=seasonality_data,
        vine_claims=vine_data,
        today=TODAY,
        settings=settings
    )
    
    # Show results
    print(f"\nF_peak (max adjusted units): {result.get('F_peak', 0):.2f}")
    print(f"Last historical seasonality: {result.get('last_seasonality', 0):.4f}")
    print(f"Elasticity: {result.get('elasticity', 0.65)}")
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
    print("RESULTS (0-6m Algorithm)")
    print("="*70)
    print(f"  Units to Make: {our_units}")
    print(f"  DOI Total: {our_doi_total} days")
    print(f"  DOI FBA: {our_doi_fba} days")
    
    if EXCEL_UNITS_TO_MAKE is not None:
        print("\n" + "="*70)
        print("COMPARISON WITH EXCEL")
        print("="*70)
        print(f"{'Metric':<20} {'Ours':>12} {'Excel':>12} {'Diff':>10}")
        print("-"*54)
        
        units_diff = our_units - EXCEL_UNITS_TO_MAKE
        doi_total_diff = our_doi_total - EXCEL_DOI_TOTAL
        doi_fba_diff = our_doi_fba - EXCEL_DOI_FBA
        
        print(f"{'Units to Make':<20} {our_units:>12} {EXCEL_UNITS_TO_MAKE:>12} {units_diff:>10}")
        print(f"{'DOI Total':<20} {our_doi_total:>12} {EXCEL_DOI_TOTAL:>12} {doi_total_diff:>10}")
        print(f"{'DOI FBA':<20} {our_doi_fba:>12} {EXCEL_DOI_FBA:>12} {doi_fba_diff:>10}")
    else:
        print("\n[!] Update EXCEL_UNITS_TO_MAKE, EXCEL_DOI_TOTAL, EXCEL_DOI_FBA with values from Excel to compare")

