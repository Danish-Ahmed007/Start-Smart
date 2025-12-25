"""
Migrate data from local database to Render PostgreSQL.

Usage:
    python scripts/migrate_to_render.py
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Local database
LOCAL_DB = "postgresql://postgres:admin@localhost:5432/startsmart_dev"

# Render database (from environment or hardcoded)
RENDER_DB = os.getenv(
    "RENDER_DATABASE_URL",
    "postgresql://startsmart_user:Tzlv9hzTwd2IVFV6SZmiWCl7LjmBjYpU@dpg-d4rf0r24i8rc738dcvig-a.oregon-postgres.render.com/startsmart_dev"
)

def migrate_data():
    """Copy all data from local to Render database."""
    
    print("🔄 Starting migration to Render...")
    
    # Connect to both databases
    local_engine = create_engine(LOCAL_DB)
    render_engine = create_engine(RENDER_DB)
    
    LocalSession = sessionmaker(bind=local_engine)
    RenderSession = sessionmaker(bind=render_engine)
    
    try:
        with LocalSession() as local_session, RenderSession() as render_session:
            
            # 1. Create tables on Render
            print("\n📋 Creating tables on Render...")
            from src.database.connection import Base
            Base.metadata.create_all(bind=render_engine)
            print("✅ Tables created")
            
            # 2. Copy micro_grids
            print("\n📍 Migrating micro_grids...")
            grids = local_session.execute(text("SELECT * FROM micro_grids")).fetchall()
            print(f"   Found {len(grids)} grids in local DB")
            
            if grids:
                # Get column names
                columns = local_session.execute(text("SELECT * FROM micro_grids LIMIT 0")).keys()
                
                for grid in grids:
                    grid_dict = dict(zip(columns, grid))
                    # Insert into Render
                    insert_stmt = text(f"""
                        INSERT INTO micro_grids ({', '.join(columns)})
                        VALUES ({', '.join([f":{col}" for col in columns])})
                        ON CONFLICT (grid_id) DO NOTHING
                    """)
                    render_session.execute(insert_stmt, grid_dict)
                
                render_session.commit()
                print(f"✅ Migrated {len(grids)} grids")
            
            # 3. Copy businesses
            print("\n🏢 Migrating businesses...")
            businesses = local_session.execute(text("SELECT * FROM businesses")).fetchall()
            print(f"   Found {len(businesses)} businesses in local DB")
            
            if businesses:
                columns = local_session.execute(text("SELECT * FROM businesses LIMIT 0")).keys()
                
                for biz in businesses:
                    biz_dict = dict(zip(columns, biz))
                    insert_stmt = text(f"""
                        INSERT INTO businesses ({', '.join(columns)})
                        VALUES ({', '.join([f":{col}" for col in columns])})
                        ON CONFLICT (business_id) DO NOTHING
                    """)
                    render_session.execute(insert_stmt, biz_dict)
                
                render_session.commit()
                print(f"✅ Migrated {len(businesses)} businesses")
            
            # 4. Verify data on Render
            print("\n🔍 Verifying Render database...")
            grid_count = render_session.execute(text("SELECT COUNT(*) FROM micro_grids")).scalar()
            biz_count = render_session.execute(text("SELECT COUNT(*) FROM businesses")).scalar()
            
            print(f"   Render DB has {grid_count} grids")
            print(f"   Render DB has {biz_count} businesses")
            
            print("\n✅ Migration complete!")
            print(f"\n🌐 Test your API: https://startsmart-api.onrender.com/api/v1/neighborhoods")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_data()
