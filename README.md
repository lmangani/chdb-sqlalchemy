<img src="https://avatars.githubusercontent.com/u/132536224?s=200&v=4" width=150>

[![Test Package](https://github.com/lmangani/chdb-sqlalchemy/actions/workflows/python-package.yml/badge.svg)](https://github.com/lmangani/chdb-sqlalchemy/actions/workflows/python-package.yml)

# chdb-sqlalchemy
Basic, Ugly, Hackish sqlalchemy driver for chdb

> Warning: this hack probably doesn't work past this example ⚠️ 

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
