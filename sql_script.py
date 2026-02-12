# Requirements: pandas, openpyxl, psycopg2-binary, sshtunnel
import pandas as pd
import os
import datetime
import psycopg2
from sshtunnel import SSHTunnelForwarder

# ==========================================
# CONFIGURATION
# ==========================================
# I have updated this to your specific local path using a raw string (r"...") 
# to handle the backslashes correctly.
INPUT_EXCEL_FILE = "Property Office Instrument and Equipment List 4.xlsx"
OUTPUT_SQL_FILE = 'property_office_inserts.sql'

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',  # Connect through SSH tunnel
    'user': 'propoff',
    'password': 'student',
    'database': 'propertyoffice',
    'port': 5432
}

# SSH Tunnel Configuration
SSH_CONFIG = {
    'ssh_address_or_host': ('157.201.16.128', 22),
    'ssh_username': 'propoff',
    'ssh_password': 'propertyoffice',
    'remote_bind_address': ('localhost', 5432),
    'local_bind_address': ('localhost', 5432)
}

# Strict Schema Definition - Updated to match actual database schema
TARGET_TABLES = {
    'instrument': [
        'instrument_type', 'instrument_section', 'instrument_barcode', 
        'instrument_call_number', 'instrument_serial_number', 'instrument_asset_tag', 
        'instrument_make', 'instrument_model', 'instrument_location', 
        'instrument_condition', 'last_inventory', 'last_cleaned', 'instrument_notes'
    ],
    'books': [
        'book_type', 'barcode', 'location', 'bookscol', 'quantity', 
        'condition', 'book_name', 'author', 'last_inventoried'  # Fixed: was 'last_inventory'
    ],
    'financial': [
        'financial_date', 'financial_amount', 'financial_type'
    ],
    'accessory': [
        'accessory_type', 'barcode', 'location', 'brand', 'condition'
    ],
    'locker': [
        'locker_type', 'locker_priority', 'locker_room', 'locks', 'locker_code'
    ],
    'user': [
        'f_name', 'l_name', 'I_num', 'Role', 'usercol'
    ],
    'keys_locks': [
        'locks_new_number', 'locks_old_number', 'combination', 'barcode'
    ]
}

# ==========================================
# PHASE 1: EXTRACT
# ==========================================
def extract_from_excel(file_path):
    """
    Loads the Excel file and separates it into raw dataframes (sheets).
    """
    print(f"[EXTRACT] Loading data from: {file_path}")
    
    if not os.path.exists(file_path):
        # Specific error message to help debug path issues
        raise FileNotFoundError(f"Could not find file at: {file_path}\nCheck that the file exists and is not open in Excel.")
        
    # Read all sheets at once
    try:
        raw_data = pd.read_excel(file_path, sheet_name=None)
        print(f"   -> Successfully loaded {len(raw_data)} sheets.")
        return raw_data
    except Exception as e:
        print(f"Debug: pd.read_excel failed with error type {type(e).__name__}: {e}")
        raise Exception(f"Failed to read Excel file: {e}")

# ==========================================
# PHASE 2: TRANSFORM
# ==========================================
def format_sql_value(value):
    """
    Helper to format Python values into SQL-safe strings strictly for text generation.
    - None -> NULL
    - String -> 'String' (escaped quotes)
    - Date -> 'YYYY-MM-DD'
    - Number -> Number
    """
    if pd.isna(value) or value == '':
        return "NULL"
    
    if isinstance(value, (int, float)):
        return str(value)
    
    if isinstance(value, (datetime.date, datetime.datetime)):
        return f"'{value}'"
    
    # Handle strings: Escape single quotes (O'Connor -> O''Connor)
    clean_str = str(value).replace("'", "''").strip()
    return f"'{clean_str}'"

def normalize_name(name):
    """Normalizes string to lowercase, no spaces (e.g., 'Keys Locks' -> 'keyslocks')"""
    return name.lower().replace(" ", "").replace("_", "")

