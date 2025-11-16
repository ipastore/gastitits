# IMPLEMENTATION STEPS

**Project**: Home Expenses ETL Pipeline  
**Goal**: Build a production-ready ETL pipeline to transform bank transaction exports (CSV/XLS) into a PostgreSQL star schema for analytics with Tableau.

**How to use this plan**: Execute each step sequentially with an AI agent. Each step is designed to be self-contained and testable before moving to the next.

---

## Step 1: Configuration Loader and YAML Setup

### Objective
Create the configuration management system to load and validate category definitions and merchant alias mappings from YAML files.

### Files to Create/Modify
- `config/categories.yaml` - Define all transaction categories and their matching rules
- `config/merchant_aliases.yaml` - Define merchant name normalization patterns
- `src/gastitis/config_loader.py` - Module to load and validate YAML configs

### Key Implementation Requirements

**categories.yaml structure**:

**merchant_aliases.yaml structure**:
```yaml
LIDL:
  patterns:
    - "lidl"
    - "li dl"
    
MERCADONA:
  patterns:
    - "mercadona"
    - "mercadona s.a"
    
ALCAMPO:
  patterns:
    - "alcampo"
    - "mi alcampo"

# ... add more merchants
```

**config_loader.py must**:
- Load both YAML files using PyYAML
- Validate structure (all expected categories present)
- Provide functions:
  - `load_categories() -> dict`
  - `load_merchant_aliases() -> dict`
  - `get_valid_categories() -> list[str]`
- Raise clear errors if YAML files are missing/malformed
- Use pathlib to locate config files relative to project root

### Dependencies
None - this is the foundation step.

### Testing/Validation
- Create a simple test script that loads both configs
- Print loaded categories and merchant aliases
- Verify all expected categories from plan.md are present
- Verify YAML syntax is valid

### Expected Outputs
- Two populated YAML files with initial data
- Working config_loader.py module
- Ability to import and use: `from gastitis.config_loader import load_categories, load_merchant_aliases`

---

## Step 2: Database Schema Design and Creation

### Objective
Design and implement the PostgreSQL star schema with fact table (transactions) and dimension tables (banks, persons, merchants, categories).

### Files to Create/Modify
- `scripts/schema.sql` - DDL statements for all tables
- `src/gastitis/db/__init__.py` - Database package
- `src/gastitis/db/connection.py` - Database connection utilities
- `src/gastitis/db/schema.py` - Schema management functions

### Key Implementation Requirements

**schema.sql must include**:

```sql
-- Dimension: Banks
CREATE TABLE IF NOT EXISTS banks (
    bank_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Dimension: Persons
CREATE TABLE IF NOT EXISTS persons (
    person_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Dimension: Merchants
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Dimension: Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Fact: Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(bank_id),
    person_id INTEGER NOT NULL REFERENCES persons(person_id),
    merchant_id INTEGER REFERENCES merchants(merchant_id),
    category_id INTEGER REFERENCES categories(category_id),
    date DATE NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    raw_description TEXT,
    is_transfer BOOLEAN DEFAULT FALSE,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_person ON transactions(person_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_is_transfer ON transactions(is_transfer);
```

**connection.py must**:
- Use SQLAlchemy to create engine
- Support connection string from environment variable or parameter
- Provide `get_engine(db_url: str) -> Engine` function
- Handle connection errors gracefully

**schema.py must**:
- Provide `create_schema(engine: Engine) -> None` function
- Execute the SQL from schema.sql
- Optionally provide `drop_schema(engine: Engine) -> None` for testing

### Dependencies
- SQLAlchemy must be installed (already in pyproject.toml)
- PostgreSQL must be running (document setup in comments)
- Requires `psycopg2-binary` for PostgreSQL driver

### Testing/Validation
- Add psycopg2-binary to dependencies if not present
- Create a test script that:
  - Connects to a test PostgreSQL database
  - Runs `create_schema()`
  - Verifies all tables exist
  - Verifies foreign keys are set up
- Document the connection string format: `postgresql://user:password@localhost:5432/dbname`

### Expected Outputs
- Complete schema.sql file
- Working database connection module
- Ability to create the schema in PostgreSQL
- All tables created with proper constraints and indexes

---

## Step 3: Santander XLS Parser

### Objective
Parse Santander bank XLS exports and convert them into a standardized pandas DataFrame.

### Files to Create/Modify
- `src/gastitis/parsers/__init__.py` - Parsers package
- `src/gastitis/parsers/santander.py` - Santander-specific parser
- `src/gastitis/parsers/base.py` - Base parser interface/utilities

### Key Implementation Requirements

**Santander XLS format** (based on 202508.xls):
- File is Excel format (.xls)
- Transaction table starts after header rows
- Columns: FECHA OPERACIÓN, FECHA VALOR, CONCEPTO, IMPORTE, SALDO
- Dates are in DD/MM/YYYY format
- Amounts include EUR symbol and use comma for decimals
- Negative amounts are expenses, positive are income

