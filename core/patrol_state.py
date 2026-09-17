"""Restart-persistent operator posture; never a managed-mutation grant."""
import json

DEFAULT = {'lifecycle': 'CONSTRUCTION', 'mode': 'Sweep-and-Build',
           'authority': 'Shadow/explicit approval', 'paused': False}


def read_state(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS patrol_control_events (
        id INTEGER PRIMARY KEY, state_json TEXT NOT NULL, reason TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')))''')
    row = conn.execute('SELECT id,state_json FROM patrol_control_events ORDER BY id DESC LIMIT 1').fetchone()
    if row is None:
        conn.execute('INSERT INTO patrol_control_events(state_json,reason) VALUES(?,?)',
                     (json.dumps(DEFAULT), 'Gate A initial posture'))
        conn.commit()
        return read_state(conn)
    return {**json.loads(row[1]), 'version': row[0]}


def update_state(conn, *, version, paused, reason):
    if type(paused) is not bool or not isinstance(reason, str) or not reason.strip():
        raise ValueError('A boolean paused value and an explicit reason are required')
    read_state(conn)
    conn.execute('BEGIN IMMEDIATE')
    try:
        current = read_state(conn)
        if current['version'] != version:
            raise ValueError('Patrol state changed; refresh before retrying')
        state = {**DEFAULT, 'paused': paused}
        conn.execute('INSERT INTO patrol_control_events(state_json,reason) VALUES(?,?)',
                     (json.dumps(state), reason.strip()))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return read_state(conn)
