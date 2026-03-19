import pandas as pd
import os
import datetime

print('🚀 Running ETL for all sheets...')

# Extract
excel_file = 'test_inventory.xlsx'
print(f'[EXTRACT] Loading {excel_file}')
raw_data = pd.read_excel(excel_file, sheet_name=None)
print(f'   -> Found {len(raw_data)} sheets: {list(raw_data.keys())}')

# Transform
TARGET_TABLES = {
    'instrument': [
        'instrument_type', 'instrument_section', 'instrument_barcode',
        'instrument_call_number', 'instrument_serial_number', 'instrument_asset_tag',
        'instrument_make', 'instrument_model', 'instrument_location',
        'instrument_condition', 'last_inventory', 'last_cleaned', 'instrument_notes'
    ],
    'books': [
        'book_type', 'barcode', 'location', 'bookscol', 'quantity',
        'condition', 'book_name', 'author', 'last_inventoried'
    ]
}

def normalize_name(name):
    return name.lower().replace(' ', '').replace('_', '')

def format_sql_value(value):
    if pd.isna(value) or value == '':
        return 'NULL'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return f"'{value}'"
    clean_str = str(value).replace("'", "''").strip()
    return f"'{clean_str}'"

sql_statements = []
sql_statements.append('BEGIN;')

processed_sheets = set()
total_rows = 0

for table_name, target_columns in TARGET_TABLES.items():
    sheet_df = None
    matched_sheet_name = None
    for sheet_name, df in raw_data.items():
        if normalize_name(sheet_name) == normalize_name(table_name):
            sheet_df = df
            matched_sheet_name = sheet_name
            processed_sheets.add(sheet_name)
            break

    if sheet_df is None:
        print(f'⚠️  Skipping {table_name}: No matching sheet')
        continue

    print(f'✓ Processing {table_name} (Sheet: {matched_sheet_name})')

    # Normalize columns
    sheet_df.columns = [str(c).strip().lower() for c in sheet_df.columns]

    safe_table_name = f'"{table_name}"' if table_name == 'user' else table_name
    cols_str = ', '.join(target_columns)

    row_count = 0
    for _, row in sheet_df.iterrows():
        values_list = []
        for col in target_columns:
            val = row[col.lower()] if col.lower() in sheet_df.columns else None
            formatted_val = format_sql_value(val)
            values_list.append(formatted_val)

        vals_str = ', '.join(values_list)
        sql = f'INSERT INTO public.{safe_table_name} ({cols_str}) VALUES ({vals_str});'
        sql_statements.append(sql)
        row_count += 1
        total_rows += 1

    print(f'   -> Generated {row_count} INSERT statements')
    sql_statements.append(f'-- End of inserts for {table_name}')

sql_statements.append('COMMIT;')

print(f'✅ ETL Complete! Generated {len(sql_statements)} SQL statements for {total_rows} total rows')

# Show sample SQL
print('\n📋 Sample SQL statements:')
for i, sql in enumerate(sql_statements[:5]):
    print(f'{i+1}. {sql}')
if len(sql_statements) > 5:
    print(f'... and {len(sql_statements)-5} more statements')

# Save to file
output_file = 'property_office_inserts.sql'
print(f'\n💾 Saving to {output_file}...')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('-- ETL Generated SQL Script\n')
    f.write(f'-- Generated on: {datetime.datetime.now()}\n')
    f.write(f'-- Total sheets processed: {len(processed_sheets)}\n')
    f.write(f'-- Total rows: {total_rows}\n\n')

    for line in sql_statements:
        f.write(line + '\n')

print(f'✅ SQL file saved: {os.path.abspath(output_file)}')

# Show unmatched sheets
unmatched = set(raw_data.keys()) - processed_sheets
if unmatched:
    print(f'⚠️  {len(unmatched)} sheets not matched: {list(unmatched)}')