**santander.py must**:
```python
import pandas as pd
from pathlib import Path

def parse_santander_xls(file_path: Path) -> pd.DataFrame:
    """
    Parse Santander XLS export into standardized DataFrame.
    
    Returns DataFrame with columns:
    - date: datetime64[ns] (from FECHA OPERACIÓN)
    - amount: float (from IMPORTE, cleaned)
    - raw_description: str (from CONCEPTO)
    - balance: float (from SALDO, for validation)
    - bank_name: str = "Santander"
    - person: str = "nacho"
    - source_file: str (file name)
    """
    # Read XLS, skipping header rows
    # Find the row with "FECHA OPERACIÓN" header
    # Parse dates from DD/MM/YYYY to datetime
    # Clean amounts: remove EUR, convert comma to dot, convert to float
    # Assign bank_name = "Santander"
    # Assign person = "nacho" (fixed mapping)
    # Return standardized DataFrame
```

**base.py should define**:
- Common date parsing utilities
- Amount cleaning functions
- Base DataFrame schema validation

### Dependencies
- pandas (already installed)
- openpyxl or xlrd for Excel reading
- Step 1 completed (config loader)

### Testing/Validation
- Test with `data_raw/Santander/202508.xls`
- Verify all transactions are parsed
- Verify dates are correctly converted
- Verify amounts match the XLS (check a few manually)
- Verify person is always "nacho"
- Compare output with expected 202508_corrected.xls structure if available
- Test error handling for malformed XLS files

### Expected Outputs
- Working `parse_santander_xls()` function
- Successfully parsed DataFrame from 202508.xls
- All dates, amounts, and descriptions correctly extracted
- Consistent column names for downstream processing

---

## Step 4: Imagine CSV Parser

### Objective
Parse Imagine bank CSV exports and convert them into the same standardized pandas DataFrame format as Santander.

### Files to Create/Modify
- `src/gastitis/parsers/imagine.py` - Imagine-specific parser

### Key Implementation Requirements

**Imagine CSV format** (determine from actual files):
- CSV with specific columns (date, description, amount, etc.)
- Date format (determine from sample)
- Amount format (determine from sample)
- CSV delimiter and encoding

**imagine.py must**:
```python
import pandas as pd
from pathlib import Path

def parse_imagine_csv(file_path: Path) -> pd.DataFrame:
    """
    Parse Imagine CSV export into standardized DataFrame.
    
    Returns DataFrame with same columns as Santander parser:
    - date: datetime64[ns]
    - amount: float
    - raw_description: str
    - bank_name: str = "Imagine"
    - person: str = "delfi"
    - source_file: str
    """
    # Read CSV with appropriate delimiter and encoding
    # Parse date column
    # Parse amount column
    # Assign bank_name = "Imagine"
    # Assign person = "delfi" (fixed mapping)
    # Return standardized DataFrame
```

### Dependencies
- pandas
- Step 3 completed (to use same utility functions from base.py)
- Actual Imagine CSV samples in data_raw/Imagine/

### Testing/Validation
- Test with actual Imagine CSV files from data_raw/Imagine/
- Verify column mapping is correct
- Verify dates and amounts parse correctly
- Verify person is always "delfi"
- Ensure output schema matches Santander parser exactly
- Test with multiple CSV files if available

### Expected Outputs
- Working `parse_imagine_csv()` function
- Successfully parsed DataFrames from all Imagine CSVs
- Same column schema as Santander parser
- Ready to combine with Santander data

---

## Step 5: Merchant Normalization Module

### Objective
Extract merchant entity from raw transaction descriptions using regex patterns and normalize merchant names using alias rules from config.

### Files to Create/Modify
- `src/gastitis/transformers/__init__.py` - Transformers package
- `src/gastitis/transformers/merchant_normalizer.py` - Merchant normalization logic

### Key Implementation Requirements

**Common Santander patterns** (from 202508.xls examples):
- "Pago Movil En {MERCHANT}, {LOCATION}, Tarj. :*{CARD}"
- "Compra {MERCHANT}, {LOCATION}, Tarjeta {CARD} , Comision {AMOUNT}"
- "Transferencia De {MERCHANT}, Concepto {CONCEPT}"
- "Recibo {MERCHANT} {DETAILS}"
- "Bizum De {MERCHANT} Concepto {CONCEPT}"

**merchant_normalizer.py must**:
```python
import re
from gastitis.config_loader import load_merchant_aliases

def extract_merchant(raw_description: str) -> str:
    """
    Extract merchant entity from raw transaction description using regex.
    
    Patterns to try in order:
    1. Pago Movil En (.+?),
    2. Compra (.+?),
    3. Transferencia [De|A Favor De] (.+?),
    4. Recibo (.+?) 
    5. Bizum [De|A Favor De] (.+?) Concepto
    6. Fallback: first N words of description
    
    Returns extracted merchant name (may still need normalization).
    """
    # Apply regex patterns in order
    # Return first match or fallback to raw description
    
def normalize_merchant(merchant: str, aliases: dict) -> str:
    """
    Normalize merchant name using alias rules.
    
    - Convert to lowercase
    - Strip whitespace
    - Check each alias pattern for match
    - Return canonical name if match found
    - Return cleaned merchant if no match
    """
    # Lowercase and strip
    # For each canonical merchant, check patterns
    # Return canonical name or cleaned input
    
def process_merchants(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add normalized_merchant column to DataFrame.
    
    For each row:
    1. Extract merchant from raw_description
    2. Normalize using aliases
    3. Store in normalized_merchant column
    """
    aliases = load_merchant_aliases()
    df['normalized_merchant'] = df['raw_description'].apply(
        lambda x: normalize_merchant(extract_merchant(x), aliases)
    )
    return df
```

