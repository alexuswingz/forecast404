"""Fix inventories to match Excel exactly"""
from app import create_app, db
from app.models import Product, Inventory

# Excel values from screenshots
target_inventories = {
    'B073ZNW8MX': 6638,
}

app = create_app()
with app.app_context():
    for asin, target in target_inventories.items():
        product = Product.query.filter_by(asin=asin).first()
        if not product:
            continue
        
        inv = Inventory.query.filter_by(product_id=product.id).first()
        if inv:
            current = inv.total_inventory
            diff = target - current
            
            print(f"{asin}:")
            print(f"  Current total: {current}")
            print(f"  Target: {target}")
            print(f"  Difference: {diff}")
            
            if diff != 0:
                # Adjust fba_inbound to make up the difference
                inv.fba_inbound += diff
                db.session.commit()
                print(f"  Adjusted fba_inbound by {diff}")
                print(f"  New total: {inv.total_inventory}")
