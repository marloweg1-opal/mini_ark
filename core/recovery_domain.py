"""Derivative-only recovery orchestration contract, not retirement authority."""
from dataclasses import dataclass
from enum import IntEnum
import hashlib
import json
from pathlib import Path
from typing import Protocol


class Effort(IntEnum):
    OBSERVE = 0
    VALIDATE = 1
    DIAGNOSE = 2
    SAFE_RECONSTRUCTION = 3
    DEEP_RECOVERY = 4
    MAXIMUM_SAFE_RECOVERY = 5


@dataclass(frozen=True)
class RecoveryAuthority:
    scope: str
    max_effort: Effort = Effort.DIAGNOSE
    derivative_output_authorized: bool = False
    authority_receipt: str = ''
    output_scope: str = ''


class RecoveryProvider(Protocol):
    name: str
    levels: tuple[Effort, ...]

    def attempt(self, source: bytes, level: Effort) -> bytes | None: ...
    def prove_usable(self, candidate: bytes) -> dict: ...


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS recovery_attempts (
        id INTEGER PRIMARY KEY, provider TEXT NOT NULL, source_sha256 TEXT NOT NULL,
        effort TEXT NOT NULL, authority_receipt TEXT NOT NULL, state TEXT NOT NULL,
        proof_json TEXT, output_path TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')))''')


def recover_derivative(conn, source, output_root, provider, authority, *, max_bytes=16_000_000):
    """Trusted providers receive immutable bytes, never a source path or delete grant.

    No production repair providers are installed. This bounded orchestrator is
    exercised with disposable providers/fixtures before real repair execution.
    """
    from core.perception_policy import contains
    source, output_root = Path(source), Path(output_root)
    if not contains(authority.scope, str(source)):
        raise PermissionError('Source outside task authority')
    if not authority.derivative_output_authorized or not authority.authority_receipt:
        return {'state':'AWAITING_DERIVATIVE_AUTHORITY','retirement_authorized':False}
    if not authority.output_scope or not contains(authority.output_scope, str(output_root)):
        raise PermissionError('Derivative workspace outside task authority')
    from core.recovery_inspection import file_identity
    before = file_identity(source)
    if before is None or before['size'] > max_bytes:
        return {'state':'REVIEW','reason':'Source identity or byte budget not established'}
    if not output_root.is_dir() or output_root.is_symlink() or output_root.resolve() == source.parent.resolve():
        raise ValueError('A separate existing derivative workspace is required')
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != before['sha256']:
        return {'state':'REVIEW','reason':'Source changed during read'}
    initialize(conn)
    for level in sorted(set(provider.levels)):
        if level < Effort.SAFE_RECONSTRUCTION or level > authority.max_effort:
            continue
        cur = conn.execute('INSERT INTO recovery_attempts(provider,source_sha256,effort,authority_receipt,state) VALUES(?,?,?,?,?)',
            (provider.name,before['sha256'],level.name,authority.authority_receipt,'RUNNING'))
        conn.commit()
        attempt_id = cur.lastrowid
        try:
            candidate = provider.attempt(data,level)
            proof = provider.prove_usable(candidate) if isinstance(candidate,bytes) and 0 < len(candidate) <= max_bytes else {'usable':False,'reason':'No bounded output'}
            if file_identity(source) != before:
                raise RuntimeError('Source identity changed; stop recovery')
            if proof.get('usable') is not True or not proof.get('checks') or any(value is not True for value in proof['checks'].values()):
                conn.execute("UPDATE recovery_attempts SET state='REJECTED',proof_json=? WHERE id=?",(json.dumps(proof),attempt_id))
                conn.commit()
                continue
            output = output_root / f'recovery-{attempt_id}-{before["sha256"][:12]}.bin'
            conn.execute("UPDATE recovery_attempts SET state='WRITING_DERIVATIVE',output_path=?,proof_json=? WHERE id=?",(str(output),json.dumps(proof),attempt_id))
            conn.commit()
            with output.open('xb') as stream:
                stream.write(candidate)
                stream.flush()
                import os
                os.fsync(stream.fileno())
            if hashlib.sha256(output.read_bytes()).digest() != hashlib.sha256(candidate).digest():
                raise RuntimeError('Derivative write verification failed')
            conn.execute("UPDATE recovery_attempts SET state='VERIFIED' WHERE id=?",(attempt_id,))
            conn.commit()
            return {'state':'VERIFIED','output':str(output),'attempt_id':attempt_id,'proof':proof,'retirement_authorized':False}
        except Exception as exc:
            conn.execute("UPDATE recovery_attempts SET state='MANUAL_RECOVERY_REQUIRED',proof_json=? WHERE id=?",(json.dumps({'error':str(exc)}),attempt_id))
            conn.commit()
            return {'state':'MANUAL_RECOVERY_REQUIRED','attempt_id':attempt_id,'retirement_authorized':False}
    return {'state':'NO_PROVEN_RECOVERY','retirement_authorized':False}


def capability_status():
    return {'domain':'Recovery & Repair','effort_levels':[level.name for level in Effort],
            'patrol_mode':'structural_observation_only','task_mode':'bounded_derivative_contract',
            'production_repair_providers':[], 'originals':'immutable_by_default',
            'retirement_authority':False, 'semantic_providers_enabled':False}


def observe(path, size):
    from core.media_recovery import VIDEO, PHOTO
    return {'domain':'Recovery & Repair', 'effort':'OBSERVE',
            'state':'SUSPECT_EMPTY_MEDIA' if Path(path).suffix.lower() in VIDEO|PHOTO and size==0 else 'NOT_VALIDATED',
            'semantic_inspection':False,'repair_authorized':False}
