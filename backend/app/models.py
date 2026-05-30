"""SQLAlchemy ORM models for BrandPulse."""
from datetime import datetime
from app.extensions import db


class Brand(db.Model):
    """D2C brand entity."""
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)       # fashion, lifestyle, footwear
    launch_date = db.Column(db.Date, nullable=False)
    region = db.Column(db.String(100), nullable=False)

    sales_records = db.relationship(
        'SalesRecord', backref='brand', lazy='dynamic', cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'launch_date': self.launch_date.isoformat() if self.launch_date else None,
            'region': self.region,
        }


class SalesRecord(db.Model):
    """Individual sales record tied to a brand, date, and platform."""
    __tablename__ = 'sales_records'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    units_sold = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(50), nullable=False)        # Amazon, Flipkart, Direct
    return_rate = db.Column(db.Float, default=0.0)
    revenue_per_unit = db.Column(db.Float)
    is_anomalous = db.Column(db.Boolean, default=False)
    ingestion_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('brand_id', 'date', 'platform', name='uq_brand_date_platform'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'date': self.date.isoformat() if self.date else None,
            'revenue': self.revenue,
            'units_sold': self.units_sold,
            'platform': self.platform,
            'return_rate': self.return_rate,
            'revenue_per_unit': self.revenue_per_unit,
            'is_anomalous': self.is_anomalous,
            'ingestion_timestamp': self.ingestion_timestamp.isoformat() if self.ingestion_timestamp else None,
        }


class ETLLog(db.Model):
    """Tracks each ETL pipeline execution."""
    __tablename__ = 'etl_logs'

    id = db.Column(db.Integer, primary_key=True)
    run_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    records_processed = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')      # success, failed, running
    error_message = db.Column(db.Text, nullable=True)
    anomalies_detected = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'run_timestamp': self.run_timestamp.isoformat() if self.run_timestamp else None,
            'records_processed': self.records_processed,
            'status': self.status,
            'error_message': self.error_message,
            'anomalies_detected': self.anomalies_detected,
            'duration_seconds': self.duration_seconds,
        }


class ChatRoom(db.Model):
    """Chat room for brand discussions and alerts."""
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)
    room_type = db.Column(db.String(20))  # brand / general / alerts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('ChatMessage', backref='room', lazy='dynamic')
    brand = db.relationship('Brand', backref='chat_rooms')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand_id': self.brand_id,
            'room_type': self.room_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ChatMessage(db.Model):
    """Individual message in a chat room."""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_name = db.Column(db.String(100))
    sender_type = db.Column(db.String(20))  # user / bot / system
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')
    # text / anomaly_alert / etl_complete / kpi_update
    metadata_json = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'sender_name': self.sender_name,
            'sender_type': self.sender_type,
            'content': self.content,
            'message_type': self.message_type,
            'metadata_json': self.metadata_json,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

