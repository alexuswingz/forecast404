"""Debug 6-18m algorithm calculations."""

from datetime import date
from app import create_app, db
from app.models import Product, UnitsSold, Seasonality

ASIN = "B0DQ82P4HR"
TODAY = date(2026, 1, 8)

app = create_app()
with app.app_context():
    product = Product.query.filter_by(asin=ASIN).first()
    units_sold = UnitsSold.query.filter_by(product_id=product.id).order_by(UnitsSold.week_end).all()
    seasonality = Seasonality.query.order_by(Seasonality.week_of_year).all()
    
    # Build lookups
    sv_lookup = {s.week_of_year: s.search_volume * 0.97 for s in seasonality}
    
    print("Calculating E values (CVR = units / search_volume):")
    print(f"{'Week End':<12} {'Week#':<6} {'Units':<8} {'SV':<10} {'CVR':<10}")
    print("-" * 50)
    
    e_values = []
    for u in units_sold:
        week_of_year = u.week_end.isocalendar()[1]
        sv = sv_lookup.get(week_of_year, 100)
        cvr = u.units / sv if sv > 0 and u.units > 0 else 0
        e_values.append(cvr)
        
        if u.units > 0:  # Only show rows with sales
            print(f"{u.week_end} {week_of_year:<6} {u.units:<8} {sv:<10.2f} {cvr:<10.4f}")
    
    # Calculate F (peak CVR)
    non_zero = [e for e in e_values if e > 0]
    if non_zero:
        max_cvr = max(non_zero)
        max_idx = e_values.index(max_cvr)
        
        # 5-week window
        start = max(0, max_idx - 2)
        end = min(len(e_values), max_idx + 3)
        window = [e for e in e_values[start:end] if e > 0]
        F = sum(window) / len(window) if window else max_cvr
        
        print(f"\nMax CVR: {max_cvr:.4f} at index {max_idx}")
        print(f"Window values: {[f'{v:.4f}' for v in window]}")
        print(f"F (avg peak CVR): {F:.4f}")
    
    # What Excel expects
    print("\n" + "="*50)
    print("Excel expects F (peak CVR) around 0.15-0.17")
    print("Our calculated F:", F if non_zero else "N/A")

