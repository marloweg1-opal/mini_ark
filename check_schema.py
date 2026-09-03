import sqlite3
conn = sqlite3.connect(r'C:\mini_ark\ark.sqlite')
print(conn.execute("SELECT sql FROM sqlite_master WHERE name='files';").fetchone()[0])