def transform_data(raw_data):
    """
    Iterates through the raw data, identifies tables, and generates valid SQL statements.
    Returns a DataFrame with columns: table_name, sql_statement, sheet_name, row_count
    """
    print(f"[TRANSFORM] Processing data and generating SQL statements...")
    print(f"[TRANSFORM] Found {len(raw_data)} sheets in Excel file:")
    
    # Display all sheets found
    for i, sheet_name in enumerate(raw_data.keys(), 1):
        print(f"   {i}. {sheet_name}")
    
    # Initialize DataFrame to store results
    sql_data = []
    
    processed_sheets = set()
    
    for table_name, target_columns in TARGET_TABLES.items():
        # 1. Find matching sheet (fuzzy match)
        sheet_df = None
        matched_sheet_name = None
        for sheet_name, df in raw_data.items():
            if normalize_name(sheet_name) == normalize_name(table_name):
                sheet_df = df
                matched_sheet_name = sheet_name
                processed_sheets.add(sheet_name)
                break
        
        if sheet_df is None:
            print(f"   ⚠️  Skipping Table '{table_name}': No matching Excel sheet found.")
            continue

        print(f"   -> Processing Table: {table_name} (Sheet: '{matched_sheet_name}')")
        
        # Normalize Excel columns
        sheet_df.columns = [str(c).strip().lower() for c in sheet_df.columns]
        
        # 2. Build Insert Statement Template
        # Handle "user" reserved word by wrapping in double quotes
        safe_table_name = f'"{table_name}"' if table_name == 'user' else table_name
        
        cols_str = ", ".join([col for col in target_columns])
        
        row_count = 0
        for _, row in sheet_df.iterrows():
            values_list = []
            
            # 3. Extract & Clean Data (The Core Logic)
            for col in target_columns:
                # If column exists in Excel, take it. Else -> NULL
                if col.lower() in sheet_df.columns:
                    val = row[col.lower()]
                else:
                    val = None
                
                # Format the value for SQL
                formatted_val = format_sql_value(val)
                values_list.append(formatted_val)
            
            # 4. Construct the SQL String
            vals_str = ", ".join(values_list)
            sql = f"INSERT INTO {safe_table_name} ({cols_str}) VALUES ({vals_str});"
            # Add to DataFrame data
            sql_data.append({
                'table_name': table_name,
                'sql_statement': sql,
                'sheet_name': matched_sheet_name,
                'row_number': row_count + 1
            })
            
            row_count += 1
            
        print(f"      Generated {row_count} rows.")

    # Report any unmatched sheets
    unmatched_sheets = set(raw_data.keys()) - processed_sheets
    if unmatched_sheets:
        print(f"\n   ⚠️  {len(unmatched_sheets)} sheets were not matched to any table:")
        for sheet in unmatched_sheets:
            print(f"      - {sheet}")

    # Convert to DataFrame
    sql_df = pd.DataFrame(sql_data)
    print(f"\n   -> Total SQL statements generated: {len(sql_df)}")
    
    return sql_df

# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_db_connection():
    """
    Establishes database connection. First tries SSH tunnel, then direct connection.
    """
    print("\n--- Database Connection ---")
    print("Choose connection method:")
    print("1. Automatic SSH tunnel (recommended)")
    print("2. Direct connection (if SSH tunnel already established)")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == '1':
        return get_db_connection_ssh()
    else:
        return get_db_connection_direct()

def get_db_connection_ssh():
    """
    Establishes SSH tunnel and database connection.
    """
    try:
        print("[SSH] Establishing tunnel to 157.201.16.128...")

        # For now, provide manual instructions since auto-tunnel has compatibility issues
        print("⚠️  Automatic SSH tunnel setup has compatibility issues.")
        print("Please establish SSH tunnel manually:")
        print("1. Open a new terminal/command prompt")
        print("2. Run this command:")
        print("   ssh -L 5432:localhost:5432 -N propoff@157.201.16.128")
        print("3. Enter password: propertyoffice")
        print("4. Keep this terminal open and return here")
        input("Press Enter when SSH tunnel is established...")

        # Now connect through the tunnel
        connection = psycopg2.connect(
            host='localhost',
            port=5432,
            user='propoff',
            password='student',
            database='propertyoffice'
        )

        print("[DATABASE] Connected to propertyoffice database through SSH tunnel")
        return connection

    except Exception as e:
        print(f"❌ SSH tunnel connection failed: {e}")
        print("Falling back to direct connection...")
        return get_db_connection_direct()

