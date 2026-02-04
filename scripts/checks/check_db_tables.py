import sqlite3

conn = sqlite3.connect('/app/data/ai_automation.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=" * 60)
print("TABLES IN DATABASE:")
print("=" * 60)
for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  Row count: {count}")
    
    # Check if it's pattern or synergy related
    if 'pattern' in table_name.lower() or 'synerg' in table_name.lower():
        print("  *** PATTERN/SYNERGY TABLE ***")
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print("  Sample data (first 3 rows):")
            for i, row in enumerate(rows, 1):
                print(f"    Row {i}: {row[:5] if len(row) > 5 else row}...")  # Show first 5 columns

conn.close()