### Dependencies
- Step 1 completed (config loader with merchant_aliases.yaml)
- Step 3 or 4 completed (to have DataFrames to process)

### Testing/Validation
- Test `extract_merchant()` with sample descriptions from 202508.xls
  - "Pago Movil En Lidl, Zaragoza, Tarj. :*135542" → "Lidl"
  - "Compra Mercadona, Barcelona, Tarjeta 516..." → "Mercadona"
- Test `normalize_merchant()` with variants
  - "lidl" → "LIDL" (via aliases)
  - "mi alcampo zara" → "ALCAMPO" (via aliases)
- Test full pipeline with sample DataFrame
- Verify normalized_merchant column is added correctly
- Check edge cases (no merchant found, unknown merchants)

### Expected Outputs
- Working merchant normalization functions
- Ability to add `normalized_merchant` column to any DataFrame
- Merchants normalized according to YAML aliases
- Clear fallback behavior for unrecognized merchants

---

## Step 6: Categorization Module

### Objective
Assign transaction categories based on strict entity→category mappings from config file.

### Files to Create/Modify
- `src/gastitis/transformers/categorizer.py` - Categorization logic
- Update `config/categories.yaml` to include entity→category mappings

### Key Implementation Requirements

**Enhanced categories.yaml structure**:
```yaml
Housing:
  keywords:
    - "alquiler"
    - "rent"
  entities:
    - "MARTA SANZ VICTORIA"  # Landlord
    
Utilities:
  keywords:
    - "endesa"
    - "electricidad"
  entities:
    - "ENDESA ENERGIA"
    - "AEGON ESPANA"
    
Groceries:
  keywords: []
  entities:
    - "LIDL"
    - "MERCADONA"
    - "ALCAMPO"
    
# ... etc
```

**categorizer.py must**:
```python
import pandas as pd
from gastitis.config_loader import load_categories

def build_entity_category_map(categories: dict) -> dict:
    """
    Build a mapping from entity to category.
    
    Returns: {"LIDL": "Groceries", "ENDESA ENERGIA": "Utilities", ...}
    """
    mapping = {}
    for category, rules in categories.items():
        for entity in rules.get('entities', []):
            mapping[entity.upper()] = category
    return mapping

def assign_category(normalized_merchant: str, entity_map: dict) -> str:
    """
    Assign category based on exact entity match.
    
    - Convert merchant to uppercase
    - Check if in entity_map
    - Return category or "Other"
    """
    merchant_upper = normalized_merchant.upper()
    return entity_map.get(merchant_upper, "Other")

def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add category column to DataFrame based on normalized_merchant.
    """
    categories = load_categories()
    entity_map = build_entity_category_map(categories)
    df['category'] = df['normalized_merchant'].apply(
        lambda x: assign_category(x, entity_map)
    )
    return df
```

### Dependencies
- Step 1 completed (config loader)
- Step 5 completed (merchant normalization)

### Testing/Validation
- Update categories.yaml with actual merchants from your bank data
- Test categorization with sample transactions:
  - "LIDL" → "Groceries"
  - "ENDESA ENERGIA" → "Utilities"
  - "MARTA SANZ VICTORIA" → "Housing"
  - "UNKNOWN MERCHANT" → "Other"
- Verify all categories from plan.md are supported
- Test with full DataFrame from parsers
- Check percentage of "Other" category (should be low if config is good)

### Expected Outputs
- Enhanced categories.yaml with entity mappings
- Working categorization functions
- Ability to add `category` column to DataFrame
- Most transactions correctly categorized (minimize "Other")

---

## Step 7: Transfer Detection Module

### Objective
Identify internal transfers between accounts (Santander ↔ Imagine) and mark them with `is_transfer` flag.

### Files to Create/Modify
- `src/gastitis/transformers/transfer_detector.py` - Transfer detection logic

### Key Implementation Requirements

**Transfer patterns to detect**:
1. Transfers between Pierre Ianni and Ignacio Pastore (salary/payments)
2. Transfers between Delfina and Ignacio
3. Bizum between nacho and delfi
4. Any transaction with matching absolute amounts on same/nearby dates

**transfer_detector.py must**:
```python
import pandas as pd

def detect_transfers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mark internal transfers in the DataFrame.
    
    Detection strategies:
    1. Keyword-based:
       - "Transferencia De Pierre Ianni" (salary/income)
       - "Transferencia A Favor De Delfina Mathe"
       - "Bizum De Delfina Mathe"
    
    2. Amount matching (optional, more complex):
       - Find pairs of transactions with same absolute amount
       - Within 3 days of each other
       - Opposite signs (one positive, one negative)
       - Different persons
    
    Add is_transfer boolean column.
    """
    df['is_transfer'] = False
    
    # Keyword-based detection
    transfer_keywords = [
        'PIERRE IANNI',
        'DELFINA MATHE',
        'IGNACIO PASTORE',
        'TRANSFERENCIA INMEDIATA DE',
        'TRANSFERENCIA INMEDIATA A FAVOR DE'
    ]
    
    for keyword in transfer_keywords:
        df.loc[df['raw_description'].str.contains(keyword, case=False, na=False), 'is_transfer'] = True
    
    # Optional: amount-based matching
    # (implement if keyword-based is insufficient)
    
    return df
```

