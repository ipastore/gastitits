# PLAN.md

You are helping me design and implement a small but “real-world style” data project: an **ETL pipeline** to build an **OLAP-ready dataset** for my personal/home finances.

## Context

- I live with my girlfriend, and we each have **one bank account** from **two different banks**.
- Each bank lets us **download exports** of our transactions (Imagine provides CSVs; Santander currently provides an XLS such as `202508.xls`).
- I will share the raw `202508.xls` and the desired `202508_corrected.xls` so we can validate the Santander parser and regex rules before generalizing.
- I want to:
-  - Parse and clean those CSV/XLS exports,
  - Combine them into a unified data model,
  - Store them in a **SQL database** (most likely PostgreSQL),
  - And then connect **Tableau** to that database to create dashboards and metrics.

This is a self-learning project, so I’m intentionally **overengineering a bit** to learn good data practices: ETL, OLAP, star schema, etc.

---

## Goal

Build a **small analytics stack** that looks like a tiny version of what companies do:

- **Source (OLTP side)**: banks’ internal systems → me downloading CSVs.
- **ETL**:
  - **Extract**: read CSVs from multiple banks.
  - **Transform**: clean, normalize, categorize, detect internal transfers, and assign each transaction to a person (me vs girlfriend).
  - **Load**: write the transformed data into a **PostgreSQL** database with a **dimensional (star) schema**.
- **OLAP / Analytics**:
  - Use **Tableau** on top of that PostgreSQL schema (or a clean Parquet/CSV) to explore and visualize:
    - Monthly spending by category,
    - Comparison “me vs girlfriend” (who spends what),
    - Top merchants,
    - Trends over time,
    - With the ability to filter out internal transfers.

---

## Technical direction & preferences

- **Language**: Python.
- **Environment & deps**:
  - I’m using **uv** (not conda) to manage Python and dependencies via `pyproject.toml`.
  - Core libraries:
    - `pandas`
    - `pyyaml`
    - `python-dateutil`
    - `pyarrow`
    - `typer`
    - `sqlalchemy` (plus a Postgres driver like `psycopg2` or `psycopg2-binary`)

- **Data flow** (high level):
   1. Parse each bank’s CSV/XLS into a pandas DataFrame with **bank-specific parsers** (Santander will come from `202508.xls`).
  2. Normalize and combine them into **one unified DataFrame** (staging layer).
  3. Add logic:
     - Standardized dates and amounts (negative = expense, positive = income),
  - Assign `bank_name` and `person` for each transaction (Santander defaults to `nacho`, Imagine defaults to `delfi`),
  - Apply regex-driven rules to extract the merchant entity and normalize merchant names (e.g. via YAML aliases),
  - Assign categories based on strict entity → category mappings loaded from a config file,
     - Detect internal transfers between our own accounts and mark them.
  4. Use this unified DataFrame as the **source of truth** for:
     - Exporting a clean Parquet file (Parquet is the canonical cleaned output; CSV is only used for the original raw bank exports),  
     - Populating the SQL database (fact + dimensions).

---

## Unified OLAP DataFrame (staging schema)

The unified pandas DataFrame (staging layer) should have, at minimum, the following columns:

- `transaction_id`  
  Unique, stable ID per transaction (e.g. hash of bank + date + amount + description).

- `bank_name`  
  Name/label of the bank (e.g. `"Santander"`, `"Imagine"`).

- `person`  
  Owner of the account / who paid:
  - `"nacho"`
  - `"delfi"`

- `date`  
  Transaction date as `datetime64[ns]`.

- `amount`  
  Numeric (float or decimal):
  - Negative = expense
  - Positive = income  
  (All in EUR; no `currency` column for now.)

- `raw_description`  
  Original text from the bank statement (for debugging, rule refinement, and traceability).

- `normalized_merchant`  
  Cleaned merchant name (e.g. `"LIDL"`, `"MERCADONA"`, `"REPSOL"`, `"MCDONALDS"`).

- `category`  
  Categorical label for what the transaction represents (see next section).

- `is_transfer`  
  Boolean flag indicating whether the transaction is an internal transfer between our own accounts.

- `source_file`  
  Name/path of the original CSV file the transaction came from (useful for debugging and lineage).

This DataFrame is the **staging / modeling layer** and acts as the “single source of truth” before loading into the SQL star schema.

