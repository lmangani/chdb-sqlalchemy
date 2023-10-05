#!/usr/bin/env python
#
# See http://www.python.org/dev/peps/pep-0249/
#
# Many docstrings in this file are based on the PEP, which is in the public domain.

from __future__ import absolute_import
from __future__ import unicode_literals
import re
import uuid
import requests
from infi.clickhouse_orm.models import ModelBase
from infi.clickhouse_orm.database import Database
from datetime import datetime

import chdb as chdb
import chdb.dbapi as dbapi

from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    cast,
)

# PEP 249 module globals
apilevel = '2.0'
threadsafety = 2  # Threads may share the module and connections.
paramstyle = 'pyformat'  # Python extended format codes, e.g. ...WHERE name=%(name)s

# Python 2/3 compatibility
try:
    isinstance(obj, basestring)
except NameError:
    basestring = str

class Error(Exception):
    """Exception that is the base class of all other error exceptions.
    You can use this to catch all errors with one single except statement.
    """
    pass

class ParamEscaper(object):
    def escape_args(self, parameters):
        if isinstance(parameters, dict):
            return {k: self.escape_item(v) for k, v in parameters.items()}
        elif isinstance(parameters, (list, tuple)):
            return tuple(self.escape_item(x) for x in parameters)
        else:
            raise Exception("Unsupported param format: {}".format(parameters))

    def escape_number(self, item):
        return item

    def escape_string(self, item):
        # Need to decode UTF-8 because of old sqlalchemy.
        # Newer SQLAlchemy checks dialect.supports_unicode_binds before encoding Unicode strings
        # as byte strings. The old version always encodes Unicode as byte strings, which breaks
        # string formatting here.
        if isinstance(item, bytes):
            item = item.decode('utf-8')
        return "'{}'".format(item.replace("\\", "\\\\").replace("'", "\\'").replace("$", "$$"))

    def escape_item(self, item):
        if item is None:
            return 'NULL'
        elif isinstance(item, (int, float)):
            return self.escape_number(item)
        elif isinstance(item, basestring):
            return self.escape_string(item)
        elif isinstance(item, datetime):
            return self.escape_string(item.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            raise Exception("Unsupported object {}".format(item))

_escaper = ParamEscaper()

# Patch ORM library
@classmethod
def create_ad_hoc_field(cls, db_type):
    import infi.clickhouse_orm.fields as orm_fields

    # Enums
    if db_type.startswith('Enum'):
        db_type = 'String' # enum.Eum is not comparable
    # Arrays
    if db_type.startswith('Array'):
        inner_field = cls.create_ad_hoc_field(db_type[6 : -1])
        return orm_fields.ArrayField(inner_field)
    # FixedString
    if db_type.startswith('FixedString'):
        db_type = 'String'

    if db_type == 'LowCardinality(String)':
        db_type = 'String'

    if db_type.startswith('DateTime'):
        db_type = 'DateTime'

    if db_type.startswith('Nullable'):
        inner_field = cls.create_ad_hoc_field(db_type[9 : -1])
        return orm_fields.NullableField(inner_field)
   
    # db_type for Deimal comes like 'Decimal(P, S) string where P is precision and S is scale'
    if db_type.startswith('Decimal'):
        nums = [int(n) for n in db_type[8:-1].split(',')]
        return orm_fields.DecimalField(nums[0], nums[1])
    
    # Simple fields
    name = db_type + 'Field'
    if not hasattr(orm_fields, name):
        raise NotImplementedError('No field class for %s' % db_type)
    return getattr(orm_fields, name)()
ModelBase.create_ad_hoc_field = create_ad_hoc_field

from six import PY3, string_types
def _send(self, data, settings=None, stream=False):
    if PY3 and isinstance(data, string_types):
        data = data.encode('utf-8')
    params = self._build_params(settings)
    r = self.request_session.post(self.db_url, params=params, data=data, stream=stream, timeout=self.timeout)
    if r.status_code != 200:
        raise Exception(r.text)
    return r
Database._send = _send

#
# Connector interface
#

def connect(self, *cargs: Any, **cparams: Any) -> "Connection":
    return ConnectionWrapper(dbapi.connect().cursor())

def on_connect(self) -> None:
    pass

class ConnectionWrapper:
    __c: chdb
    notices: List[str]
    autocommit = None  # chdb doesn't support setting autocommit
    closed = False

    def __init__(self, c: chdb) -> None:
        self.__c = c
        self.notices = list()
        self.apilevel = '2.0'
        self.threadsafety = 2  # Threads may share the module and connections.
        self.paramstyle = 'pyformat'  # Python extended format codes, e.g. ...WHERE name=%(name)s


    def cursor(self) -> "Connection":
        return dbapi.connect().cursor()

    def fetchmany(self, size: Optional[int] = None) -> List:
        if hasattr(self.__c, "fetchmany"):
            # fetchmany was only added in 0.5.0
            if size is None:
                return self.__c.fetchmany()
            else:
                return self.__c.fetchmany(size)

        try:
            return cast(list, self.__c.fetch_df_chunk().values.tolist())
        except RuntimeError as e:
            if e.args[0].startswith(
                "Invalid Input Error: Attempting to fetch from an unsuccessful or closed streaming query result"
            ):
                return []
            else:
                raise e

    @property
    def c(self) -> chdb:
        warnings.warn(
            "Directly accessing the internal connection object is deprecated (please go via the __getattr__ impl)",
            DeprecationWarning,
        )
        return self.__c

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__c, name)

    @property
    def connection(self) -> "Connection":
        return self

    def close(self) -> None:
        # chdb doesn't support 'soft closes'
        pass

    @property
    def rowcount(self) -> int:
        return -1

    def executemany(
        self,
        statement: str,
        parameters: Optional[List[Dict]] = None,
        context: Optional[Any] = None,
    ) -> None:
        self.__c.executemany(statement, parameters)

    def execute(
        self,
        statement: str,
        format: Optional[Any] = None,
    ) -> None:
        try:
            if format is None:
                self.__c.execute(statement)
            else:
                self.__c.execute(statement, format)
        except RuntimeError as e:
            if e.args[0].startswith("Not implemented Error"):
                raise NotImplementedError(*e.args) from e
            elif (
                e.args[0]
                == "TransactionContext Error: cannot commit - no transaction is active"
            ):
                return
            else:
                raise e


class ChDBEngineWarning(Warning):
    pass


def index_warning() -> None:
    warnings.warn(
        "chdb-engine doesn't yet support reflection on indices",
        ChDBEngineWarning,
    )
