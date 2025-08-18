"""
Database Query Optimization for WeatherWise
Analyzes and optimizes database performance
"""

import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization and performance analysis."""
    
    def __init__(self):
        """Initialize database optimizer."""
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info("Database optimizer initialized")
    
    def analyze_table_sizes(self):
        """Analyze table sizes and row counts."""
        logger.info("📊 Analyzing table sizes...")
        
        size_query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname = 'public'
        ORDER BY tablename, attname;
        """
        
        row_count_query = """
        SELECT 
            'current_weather' as table_name,
            COUNT(*) as row_count
        FROM current_weather
        UNION ALL
        SELECT 
            'weather_forecasts' as table_name,
            COUNT(*) as row_count
        FROM weather_forecasts
        UNION ALL
        SELECT 
            'disaster_alerts' as table_name,
            COUNT(*) as row_count
        FROM disaster_alerts
        UNION ALL
        SELECT 
            'risk_assessments' as table_name,
            COUNT(*) as row_count
        FROM risk_assessments
        UNION ALL
        SELECT 
            'analysis_reports' as table_name,
            COUNT(*) as row_count
        FROM analysis_reports;
        """
        
        with self.engine.connect() as conn:
            # Get row counts
            result = conn.execute(text(row_count_query))
            rows = result.fetchall()
            
            print("\n📋 Table Row Counts:")
            print("-" * 40)
            for row in rows:
                print(f"{row[0]:<20}: {row[1]:>10} rows")
            
            # Get table sizes
            size_info_query = """
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """
            
            result = conn.execute(text(size_info_query))
            sizes = result.fetchall()
            
            print("\n💾 Table Sizes:")
            print("-" * 40)
            for table, size in sizes:
                print(f"{table:<20}: {size}")
    
    def analyze_query_performance(self):
        """Analyze query performance for common operations."""
        logger.info("⚡ Analyzing query performance...")
        
        queries = [
            ("Recent weather by location", """
                SELECT * FROM current_weather 
                WHERE location = 'Manila,PH' 
                AND timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC
                LIMIT 10;
            """),
            ("Weather conditions summary", """
                SELECT weather_condition, COUNT(*) 
                FROM current_weather 
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY weather_condition
                ORDER BY COUNT(*) DESC;
            """),
            ("Temperature trends", """
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    AVG(temperature) as avg_temp,
                    location
                FROM current_weather 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY hour, location
                ORDER BY hour, location;
            """),
            ("Multi-location comparison", """
                SELECT 
                    location,
                    AVG(temperature) as avg_temp,
                    AVG(humidity) as avg_humidity,
                    AVG(pressure) as avg_pressure
                FROM current_weather 
                WHERE timestamp >= NOW() - INTERVAL '48 hours'
                GROUP BY location;
            """)
        ]
        
        print("\n⚡ Query Performance Analysis:")
        print("-" * 60)
        
        with self.engine.connect() as conn:
            for query_name, query in queries:
                # Measure query execution time
                start_time = time.time()
                result = conn.execute(text(query))
                rows = result.fetchall()
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # Convert to ms
                
                print(f"{query_name:<30}: {execution_time:>6.2f}ms ({len(rows)} rows)")
    
    def check_index_usage(self):
        """Check index usage and effectiveness."""
        logger.info("📇 Checking index usage...")
        
        # Fix: Use correct PostgreSQL system catalog columns
        index_usage_query = """
        SELECT 
            schemaname,
            relname as tablename,
            indexrelname as indexname,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes 
        WHERE schemaname = 'public'
        ORDER BY relname, indexrelname;
        """
        
        missing_indexes_query = """
        SELECT 
            schemaname,
            relname as tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            idx_tup_fetch
        FROM pg_stat_user_tables 
        WHERE schemaname = 'public';
        """
        
        with self.engine.connect() as conn:
            # Check index usage
            result = conn.execute(text(index_usage_query))
            indexes = result.fetchall()
            
            print("\n📇 Index Usage Statistics:")
            print("-" * 80)
            print(f"{'Table':<20} {'Index':<30} {'Reads':<10} {'Fetches':<10}")
            print("-" * 80)
            
            for schema, table, index, reads, fetches in indexes:
                print(f"{table:<20} {index:<30} {reads:<10} {fetches:<10}")
            
            # Check table scan statistics
            result = conn.execute(text(missing_indexes_query))
            tables = result.fetchall()
            
            print("\n🔍 Table Scan vs Index Scan Ratio:")
            print("-" * 60)
            print(f"{'Table':<20} {'Seq Scans':<12} {'Index Scans':<12} {'Ratio':<10}")
            print("-" * 60)
            
            for schema, table, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch in tables:
                total_scans = seq_scan + (idx_scan or 0)
                if total_scans > 0:
                    seq_ratio = (seq_scan / total_scans) * 100
                    print(f"{table:<20} {seq_scan:<12} {idx_scan or 0:<12} {seq_ratio:>6.1f}%")
    
    def suggest_optimizations(self):
        """Suggest database optimizations."""
        logger.info("💡 Generating optimization suggestions...")
        
        suggestions = []
        
        with self.engine.connect() as conn:
            # Check for missing indexes on frequently queried columns
            frequent_where_conditions = [
                ("current_weather", "location", "Frequently filtered by location"),
                ("current_weather", "timestamp", "Frequently filtered by time range"),
                ("weather_forecasts", "location", "Frequently filtered by location"),
                ("weather_forecasts", "forecast_date", "Frequently filtered by date"),
                ("disaster_alerts", "status", "Frequently filtered by status"),
                ("disaster_alerts", "alert_type", "Frequently filtered by type")
            ]
            
            # Check if composite indexes might be beneficial
            composite_suggestions = [
                ("current_weather", "location, timestamp", "For location + time range queries"),
                ("weather_forecasts", "location, forecast_date", "For location + date queries"),
                ("disaster_alerts", "status, alert_type", "For status + type queries")
            ]
            
            print("\n💡 Optimization Suggestions:")
            print("-" * 60)
            
            print("\n🔍 Consider these additional indexes:")
            for table, columns, reason in composite_suggestions:
                print(f"  CREATE INDEX idx_{table}_{columns.replace(', ', '_').replace(',', '_')} ")
                print(f"  ON {table} ({columns}); -- {reason}")
            
            print("\n⚡ Query Optimization Tips:")
            tips = [
                "Use LIMIT when querying large result sets",
                "Use specific column names instead of SELECT *",
                "Consider partitioning tables if they grow very large (>1M rows)",
                "Use EXPLAIN ANALYZE to identify slow queries",
                "Consider materialized views for complex aggregations",
                "Regularly run VACUUM and ANALYZE on tables"
            ]
            
            for i, tip in enumerate(tips, 1):
                print(f"  {i}. {tip}")
    
    def run_maintenance_tasks(self):
        """Run database maintenance tasks."""
        logger.info("🧹 Running database maintenance...")
        
        maintenance_queries = [
            ("Updating table statistics", "ANALYZE;"),
            ("Cleaning up dead tuples", "VACUUM;")
        ]
        
        print("\n🧹 Database Maintenance:")
        print("-" * 40)
        
        with self.engine.connect() as conn:
            for task_name, query in maintenance_queries:
                try:
                    start_time = time.time()
                    conn.execute(text(query))
                    conn.commit()
                    end_time = time.time()
                    
                    print(f"✅ {task_name}: {(end_time - start_time)*1000:.2f}ms")
                except Exception as e:
                    print(f"❌ {task_name}: Error - {e}")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report."""
        print("🚀 WeatherWise Database Performance Report")
        print("=" * 60)
        
        self.analyze_table_sizes()
        self.analyze_query_performance()
        self.check_index_usage()
        self.suggest_optimizations()
        self.run_maintenance_tasks()
        
        print(f"\n✅ Performance analysis complete!")
        print(f"📊 Review the suggestions above to optimize your database")


if __name__ == "__main__":
    optimizer = DatabaseOptimizer()
    optimizer.generate_performance_report()