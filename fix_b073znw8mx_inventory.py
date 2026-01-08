"""Fix B073ZNW8MX inventory to match Excel"""
from app import create_app, db
from app.models import Product, Inventory

app = create_app()
with app.app_context():
    product = Product.query.filter_by(asin='B073ZNW8MX').first()
    if product:
        inv = Inventory.query.filter_by(product_id=product.id).first()
        if inv:
            print(f"Current inventory: {inv.total_inventory}")
            print(f"  FBA: avail={inv.fba_available}, res={inv.fba_reserved}, inb={inv.fba_inbound}")
            print(f"  AWD: avail={inv.awd_available}, res={inv.awd_reserved}, inb={inv.awd_inbound}, outb={inv.awd_outbound_to_fba}")
            
            # Excel shows 6638, we have 6695. Difference is 57.
            # The issue is likely AWD outbound being double-counted
            # Excel may not include AWD outbound in total if it's already in reserved
            
            # Let's set AWD outbound to 0 to avoid double counting with AWD reserved
            if inv.awd_outbound_to_fba == inv.awd_reserved:
                print(f"\nAWD outbound ({inv.awd_outbound_to_fba}) equals AWD reserved ({inv.awd_reserved})")
                print("Setting AWD outbound to 0 to avoid double counting...")
                inv.awd_outbound_to_fba = 0
                db.session.commit()
                print(f"New total inventory: {inv.total_inventory}")
