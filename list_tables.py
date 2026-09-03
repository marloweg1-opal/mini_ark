import sqlite3
conn = sqlite3.connect(r'C:\mini_ark\ark.sqlite')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
for t in tables:
    print(t[0])
