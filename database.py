"""MySQL connection, schema discovery, and read-only execution."""
import os
from pathlib import Path
import mysql.connector
import sqlglot
from sqlglot import exp
from dotenv import load_dotenv

# Read local settings once when the backend starts. Never print the password.
load_dotenv(Path(__file__).with_name('.env'))


def connect():
    """Open the real database named in .env; no sample data is loaded here."""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', os.getenv('MY_HOST', 'localhost')),
        user=os.getenv('MYSQL_USER', 'sql_reader'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'sql_mini_project'),
        port=int(os.getenv('MYSQL_PORT', '3306')), connection_timeout=5,
    )


def database_error_message(error):
    """Explain common MySQL errors without exposing server details or secrets."""
    messages = {
        1045: 'MySQL login rejected (1045). Check MYSQL_USER and MYSQL_PASSWORD, '
              'and whether that account may connect from this computer.',
        1044: 'MySQL database access denied (1044). Ask the administrator for '
              'SELECT permission on the configured database.',
        1049: 'MySQL database not found (1049). Check MYSQL_DATABASE in .env.',
        2003: 'Cannot reach MySQL (2003). Check the server, MYSQL_HOST, MYSQL_PORT, and network access.',
        2005: 'MySQL host not found (2005). Check MYSQL_HOST in .env.',
        1142: 'MySQL permission denied (1142). The account needs SELECT permission on this table.',
        1146: 'A table was not found (1146). Reload the schema and check your SQL.',
        1054: 'A column was not found (1054). Reload the schema and check your SQL.',
        1064: 'MySQL could not understand this query (1064). Review the generated SQL.',
        3024: 'The query took too long (3024). Add filters or simplify the query.',
    }
    return messages.get(error.errno, 'Database request failed. Check MySQL settings, SQL, and permissions.')


def check_connection():
    """Check a real read-only query and schema access without reading table rows."""
    execute_query('SELECT 1 AS connection_test')
    schema = get_schema()
    return {'connected': True, 'database': schema['database'],
            'table_count': len(schema['tables'])}


def get_schema():
    """Ask MySQL for current table names, column names, and types."""
    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE '
                       'FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() '
                       'ORDER BY TABLE_NAME, ORDINAL_POSITION')
        tables = {}  # Group columns under the table they belong to.
        for table, column, data_type in cursor.fetchall():
            tables.setdefault(table, []).append({'name': column, 'type': data_type})
        return {'database': connection.database, 'tables': tables}
    finally:
        connection.close()


def validate_sql(sql):
    """An AI instruction alone is not enough: parse SQL before execution."""
    try:
        statements = sqlglot.parse(sql, read='mysql')
    except sqlglot.errors.ParseError as error:
        raise ValueError('This is not valid MySQL SQL.') from error
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError('Enter one SELECT query only.')
    tree = statements[0]
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop,
                 exp.Alter, exp.Command, exp.Into, exp.Lock)
    if any(isinstance(node, forbidden) for node in tree.walk()):
        raise ValueError('Only read-only SELECT queries are allowed.')
    allowed = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'COALESCE',
               'LOWER', 'UPPER', 'LENGTH', 'CONCAT', 'ABS'}
    for function in tree.find_all(exp.Func):
        name = function.name if isinstance(function, exp.Anonymous) else function.sql_name()
        if name.upper() not in allowed:
            raise ValueError(f'Function {name} is not supported in this mini project.')
    for table in tree.find_all(exp.Table):
        if table.catalog or (table.db and table.db != os.getenv('MYSQL_DATABASE', 'sql_mini_project')):
            raise ValueError('Query only the configured database.')
    return tree.sql(dialect='mysql')


def execute_query(sql):
    """Validate first, then run against the real server in a read-only transaction."""
    query = validate_sql(sql)
    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute('SET SESSION MAX_EXECUTION_TIME = 5000')
        cursor.execute('SET SESSION SQL_SELECT_LIMIT = 201')
        connection.start_transaction(readonly=True)
        cursor.execute(query)
        rows = cursor.fetchmany(201)  # The extra row tells us whether to show a cap notice.
        return {'columns': [c[0] for c in cursor.description],
                'rows': [list(row) for row in rows[:200]], 'truncated': len(rows) > 200}
    finally:
        connection.close()
