import sqlite3

conn = sqlite3.connect('C:/Users/tydaw/ai_assistant/assistant.db')

# Check table schema
schema = conn.execute('PRAGMA table_info(memories)').fetchall()
print('Memories table schema:')
for row in schema:
    print(f'  {row[1]} {row[2]} (NOT NULL: {bool(row[3])}, DEFAULT: {row[4]})')

# Check indexes
indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='memories'").fetchall()
print('\nIndexes:')
for idx in indexes:
    print(f'  {idx[0]}')

conn.close()