### Dependencies
- Step 3 or 4 completed (to have DataFrames)
- Step 5 completed (merchant normalization helps identify transfer recipients)

### Testing/Validation
- Test with known transfers from 202508.xls:
  - "Transferencia De Pierre Ianni, Concepto Varios."
  - "Transferencia Inmediata A Favor De Delfina Mathe Leitner"
  - "Bizum De Delfina Mathe Concepto..."
- Verify these are marked as `is_transfer = True`
- Verify regular purchases are `is_transfer = False`
- Check for false positives/negatives
- Document any ambiguous cases

### Expected Outputs
- Working `detect_transfers()` function
- Ability to add `is_transfer` column to DataFrame
- Known transfers correctly identified
- Minimal false positives

---

## Step 8: Unified DataFrame Builder

### Objective
Combine all parsed transactions from both banks into a single unified DataFrame with all transformations applied and stable transaction IDs generated.

### Files to Create/Modify
- `src/gastitis/pipeline/__init__.py` - Pipeline package
- `src/gastitis/pipeline/unify.py` - DataFrame unification logic

### Key Implementation Requirements

**unify.py must**:
```python
import pandas as pd
import hashlib
from pathlib import Path
from gastitis.parsers.santander import parse_santander_xls
from gastitis.parsers.imagine import parse_imagine_csv
from gastitis.transformers.merchant_normalizer import process_merchants
from gastitis.transformers.categorizer import categorize_transactions
from gastitis.transformers.transfer_detector import detect_transfers

def generate_transaction_id(row: pd.Series) -> str:
    """
    Generate stable transaction ID from row data.
    
    Hash components:
    - bank_name
    - person
    - date (as string)
    - amount
    - raw_description
    
    Returns: SHA256 hash (first 16 chars for readability)
    """
    components = f"{row['bank_name']}|{row['person']}|{row['date']}|{row['amount']}|{row['raw_description']}"
    hash_obj = hashlib.sha256(components.encode('utf-8'))
    return hash_obj.hexdigest()[:16]

def build_unified_dataframe(raw_dir: Path) -> pd.DataFrame:
    """
    Build unified DataFrame from all raw bank exports.
    
    Steps:
    1. Parse all Santander XLS files from raw_dir/Santander/
    2. Parse all Imagine CSV files from raw_dir/Imagine/
    3. Concatenate all DataFrames
    4. Apply merchant normalization
    5. Apply categorization
    6. Detect transfers
    7. Generate transaction IDs
    8. Validate schema
    9. Return unified DataFrame
    """
    dfs = []
    
    # Parse Santander files
    santander_dir = raw_dir / "Santander"
    for xls_file in santander_dir.glob("*.xls"):
        df = parse_santander_xls(xls_file)
        dfs.append(df)
    
    # Parse Imagine files
    imagine_dir = raw_dir / "Imagine"
    for csv_file in imagine_dir.glob("*.csv"):
        df = parse_imagine_csv(csv_file)
        dfs.append(df)
    
    # Combine
    unified = pd.concat(dfs, ignore_index=True)
    
    # Transform
    unified = process_merchants(unified)
    unified = categorize_transactions(unified)
    unified = detect_transfers(unified)
    
    # Generate IDs
    unified['transaction_id'] = unified.apply(generate_transaction_id, axis=1)
    
    # Validate and return
    validate_schema(unified)
    return unified

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate unified DataFrame has all required columns.
    
    Required columns:
    - transaction_id
    - bank_name
    - person
    - date
    - amount
    - raw_description
    - normalized_merchant
    - category
    - is_transfer
    - source_file
    """
    required_cols = [
        'transaction_id', 'bank_name', 'person', 'date', 'amount',
        'raw_description', 'normalized_merchant', 'category', 
        'is_transfer', 'source_file'
    ]
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Check data types
    assert df['date'].dtype == 'datetime64[ns]', "Date must be datetime64"
    assert df['amount'].dtype in ['float64', 'int64'], "Amount must be numeric"
    assert df['is_transfer'].dtype == 'bool', "is_transfer must be boolean"
```

### Dependencies
- Steps 3-7 completed (all parsers and transformers)

### Testing/Validation
- Run `build_unified_dataframe()` with data_raw/ directory
- Verify all XLS and CSV files are processed
- Check row count matches sum of individual files
- Verify all columns are present
- Check for duplicate transaction IDs (should be none)
- Verify date ranges are reasonable
- Check category distribution
- Verify person assignments (Santander→nacho, Imagine→delfi)
- Print summary statistics

### Expected Outputs
- Working `build_unified_dataframe()` function
- Single DataFrame with all transactions from both banks
- All transformations applied
- Stable transaction IDs
- Valid schema ready for export/loading

---

## Step 9: Database Loader

### Objective
Load the unified DataFrame into PostgreSQL star schema, populating dimension tables and fact table with proper foreign key relationships.

### Files to Create/Modify
- `src/gastitis/db/loader.py` - Database loading logic

### Key Implementation Requirements

