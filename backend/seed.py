"""
Seed script — generates 10 realistic D2C brands, 2,000 sales records, and chat rooms.

Called by entrypoint.sh on container start. Only seeds if the brands table is empty,
so it's safe to run multiple times (idempotent).
"""
import os
import sys
import csv
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models import Brand, SalesRecord, ChatRoom, ChatMessage

# -- Brand seed data --
BRANDS = [
    {"name": "UrbanWeave", "category": "fashion", "region": "North India"},
    {"name": "SoleStrike", "category": "footwear", "region": "West India"},
    {"name": "AuraLiving", "category": "lifestyle", "region": "South India"},
    {"name": "ThreadCraft", "category": "fashion", "region": "East India"},
    {"name": "StrideX", "category": "footwear", "region": "Pan India"},
    {"name": "ZenNest", "category": "lifestyle", "region": "North India"},
    {"name": "VogueFlare", "category": "fashion", "region": "West India"},
    {"name": "TrailBlaze", "category": "footwear", "region": "South India"},
    {"name": "PureEssence", "category": "lifestyle", "region": "Pan India"},
    {"name": "NovaStitch", "category": "fashion", "region": "East India"},
]

PLATFORMS = ["Amazon", "Flipkart", "Direct"]


def generate_sales_records(brands, count=2000):
    """Generate realistic fake sales records with unique constraints."""
    records = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 1)
    date_range = (end_date - start_date).days
    seen = set()

    attempts = 0
    while len(records) < count and attempts < count * 5:
        attempts += 1
        brand = random.choice(brands)
        date = (start_date + timedelta(days=random.randint(0, date_range))).date()
        platform = random.choice(PLATFORMS)

        key = (brand.id, date, platform)
        if key in seen:
            continue
        seen.add(key)

        units_sold = random.randint(5, 500)
        base_price = {"fashion": 1200, "footwear": 2500, "lifestyle": 800}
        price = base_price.get(brand.category, 1000)
        revenue = round(units_sold * price * random.uniform(0.6, 1.4), 2)
        return_rate = round(random.uniform(0.01, 0.45), 4)
        revenue_per_unit = round(revenue / units_sold, 2) if units_sold > 0 else 0
        is_anomalous = return_rate > 0.3

        records.append({
            "brand_id": brand.id,
            "date": date,
            "revenue": revenue,
            "units_sold": units_sold,
            "platform": platform,
            "return_rate": return_rate,
            "revenue_per_unit": revenue_per_unit,
            "is_anomalous": is_anomalous,
            "ingestion_timestamp": datetime.utcnow(),
        })

    return records


def write_seed_csv(records, brands_map):
    """Write seed data to CSV for future ETL pipeline runs."""
    csv_dir = os.path.join(os.path.dirname(__file__), 'data', 'raw')
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = os.path.join(csv_dir, 'seed_sales_data.csv')

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'brand_id', 'date', 'revenue', 'units_sold',
            'platform', 'return_rate'
        ])
        writer.writeheader()
        for r in records:
            writer.writerow({
                'brand_id': r['brand_id'],
                'date': r['date'],
                'revenue': r['revenue'],
                'units_sold': r['units_sold'],
                'platform': r['platform'],
                'return_rate': r['return_rate'],
            })

    print(f"  Wrote {len(records)} records to {csv_path}")


def seed_chat_rooms(brands):
    """Create default chat rooms and welcome messages."""
    if ChatRoom.query.first():
        print("  Chat rooms already seeded -- skipping.")
        return

    print("  Seeding chat rooms...")

    # General rooms
    general_room = ChatRoom(name="General", room_type="general")
    alerts_room = ChatRoom(name="ETL Alerts", room_type="alerts")
    db.session.add_all([general_room, alerts_room])
    db.session.flush()

    # Brand rooms for first 5 brands
    for brand in brands[:5]:
        room = ChatRoom(
            name=f"{brand.name} -- Analytics",
            brand_id=brand.id,
            room_type="brand",
        )
        db.session.add(room)

    db.session.flush()

    # Seed welcome messages
    for room in ChatRoom.query.all():
        msg = ChatMessage(
            room_id=room.id,
            sender_name="System",
            sender_type="system",
            content=f"Welcome to {room.name}. BrandBot is ready -- type @bot to ask questions.",
            message_type="text",
        )
        db.session.add(msg)

    db.session.commit()
    print(f"  Seeded {ChatRoom.query.count()} chat rooms with welcome messages.")


def seed():
    """Main seed function -- idempotent."""
    app = create_app()
    with app.app_context():
        # Check if already seeded
        if Brand.query.first():
            print("  Database already seeded -- skipping brands/sales.")
            # Still seed chat rooms if missing
            seed_chat_rooms(Brand.query.all())
            return

        print("  Seeding brands...")
        brands = []
        for b in BRANDS:
            brand = Brand(
                name=b["name"],
                category=b["category"],
                launch_date=datetime(
                    random.randint(2018, 2023),
                    random.randint(1, 12),
                    random.randint(1, 28)
                ).date(),
                region=b["region"],
            )
            db.session.add(brand)
            brands.append(brand)

        db.session.flush()  # Get IDs assigned

        print("  Generating 2,000 sales records...")
        records = generate_sales_records(brands, count=2000)

        # Write CSV for ETL pipeline
        brands_map = {b.id: b.name for b in brands}
        write_seed_csv(records, brands_map)

        # Insert directly into DB
        for r in records:
            db.session.add(SalesRecord(**r))

        db.session.commit()
        print(f"  Seeded {len(brands)} brands and {len(records)} sales records.")

        # Seed chat rooms
        seed_chat_rooms(brands)


if __name__ == '__main__':
    seed()
