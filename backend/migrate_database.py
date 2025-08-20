"""
Database Schema Migration for Enhanced Agent System
Add the necessary tables for agent workflows and communication
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

# Add .env to path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_migration():
    """Execute the database migration for enhanced agent system."""
    
    print("🗄️  WeatherWise Agent System - Database Migration")
    print("=" * 60)
    
    # Database connection
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise')
    
    try:
        engine = create_engine(DATABASE_URL)
        
        print("📡 Connecting to database...")
        
        with engine.connect() as connection:
            print("✅ Database connection established")
            
            # Check if tables already exist
            existing_tables = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN (
                    'agent_executions', 'agent_workflows', 'agent_messages', 
                    'realtime_events', 'agent_performance_metrics', 'agent_configurations'
                )
            """)).fetchall()
            
            if existing_tables:
                print(f"⚠️  Found {len(existing_tables)} existing agent tables")
                response = input("Do you want to continue? This will create missing tables only. (y/n): ")
                if response.lower() != 'y':
                    print("❌ Migration cancelled")
                    return False
            
            print("\n🏗️  Creating agent system tables...")
            
            # Execute migration SQL
            migration_sql = """
            -- Agent execution tracking table
            CREATE TABLE IF NOT EXISTS agent_executions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_name VARCHAR(100) NOT NULL,
                execution_type VARCHAR(50) NOT NULL,
                workflow_id UUID,
                input_data JSONB NOT NULL,
                output_data JSONB,
                execution_status VARCHAR(20) CHECK (execution_status IN ('running', 'completed', 'failed', 'timeout')),
                execution_time_ms INTEGER,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            );

            -- Agent workflows table
            CREATE TABLE IF NOT EXISTS agent_workflows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_type VARCHAR(50) NOT NULL,
                initiator VARCHAR(100) NOT NULL,
                status VARCHAR(20) CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                context JSONB NOT NULL,
                agents_involved TEXT[] DEFAULT '{}',
                location VARCHAR(255),
                priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                started_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ,
                total_execution_time_ms INTEGER
            );

            -- Agent messages/communication table
            CREATE TABLE IF NOT EXISTS agent_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                message_type VARCHAR(50) NOT NULL,
                sender_agent VARCHAR(100) NOT NULL,
                recipient_agent VARCHAR(100) NOT NULL,
                workflow_id UUID,
                correlation_id UUID,
                payload JSONB NOT NULL,
                priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                status VARCHAR(20) CHECK (status IN ('sent', 'delivered', 'processed', 'failed')),
                sent_at TIMESTAMPTZ DEFAULT NOW(),
                processed_at TIMESTAMPTZ
            );

            -- Real-time events table
            CREATE TABLE IF NOT EXISTS realtime_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type VARCHAR(50) NOT NULL,
                location VARCHAR(255) NOT NULL,
                severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'critical', 'emergency')),
                event_data JSONB NOT NULL,
                triggered_by VARCHAR(100),
                auto_resolved BOOLEAN DEFAULT FALSE,
                expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ
            );

            -- Agent performance metrics table
            CREATE TABLE IF NOT EXISTS agent_performance_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_name VARCHAR(100) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(10, 4) NOT NULL,
                measurement_period TSTZRANGE NOT NULL,
                location VARCHAR(255),
                workflow_type VARCHAR(50),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            -- Agent configuration table
            CREATE TABLE IF NOT EXISTS agent_configurations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_name VARCHAR(100) NOT NULL UNIQUE,
                configuration JSONB NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                version VARCHAR(20) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
            
            connection.execute(text(migration_sql))
            connection.commit()
            print("✅ Agent system tables created")
            
            # Create indexes
            print("🔍 Creating performance indexes...")
            
            index_sql = """
            -- Indexes for performance optimization
            CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_name ON agent_executions(agent_name);
            CREATE INDEX IF NOT EXISTS idx_agent_executions_workflow_id ON agent_executions(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_agent_executions_created_at ON agent_executions(created_at);
            CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(execution_status);

            CREATE INDEX IF NOT EXISTS idx_agent_workflows_type ON agent_workflows(workflow_type);
            CREATE INDEX IF NOT EXISTS idx_agent_workflows_status ON agent_workflows(status);
            CREATE INDEX IF NOT EXISTS idx_agent_workflows_location ON agent_workflows(location);
            CREATE INDEX IF NOT EXISTS idx_agent_workflows_priority ON agent_workflows(priority);
            CREATE INDEX IF NOT EXISTS idx_agent_workflows_started_at ON agent_workflows(started_at);

            CREATE INDEX IF NOT EXISTS idx_agent_messages_workflow_id ON agent_messages(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_agent_messages_sender ON agent_messages(sender_agent);
            CREATE INDEX IF NOT EXISTS idx_agent_messages_recipient ON agent_messages(recipient_agent);
            CREATE INDEX IF NOT EXISTS idx_agent_messages_type ON agent_messages(message_type);
            CREATE INDEX IF NOT EXISTS idx_agent_messages_sent_at ON agent_messages(sent_at);

            CREATE INDEX IF NOT EXISTS idx_realtime_events_type ON realtime_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_realtime_events_location ON realtime_events(location);
            CREATE INDEX IF NOT EXISTS idx_realtime_events_severity ON realtime_events(severity);
            CREATE INDEX IF NOT EXISTS idx_realtime_events_created_at ON realtime_events(created_at);
            CREATE INDEX IF NOT EXISTS idx_realtime_events_expires_at ON realtime_events(expires_at);

            CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_name ON agent_performance_metrics(agent_name);
            CREATE INDEX IF NOT EXISTS idx_agent_performance_metric_name ON agent_performance_metrics(metric_name);
            """
            
            connection.execute(text(index_sql))
            connection.commit()
            print("✅ Performance indexes created")
            
            # Add columns to existing tables
            print("🔧 Enhancing existing tables...")
            
            enhancement_sql = """
            -- Enhanced disaster alerts with agent integration
            ALTER TABLE disaster_alerts ADD COLUMN IF NOT EXISTS triggered_by_agent VARCHAR(100);
            ALTER TABLE disaster_alerts ADD COLUMN IF NOT EXISTS agent_workflow_id UUID;
            ALTER TABLE disaster_alerts ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(4, 3);
            ALTER TABLE disaster_alerts ADD COLUMN IF NOT EXISTS auto_generated BOOLEAN DEFAULT FALSE;

            -- Enhanced risk assessments with agent tracking
            ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS generated_by_agent VARCHAR(100);
            ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS agent_execution_id UUID;
            ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS model_version VARCHAR(50);
            ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS validation_status VARCHAR(20) DEFAULT 'pending';
            """
            
            connection.execute(text(enhancement_sql))
            connection.commit()
            print("✅ Existing tables enhanced")
            
            # Create helper functions
            print("⚙️  Creating helper functions...")
            
            function_sql = """
            -- Function to start agent workflow
            CREATE OR REPLACE FUNCTION start_agent_workflow(
                p_workflow_type VARCHAR(50),
                p_initiator VARCHAR(100),
                p_context JSONB,
                p_location VARCHAR(255) DEFAULT NULL,
                p_priority INTEGER DEFAULT 3
            ) RETURNS UUID AS $$
            DECLARE
                workflow_id UUID;
            BEGIN
                INSERT INTO agent_workflows (workflow_type, initiator, context, location, priority, status)
                VALUES (p_workflow_type, p_initiator, p_context, p_location, p_priority, 'pending')
                RETURNING id INTO workflow_id;
                
                RETURN workflow_id;
            END;
            $$ LANGUAGE plpgsql;

            -- Function to complete agent workflow
            CREATE OR REPLACE FUNCTION complete_agent_workflow(
                p_workflow_id UUID,
                p_status VARCHAR(20) DEFAULT 'completed'
            ) RETURNS VOID AS $$
            BEGIN
                UPDATE agent_workflows 
                SET 
                    status = p_status,
                    completed_at = NOW(),
                    total_execution_time_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
                WHERE id = p_workflow_id;
            END;
            $$ LANGUAGE plpgsql;

            -- Function to log agent execution
            CREATE OR REPLACE FUNCTION log_agent_execution(
                p_agent_name VARCHAR(100),
                p_execution_type VARCHAR(50),
                p_workflow_id UUID,
                p_input_data JSONB,
                p_output_data JSONB DEFAULT NULL,
                p_execution_status VARCHAR(20) DEFAULT 'completed',
                p_execution_time_ms INTEGER DEFAULT NULL,
                p_error_message TEXT DEFAULT NULL
            ) RETURNS UUID AS $$
            DECLARE
                execution_id UUID;
            BEGIN
                INSERT INTO agent_executions (
                    agent_name, execution_type, workflow_id, input_data, 
                    output_data, execution_status, execution_time_ms, error_message, completed_at
                )
                VALUES (
                    p_agent_name, p_execution_type, p_workflow_id, p_input_data,
                    p_output_data, p_execution_status, p_execution_time_ms, p_error_message,
                    CASE WHEN p_execution_status IN ('completed', 'failed') THEN NOW() ELSE NULL END
                )
                RETURNING id INTO execution_id;
                
                RETURN execution_id;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            connection.execute(text(function_sql))
            connection.commit()
            print("✅ Helper functions created")
            
            # Insert default agent configurations
            print("⚙️  Inserting default agent configurations...")
            
            config_sql = """
            INSERT INTO agent_configurations (agent_name, configuration, version) VALUES
            ('WeatherAnalysisAgent', '{
                "analysis_types": ["patterns", "anomalies", "trends"],
                "default_time_range_days": 7,
                "confidence_threshold": 0.7,
                "max_execution_time_seconds": 120
            }', '1.0'),
            ('RiskAssessmentAgent', '{
                "risk_categories": ["typhoon", "flooding", "heat_stress", "general_weather"],
                "default_forecast_hours": 24,
                "risk_thresholds": {
                    "typhoon": {"wind_speed": [40, 60, 90, 120], "pressure_drop": [5, 10, 15, 25]},
                    "flooding": {"humidity": [70, 80, 90, 95], "rainfall_intensity": [10, 25, 50, 100]},
                    "heat": {"temperature": [32, 35, 38, 42], "heat_index": [32, 40, 52, 54]}
                }
            }', '1.0'),
            ('ActionPlanningAgent', '{
                "action_categories": ["immediate", "short_term", "coordination"],
                "resource_types": ["personnel", "equipment", "facilities", "transportation"],
                "priority_levels": [1, 2, 3, 4, 5],
                "coordination_threshold": "HIGH"
            }', '1.0'),
            ('ReportGenerationAgent', '{
                "report_types": ["executive", "technical", "operational"],
                "default_sections": ["executive_summary", "risk_assessment", "recommendations"],
                "output_formats": ["pdf", "json", "html"],
                "max_report_generation_time_seconds": 300
            }', '1.0')
            ON CONFLICT (agent_name) DO NOTHING;
            """
            
            connection.execute(text(config_sql))
            connection.commit()
            print("✅ Default agent configurations inserted")
            
            # Verify migration
            print("\n🔍 Verifying migration...")
            
            tables_check = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE '%agent%'
                ORDER BY table_name
            """)).fetchall()
            
            print(f"✅ Created {len(tables_check)} agent-related tables:")
            for table in tables_check:
                print(f"   - {table[0]}")
            
            # Check configurations
            config_count = connection.execute(text("""
                SELECT COUNT(*) FROM agent_configurations WHERE is_active = true
            """)).scalar()
            
            print(f"✅ Inserted {config_count} agent configurations")
            
        print(f"\n🎉 Migration completed successfully!")
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify that migration was successful."""
    
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise')
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Test helper functions
            workflow_id = connection.execute(text("""
                SELECT start_agent_workflow('test', 'migration_test', '{"test": true}', 'Test Location', 3)
            """)).scalar()
            
            if workflow_id:
                print(f"✅ Helper functions working - test workflow created: {workflow_id}")
                
                # Clean up test data
                connection.execute(text("""
                    DELETE FROM agent_workflows WHERE id = :workflow_id
                """), {"workflow_id": workflow_id})
                connection.commit()
                
                return True
            else:
                print("❌ Helper functions not working properly")
                return False
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting WeatherWise Agent System Database Migration...")
    print("Make sure your PostgreSQL database is running!")
    print()
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set it to: postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise")
        sys.exit(1)
    
    # Run migration
    success = run_migration()
    
    if success:
        print("\n🧪 Running verification tests...")
        verification_success = verify_migration()
        
        if verification_success:
            print("\n✅ ALL CHECKS PASSED!")
            print("🚀 Your database is ready for the enhanced agent system!")
            print("\nNext steps:")
            print("1. Run the agent system tests")
            print("2. Update your existing agents to use the new features")
            print("3. Test the enhanced communication system")
        else:
            print("\n⚠️  Migration completed but verification failed")
            print("Please check the database manually")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again")
        sys.exit(1)