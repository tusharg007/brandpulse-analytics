"""
Local development runner -- no Docker, no PostgreSQL, no Redis needed.
Uses SQLite for the database and skips Redis caching.
SocketIO runs in threading mode for local dev.
"""
import os
import sys

# Set environment for local SQLite mode
os.environ['DATABASE_URL'] = 'sqlite:///brandpulse_local.db'
os.environ['REDIS_URL'] = ''
os.environ['FLASK_ENV'] = 'development'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app
from app.extensions import db, socketio
from app.models import Brand, SalesRecord, ETLLog, ChatRoom, ChatMessage

app = create_app()

with app.app_context():
    # Create all tables directly (no Alembic needed for SQLite)
    db.create_all()
    print("[OK] Database tables created")

    # Seed if empty
    if not Brand.query.first():
        print("[SEED] Seeding database...")
        import random
        from datetime import datetime, timedelta

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

        brands = []
        for b in BRANDS:
            brand = Brand(
                name=b["name"], category=b["category"],
                launch_date=datetime(random.randint(2018, 2023), random.randint(1, 12), random.randint(1, 28)).date(),
                region=b["region"],
            )
            db.session.add(brand)
            brands.append(brand)
        db.session.flush()

        # Generate unique (brand_id, date, platform) combinations
        base_price = {"fashion": 1200, "footwear": 2500, "lifestyle": 800}
        start_date = datetime(2024, 1, 1)
        date_range = (datetime(2025, 6, 1) - start_date).days

        seen = set()
        count = 0
        attempts = 0

        while count < 2000 and attempts < 10000:
            attempts += 1
            brand = random.choice(brands)
            date = (start_date + timedelta(days=random.randint(0, date_range))).date()
            platform = random.choice(PLATFORMS)

            key = (brand.id, date, platform)
            if key in seen:
                continue
            seen.add(key)

            units_sold = random.randint(5, 500)
            revenue = round(units_sold * base_price.get(brand.category, 1000) * random.uniform(0.6, 1.4), 2)
            return_rate = round(random.uniform(0.01, 0.45), 4)

            db.session.add(SalesRecord(
                brand_id=brand.id, date=date, revenue=revenue,
                units_sold=units_sold, platform=platform,
                return_rate=return_rate,
                revenue_per_unit=round(revenue / units_sold, 2) if units_sold > 0 else 0,
                is_anomalous=return_rate > 0.3,
                ingestion_timestamp=datetime.utcnow(),
            ))
            count += 1

        db.session.commit()
        print(f"[OK] Seeded {len(brands)} brands and {count} sales records!")
    else:
        print("[OK] Database already seeded")

    # Seed chat rooms if missing
    if not ChatRoom.query.first():
        print("[SEED] Creating chat rooms...")
        general = ChatRoom(name="General", room_type="general")
        alerts = ChatRoom(name="ETL Alerts", room_type="alerts")
        db.session.add_all([general, alerts])
        db.session.flush()

        for brand in Brand.query.limit(5).all():
            room = ChatRoom(name=f"{brand.name} -- Analytics", brand_id=brand.id, room_type="brand")
            db.session.add(room)
        db.session.flush()

        for room in ChatRoom.query.all():
            msg = ChatMessage(
                room_id=room.id, sender_name="System", sender_type="system",
                content=f"Welcome to {room.name}. BrandBot is ready -- type @bot to ask questions.",
                message_type="text",
            )
            db.session.add(msg)
        db.session.commit()
        print(f"[OK] Seeded {ChatRoom.query.count()} chat rooms")
    else:
        print("[OK] Chat rooms already seeded")

print("")
print("=" * 50)
print("  BrandPulse API running at http://localhost:5000")
print("  WebSocket enabled (threading mode)")
print("  Health check: http://localhost:5000/api/health")
print("  Press Ctrl+C to stop")
print("=" * 50)
print("")

# Use socketio.run for WebSocket support
socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
