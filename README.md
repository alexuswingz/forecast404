# TPS AutoForecast - Local Database & Forecasting System

A Flask-based web application that replicates the Excel AutoForecast algorithms for product inventory and sales forecasting.

## Features

- **Data Import**: Import products, sales history, and inventory from Excel files
- **Forecasting Algorithms**: 
  - 0-6 Month: Max Week Seasonality approach
  - 6-18 Month: Weighted Weekly Average with seasonality
  - 18+ Month: Prior Year Smoothed with velocity adjustments
- **Seasonality Calculation**: Automatic seasonality index calculation from search volume data
- **DOI Analysis**: Days of Inventory calculations with runout date predictions
- **Production Planning**: Automated production needs calculation based on lead time and safety stock
- **Interactive Dashboard**: View products, sales charts, and forecasts

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python run.py
   ```

3. **Open Browser**: Navigate to http://localhost:5000

4. **Import Data**: 
   - Go to the Import page
   - Upload your AutoForecast Excel file
   - Or use the Quick Import for the default file

## Project Structure

```
TPSv2/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # Database models
│   ├── algorithms.py      # Forecast algorithms
│   ├── data_import.py     # Excel import functionality
│   ├── routes.py          # API & web routes
│   └── templates/         # HTML templates
│       ├── base.html
│       ├── index.html
│       ├── product.html
│       ├── forecast.html
│       ├── import.html
│       └── settings.html
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── inventory.db          # SQLite database (created on first run)
└── README.md
```

## Database Models

- **Product**: ASIN, product name, size
- **UnitsSold**: Weekly sales data per product
- **Inventory**: FBA and AWD inventory snapshots
- **VineClaim**: Vine program claim tracking
- **Seasonality**: Weekly seasonality indices
- **ForecastSettings**: Algorithm configuration
- **ForecastResult**: Cached forecast results

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/products` | GET | List all products |
| `/api/products/<asin>` | GET | Get product details |
| `/api/products/<asin>/sales` | GET | Get sales history |
| `/api/products/<asin>/inventory` | GET | Get current inventory |
| `/api/products/<asin>/forecast` | GET | Generate forecast |
| `/api/seasonality` | GET/POST | Get or update seasonality |
| `/api/inventory` | POST | Update inventory |
| `/api/settings` | GET/POST | Get or update settings |
| `/api/import` | POST | Import from Excel file |

## Algorithms

### Seasonality Calculation
Replicates Excel formulas:
1. Peak envelope smoothing
2. Offset smoothing
3. Rolling averages
4. Seasonality index (normalized 0-1)
5. Seasonality multiplier (relative to average)

### Forecast 0-6 Months
Uses the maximum units week adjusted by seasonality curve:
```
forecast = max_units_week × seasonality_index
```

### Forecast 6-18 Months
Uses weighted weekly average (recent weeks weighted higher):
```
forecast = weighted_avg × seasonality_multiplier
```

### Forecast 18+ Months
Uses prior year smoothed data with adjustments:
```
forecast = prior_year_smooth × (1 + velocity_adj × factor) × (1 + growth_factor)
```

### DOI (Days of Inventory)
Calculates remaining inventory per week:
```
DOI = current_inventory - cumulative_forecast
Runout Date = week when DOI ≤ 0
```

## Configuration

Edit settings via the web interface or API:

| Setting | Default | Description |
|---------|---------|-------------|
| velocity_adj_factor | 0.1 | Trend responsiveness |
| growth_factor | 0.05 | YoY growth assumption |
| lead_time_days | 90 | Production lead time |
| safety_stock_weeks | 4 | Safety buffer |
| smoothing_factor | 0.85 | Conservative multiplier |

## License

Internal use only - TPS Nutrients


