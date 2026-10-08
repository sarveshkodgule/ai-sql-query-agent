# Mini-project presentation and viva guide

## Project title

**AI-Powered SQL Query Generator Using Python, FastAPI, Streamlit, and MySQL**

Use your own name, class, and database domain on the title slide.

## Abstract

This project helps users query a MySQL database through English questions. A Streamlit
interface sends a question to a FastAPI backend. The backend reads the database's table
and column metadata and sends that context to an AI API. The generated SQL is checked
and displayed for review. On user request, the application executes supported SELECT
queries in a read-only transaction and displays real database results. The project
demonstrates API integration, schema discovery, SQL generation, validation, and a Python UI.

## Slide outline with speaking notes

| Slide | Content | What to say |
|---|---|---|
| 1. Title | Project name, your details | “My project helps users turn an English question into SQL.” |
| 2. Problem | SQL knowledge and schema knowledge are barriers | “Users need both SQL syntax and knowledge of table names to query data.” |
| 3. Objectives | Generate SQL, review it, run read-only, show results | “I wanted a small, explainable application with a Python API and UI.” |
| 4. Technology | Python, Streamlit, FastAPI, MySQL, AI API | “Each tool has one clear job: interface, routing, storage, or generation.” |
| 5. Architecture | Diagram in CODE_EXPLAINED.md | “The AI writes SQL; the database supplies the result rows.” |
| 6. Implementation | Four core Python files | “The code separates UI, API, database access, and AI generation.” |
| 7. Demonstration | Real schema, question, SQL, results | “These table names and rows come from my configured MySQL database.” |
| 8. Validation | SQL checks, read-only transaction, user review | “AI output is checked, and execution requires a separate button.” |
| 9. Testing and limits | Automated tests plus live checks actually performed | “Mocked tests check logic; real connection tests check integration.” |
| 10. Future work | Relationships, more SQL functions, other databases, authentication | “These are future improvements, not completed features.” |

## Two-minute speaking script

“My mini project is an AI-powered SQL query generator. The problem is that a user may
understand the information they want but may not know the SQL syntax or database structure.

The application has a Streamlit frontend and a FastAPI backend. MySQL stores the data.
An external AI model converts the question into SQL. I use the model through an API;
I have not trained a new model.

First, the backend reads table names, column names, and data types from the selected
database. When the user asks a question, that metadata and the question are sent to
the model. The model returns a SQL statement using that context.

The backend parses the SQL and allows a limited set of read-only operations. The UI
then displays the SQL for review. The user can edit it and click Run query. Only then
does the application execute it on MySQL and display the returned rows. Results can
also be downloaded as CSV.

I kept four core files so the design is easy to explain: ui.py for the interface,
app.py for routes, database.py for MySQL work, and query_generator.py for the AI request.

The application uses the real database selected in its local settings. Automated tests
use mocked services separately so they can run without an API key. The main limitations
are AI mistakes, API availability, a restricted SQL subset, and support for databases
on one MySQL server. Multiple databases can be selected together. Future work could add
relationship-aware prompts and more database types.”

## Live demonstration checklist

1. Before presenting, run `check_database.py` and correct any connection errors.
2. Confirm your AI key/model works with one small question. Do not display the key.
3. Start FastAPI and Streamlit in separate terminals using the README commands.
4. Click Test database connection, Load databases, select the databases you want, then Load tables and columns.
5. Explain one real table and two or three columns from your database.
6. Run a manual SELECT with LIMIT 5 to show real database access independently of AI.
7. Ask one simple English question using those actual column names.
8. Read the generated SQL aloud and explain SELECT, FROM, WHERE, and LIMIT if present.
9. Click Run query and explain the returned values using your domain knowledge.
10. Optionally compare the same query in Workbench and demonstrate CSV download.

Use your own table names. The examples about `users`, `orders`, and age apply only if
those tables/columns exist. Prepare one filter question, one COUNT/GROUP BY question,
and one join question only if you know the correct relationship between your tables.

