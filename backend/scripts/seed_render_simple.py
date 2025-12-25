"""
Simple script to seed Render database with sample data for testing.
This creates minimal data so the API endpoints work.
"""

import os
from sqlalchemy import create_engine, text

# Render database URL
RENDER_DB = "postgresql://startsmart_user:Tzlv9hzTwd2IVFV6SZmiWCl7LjmBjYpU@dpg-d4rf0r24i8rc738dcvig-a.oregon-postgres.render.com/startsmart_dev"

def seed_minimal_data():
    """Seed with minimal test data."""
    
    print("🌱 Seeding Render database with minimal data...")
    
    engine = create_engine(RENDER_DB)
    
    with engine.connect() as conn:
        
        # Create tables first
        print("\n📋 Creating tables...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_cells (
                grid_id VARCHAR(50) PRIMARY KEY,
                neighborhood VARCHAR(100),
                lat_center DECIMAL(10, 7),
                lon_center DECIMAL(10, 7),
                lat_north DECIMAL(10, 7),
                lat_south DECIMAL(10, 7),
                lon_east DECIMAL(10, 7),
                lon_west DECIMAL(10, 7),
                area_km2 DECIMAL(5, 2) DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS businesses (
                business_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255),
                lat DECIMAL(10, 7),
                lon DECIMAL(10, 7),
                category VARCHAR(50),
                rating DECIMAL(2, 1),
                grid_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
        print("✅ Tables created")
        
        # Insert sample grid in Clifton
        print("\n📍 Inserting sample grid...")
        conn.execute(text("""
            INSERT INTO grid_cells (grid_id, neighborhood, lat_center, lon_center, lat_north, lat_south, lon_east, lon_west)
            VALUES ('CLIFTON_001', 'Clifton', 24.8138, 67.0299, 24.8143, 24.8133, 67.0304, 67.0294)
            ON CONFLICT (grid_id) DO NOTHING
        """))
        conn.commit()
        
        # Insert sample businesses
        print("\n🏢 Inserting sample businesses...")
        conn.execute(text("""
            INSERT INTO businesses (business_id, name, lat, lon, category, rating, grid_id)
            VALUES 
                ('BIZ_GYM_001', 'Sample Gym', 24.8138, 67.0299, 'Gym', 4.5, 'CLIFTON_001'),
                ('BIZ_CAFE_001', 'Sample Cafe', 24.8140, 67.0300, 'Cafe', 4.2, 'CLIFTON_001')
            ON CONFLICT (business_id) DO NOTHING
        """))
        conn.commit()
        
        # Verify
        grid_count = conn.execute(text("SELECT COUNT(*) FROM grid_cells")).scalar()
        biz_count = conn.execute(text("SELECT COUNT(*) FROM businesses")).scalar()
        
        print(f"\n✅ Seeding complete!")
        print(f"   Grids: {grid_count}")
        print(f"   Businesses: {biz_count}")
        print(f"\n🌐 Test: https://startsmart-api.onrender.com/api/v1/neighborhoods")

if __name__ == "__main__":
    seed_minimal_data()