---

## Categories

I want a **small but expressive category list** that is meaningful for personal finance decisions. For now, the main `category` values will be:

- `Housing`  
  Rent, community fees, home insurance.

- `Utilities`  
  Electricity, water, gas, internet, phone.

- `Groceries`  
  Supermarkets and regular food shopping (Lidl, Mercadona, Carrefour, etc.).

- `EatingOut`  
  Restaurants, bars, cafes, take-away, delivery.

- `Transport`  
  Public transport, fuel, taxis, trains, buses.

- `Health`  
  Pharmacy, doctors, health insurance, therapy.

- `Leisure`  
  Cinema, hobbies, entertainment, streaming services, books.

- `Shopping`  
  Clothes, electronics, non-grocery shopping.

- `Travel`  
  Hotels, flights, trips, holiday-related spending.

- `Financial`  
  Bank fees, commissions, interests, financial charges.

- `Income`  
  Salary, refunds, reimbursements, any positive cash inflows.

- `Other`  
  Anything that doesn’t clearly fit the above (temporary bucket until I create a better category).

These will be configured via a YAML file (`config/categories.yaml`) with keywords per category and can be refined over time.

---

## Data modeling (OLAP / warehouse-style)

I want to design a **star-like schema** in PostgreSQL, based on the unified DataFrame.

### Fact table

- `transactions`  
  One row per transaction.

  Suggested columns (in SQL terms):

  - `transaction_id` (TEXT, PRIMARY KEY)
  - `bank_id` (INTEGER, FK → `banks.bank_id`)
  - `person_id` (INTEGER, FK → `persons.person_id`)
  - `merchant_id` (INTEGER, FK → `merchants.merchant_id`, nullable)
  - `category_id` (INTEGER, FK → `categories.category_id`, nullable)
  - `date` (DATE, not null)
  - `amount` (NUMERIC(12,2), not null)
  - `raw_description` (TEXT)
  - `is_transfer` (BOOLEAN, default FALSE)
  - `source_file` (TEXT)

### Dimension tables

- `banks`
  - `bank_id` (SERIAL, PK)
  - `name` (TEXT, UNIQUE, not null)

- `persons`
  - `person_id` (SERIAL, PK)
  - `name` (TEXT, UNIQUE, not null)  
    Examples: `"nacho"`, `"delfi"`.

- `merchants`
  - `merchant_id` (SERIAL, PK)
  - `name` (TEXT, UNIQUE, not null)  
    This corresponds to `normalized_merchant`.

- `categories`
  - `category_id` (SERIAL, PK)
  - `name` (TEXT, UNIQUE, not null)  
    Values from the category list above (e.g. `"Groceries"`, `"Rent"` is `Housing`, `"Utilities"`, etc.).

This gives a simple, readable star schema:

- A central **fact table**: `transactions`,
- Four **dimension tables**: `banks`, `persons`, `merchants`, `categories`.

From the unified pandas DataFrame, we will:

- Extract unique values for banks, persons, merchants, and categories,
- Insert them into their dimension tables,
- Build mapping dicts (`name → id`),
- Replace `bank_name`, `person`, `normalized_merchant`, `category` in the DataFrame with foreign key IDs,
- And then load the fact table into `transactions`.

---

## What I want from you (the AI)

- Help me **refine and implement** this ETL + OLAP design based on the schema above.
- Suggest a **clean Python architecture** (folder structure, modules) consistent with:
  - `src/home_expenses_pipeline/` layout,
  - Separation of parsing, transformation, and loading logic.
- Propose **concrete DDL schemas** for PostgreSQL tables (`CREATE TABLE` statements).
- Show me how to:
  - Go from **CSV → pandas** (Extract & Transform),
  - Then from **pandas → Postgres tables** (Load) using `sqlalchemy`,
  - And how to make this process **repeatable** (e.g. a Typer CLI command like `home-expenses run`).
- Keep explanations at a level that connects **data engineering concepts** (OLTP vs OLAP, ETL, star schema) with **practical code** I can run for this project.

You can assume:

- I’m comfortable with Python and basic SQL,
- I’m learning data engineering / analytics patterns,
- I want solutions that are realistic enough to mirror what’s done with tools like Fivetran + dbt + Snowflake, but scaled down to:
  - **Python + pandas + PostgreSQL + Tableau** for a personal finance use case.