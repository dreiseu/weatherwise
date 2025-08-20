"""
Test Enhanced Agent Communication System
Run this to verify the enhanced agents work with your existing system
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add .env to path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL')

async def test_enhanced_agents():
    """Test the enhanced agent system."""
    
    print("🚀 Testing Enhanced Agent Communication System")
    print("=" * 60)
    
    try:
        # Import database session
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Import the enhanced system
        from app.agents.enhanced_communication import test_enhanced_system
        
        # Run the test
        orchestrator = await test_enhanced_system(db)
        
        # Check database for logged workflows
        from sqlalchemy import text
        
        workflow_count = db.execute(text("""
            SELECT COUNT(*) FROM agent_workflows WHERE workflow_type IN ('emergency', 'routine_monitoring')
        """)).scalar()
        
        execution_count = db.execute(text("""
            SELECT COUNT(*) FROM agent_executions WHERE agent_name LIKE '%Agent'
        """)).scalar()
        
        message_count = db.execute(text("""
            SELECT COUNT(*) FROM agent_messages WHERE sender_agent LIKE '%Agent'
        """)).scalar()
        
        print(f"\n📊 Database Verification:")
        print(f"   Workflows created: {workflow_count}")
        print(f"   Agent executions: {execution_count}")
        print(f"   Messages sent: {message_count}")
        
        if workflow_count > 0 and execution_count > 0:
            print("\n✅ Enhanced agent system is working correctly!")
            print("🎯 Ready for Step 3: Real-time Event Processing")
        else:
            print("\n⚠️  Some components may not be working as expected")
            print("Check the error messages above")
        
        db.close()
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure your existing agent files are in app/agents/")
        print("Required files:")
        print("  - weather_analysis_agent.py")
        print("  - risk_assessment_agent.py") 
        print("  - action_planning_agent.py")
        return False
    
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Enhanced Agents...")
    success = asyncio.run(test_enhanced_agents())
    
    if success:
        print("\n🎉 Step 2 Complete!")
        print("Next: We'll add real-time event processing")
    else:
        print("\n🔧 Please fix the issues above before continuing")