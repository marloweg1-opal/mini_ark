"""Registry-owned privacy policy. Resolution never opens content."""
import json
import ntpath

MODES = {'OPEN', 'LIMITED', 'SEALED'}


def normalize_scope(path):
    value = ntpath.normpath(str(path)).casefold()
    if not ntpath.isabs(value) or not ntpath.splitdrive(value)[0] or value.startswith('\\\\?\\'):
        raise ValueError('An absolute, non-device scope is required')
    return value.rstrip('\\') + ('\\' if value.endswith(':\\') else '')


def contains(root, path):
    root, path = normalize_scope(root), normalize_scope(path)
    return path == root or path.startswith(root.rstrip('\\') + '\\')


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS perception_policy_events (
        id INTEGER PRIMARY KEY, scope TEXT NOT NULL, mode TEXT NOT NULL,
        permissions_json TEXT NOT NULL, purposes_json TEXT NOT NULL,
        source_id TEXT, reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')))''')


def set_policy(conn, scope, mode, *, reason, purposes=(), retention=False, learning=False, source_id=None):
    if mode not in MODES or not isinstance(reason, str) or not reason.strip():
        raise ValueError('Known policy and explicit reason required')
    if type(retention) is not bool or type(learning) is not bool:
        raise ValueError('Separate boolean retention and learning permissions required')
    if isinstance(purposes, str) or any(not isinstance(p, str) or not p.strip() for p in purposes):
        raise ValueError('Purposes must be explicit nonempty strings')
    if mode == 'LIMITED' and not purposes:
        raise ValueError('LIMITED requires an explicit purpose')
    if mode == 'SEALED' and (retention or learning):
        raise ValueError('SEALED cannot grant semantic retention or learning')
    initialize(conn)
    cur = conn.execute('INSERT INTO perception_policy_events(scope,mode,permissions_json,purposes_json,source_id,reason) VALUES(?,?,?,?,?,?)',
        (normalize_scope(scope), mode, json.dumps({'semantic_retention_permission':retention,'learning_permission':learning}),
         json.dumps(list(purposes)),source_id,reason.strip()))
    conn.commit()
    return cur.lastrowid


def effective_policy(conn, path, *, purpose=None):
    target = normalize_scope(path)
    initialize(conn)
    rows = conn.execute('SELECT id,scope,mode,permissions_json,purposes_json,source_id FROM perception_policy_events ORDER BY id DESC').fetchall()
    matches = [r for r in rows if contains(r[1], target)]
    matches.sort(key=lambda r:(len(r[1]),r[0]), reverse=True)
    if not matches:
        return {'mode':'SEALED','version':0,'scope':None,'inherited':True,'source_id':None,
                'inspection_permission':'STRUCTURAL_ONLY','semantic_retention_permission':False,'learning_permission':False}
    row = matches[0]
    allowed = row[2]=='OPEN' or (row[2]=='LIMITED' and purpose in json.loads(row[4]))
    permissions = json.loads(row[3])
    return {'mode':row[2], 'version':row[0], 'scope':row[1], 'source_id':row[5], 'inherited':row[1]!=target,
            'inspection_permission':'SEMANTIC_ALLOWED' if allowed else 'STRUCTURAL_ONLY',
            'semantic_retention_permission':allowed and permissions['semantic_retention_permission'],
            'learning_permission':allowed and permissions['learning_permission']}


def semantic_gateway(conn, path, purpose, read_content, provider, *, providers_enabled=False):
    policy = effective_policy(conn, path, purpose=purpose)
    if policy['inspection_permission'] != 'SEMANTIC_ALLOWED' or not providers_enabled:
        raise PermissionError('Semantic provider disabled or scope does not permit this inspection')
    return provider(read_content()), policy
