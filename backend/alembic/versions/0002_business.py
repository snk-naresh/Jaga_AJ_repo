"""customers, items, inventory, notifications, and audit log"""
from alembic import op
import sqlalchemy as sa

revision = "0002_business"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("customers", sa.Column("alternate_phone", sa.String(20)))
    op.add_column("customers", sa.Column("email", sa.String(180)))
    op.add_column("customers", sa.Column("address", sa.Text))
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("low_stock_threshold", sa.Integer, nullable=False, server_default="2"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("weight", sa.String(40)),
        sa.Column("purity", sa.String(40)),
        sa.Column("price", sa.Float),
        sa.Column("image_key", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_inventory_items_category", "inventory_items", ["category"])
    op.add_column("order_items", sa.Column("quantity", sa.Integer, nullable=False, server_default="1"))
    op.add_column("order_items", sa.Column("estimated_value", sa.Float))
    op.add_column("order_items", sa.Column("expected_date", sa.Date))
    op.add_column("order_items", sa.Column("ready_at", sa.DateTime(timezone=True)))
    op.add_column("order_items", sa.Column("inventory_item_id", sa.Integer, sa.ForeignKey("inventory_items.id")))
    op.add_column("order_items", sa.Column("stock_state", sa.String(20), nullable=False, server_default="NONE"))
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.add_column("notifications", sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.id")))
    op.add_column("notifications", sa.Column("notification_type", sa.String(40), nullable=False, server_default="ITEM_READY"))
    op.add_column("notifications", sa.Column("message", sa.Text))
    op.add_column("notifications", sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"))
    op.alter_column("notifications", "order_item_id", existing_type=sa.Integer, nullable=True)
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("entity", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.String(40), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("details", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.alter_column("notifications", "order_item_id", existing_type=sa.Integer, nullable=False)
    op.drop_column("notifications", "retry_count")
    op.drop_column("notifications", "message")
    op.drop_column("notifications", "notification_type")
    op.drop_column("notifications", "order_id")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_column("order_items", "stock_state")
    op.drop_column("order_items", "inventory_item_id")
    op.drop_column("order_items", "ready_at")
    op.drop_column("order_items", "expected_date")
    op.drop_column("order_items", "estimated_value")
    op.drop_column("order_items", "quantity")
    op.drop_index("ix_inventory_items_category", table_name="inventory_items")
    op.drop_table("inventory_items")
    op.drop_column("customers", "address")
    op.drop_column("customers", "email")
    op.drop_column("customers", "alternate_phone")
