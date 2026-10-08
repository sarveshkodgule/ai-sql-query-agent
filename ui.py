"""Streamlit frontend. Keep the FastAPI terminal running too."""
import pandas as pd
import requests
import streamlit as st
from urllib.parse import urlencode

API_URL = 'http://127.0.0.1:8000'
st.set_page_config(page_title='AI SQL Generator', layout='centered')


def call_api(path, payload=None):
    try:
        if payload is None:
            response = requests.get(API_URL + path, timeout=10)
        else:
            response = requests.post(API_URL + path, json=payload, timeout=60)
        data = response.json()
        if not response.ok:
            st.error(data.get('detail', 'Request failed.'))
            return None
        return data
    except (requests.RequestException, ValueError):
        st.error('Cannot reach the API. Start FastAPI in another terminal and try again.')
        return None


st.title('AI SQL Generator')
st.write('Ask in English, review the SQL, and run it on your MySQL database.')


def clear_query():
    # Old SQL and results belong to the previous database selection.
    for key in ('sql', 'result', 'schema', 'executed_sql'):
        st.session_state.pop(key, None)


with st.sidebar:
    st.header('Database explorer')
    if st.button('Test database connection'):
        connection = call_api('/connection')
        if connection:
            st.success(f"Connected to {connection['database']}")
            st.caption(f"{connection['table_count']} table(s) visible. Read-only check passed.")
    if st.button('Load databases'):
        data = call_api('/databases')
        if data is not None:
            st.session_state.available_databases = data['databases']
            st.session_state.selected_databases = [
                name for name in st.session_state.get('selected_databases', [])
                if name in data['databases']]
            clear_query()
    available = st.session_state.get('available_databases', [])
    selected = st.multiselect('Select databases', available,
                              key='selected_databases', on_change=clear_query)
    if not selected:
        st.caption('Load databases, then choose one or more. Until then, the .env database is used.')
    if st.button('Load tables and columns'):
        params = '?' + urlencode({'databases': selected}, doseq=True) if selected else ''
        st.session_state.schema = call_api('/schema' + params)
    schema = st.session_state.get('schema')
    if schema:
        st.caption('Databases: ' + ', '.join(schema.get('databases', [schema['database']])))
        if not schema['tables']:
            st.info('No tables are visible. Check the database and account permissions.')
        for table, columns in schema['tables'].items():
            with st.expander(table):
                st.dataframe(columns, hide_index=True)
    st.caption('Selected databases must be on this MySQL server. System databases are excluded.')

with st.form('question_form'):
    # A form waits for Generate SQL instead of calling the API on every edit.
    question = st.text_area('Your question', placeholder='Show all users older than 30')
    generate = st.form_submit_button('Generate SQL')
if generate:
    st.session_state.pop('result', None)
    st.session_state.sql = ''
    if not question.strip():
        st.warning('Please enter a question.')
    else:
        with st.spinner('Generating SQL…'):
            data = call_api('/generate-sql', {'question': question, 'databases': selected or None})
        if data:
            st.session_state.sql = data['sql']

st.subheader('Review and execute')
st.caption('Edit the SQL or enter your own SELECT query without an AI key.')
sql = st.text_area('SQL query', key='sql', height=150)
if st.button('Run query', disabled=not sql.strip()):
    with st.spinner('Running query…'):
        st.session_state.result = call_api('/execute-query', {'sql': sql, 'databases': selected or None})
        st.session_state.executed_sql = sql
result = st.session_state.get('result')
if result:
    st.subheader('Results')
    st.code(st.session_state.executed_sql, language='sql')
    frame = pd.DataFrame(result['rows'], columns=result['columns'])
    st.dataframe(frame, hide_index=True, use_container_width=True)
    st.caption(f'{len(frame)} row(s) displayed.')
    if result['truncated']:
        st.info('Showing the first 200 rows. Add filters to narrow the query.')
    st.download_button('Download CSV', frame.to_csv(index=False), 'results.csv', 'text/csv')