**loader.py must**:
```python
import pandas as pd
from sqlalchemy import Engine, text

def load_dimensions(engine: Engine, df: pd.DataFrame) -> dict:
    """
    Populate dimension tables and return ID mappings.
    
    Returns:
    {
        'banks': {'Santander': 1, 'Imagine': 2},
        'persons': {'nacho': 1, 'delfi': 2},
        'merchants': {'LIDL': 1, 'MERCADONA': 2, ...},
        'categories': {'Groceries': 1, 'Utilities': 2, ...}
    }
    """
    mappings = {}
    
    # Banks
    banks = df['bank_name'].unique()
    with engine.begin() as conn:
        for bank in banks:
            conn.execute(text(
                "INSERT INTO banks (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"
            ), {'name': bank})
        
        result = conn.execute(text("SELECT bank_id, name FROM banks"))
        mappings['banks'] = {row.name: row.bank_id for row in result}
    
    # Persons (similar pattern)
    # Merchants (similar pattern)
    # Categories (similar pattern)
    
    return mappings

def load_fact_table(engine: Engine, df: pd.DataFrame, mappings: dict) -> None:
    """
    Load transactions fact table with foreign key IDs.
    
    Steps:
    1. Add ID columns to DataFrame
    2. Map names to IDs using mappings
    3. Select only needed columns for fact table
    4. Load to database (append or replace)
    """
    # Add FK columns
    df['bank_id'] = df['bank_name'].map(mappings['banks'])
    df['person_id'] = df['person'].map(mappings['persons'])
    df['merchant_id'] = df['normalized_merchant'].map(mappings['merchants'])
    df['category_id'] = df['category'].map(mappings['categories'])
    
    # Select fact table columns
    fact_df = df[[
        'transaction_id', 'bank_id', 'person_id', 'merchant_id', 'category_id',
        'date', 'amount', 'raw_description', 'is_transfer', 'source_file'
    ]]
    
    # Load to database
    fact_df.to_sql('transactions', engine, if_exists='append', index=False)

def load_to_database(df: pd.DataFrame, db_url: str) -> None:
    """
    Complete database loading process.
    
    1. Create engine
    2. Load dimensions
    3. Load fact table
    """
    from gastitis.db.connection import get_engine
    
    engine = get_engine(db_url)
    mappings = load_dimensions(engine, df)
    load_fact_table(engine, df, mappings)
    
    print(f"Loaded {len(df)} transactions to database")
```

### Dependencies
- Step 2 completed (database schema)
- Step 8 completed (unified DataFrame)
- PostgreSQL running and accessible

### Testing/Validation
- Create test database
- Run `load_to_database()` with sample unified DataFrame
- Query dimension tables to verify data
- Query transactions fact table
- Verify foreign key relationships
- Check for data integrity (no NULL in required fields)
- Test idempotency (can run multiple times without duplicates)
- Verify transaction counts match DataFrame

### Expected Outputs
- Working database loader
- Populated dimension tables
- Populated fact table with proper FKs
- Data ready for Tableau queries

---

## Step 10: Parquet Exporter

### Objective
Export the unified DataFrame to Parquet format for archival and alternative analytics workflows.

### Files to Create/Modify
- `src/gastitis/exporters/__init__.py` - Exporters package
- `src/gastitis/exporters/parquet_exporter.py` - Parquet export logic

### Key Implementation Requirements

**parquet_exporter.py must**:
```python
import pandas as pd
from pathlib import Path

def export_to_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """
    Export unified DataFrame to Parquet file.
    
    Args:
        df: Unified DataFrame with all transformations
        output_path: Path to output .parquet file
    
    Features:
    - Use snappy compression
    - Preserve datetime types
    - Include metadata
    - Validate before export
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export with compression
    df.to_parquet(
        output_path,
        engine='pyarrow',
        compression='snappy',
        index=False
    )
    
    # Verify file was created
    if not output_path.exists():
        raise IOError(f"Failed to create Parquet file: {output_path}")
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Exported {len(df)} rows to {output_path}")
    print(f"File size: {file_size_mb:.2f} MB")

def read_parquet(file_path: Path) -> pd.DataFrame:
    """
    Read Parquet file back into DataFrame.
    
    Useful for:
    - Loading data without reprocessing
    - Validation
    - Alternative to database
    """
    return pd.read_parquet(file_path, engine='pyarrow')
```

### Dependencies
- Step 8 completed (unified DataFrame)
- pyarrow installed (already in pyproject.toml)

### Testing/Validation
- Export sample unified DataFrame to Parquet
- Verify file is created in data_processed/
- Read file back and compare with original DataFrame
- Check file size is reasonable (should be compressed)
- Verify datetime columns are preserved
- Test with large DataFrame (all transactions)

### Expected Outputs
- Working Parquet export function
- Compressed Parquet file in data_processed/
- Ability to read back without data loss
- Alternative to database for some analyses

---

## Step 11: CLI with Typer

### Objective
Create a command-line interface to orchestrate the entire ETL pipeline and provide utility commands.

### Files to Create/Modify
- `src/gastitis/cli.py` - Typer CLI application
- `pyproject.toml` - Add CLI entry point

### Key Implementation Requirements

**Update pyproject.toml**:
```toml
[project.scripts]
gastitis = "gastitis.cli:app"
```

