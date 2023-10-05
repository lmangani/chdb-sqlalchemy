import pytest
from sqlalchemy import text
from sqlalchemy.engine import create_engine

# Register SQLAlchemy dialect
from sqlalchemy.dialects import registry
registry.register("chdb", "base", "dialect")

@pytest.fixture
def chdb_engine():
    engine = create_engine('chdb://')
    yield engine
    engine.dispose()

def test_connector_usage():
    # Use connector directly
    import connector
    cursor = connector.connect('default').cursor()
    cursor.execute('SELECT * FROM system.settings LIMIT 10')
    result = cursor.fetchone()
    assert result is not None  # Add more specific assertions if needed

def test_sqlalchemy_usage(chdb_engine):
    # Test engine and table
    conn = chdb_engine.connect()
    result = conn.execute(text('SELECT * FROM system.settings LIMIT 10'))
    for row in result:
        assert row is not None  # Add more specific assertions if needed

if __name__ == '__main__':
    pytest.main()
