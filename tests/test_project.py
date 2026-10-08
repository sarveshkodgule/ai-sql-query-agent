import os
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from mysql.connector import Error as DatabaseError

import database
import query_generator
from app import app


class ProjectTests(unittest.TestCase):
    def test_cross_database_validation(self):
        sql = 'SELECT a.id FROM college.students a JOIN office.staff b ON a.id=b.id'
        self.assertIn('office.staff', database.validate_sql(sql, ['college', 'office']))
        with self.assertRaises(ValueError):
            database.validate_sql(sql, ['college'])
        with self.assertRaises(ValueError):
            database.validate_sql('SELECT * FROM students', ['college', 'office'])
        with self.assertRaises(ValueError):
            database.validate_sql('SELECT * FROM mysql.user', ['college', 'office'])
        self.assertIn('SELECT', database.validate_sql(
            'WITH s AS (SELECT id FROM college.students) SELECT * FROM s', ['college', 'office']))

    @patch('database.list_databases', return_value=['college', 'office'])
    @patch('database.connect')
    def test_multiple_schema_keeps_duplicate_table_names(self, connect, listing):
        cursor = connect.return_value.cursor.return_value
        cursor.fetchall.return_value = [('college', 'users', 'id', 'int'),
                                       ('office', 'users', 'name', 'varchar')]
        schema = database.get_schema(['college', 'office'])
        self.assertEqual(set(schema['tables']), {'college.users', 'office.users'})
        self.assertEqual(cursor.execute.call_args.args[1], ('college', 'office'))
        with self.assertRaises(ValueError):
            database.get_schema(['unavailable'])

    @patch('database.list_databases', return_value=['college', 'office'])
    @patch('database.connect')
    def test_execute_uses_selected_database(self, connect, listing):
        cursor = connect.return_value.cursor.return_value
        cursor.description = [('id',)]
        cursor.fetchmany.return_value = []
        database.execute_query('SELECT id FROM users', ['office'])
        connect.assert_called_once_with(database='office')

    def test_api_passes_database_selection(self):
        client = TestClient(app)
        with patch('app.get_schema', return_value={'tables': {'office.users': []}}) as schema:
            client.get('/schema', params=[('databases', 'college'), ('databases', 'office')])
            schema.assert_called_once_with(['college', 'office'])
        with patch('app.execute_query', return_value={'rows': []}) as execute:
            client.post('/execute-query', json={'sql': 'SELECT 1', 'databases': ['office']})
            execute.assert_called_once_with('SELECT 1', ['office'])

    @patch('requests.get')
    def test_ui_selection_clears_old_results(self, get):
        get.return_value.ok = True
        get.return_value.json.return_value = {'databases': ['college', 'office']}
        ui = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'ui.py')).run(timeout=15)
        next(b for b in ui.button if b.label == 'Load databases').click().run()
        ui.text_area[1].set_value('SELECT 1').run()
        ui.multiselect[0].set_value(['college', 'office']).run()
        self.assertEqual(ui.text_area[1].value, '')
        self.assertEqual(len(ui.exception), 0)

    def test_select_and_join(self):
        query = 'SELECT u.name, SUM(o.amount) FROM users u JOIN orders o ON u.id=o.user_id GROUP BY u.name'
        self.assertIn('SELECT', database.validate_sql(query))

    def test_reject_unsafe_queries(self):
        queries = ['DELETE FROM users', 'SELECT 1; DROP TABLE users',
                   "SELECT * INTO OUTFILE '/tmp/a' FROM users", 'SELECT SLEEP(10)',
                   'SELECT * FROM users FOR UPDATE', 'SELECT * FROM mysql.user',
                   "SELECT LOAD_FILE('/etc/passwd')", '', 'SELECT GET_LOCK(\'a\', 1)']
        for query in queries:
            with self.subTest(query=query), self.assertRaises(ValueError):
                database.validate_sql(query)

    @patch('database.connect')
    def test_execution_readonly_and_limit(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value
        cursor.description = [('id',)]
        cursor.fetchmany.return_value = [(i,) for i in range(201)]
        result = database.execute_query('SELECT id FROM users')
        connection.start_transaction.assert_called_once_with(readonly=True)
        self.assertEqual(len(result['rows']), 200)
        self.assertTrue(result['truncated'])
        connection.close.assert_called_once()

    @patch.dict(os.environ, {'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': ''})
    def test_missing_key(self):
        with self.assertRaisesRegex(ValueError, 'GEMINI_API_KEY'):
            query_generator.generate_sql('Show users', {})

    @patch.dict(os.environ, {'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'fake-test-key'})
    @patch('query_generator.requests.post')
    def test_generation_and_quota(self, post):
        response = post.return_value
        response.status_code = 200
        response.json.return_value = {'choices': [{'message': {'content': '```sql\nSELECT name FROM users\n```'}}]}
        self.assertEqual(query_generator.generate_sql('Show names', {}), 'SELECT name FROM users')
        response.status_code = 429
        with self.assertRaisesRegex(ValueError, 'quota'):
            query_generator.generate_sql('Show names', {})

    def test_api_validation(self):
        client = TestClient(app)
        self.assertEqual(client.post('/generate-sql', json={'question': ''}).status_code, 422)
        self.assertEqual(client.post('/generate-sql', json={'question': '   '}).status_code, 400)
        self.assertEqual(client.post('/execute-query', json={'sql': 'DROP TABLE users'}).status_code, 400)
        with patch('app.get_schema', return_value={'database': 'demo', 'tables': {}}):
            self.assertEqual(client.get('/schema').json()['database'], 'demo')

    @patch.dict(os.environ, {'AI_PROVIDER': 'groq', 'GROQ_API_KEY': 'test-key', 'AI_MODEL': 'openai/gpt-oss-20b'})
    @patch('query_generator.requests.post')
    def test_groq_generation(self, post):
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'choices': [{'message': {'content': 'SELECT 1'}}]}
        self.assertEqual(query_generator.generate_sql('Return 1', {}), 'SELECT 1')
        self.assertEqual(post.call_args.args[0], 'https://api.groq.com/openai/v1/chat/completions')
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer test-key')

    def test_connection_endpoint_and_private_error(self):
        client = TestClient(app)
        with patch('app.check_connection', return_value={
                'connected': True, 'database': 'real_database', 'table_count': 3}):
            response = client.get('/connection')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['table_count'], 3)
        with patch('app.check_connection', side_effect=DatabaseError(
                msg='private-server-details', errno=1045)):
            response = client.get('/connection')
            self.assertEqual(response.status_code, 400)
            self.assertIn('1045', response.json()['detail'])
            self.assertNotIn('private-server-details', response.text)

    @patch('app.generate_sql')
    @patch('app.get_schema', return_value={'database': 'empty', 'tables': {}})
    def test_empty_schema_does_not_call_ai(self, schema, generate):
        response = TestClient(app).post('/generate-sql', json={'question': 'Show records'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('No tables', response.json()['detail'])
        generate.assert_not_called()

    @patch('database.get_schema', return_value={'database': 'existing', 'tables': {'students': []}})
    @patch('database.execute_query')
    def test_connection_checks_execution_and_schema(self, execute, schema):
        result = database.check_connection()
        execute.assert_called_once_with('SELECT 1 AS connection_test')
        self.assertEqual(result, {'connected': True, 'database': 'existing', 'table_count': 1})

    @patch('requests.get')
    def test_ui_connection_check(self, get):
        get.return_value.ok = True
        get.return_value.json.return_value = {
            'connected': True, 'database': 'existing', 'table_count': 2}
        ui = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'ui.py')).run(timeout=15)
        next(b for b in ui.button if b.label == 'Test database connection').click().run()
        self.assertEqual(len(ui.exception), 0)
        self.assertIn('existing', ui.success[0].value)

    def test_ui_loads(self):
        ui = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'ui.py')).run(timeout=15)
        self.assertEqual(len(ui.exception), 0)
        self.assertTrue(any(b.label == 'Run query' and b.disabled for b in ui.button))

    @patch('requests.post')
    def test_ui_generate_and_execute(self, post):
        post.return_value.ok = True
        post.return_value.json.return_value = {'sql': 'SELECT name FROM users'}
        ui = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'ui.py')).run(timeout=15)
        ui.text_area[0].set_value('Show users')
        next(b for b in ui.button if b.label == 'Generate SQL').click().run()
        self.assertEqual(ui.text_area[1].value, 'SELECT name FROM users')
        post.return_value.json.return_value = {
            'columns': ['name'], 'rows': [['Asha']], 'truncated': False}
        next(b for b in ui.button if b.label == 'Run query').click().run()
        self.assertEqual(len(ui.exception), 0)
        self.assertEqual(ui.dataframe[0].value.iloc[0, 0], 'Asha')


if __name__ == '__main__':
    unittest.main()
