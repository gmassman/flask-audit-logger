import pytest

from tests.separate_schema.conftest import ALEMBIC_CONFIG
from tests.separate_schema.flask_app import db
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
            "op.create_index(op.f('ix_audit_logs_activity_native_transaction_id'), 'activity', ['native_transaction_id'], unique=False, schema='audit_logs')"
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
        assert "op.init_audit_logger_triggers('article', excluded_columns=['created'])" in upgrade
        assert (
            "op.init_audit_logger_triggers('user', excluded_columns=['age', 'height'])" in upgrade
        )

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
            "op.drop_index(op.f('ix_audit_logs_activity_native_transaction_id'), table_name='activity', schema='audit_logs')"
            in downgrade
        )
        assert "op.drop_table('activity', schema='audit_logs')" in downgrade
        assert "op.drop_table('transaction', schema='audit_logs')" in downgrade
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
