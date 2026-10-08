"""Run a real MySQL connection check. No AI key or running API is needed."""
from mysql.connector import Error as DatabaseError
from database import check_connection, database_error_message


def main():
    try:
        result = check_connection()
    except DatabaseError as error:
        print(database_error_message(error))
        return 1
    except ValueError:
        print('Check .env: MYSQL_PORT must be a valid number and SQL settings must be valid.')
        return 1
    print('Real MySQL connection successful.')
    print('Database:', result['database'])
    print('Visible tables:', result['table_count'])
    print('Read-only query successful. No table rows were read or changed.')
    if result['table_count'] == 0:
        print('No tables are visible. Check the database name and SELECT permissions.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