**cli.py must include**:
```python
import typer
from pathlib import Path
from gastitis.pipeline.unify import build_unified_dataframe
from gastitis.exporters.parquet_exporter import export_to_parquet
from gastitis.db.loader import load_to_database
from gastitis.db.schema import create_schema
from gastitis.db.connection import get_engine

app = typer.Typer(help="Home Expenses ETL Pipeline")

@app.command()
def run(
    raw_dir: Path = typer.Option("data_raw", help="Directory with raw bank exports"),
    output_file: Path = typer.Option("data_processed/transactions.parquet", help="Output Parquet file"),
    db_url: str = typer.Option(None, help="PostgreSQL connection URL (optional)")
):
    """
    Run the complete ETL pipeline.
    
    Steps:
    1. Parse all bank exports from raw_dir
    2. Apply transformations
    3. Export to Parquet
    4. Load to database (if db_url provided)
    """
    typer.echo(f"🏦 Processing bank exports from {raw_dir}...")
    df = build_unified_dataframe(raw_dir)
    
    typer.echo(f"✅ Processed {len(df)} transactions")
    typer.echo(f"📊 Summary:")
    typer.echo(f"  - Banks: {df['bank_name'].nunique()}")
    typer.echo(f"  - Date range: {df['date'].min()} to {df['date'].max()}")
    typer.echo(f"  - Total amount: {df['amount'].sum():.2f} EUR")
    
    typer.echo(f"\n💾 Exporting to {output_file}...")
    export_to_parquet(df, output_file)
    
    if db_url:
        typer.echo(f"\n🗄️  Loading to database...")
        load_to_database(df, db_url)
        typer.echo("✅ Database loaded successfully")
    
    typer.echo("\n✨ Pipeline completed!")

@app.command()
def init_db(
    db_url: str = typer.Option(..., help="PostgreSQL connection URL")
):
    """
    Initialize database schema.
    """
    typer.echo(f"Creating database schema...")
    engine = get_engine(db_url)
    create_schema(engine)
    typer.echo("✅ Schema created successfully")

@app.command()
def validate(
    file: Path = typer.Argument(..., help="Parquet file to validate")
):
    """
    Validate a Parquet file.
    """
    from gastitis.exporters.parquet_exporter import read_parquet
    from gastitis.pipeline.unify import validate_schema
    
    typer.echo(f"Validating {file}...")
    df = read_parquet(file)
    validate_schema(df)
    typer.echo(f"✅ File is valid ({len(df)} rows)")

if __name__ == "__main__":
    app()
```

### Dependencies
- All previous steps completed
- Typer installed (already in pyproject.toml)

### Testing/Validation
- Reinstall package: `uv pip install -e .`
- Test commands:
  ```bash
  uv run gastitis --help
  uv run gastitis run --raw-dir data_raw --output-file data_processed/transactions.parquet
  uv run gastitis init-db --db-url postgresql://localhost/expenses_test
  uv run gastitis validate data_processed/transactions.parquet
  ```
- Verify all commands work
- Check help text is clear
- Test error handling (bad paths, missing DB, etc.)

### Expected Outputs
- Working CLI with multiple commands
- User-friendly command-line interface
- Ability to run full pipeline with one command
- Helpful error messages and progress indicators

---

## Step 12: Comprehensive Tests

### Objective
Create a complete test suite covering parsers, transformers, pipeline, and database operations.

### Files to Create/Modify
- `tests/test_config_loader.py` - Config loading tests
- `tests/test_parsers.py` - Parser tests
- `tests/test_transformers.py` - Transformer tests
- `tests/test_pipeline.py` - Integration tests
- `tests/test_db.py` - Database tests
- `tests/fixtures/` - Test data fixtures

### Key Implementation Requirements

**Test structure**:
```python
# tests/test_parsers.py
import pytest
from pathlib import Path
from gastitis.parsers.santander import parse_santander_xls

def test_parse_santander_xls():
    """Test Santander parser with actual 202508.xls file."""
    test_file = Path("data_raw/Santander/202508.xls")
    df = parse_santander_xls(test_file)
    
    # Verify structure
    assert 'date' in df.columns
    assert 'amount' in df.columns
    assert 'raw_description' in df.columns
    assert 'bank_name' in df.columns
    assert 'person' in df.columns
    
    # Verify data
    assert len(df) > 0
    assert (df['bank_name'] == 'Santander').all()
    assert (df['person'] == 'nacho').all()
    assert df['date'].dtype == 'datetime64[ns]'

# tests/test_transformers.py
from gastitis.transformers.merchant_normalizer import extract_merchant, normalize_merchant

@pytest.mark.parametrize("description,expected", [
    ("Pago Movil En Lidl, Zaragoza, Tarj. :*135542", "Lidl"),
    ("Compra Mercadona, Barcelona, Tarjeta 516...", "Mercadona"),
    ("Transferencia De Pierre Ianni, Concepto Varios", "Pierre Ianni"),
])
def test_extract_merchant(description, expected):
    """Test merchant extraction from various description formats."""
    result = extract_merchant(description)
    assert expected.lower() in result.lower()

# tests/test_pipeline.py
def test_build_unified_dataframe():
    """Test full pipeline integration."""
    from gastitis.pipeline.unify import build_unified_dataframe
    
    df = build_unified_dataframe(Path("data_raw"))
    
    # Verify all required columns exist
    required_cols = [
        'transaction_id', 'bank_name', 'person', 'date', 'amount',
        'raw_description', 'normalized_merchant', 'category', 
        'is_transfer', 'source_file'
    ]
    for col in required_cols:
        assert col in df.columns
    
    # Verify no duplicate transaction IDs
    assert df['transaction_id'].is_unique
    
    # Verify categories are valid
    from gastitis.config_loader import get_valid_categories
    valid_categories = get_valid_categories() + ['Other']
    assert df['category'].isin(valid_categories).all()
```

