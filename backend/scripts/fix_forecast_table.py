"""
Fix the weather_forecasts table schema - add all missing columns
"""

from sqlalchemy import create_engine, text

def fix_forecast_table():
    """Add all missing columns to weather_forecasts table."""
    
    DATABASE_URL = "postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise"
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Add all missing columns
            missing_columns = [
                "ALTER TABLE weather_forecasts ADD COLUMN IF NOT EXISTS temperature DECIMAL(5,2);",
                "ALTER TABLE weather_forecasts ADD COLUMN IF NOT EXISTS wind_direction INTEGER;",
                "ALTER TABLE weather_forecasts ADD COLUMN IF NOT EXISTS pressure DECIMAL(7,2);",
                "ALTER TABLE weather_forecasts ADD COLUMN IF NOT EXISTS weather_condition VARCHAR(50);",
                "ALTER TABLE weather_forecasts ADD COLUMN IF NOT EXISTS weather_description VARCHAR(255);"
            ]
            
            for sql in missing_columns:
                connection.execute(text(sql))
                print(f"✅ Executed: {sql}")
            
            connection.commit()
            print("\n✅ All missing columns added to weather_forecasts table")
            
            # Show the current table structure
            result = connection.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'weather_forecasts' ORDER BY ordinal_position;"))
            print("\n📋 Current weather_forecasts table structure:")
            for row in result:
                print(f"   - {row[0]}: {row[1]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_forecast_table()