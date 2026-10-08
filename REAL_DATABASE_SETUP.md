# Connect your own MySQL database

The application already connects to a real MySQL server. It does not invent rows or
use the mocked values from the test files. `sample_data.sql` is only an optional
practice database. You do not need to import it to use your existing database.

This version supports MySQL 8+. SQL Server, PostgreSQL, Oracle, and SQLite require
changes to the database driver, schema queries, and SQL dialect; changing the port alone is not enough.

## 1. Find the connection that already works

Open your normal MySQL Workbench connection. Its settings show the hostname, port,
and username. In Workbench, check the **SCHEMAS** panel for your actual database name.
The database name is not the friendly connection name displayed on Workbench's home page.

For example, a connection might be called `Local instance MySQL80`, while the database
inside it is `college`. Use `college` in `MYSQL_DATABASE` in that example.

## 2. Put your settings in the local .env file

Edit the existing `.env` in the project folder. Replace these examples with your values:

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=your_existing_database
MYSQL_USER=your_reader_username
MYSQL_PASSWORD="your_actual_password"
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
AI_MODEL=gemini-2.5-flash
```

| Setting | Plain-language meaning |
|---|---|
| `MYSQL_HOST` | Computer running MySQL; `localhost` means this computer |
| `MYSQL_PORT` | MySQL's network port; use the value from Workbench |
| `MYSQL_DATABASE` | Existing database whose tables you want to query |
| `MYSQL_USER` | MySQL account allowed to read those tables |
| `MYSQL_PASSWORD` | That MySQL account's password, not your Windows password |
| `AI_PROVIDER` | `gemini` or `openai` |
| `GEMINI_API_KEY` | Key used only when Gemini generates SQL |
| `AI_MODEL` | Model requested from the selected provider |

The old `MY_HOST` setting is accepted if `MYSQL_HOST` is absent. Avoid conflicting
values. Keep one entry per setting. Quote passwords containing spaces or `#`.
If the password contains quote characters, use the appropriate dotenv escaping.
Existing operating-system environment variables take precedence over `.env`.

The program loads `.env` when Python starts. **Restart FastAPI after editing it**;
`--reload` does not guarantee that an `.env` edit triggers a restart.
Keep secrets local. Do not paste the contents of `.env` into chat or your presentation.

## 3. Use a database account with read permission

An administrator can give you a separate account for this project. For a local server,
the following is an example only: replace the database name and password before running.

```sql
CREATE USER 'sql_reader'@'localhost' IDENTIFIED BY 'a_password_you_choose';
GRANT SELECT ON `your_existing_database`.* TO 'sql_reader'@'localhost';
```

Run `CREATE USER` only when the account does not already exist. Creating an account
requires administrator permission. If this is a shared or company server, ask its
administrator to supply the correct reader account rather than changing permissions yourself.
For a remote connection, the account's allowed client host must match your computer;
the local example is not a complete remote-server configuration.

Do not copy your tables into the sample database. The application reads them where they are.
It does not migrate, create, or delete tables during normal use.

## 4. Test MySQL before using AI

Run from the project folder:

```powershell
.\.venv\Scripts\python.exe check_database.py
```

This performs a real `SELECT 1`, tests a read-only transaction, and reads schema metadata.
It prints the database name and table count, not your password or table contents.
It needs neither an AI key nor running FastAPI/Streamlit processes.

Success means the connection and those checks worked at that moment. It does not
prove every generated query will be correct or that the AI key works.

At the time of the implementation check, the saved login returned **1045: access denied**.
The real connection must be retested after the credentials or account permissions are corrected.

## 5. Start the API and UI

In terminal 1:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1
```

In terminal 2:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui.py --server.address 127.0.0.1
```

Open http://localhost:8501. Click **Test database connection**, then **Load tables and columns**.
The sidebar should show your database and its real tables.

First test a SQL statement that does not require AI:

```sql
SELECT 1 AS connection_test;
```

Then use an actual table and column from your sidebar, for example:

```sql
SELECT `actual_column` FROM `actual_table` LIMIT 5;
```

Replace both placeholder names. Click **Run query**. Once this works, ask an English
question about those same columns and click **Generate SQL**. Review before executing.

For an independent check, run the same SELECT in Workbench against the same database
and compare results. Add `ORDER BY` when comparing row order; without it SQL does not
guarantee a particular order. Data may also change between two executions.

## 6. Understand what goes to the AI

The selected provider receives your question and the configured database's visible
table names, column names, and data types. Existing code does not send result rows
or database passwords to the AI. Any sensitive data you type into the question is
part of the question sent to the provider. Use a database whose metadata you are allowed to share.

## Troubleshooting

| Message | What to check |
|---|---|
| 1045: login rejected | Username/password and whether the account can connect from this host |
| 1044 or 1142: permission denied | SELECT access to the intended database/tables |
| 1049: database not found | Actual schema name, spelling, and selected MySQL server |
| 2003: cannot reach server | Running MySQL service, host, port, firewall, or required VPN |
| 2005: host not found | Hostname spelling and DNS |
| No visible tables | Empty/wrong database or insufficient metadata/table permissions |
| 1054 or 1146 | Generated SQL uses a nonexistent column/table; reload schema and correct it |
| 3024: query too slow | Narrow filters, smaller joins, or a simpler query |
| AI key missing | Add the provider key locally; restart FastAPI |
| AI quota reached | Provider quota or billing status; unrelated to MySQL login |

If Workbench uses SSH tunneling, SSL certificates, or a managed-service proxy, its
connection is not equivalent to a plain host/port login. This project's simple connector
does not yet configure those options explicitly. Do not disable required server security;
that connection setup needs to be added for your environment.