### Dependencies
- All previous steps completed
- pytest installed (already in dev dependencies)
- Test data available in data_raw/

### Testing/Validation
- Run full test suite: `uv run pytest tests/ -v`
- Ensure all tests pass
- Check test coverage: `uv run pytest --cov=gastitis tests/`
- Aim for >80% code coverage
- Document any tests that require specific setup (DB, etc.)

### Expected Outputs
- Comprehensive test suite
- All tests passing
- Good code coverage
- Confidence in code quality
- Easy to add new tests

---

## Step 13: Data Validation and Quality Checks

### Objective
Implement data quality validation to detect issues in the pipeline output.

### Files to Create/Modify
- `src/gastitis/validators/__init__.py` - Validators package
- `src/gastitis/validators/data_quality.py` - Quality check functions
- Update CLI to include validate command with quality checks

### Key Implementation Requirements

**data_quality.py must include**:
```python
import pandas as pd
from datetime import datetime, timedelta

class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def add_error(self, message: str):
        self.errors.append(message)
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_info(self, message: str):
        self.info.append(message)
    
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def print_report(self):
        """Print validation report."""
        if self.errors:
            print("❌ ERRORS:")
            for err in self.errors:
                print(f"  - {err}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warn in self.warnings:
                print(f"  - {warn}")
        
        if self.info:
            print("\nℹ️  INFO:")
            for info in self.info:
                print(f"  - {info}")
        
        if self.is_valid():
            print("\n✅ Validation passed!")

def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """
    Run all quality checks on DataFrame.
    """
    result = ValidationResult()
    
    # Check for null values in required fields
    required_fields = ['transaction_id', 'bank_name', 'person', 'date', 'amount']
    for field in required_fields:
        null_count = df[field].isna().sum()
        if null_count > 0:
            result.add_error(f"{field} has {null_count} null values")
    
    # Check date ranges
    today = datetime.now()
    future_dates = df[df['date'] > today]
    if len(future_dates) > 0:
        result.add_error(f"{len(future_dates)} transactions have future dates")
    
    old_threshold = today - timedelta(days=365*5)  # 5 years ago
    old_dates = df[df['date'] < old_threshold]
    if len(old_dates) > 0:
        result.add_warning(f"{len(old_dates)} transactions are older than 5 years")
    
    # Check amount ranges
    if df['amount'].min() < -100000 or df['amount'].max() > 100000:
        result.add_warning("Some amounts are unusually large (>100k)")
    
    # Check for duplicate transaction IDs
    duplicates = df[df['transaction_id'].duplicated()]
    if len(duplicates) > 0:
        result.add_error(f"{len(duplicates)} duplicate transaction IDs found")
    
    # Check category distribution
    from gastitis.config_loader import get_valid_categories
    valid_categories = get_valid_categories() + ['Other']
    invalid_categories = df[~df['category'].isin(valid_categories)]
    if len(invalid_categories) > 0:
        result.add_error(f"{len(invalid_categories)} transactions have invalid categories")
    
    other_pct = (df['category'] == 'Other').sum() / len(df) * 100
    if other_pct > 20:
        result.add_warning(f"{other_pct:.1f}% of transactions are in 'Other' category (consider improving categorization)")
    
    # Check person assignments
    santander_wrong = df[(df['bank_name'] == 'Santander') & (df['person'] != 'nacho')]
    if len(santander_wrong) > 0:
        result.add_error(f"{len(santander_wrong)} Santander transactions not assigned to 'nacho'")
    
    imagine_wrong = df[(df['bank_name'] == 'Imagine') & (df['person'] != 'delfi')]
    if len(imagine_wrong) > 0:
        result.add_error(f"{len(imagine_wrong)} Imagine transactions not assigned to 'delfi'")
    
    # Info: summary statistics
    result.add_info(f"Total transactions: {len(df)}")
    result.add_info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    result.add_info(f"Banks: {df['bank_name'].unique().tolist()}")
    result.add_info(f"Categories: {df['category'].value_counts().to_dict()}")
    result.add_info(f"Transfer rate: {(df['is_transfer'].sum() / len(df) * 100):.1f}%")
    
    return result
```

### Dependencies
- Step 8 completed (unified DataFrame)
- Step 11 completed (CLI to add validate command)

### Testing/Validation
- Create test DataFrame with known issues (future dates, nulls, etc.)
- Run validation and verify issues are detected
- Test with clean DataFrame and verify it passes
- Integrate into CLI validate command
- Run on actual data and review warnings/errors

### Expected Outputs
- Working validation framework
- Clear error/warning/info reporting
- Integration with CLI
- Confidence in data quality

---

## Step 14: Documentation and Usage Examples

### Objective
Create comprehensive documentation for users and developers.

