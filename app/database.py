"""Portable SQLAlchemy schema: SQLite locally, PostgreSQL/Supabase when hosted."""
from datetime import datetime, timezone
from sqlalchemy import (MetaData, Table, Column, String, Integer, Float, JSON,
                        ForeignKey, CheckConstraint, create_engine, event, text)
metadata = MetaData()
households = Table('households', metadata,
    Column('id', String, primary_key=True), Column('revision', Integer, nullable=False, default=0),
    Column('preferences', JSON, nullable=False))
plans = Table('plans', metadata,
    Column('id', String, primary_key=True), Column('household_id', String, ForeignKey('households.id'), nullable=False),
    Column('created_at', String, nullable=False), Column('opening_revision', Integer, nullable=False),
    Column('parameters', JSON, nullable=False), Column('result', JSON, nullable=False),
    Column('receipts_confirmed', Integer, nullable=False, default=0),
    Column('archived', Integer, nullable=False, default=0),
    Column('meal_status', JSON, nullable=False))
batches = Table('inventory_batches', metadata,
    Column('id', String, primary_key=True), Column('household_id', String, ForeignKey('households.id'), nullable=False),
    Column('ingredient_id', String, nullable=False), Column('quantity', Float, nullable=False),
    Column('unit', String, nullable=False), Column('created_at', String, nullable=False),
    Column('expires_on', String), Column('source', String, nullable=False),
    CheckConstraint('quantity >= 0', name='nonnegative_batch_quantity'))
events = Table('inventory_events', metadata,
    Column('id', String, primary_key=True), Column('household_id', String, ForeignKey('households.id'), nullable=False),
    Column('created_at', String, nullable=False), Column('kind', String, nullable=False),
    Column('payload', JSON, nullable=False), Column('changes', JSON, nullable=False))

DEFAULTS = {'excluded_ingredients': [], 'excluded_recipes': [], 'avoid_previous_plan': False}

def now():
    return datetime.now(timezone.utc).isoformat()

def connect(url):
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    kwargs = {'connect_args': {'check_same_thread': False, 'timeout': 30}} if url.startswith('sqlite') else {'pool_pre_ping': True}
    engine = create_engine(url, **kwargs)
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def foreign_keys(dbapi, _):
            dbapi.execute('PRAGMA foreign_keys=ON')
    metadata.create_all(engine)
    with engine.begin() as conn:
        if engine.dialect.name == 'postgresql':
            # Supabase's public Data API must not expose household records.
            for table in metadata.sorted_tables:
                conn.execute(text(f'ALTER TABLE {table.name} ENABLE ROW LEVEL SECURITY'))
                conn.execute(text(f'REVOKE ALL ON TABLE {table.name} FROM PUBLIC'))
        if conn.execute(households.select()).first() is None:
            conn.execute(households.insert().values(id='home', revision=0, preferences=DEFAULTS))
    return engine
