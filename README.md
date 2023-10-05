# chdb-sqlalchemy
Basic, Ugly, Hackish sqlalchemy driver for chdb

> Nothing to see here, move on!

### Example
```python
# Use connector directly
import connector
cursor = connector.connect('default').cursor()
cursor.execute('SELECT * FROM system.settings LIMIT 10')
print(cursor.fetchone())

# Register SQLAlchemy dialect
from sqlalchemy.dialects import registry
registry.register("chdb", "base", "dialect")

# Test engine and table
from sqlalchemy import *
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import *

engine = create_engine('chdb://')
conn = engine.connect()
result = conn.execute(text('SELECT * FROM system.settings LIMIT 10'))
for row in result:
    print(row)
```
