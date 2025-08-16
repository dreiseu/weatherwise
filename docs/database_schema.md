# WeatherWise Database Schema

## Weather Data Tables

### current_weather
- id: UUID Primary Key
- location: String (city name)
- latitude: Float
- longitude: Float
- temperature: Float (Celsius)
- humidity: Integer (percentage)
- wind_speed: Float (km/h)
- wind_direction: Integer (degrees)
- pressure: Float (hPa)
- weather_condition: String
- weather_description: String
- visibility: Float (km)
- timestamp: DateTime
- created_at: DateTime

### weather_forecasts  
- id: UUID Primary Key
- location: String
- latitude: Float
- longitude: Float
- forecast_date: DateTime
- temperature_min: Float
- temperature_max: Float
- humidity: Integer
- wind_speed: Float
- pressure: Float
- weather_condition: String
- precipitation_probability: Integer
- created_at: DateTime

### disaster_alerts
- id: UUID Primary Key
- alert_type: String (TYPHOON, FLOOD, WIND, etc.)
- severity_level: String (LOW, MODERATE, HIGH, CRITICAL)
- title: String
- description: Text
- affected_areas: JSON
- start_time: DateTime
- end_time: DateTime
- status: String (ACTIVE, EXPIRED, CANCELLED)
- created_at: DateTime
- updated_at: DateTime