### Files to Create/Modify
- `docs/USAGE.md` - User guide
- `docs/SETUP.md` - Setup instructions
- `docs/EXAMPLES.md` - Example configurations
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- Update `README.md` - Project overview

### Key Implementation Requirements

**USAGE.md should include**:
- How to download bank exports
- Where to place CSV/XLS files
- How to run the pipeline
- How to connect Tableau to PostgreSQL
- Command examples with explanations

**SETUP.md should include**:
- Environment setup with uv
- PostgreSQL installation (Docker command)
- Database creation
- Initial configuration
- Dependency installation

**EXAMPLES.md should include**:
```yaml
# Example categories.yaml
Housing:
  keywords: ["alquiler", "rent"]
  entities: ["MARTA SANZ VICTORIA"]

# Example merchant_aliases.yaml
LIDL:
  patterns: ["lidl", "li dl"]
```

**TROUBLESHOOTING.md should include**:
- Parser errors (malformed CSV/XLS)
- Database connection errors
- Missing config files
- Date parsing issues
- Category mapping problems

**README.md should include**:
```markdown
# Home Expenses ETL Pipeline

Transform bank transaction exports into analytics-ready data.

## Quick Start

1. Install dependencies: `uv sync`
2. Place bank exports in `data_raw/`
3. Run pipeline: `uv run gastitis run`

## Features

- ✅ Parse multiple bank formats (Santander XLS, Imagine CSV)
- ✅ Automatic merchant normalization
- ✅ Category assignment
- ✅ Transfer detection
- ✅ PostgreSQL star schema
- ✅ Parquet export
- ✅ Tableau-ready

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Setup Instructions](docs/SETUP.md)
- [Examples](docs/EXAMPLES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
```

### Dependencies
- All previous steps completed (to document)

### Testing/Validation
- Follow setup instructions on a fresh system
- Verify all commands work as documented
- Check examples are accurate
- Get feedback from a test user if possible

### Expected Outputs
- Complete documentation
- Easy onboarding for new users
- Clear examples
- Updated README

---

## Step 15: Logging and Error Handling

### Objective
Add production-ready logging and error handling throughout the pipeline.

### Files to Create/Modify
- `src/gastitis/utils/__init__.py` - Utils package
- `src/gastitis/utils/logging.py` - Logging configuration
- `src/gastitis/utils/errors.py` - Custom exception classes
- Update all modules to use logging

### Key Implementation Requirements

**logging.py must include**:
```python
import logging
from pathlib import Path

def setup_logging(log_file: Path = None, level: str = "INFO"):
    """
    Configure logging for the application.
    
    Args:
        log_file: Optional file path for log output
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper())
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Root logger
    root_logger = logging.getLogger('gastitis')
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get logger for a module."""
    return logging.getLogger(f'gastitis.{name}')
```

**errors.py must include**:
```python
class GastitisError(Exception):
    """Base exception for gastitis package."""
    pass

class ParserError(GastitisError):
    """Error parsing bank export file."""
    pass

class ConfigError(GastitisError):
    """Error loading or validating configuration."""
    pass

class DatabaseError(GastitisError):
    """Error with database operations."""
    pass

class ValidationError(GastitisError):
    """Data validation error."""
    pass
```

**Update modules to use logging**:
```python
# Example in parsers/santander.py
from gastitis.utils.logging import get_logger
from gastitis.utils.errors import ParserError

logger = get_logger('parsers.santander')

def parse_santander_xls(file_path: Path) -> pd.DataFrame:
    logger.info(f"Parsing Santander XLS: {file_path}")
    
    try:
        # ... parsing logic ...
        logger.info(f"Successfully parsed {len(df)} transactions")
        return df
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        raise ParserError(f"Could not parse {file_path}") from e
```

### Dependencies
- All previous steps completed

### Testing/Validation
- Run pipeline with logging enabled
- Verify log messages are helpful
- Test error scenarios and check error messages
- Verify log file is created if specified
- Check different log levels (DEBUG, INFO, etc.)

### Expected Outputs
- Structured logging throughout application
- Helpful log messages for debugging
- Custom exceptions for better error handling
- Production-ready error reporting

---

## Conclusion

This 15-step implementation plan provides a complete roadmap to build your home expenses ETL pipeline. Each step is designed to be executed independently with clear objectives, requirements, and validation criteria.

### Recommended Execution Order

1. **Foundation** (Steps 1-2): Config and database setup
2. **Extraction** (Steps 3-4): Parsers for both banks
3. **Transformation** (Steps 5-7): Merchant, category, transfer logic
4. **Integration** (Step 8): Unified DataFrame
5. **Loading** (Steps 9-10): Database and Parquet export
6. **Interface** (Step 11): CLI
7. **Quality** (Steps 12-13): Tests and validation
8. **Production** (Steps 14-15): Documentation and logging

### Key Principles

- **Iterative**: Complete and test each step before moving on
- **Testable**: Each component should have tests
- **Documented**: Keep documentation up to date
- **Configurable**: Use YAML configs for flexibility
- **Reproducible**: Use `uv` for consistent environments

### Next Steps

Begin with Step 1 and work through sequentially. After completing all steps, you will have a complete, production-ready ETL pipeline for your personal finance analytics.

Good luck! 🚀
