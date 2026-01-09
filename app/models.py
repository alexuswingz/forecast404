from . import db
from datetime import datetime


class Product(db.Model):
    """Product/ASIN information"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    asin = db.Column(db.String(20), unique=True, nullable=False, index=True)
    product_name = db.Column(db.String(255))
    size = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    units_sold = db.relationship('UnitsSold', backref='product', lazy='dynamic')
    inventory = db.relationship('Inventory', backref='product', lazy='dynamic')
    vine_claims = db.relationship('VineClaim', backref='product', lazy='dynamic')
    seasonality = db.relationship('Seasonality', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.asin}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'asin': self.asin,
            'product_name': self.product_name,
            'size': self.size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UnitsSold(db.Model):
    """Weekly units sold data"""
    __tablename__ = 'units_sold'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    week_end = db.Column(db.Date, nullable=False, index=True)
    week_number = db.Column(db.Integer)
    units = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'week_end', name='unique_product_week'),
    )
    
    def __repr__(self):
        return f'<UnitsSold {self.product_id} - {self.week_end}: {self.units}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'week_end': self.week_end.isoformat() if self.week_end else None,
            'week_number': self.week_number,
            'units': self.units
        }


class Inventory(db.Model):
    """Current inventory levels"""
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    snapshot_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    
    # FBA Inventory
    fba_available = db.Column(db.Integer, default=0)
    fba_reserved = db.Column(db.Integer, default=0)
    fba_inbound = db.Column(db.Integer, default=0)
    
    # AWD Inventory
    awd_available = db.Column(db.Integer, default=0)
    awd_reserved = db.Column(db.Integer, default=0)
    awd_inbound = db.Column(db.Integer, default=0)
    awd_outbound_to_fba = db.Column(db.Integer, default=0)
    
    # Age breakdown
    inv_age_0_90 = db.Column(db.Integer, default=0)
    inv_age_91_180 = db.Column(db.Integer, default=0)
    inv_age_181_270 = db.Column(db.Integer, default=0)
    inv_age_271_365 = db.Column(db.Integer, default=0)
    inv_age_365_plus = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_inventory(self):
        return (
            (self.fba_available or 0) +
            (self.fba_reserved or 0) +
            (self.fba_inbound or 0) +
            (self.awd_available or 0) +
            (self.awd_reserved or 0) +
            (self.awd_inbound or 0) +
            (self.awd_outbound_to_fba or 0)
        )
    
    def __repr__(self):
        return f'<Inventory {self.product_id} - Total: {self.total_inventory}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'fba_available': self.fba_available,
            'fba_reserved': self.fba_reserved,
            'fba_inbound': self.fba_inbound,
            'awd_available': self.awd_available,
            'awd_reserved': self.awd_reserved,
            'awd_inbound': self.awd_inbound,
            'awd_outbound_to_fba': self.awd_outbound_to_fba,
            'total_inventory': self.total_inventory
        }


class VineClaim(db.Model):
    """Vine program claims"""
    __tablename__ = 'vine_claims'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    claim_date = db.Column(db.Date, nullable=False)
    units_claimed = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<VineClaim {self.product_id} - {self.units_claimed}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'claim_date': self.claim_date.isoformat() if self.claim_date else None,
            'units_claimed': self.units_claimed,
            'status': self.status
        }


class Seasonality(db.Model):
    """Seasonality indices by week - PER PRODUCT (for 0-6m and 6-18m algorithms)"""
    __tablename__ = 'seasonality'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, index=True)
    week_of_year = db.Column(db.Integer, nullable=False)
    search_volume = db.Column(db.Float)
    
    # Calculated fields
    sv_peak_env = db.Column(db.Float)
    sv_peak_env_offset = db.Column(db.Float)
    sv_smooth_env = db.Column(db.Float)
    sv_final_curve = db.Column(db.Float)
    sv_smooth = db.Column(db.Float)
    sv_smooth_env_final = db.Column(db.Float)
    seasonality_index = db.Column(db.Float)  # normalized 0-1
    seasonality_multiplier = db.Column(db.Float)  # relative to average
    
    # Unique constraint: one seasonality per week per product
    __table_args__ = (
        db.UniqueConstraint('product_id', 'week_of_year', name='unique_product_seasonality'),
    )
    
    def __repr__(self):
        return f'<Seasonality Product {self.product_id} Week {self.week_of_year}: {self.seasonality_index}>'
    
    def to_dict(self):
        return {
            'product_id': self.product_id,
            'week_of_year': self.week_of_year,
            'search_volume': self.search_volume,
            'seasonality_index': self.seasonality_index,
            'seasonality_multiplier': self.seasonality_multiplier
        }


class ForecastSettings(db.Model):
    """Forecast settings/configuration"""
    __tablename__ = 'forecast_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Float)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Setting {self.name}: {self.value}>'


class ForecastResult(db.Model):
    """Cached forecast results"""
    __tablename__ = 'forecast_results'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    week_end = db.Column(db.Date, nullable=False)
    forecast_type = db.Column(db.String(20))  # '0-6m', '6-18m', '18m+'
    
    # Forecast values
    forecast_units = db.Column(db.Float)
    seasonality_index = db.Column(db.Float)
    
    # DOI calculations
    doi_total = db.Column(db.Float)
    doi_fba = db.Column(db.Float)
    runout_date_total = db.Column(db.Date)
    runout_date_fba = db.Column(db.Date)
    
    # Production
    production_needed = db.Column(db.Float)
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Forecast {self.product_id} - {self.week_end}: {self.forecast_units}>'
    
    def to_dict(self):
        return {
            'product_id': self.product_id,
            'week_end': self.week_end.isoformat() if self.week_end else None,
            'forecast_type': self.forecast_type,
            'forecast_units': self.forecast_units,
            'seasonality_index': self.seasonality_index,
            'doi_total': self.doi_total,
            'doi_fba': self.doi_fba,
            'runout_date_total': self.runout_date_total.isoformat() if self.runout_date_total else None,
            'runout_date_fba': self.runout_date_fba.isoformat() if self.runout_date_fba else None,
            'production_needed': self.production_needed
        }

