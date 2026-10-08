# AI SQL Generator — mini project

Based on the supplied lecture transcript and https://youtu.be/ITfeXrdwhF8.
This is a simplified recreation of the workflow, not the instructor's original source.
It uses Python, FastAPI, Streamlit, MySQL, and Gemini (or optionally OpenAI).

## How it works

English question → Streamlit → FastAPI → AI + database schema → SQL → review → MySQL → results.

The AI generates SQL; MySQL executes it only after you click **Run query**.
Only the question and table/column metadata are sent to the AI, not result rows.

## Windows setup

**Using your own database? Start with [REAL_DATABASE_SETUP.md](REAL_DATABASE_SETUP.md).**
The app always connects to real MySQL using `.env`. There is no mock-data mode in the UI.
`sample_data.sql` is optional; skip it when using your existing database.

For learning and presentation:

- [CODE_EXPLAINED.md](CODE_EXPLAINED.md): every file and code block in plain language.
- [PRESENTATION_GUIDE.md](PRESENTATION_GUIDE.md): slide outline, demo steps, speaking script, and viva questions.

Use Python 3.11 or newer and MySQL 8+. Open PowerShell in this folder.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

1. **Only if you want the optional sample database:** open `sample_data.sql` in MySQL Workbench and execute it as an administrator.
   It creates a separate `sql_mini_project` database with `users` and `orders`.
2. For that sample database, at the bottom are two commented statements to create a SELECT-only `sql_reader`
   account. Choose a password, uncomment those statements, and execute them once.
3. Edit your existing `.env` using `.env.example` as a guide. For your own database,
   enter its real name instead of `sql_mini_project`. Your original `.env`
   was preserved. Set `MYSQL_DATABASE=sql_mini_project` for the sample data and use
   the reader account. The older `MY_HOST` name also works; prefer `MYSQL_HOST`.
4. Create a Gemini key at https://aistudio.google.com/apikey and add these lines:

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
AI_MODEL=gemini-2.5-flash
```

Keep the key in `.env`, not in Python files or chat. Restart FastAPI after changes.
Gemini 2.5 Flash has a free tier with account-dependent limits; check
https://ai.google.dev/gemini-api/docs/pricing and your AI Studio quota.
The Gemini integration uses Google's documented OpenAI-compatible REST endpoint:
https://ai.google.dev/gemini-api/docs/openai.

To use OpenAI instead, set `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and `AI_MODEL`
to a model available to your API account. API billing is separate from this chat.
Provider errors do not silently switch to another provider or incur fallback calls.

## Run (two terminals)

### Groq alternative

Groq is also supported. Put these settings in `.env` (keep the real key out of `.env.example`):

```dotenv
AI_PROVIDER=groq
GROQ_API_KEY=your_key_here
AI_MODEL=openai/gpt-oss-20b
```

Groq and xAI Grok are different services. This configuration uses Groq.
See https://console.groq.com/docs/openai for the API format and
https://console.groq.com/docs/rate-limits for free-plan limits.
Restart FastAPI after changing providers.

Terminal 1 — backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1
```

Terminal 2 — UI:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui.py --server.address 127.0.0.1
```

Open http://localhost:8501. API documentation: http://127.0.0.1:8000/docs.
Load tables in the sidebar, ask a question, generate SQL, review it, and click Run query.
You can also paste a SELECT query directly without an AI key.

## Example questions

- Show all users older than 30.
- How many users live in each city?
- Show each user's name and their orders.
- What is the total order amount for each user?
- Show users who have not placed any orders.

Manual test query:

```sql
SELECT name, age FROM users WHERE age > 30 ORDER BY age;
```

Expected sample result: Priya (33), Rahul (35), Neha (42).

## Files to explain in your presentation

| File | Responsibility |
|---|---|
| `ui.py` | Displays the form, calls the API, and shows results |
| `app.py` | Defines routes and validates request fields |
| `database.py` | Reads schema, validates SQL, and queries MySQL |
| `query_generator.py` | Sends the schema and question to the AI |
| `sample_data.sql` | Creates example tables and rows |
| `.env` | Local database settings and API key |

`GET /schema` returns the configured database's tables and columns.
`GET /connection` verifies real read-only execution and schema access.
`POST /generate-sql` accepts `{"question": "Show users older than 30"}`.
`POST /execute-query` accepts `{"sql": "SELECT name FROM users"}`.

Unlike the lecture's multi-database explorer, this simple version uses one configured
database. It also uses fewer dependencies, a Gemini default, and read-only execution.
There is no LangChain, vector database, or multi-agent framework to explain.

## Limits and troubleshooting

This is a local teaching project, not a publicly hosted service. Use a MySQL account
with SELECT permission only on the project database. The parser, function allowlist,
read-only transaction, five-second execution limit, and 200-row display cap provide
additional restrictions; they do not replace database permissions. Some valid advanced
SQL is intentionally rejected. Generated SQL can be wrong: always review it.

- API unavailable: keep both terminals running.
- Database failure: check the MySQL service, database name, password, and permissions.
- AI access error: check key, model availability, and provider quota.
- Quota reached: wait for reset or check your provider dashboard.
- Empty results: the query ran successfully but matched no rows.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Automated tests use mocked external services, so they do not need an API key or MySQL.
Live generation requires your own key, and live execution requires a running MySQL server.

## Short presentation explanation

“My project converts an English question into SQL. Streamlit collects the question.
FastAPI reads the database structure and sends it with the question to an AI model.
The generated SQL is validated and shown for review. When the user clicks Run query,
MySQL executes it in a read-only transaction and the UI displays the results.”

The AI is an existing model accessed through an API; this project does not train a model.