If the AI is unavailable, clearly explain the failure and demonstrate a manual SELECT.
Do not label a stored screenshot, mock response, or previously generated SQL as a new live AI result.

## Common viva questions

**Why FastAPI when Streamlit could call the database directly?**
Separating the backend keeps database and AI operations in one API that another frontend
could also use. It also makes request validation and API testing easier to demonstrate.

**Is Streamlit the frontend or backend?**
It supplies the frontend experience here. Technically its Python code runs on a
Streamlit server and renders the interface in the browser. FastAPI is our separate API backend.

**What is an API?**
A defined way for one program to request work from another. Our UI calls our API,
and our API calls the external AI provider.

**What is the difference between SQL generation and execution?**
Generation creates SQL text. Execution sends that SQL to MySQL to retrieve real data.
They are separate requests and separate buttons in this project.

**How does the AI know my tables?**
The backend reads `information_schema.COLUMNS` and includes that metadata in the prompt.
The current version does not explicitly retrieve foreign-key relationships or sample rows.

**Does it work only with the sample database?**
No. Change the MySQL settings to an existing database. Table/column discovery is dynamic.
The optional sample SQL script is never loaded automatically.

**Is this an AI agent?**
It is a small AI-assisted SQL workflow with a human execution step. It is not an
autonomous agent that repeatedly plans, calls tools, repairs errors, and retries.
That distinction accurately describes what this implementation does.

**Did you train the model?**
No. I integrate an existing model through an API and guide it with a prompt and schema.

**Why send the schema?**
Without real names and data types, the model may invent tables and columns. Metadata
provides context, although it does not eliminate mistakes.

**Can it modify my database?**
Normal execution is designed for SELECT queries. SQL parsing and a read-only transaction
restrict operations. A SELECT-only database account is an additional enforcement layer.

**Is a SELECT prefix enough for safety?**
No. A statement may have additional operations or side effects. The application parses
the structure, restricts functions, and uses database permissions and a read-only transaction.

**What is SQLGlot?**
A library that parses SQL into a structure the program can examine and format.
Parsing is not the same as proving that a query has the intended meaning.

**What happens when the generated query is wrong?**
It may be rejected by validation or MySQL. The user sees an error, reviews the SQL,
and can edit or regenerate it. There is no automatic error-repair loop.

**Does it optimize every query?**
No. It generates SQL, applies some restrictions, and limits displayed rows. It does
not inspect execution plans, create indexes, or guarantee optimal performance.

**Where are passwords stored?**
In the local `.env` file or environment variables. They are not hard-coded into Python
and should not be committed to Git. The database password is not sent to the AI provider.

**What data does the AI receive?**
The question plus visible database/table/column metadata. Query result rows are not
automatically sent. Sensitive information typed into the question would be sent.

**Why use mocks in tests?**
To check behavior repeatably without requiring a live server, exposing real records,
or using AI quota. Those mocks exist in the test process, not the normal application.

**What does a passing connection test prove?**
The saved settings can connect, a small read-only query works, and metadata can be read
at that moment. It does not prove AI accuracy or permission to read every table.

**What are the limitations?**
One MySQL server (with multiple selectable databases); no public-user authentication; no explicit foreign-key
metadata; restricted SQL functions; API quota/network dependence; AI mistakes; and a
200-row display cap. Large schemas may also exceed practical AI context limits.

## Report structure

Use these headings for your college report: Abstract, Problem Statement, Objectives,
Requirements, Architecture, Module Descriptions, Implementation, Test Cases, Actual
Results, Limitations, Future Work, and References.

For Actual Results, record your own database connection check, one generated query,
the SQL reviewed, and the resulting table. Avoid including private data or credentials.
Do not claim successful live integration until your real login and query have passed.

## Acknowledgment

The project workflow was inspired by the provided tutorial:
https://youtu.be/ITfeXrdwhF8. This implementation simplifies that workflow and uses
Gemini by default, with optional OpenAI configuration. Describe any code assistance
according to your institution's project submission requirements.