def get_db_connection_direct():
    """
    Direct database connection (assumes SSH tunnel is already established).
    """
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        print(f"[DATABASE] Connected directly to {DB_CONFIG['database']} on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        return connection
    except Exception as e:
        raise Exception(f"Failed to connect to database: {e}")

# ==========================================
# PHASE 3: LOAD
# ==========================================
def load_to_database(sql_df):
    """
    Executes the SQL statements from the DataFrame against the database.
    """
    print(f"[LOAD] Executing {len(sql_df)} SQL statements in database...")
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Start transaction
        cursor.execute("BEGIN;")
        print("   -> Transaction started")
        
        # Execute each SQL statement
        executed_count = 0
        for _, row in sql_df.iterrows():
            try:
                cursor.execute(row['sql_statement'])
                executed_count += 1
                
                # Print progress every 100 statements
                if executed_count % 100 == 0:
                    print(f"      Executed {executed_count} statements...")
                    
            except Exception as e:
                print(f"   ❌ Error executing statement for {row['table_name']}: {e}")
                print(f"      SQL: {row['sql_statement'][:100]}...")
                raise e
        
        # Commit transaction
        connection.commit()
        print(f"   -> Transaction committed successfully")
        print(f"   -> Total statements executed: {executed_count}")
        
    except Exception as e:
        if connection:
            connection.rollback()
            print("   -> Transaction rolled back due to error")
        raise Exception(f"Database load failed: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("   -> Database connection closed")

def load_to_file(sql_df, output_path):
    """
    Writes the SQL statements from the DataFrame to a file (fallback option).
    """
    print(f"[LOAD] Writing SQL to '{output_path}'...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"-- ETL Generated SQL Script\n")
            f.write(f"-- Generated on: {datetime.datetime.now()}\n\n")
            f.write("BEGIN;\n\n")
            
            # Group by table for better organization
            for table_name in sql_df['table_name'].unique():
                table_statements = sql_df[sql_df['table_name'] == table_name]
                f.write(f"-- Inserts for {table_name}\n")
                
                for _, row in table_statements.iterrows():
                    f.write(row['sql_statement'] + "\n")
                
                f.write(f"-- End of inserts for {table_name}\n\n")
            
            f.write("COMMIT;\n")
                
        print(f"   -> Success! SQL file saved with {len(sql_df)} statements.")
    except Exception as e:
        raise Exception(f"Failed to write to file: {e}")

# ==========================================
# FILE VALIDATION
# ==========================================
def validate_file_exists(file_path):
    """
    Checks if the file exists at the given path.
    Returns True if file exists, False otherwise.
    """
    if os.path.exists(file_path):
        print(f"✅ File found: {os.path.abspath(file_path)}")
        return True
    else:
        print(f"❌ File not found: {file_path}")
        return False

def get_file_path():
    """
    Prompts user to provide Excel file path and validates existence.
    Returns valid file path or exits if file cannot be found.
    """
    while True:
        print("\n--- File Upload ---")
        print(f"Default file: {INPUT_EXCEL_FILE}")
        user_input = input("Enter the path to your Excel file (or press Enter to use default): ").strip('"').strip()
        
        # Use default if user pressed Enter
        excel_path = user_input if user_input else INPUT_EXCEL_FILE
        
        # Check if file exists
        if validate_file_exists(excel_path):
            return excel_path
        else:
            print("Note: Make sure your Excel file contains sheets with names like:")
            print("  - instrument, books, accessory, locker, user, keys_locks, financial")
            print("  - Sheet names are matched using fuzzy logic (spaces/case ignored)")
            retry = input("File does not exist. Try again? (yes/no): ").strip().lower()
            if retry != 'yes' and retry != 'y':
                print("❌ Exiting: No valid file provided.")
                exit(1)

# ==========================================
# MAIN ORCHESTRATION
# ==========================================
def run_etl():
    print("--- Starting ETL Process ---")
    
    # Step 0: Get and validate file path
    excel_path = get_file_path()
        
    try:
        # Step 1: Extract
        raw_data = extract_from_excel(excel_path)
        
        # Step 2: Transform
        sql_df = transform_data(raw_data)
        
        if len(sql_df) == 0:
            print("❌ No SQL statements generated. Check your Excel file and table mappings.")
            return
        
        # Step 3: Load - Choose destination
        print("\n--- Load Options ---")
        print("1. Load directly to database")
        print("2. Save to SQL file only")
        
        choice = input("Choose load method (1 or 2): ").strip()
        
        if choice == '1':
            load_to_database(sql_df)
            print("\n✅ ETL Process Complete - Data loaded to database!")
        elif choice == '2':
            load_to_file(sql_df, OUTPUT_SQL_FILE)
            print(f"\n✅ ETL Process Complete - SQL file saved to: {os.path.abspath(OUTPUT_SQL_FILE)}")
        else:
            print("❌ Invalid choice. Defaulting to file output.")
            load_to_file(sql_df, OUTPUT_SQL_FILE)
            print(f"\n✅ ETL Process Complete - SQL file saved to: {os.path.abspath(OUTPUT_SQL_FILE)}")
        
    except Exception as e:
        print(f"\n❌ ETL Failed: {e}")

if __name__ == "__main__":
    run_etl()