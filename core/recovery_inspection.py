"""Read-only recovery interpretation; never replay a filesystem operation."""
import json
import os
import hashlib
import stat
from pathlib import Path


def file_identity(path):
    """Bounded regular-file evidence; unsupported or unstable objects stay unknown."""
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or getattr(before, 'st_file_attributes', 0) & 1024 or before.st_size > 256_000_000:
            return None
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = path.lstat()
        keys = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns')
        if any(getattr(before, key) != getattr(after, key) for key in keys):
            return None
        return {'sha256':digest, 'size':after.st_size, 'inode':after.st_ino,
                'device':after.st_dev, 'mtime_ns':after.st_mtime_ns}
    except OSError:
        return None


def path_evidence(value):
    if not value:
        return {'state': 'UNKNOWN'}
    path = Path(value)
    try:
        info = path.lstat()
        return {'path': str(path), 'state': 'PRESENT', 'size': info.st_size,
                'mtime_ns': info.st_mtime_ns, 'inode': info.st_ino, 'mode': info.st_mode}
    except FileNotFoundError:
        return {'path': str(path), 'state': 'ABSENT'}
    except OSError as exc:
        return {'path': str(path), 'state': 'UNKNOWN', 'error': str(exc)}


def inspect_operation(conn, op_id):
    row = conn.execute('SELECT * FROM action_log WHERE id=?', (op_id,)).fetchone()
    if row is None:
        return {'state': 'UNDO_REQUIRES_REVIEW', 'reason': 'Missing journal receipt'}
    try:
        previous = json.loads(row['previous_state'] or '{}')
        current = json.loads(row['new_state'] or '{}')
        if not isinstance(previous, dict) or not isinstance(current, dict):
            raise ValueError('Receipt states must be objects')
        if row['action_type'] == 'file_move' and current.get('identity'):
            if not isinstance(current['identity'], dict) or not isinstance(current.get('path'), str) or not isinstance(previous.get('path'), str):
                raise ValueError('Incomplete identity-bound paths')
    except (ValueError, TypeError) as exc:
        return {'operation_id':op_id, 'state':'MANUAL_RECOVERY_REQUIRED',
                'journal_status':row['status'], 'reason':f'Invalid receipt evidence: {exc}', 'automatic_replay':False}
    source = path_evidence(previous.get('path'))
    destination = path_evidence(current.get('path') or previous.get('planned_changes', {}).get('dest'))
    if row['status'] == 'reversed':
        state = 'UNDO_COMPLETED'
    elif row['status'] == 'undo_blocked_by_drift':
        state = 'UNDO_BLOCKED_BY_DRIFT'
    elif row['status'] in {'running', 'reversing', 'manual_recovery_required'}:
        state = 'MANUAL_RECOVERY_REQUIRED'
    elif row['action_type'] == 'file_move' and source['state'] == 'PRESENT':
        state = 'UNDO_BLOCKED_BY_DRIFT'
    elif row['status'] == 'applied' and row['action_type'] == 'file_move' and current.get('identity'):
        identity = file_identity(Path(current['path']))
        parent = path_evidence(str(Path(previous['path']).parent))
        if identity is not None and identity != current['identity']:
            state = 'UNDO_BLOCKED_BY_DRIFT'
        elif identity == current['identity'] and source['state'] == 'ABSENT' and parent['state'] == 'PRESENT':
            try:
                same_volume = Path(previous['path']).parent.stat().st_dev == identity['device']
            except OSError:
                same_volume = False
            state = 'UNDO_AVAILABLE' if os.name == 'nt' and same_volume else 'UNDO_REQUIRES_REVIEW'
        else:
            state = 'UNDO_REQUIRES_REVIEW'
    else:
        # Historical success does not establish current content identity.
        state = 'UNDO_REQUIRES_REVIEW'
    return {'operation_id': op_id, 'state': state, 'journal_status': row['status'],
            'source': source, 'destination': destination, 'automatic_replay': False,
            'reason': 'Inspect current reality; path presence alone does not prove content identity or safe reversal.'}
