import pytest

from sqlalchemy import Float
from sqlalchemy.orm import mapped_column

from tests.defaults.conftest import ALEMBIC_CONFIG
from tests.defaults.flask_app import db, DynamicModificationModel
from tests.utils import run_alembic_command


@pytest.mark.usefixtures("test_client")
class TestAuditLoggerAlembicHooks:
    def test_initialize_file(self):
        with open(ALEMBIC_CONFIG / "versions" / "1_create.py") as f:
            migration_contents = f.read()

        parts = migration_contents.split("\n\n")
        upgrade = parts[-2]
        assert "def upgrade():" in upgrade
        assert "op.init_audit_logger_extension('btree_gist')" in upgrade
        assert (
            "op.init_audit_logger_schema()" not in upgrade
        )  # only present when separate schema configured
        assert "op.create_table('transaction'" in upgrade
        assert "op.create_table('activity'" in upgrade
        assert (
            "op.create_index(op.f('ix_activity_native_transaction_id'), 'activity', ['native_transaction_id'], unique=False)"
            in upgrade
        )
        assert (
            "op.init_audit_logger_function('get_setting(setting text, fallback text)')" in upgrade
        )
        assert "op.init_audit_logger_function('jsonb_subtract(arg1 jsonb, arg2 jsonb)')" in upgrade
        assert (
            "op.init_audit_logger_function('jsonb_change_key_name(data jsonb, old_key text, new_key text)')"
            in upgrade
        )
        assert "op.init_audit_logger_function('create_activity()')" in upgrade
        assert "op.init_audit_logger_triggers('article')" in upgrade
        assert "op.init_audit_logger_triggers('user')" in upgrade

        downgrade = parts[-1]
        assert "op.remove_audit_logger_triggers('user')" in downgrade
        assert "op.remove_audit_logger_triggers('article')" in downgrade
        assert "op.remove_audit_logger_function('create_activity()')" in downgrade
        assert (
            "op.remove_audit_logger_function('jsonb_change_key_name(data jsonb, old_key text, new_key text)')"
            in downgrade
        )
        assert (
            "op.remove_audit_logger_function('jsonb_subtract(arg1 jsonb, arg2 jsonb)')"
            in downgrade
        )
        assert (
            "op.remove_audit_logger_function('get_setting(setting text, fallback text)')"
            in downgrade
        )
        assert (
            "op.drop_index(op.f('ix_activity_native_transaction_id'), table_name='activity')"
            in downgrade
        )
        assert "op.drop_table('activity')" in downgrade
        assert "op.drop_table('transaction')" in downgrade
        assert "op.drop_table('user')" in downgrade
        assert "op.drop_table('article')" in downgrade
        assert "op.remove_audit_logger_extension('btree_gist')" in downgrade

    def test_second_file_is_empty(self):
        output = run_alembic_command(
            engine=db.engine,
            command="revision",
            command_kwargs={"autogenerate": True, "rev_id": "2", "message": "test"},
            alembic_config=ALEMBIC_CONFIG,
        )

        assert "versions/2_test.py" not in output
        assert "No changes in schema detected" in output

    def test_detects_new_column(self):
        # Dynamically add height column to a model specifically created for this test
        DynamicModificationModel.height = mapped_column(Float, nullable=True)

        output = run_alembic_command(
            engine=db.engine,
            command="revision",
            command_kwargs={
                "autogenerate": True,
                "rev_id": "2",
                "message": "add_height",
            },
            alembic_config=ALEMBIC_CONFIG,
        )

        assert "versions/2_add_height.py" in output

        migration_file = ALEMBIC_CONFIG / "versions" / "2_add_height.py"
        assert migration_file.exists()

        with open(migration_file) as f:
            migration_contents = f.read()

        # Check upgrade contains the new column operations
        parts = migration_contents.split("\n\n")
        upgrade = parts[-2]
        assert (
            "op.add_column('dynamic_modification_model', sa.Column('height', sa.Float(), nullable=True))"
            in upgrade
        )
        assert (
            "op.add_column_to_activity('dynamic_modification_model', 'height', default_value=None)"
            in upgrade
        )

        # Check downgrade removes the column
        downgrade = parts[-1]
        assert (
            "op.remove_column_from_activity('dynamic_modification_model', 'height')" in downgrade
        )
        assert "op.drop_column('dynamic_modification_model', 'height')" in downgrade

        # Test that upgrade and downgrade execute without errors
        run_alembic_command(
            engine=db.engine,
            command="upgrade",
            command_kwargs={"revision": "head"},
            alembic_config=ALEMBIC_CONFIG,
        )

        run_alembic_command(
            engine=db.engine,
            command="downgrade",
            command_kwargs={"revision": "-1"},
            alembic_config=ALEMBIC_CONFIG,
        )
