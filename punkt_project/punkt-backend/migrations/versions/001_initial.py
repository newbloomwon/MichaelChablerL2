"""Initial schema with partitioning and RLS

Revision ID: 001
Revises: 
Create Date: 2025-02-07 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create partition management function
    op.execute("""
    CREATE OR REPLACE FUNCTION create_monthly_partition(target_date DATE)
    RETURNS void AS $$
    DECLARE
        partition_name TEXT;
        start_date DATE;
        end_date DATE;
    BEGIN
        start_date := date_trunc('month', target_date);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'log_entries_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF log_entries
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 2. Create log_entries partitioned table
    op.execute("""
    CREATE TABLE log_entries (
        id BIGSERIAL,
        timestamp TIMESTAMPTZ NOT NULL,
        tenant_id VARCHAR(50) NOT NULL,
        source VARCHAR(100),
        level VARCHAR(20),
        message TEXT,
        raw_log TEXT,
        metadata JSONB,
        indexed_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (id, timestamp)
    ) PARTITION BY RANGE (timestamp);
    """)

    # 3. Create initial partitions
    op.execute("SELECT create_monthly_partition(CURRENT_DATE);")
    op.execute("SELECT create_monthly_partition((CURRENT_DATE + INTERVAL '1 month')::DATE);")
    op.execute("SELECT create_monthly_partition((CURRENT_DATE + INTERVAL '2 months')::DATE);")
    
    # 4. Create default partition
    op.execute("CREATE TABLE log_entries_default PARTITION OF log_entries DEFAULT;")

    # 5. Enable RLS
    op.execute("ALTER TABLE log_entries ENABLE ROW LEVEL SECURITY;")
    op.execute("""
    CREATE POLICY tenant_isolation_policy ON log_entries
    FOR ALL USING (tenant_id = current_setting('app.current_tenant', true));
    """)

    # 6. Create indexes
    op.execute("CREATE INDEX idx_log_entries_timestamp ON log_entries (timestamp DESC);")
    op.execute("CREATE INDEX idx_log_entries_tenant_time ON log_entries (tenant_id, timestamp DESC);")
    op.execute("CREATE INDEX idx_log_entries_level ON log_entries (level);")
    op.execute("CREATE INDEX idx_log_entries_source ON log_entries (source);")
    op.execute("CREATE INDEX idx_log_entries_metadata ON log_entries USING GIN (metadata);")

    # 7. Create users table for auth
    op.create_table(
        'users',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Insert a demo user (password: demo123, hashed)
    # Using passlib.hash.bcrypt.hash("demo123") -> $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31S.
    op.execute("""
    INSERT INTO users (id, username, password_hash, tenant_id)
    VALUES ('user_demo', 'demo@acme.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31S.', 'tenant_acme')
    """)

def downgrade():
    op.drop_table('users')
    op.execute("DROP TABLE log_entries;")
    op.execute("DROP FUNCTION create_monthly_partition(DATE);")
