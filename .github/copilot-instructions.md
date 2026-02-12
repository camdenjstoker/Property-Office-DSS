# AI Coding Agent Instructions - Property-Office-DSS

## Project Overview
**Property-Office-DSS** is a music department property inventory management system. It converts Excel spreadsheet data into SQL INSERT statements for populating a relational database with instrument, book, accessory, locker, financial, user, and key/lock inventory records.

## Core Architecture

### Data Flow (ETL Pattern)
The project follows a **three-phase ETL architecture** implemented in `sql_script.py`:

1. **EXTRACT** (`extract_from_excel`)
   - Reads all sheets from Excel file: `Property Office Instrument and Equipment List 4.xlsx`
   - Returns dictionary of dataframes, one per sheet
   - Handles file-not-found errors with helpful debugging messages

2. **TRANSFORM** (`transform_data`)
   - Maps Excel sheets to database tables via fuzzy name matching: `normalize_name()` strips spaces/underscores/capitalization
   - Enforces strict schema validation: `TARGET_TABLES` dict defines exact columns for each table
   - Generates transaction-wrapped INSERT statements (`BEGIN;` / `COMMIT;`)
   - Calls `format_sql_value()` for type-safe SQL generation (handles NULL, strings with escaped quotes, dates, numbers)

3. **LOAD** (`load_to_database` or `load_to_file`)
   - **Database option**: Executes INSERT statements directly in PostgreSQL using psycopg2
   - **File option**: Writes SQL to `property_office_inserts.sql` with timestamp header
   - User chooses between database execution or file output

### Database Schema
Located in `Database/Property Office Script.sql`. Seven core tables:
- **instrument** (13 columns) - Musical instruments with barcodes, serial numbers, condition tracking
- **books** (9 columns) - Library holdings with inventory dates
- **financial** (3 columns) - Transaction records
- **accessory** (5 columns) - Equipment accessories (brand, condition, location)
- **locker** (5 columns) - Storage lockers with locks and codes
- **user** (5 columns) - ⚠️ **Reserved word**: wrapped in double quotes in SQL generation
- **keys_locks** (4 columns) - Key/lock combination tracking

## Key Implementation Patterns

### Configuration Management
All inputs hardcoded at top of `sql_script.py`:
```python
INPUT_EXCEL_FILE = "Property Office Instrument and Equipment List 4.xlsx"
OUTPUT_SQL_FILE = 'property_office_inserts.sql'
DB_SCHEMA = 'public'
TARGET_TABLES = { ... }  # Strict schema definition
```
Users can override Excel path at runtime via `input()` prompt.

### SQL Value Formatting
Function `format_sql_value()` handles all type conversions:
- `pd.isna()` or empty string → `NULL`
- Strings → Single-quote-wrapped with escaped internal quotes: `"O'Connor"` → `'O''Connor'`
- Dates/datetimes → ISO format strings: `'YYYY-MM-DD'`
- Numbers → Unquoted

### Sheet-to-Table Matching
`normalize_name()` converts both Excel sheet names and target table names to lowercase, space-free format for flexible matching. Example: `"Keys Locks"` sheet matches `keys_locks` table.

### Reserved Word Handling
The `user` table is SQL-reserved, so it's wrapped in double quotes: `INSERT INTO public."user" (...)`

## Common Tasks

### Adding a New Table
1. Add entry to `TARGET_TABLES` dict with exact column list
2. Create corresponding Excel sheet with matching name (fuzzy matched by `normalize_name()`)
3. Ensure all columns are present in Excel or will be filled with `NULL`

### Debugging Failed Runs
- Check Excel file is not open in another program
- Verify sheet names match table names (case-insensitive, spaces ignored)
- Look for SQL syntax errors in generated output file
- Ensure all values in `TARGET_TABLES` columns correspond to actual Excel columns

### Extending SQL Generation
Modify `transform_data()` to add validation, logging, or post-processing. Remember:
- Transaction wrapping with `BEGIN;` / `COMMIT;` is already handled
- Always call `format_sql_value()` on data before inserting into SQL string

## Dependencies
- **pandas** - Excel file reading and dataframe manipulation
- **openpyxl** - Backend for `pd.read_excel()`
- **psycopg2-binary** - PostgreSQL database connectivity for direct database loading
- **sshtunnel** - SSH tunnel support for remote database access
- **datetime** - Timestamp generation in output headers

## Database Connection

The script connects to a remote PostgreSQL database through SSH tunnel:

**SSH Tunnel Setup:**
- SSH Host: 157.201.16.128
- SSH User: propoff
- SSH Password: propertyoffice

**Database Credentials:**
- Host: localhost (through SSH tunnel)
- Database: propertyoffice
- User: propoff
- Password: student
- Port: 5432

The script provides both automatic SSH tunnel setup and manual tunnel instructions.

## File References
- `sql_script.py` - Main ETL orchestration
- `Database/Property Office Script.sql` - Schema definition (MySQL format)
- `Database/Property Office Database.mwb` - MySQL Workbench model file
