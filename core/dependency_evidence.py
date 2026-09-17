"""Bounded reference evidence. A negative search is never global clearance."""
import hashlib
import time
from pathlib import Path, PureWindowsPath
from core.patrol import live_discover
from core.reference_formats import structured_references

TEXT_EXTENSIONS={'.ini','.json','.toml','.yaml','.yml','.xml','.cfg','.conf','.lua','.ps1','.js','.css','.html','.md','.url'}


def inspect_references(targets, roots, *, max_files=100, max_bytes=2_000_000, max_seconds=5):
    started=time.monotonic()
    references=[]
    errors=[]
    checked=[]
    remaining=max_bytes
    coverage=[]
    structured=[]
    for root in roots:
        if len(checked)>=max_files or time.monotonic()-started>=max_seconds:
            errors.append({'scope':str(root),'reason':'budget_exhausted'})
            break
        rows,discovery=live_discover(str(root),max_files=max_files-len(checked),max_seconds=max(0.01,max_seconds-(time.monotonic()-started)))
        coverage.append({'scope':str(root),**discovery})
        for row in rows:
            path=Path(row['canonical_path'])
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            if remaining<=0 or len(checked)>=max_files or time.monotonic()-started>=max_seconds:
                errors.append({'path':str(path),'reason':'budget_exhausted'})
                break
            try:
                before=path.stat()
                if before.st_size>min(remaining,256_000):
                    errors.append({'path':str(path),'reason':'file_size_budget'})
                    continue
                with path.open('rb') as stream:
                    data=stream.read(min(remaining,256_000)+1)
                after=path.stat()
                if before.st_mtime_ns!=after.st_mtime_ns or before.st_size!=after.st_size or before.st_ino!=after.st_ino:
                    errors.append({'path':str(path),'reason':'changed_during_read'})
                    continue
                if len(data)>remaining:
                    errors.append({'path':str(path),'reason':'byte_budget'})
                    break
                remaining-=len(data)
                decoded=data.decode('utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='strict')
                text=decoded.casefold()
                fingerprint=hashlib.sha256(data).hexdigest()
                literals, parse_errors=structured_references(path,decoded)
                structured.extend({'reference':str(path),'fingerprint':fingerprint,**literal} for literal in literals)
                errors.extend({'path':str(path),'reason':'parse: '+error} for error in parse_errors)
                checked.append({'path':str(path),'fingerprint':fingerprint})
                for target in targets:
                    normalized=str(PureWindowsPath(target)).casefold()
                    forms={normalized,normalized.replace('\\','/'),normalized.replace('\\','\\\\')}
                    match='explicit_path' if any(form in text for form in forms) else 'basename_only' if PureWindowsPath(target).name.casefold() in text else None
                    if match:
                        references.append({'target':target,'reference':str(path),'match':match,'fingerprint':fingerprint})
                    for literal in literals:
                        resolved=literal.get('resolved','').casefold()
                        if resolved==normalized and match!='explicit_path':
                            references.append({'target':target,'reference':str(path),'match':'resolved_literal',
                                               'field':literal['field'],'fingerprint':fingerprint})
            except (OSError,UnicodeError) as exc:
                errors.append({'path':str(path),'reason':str(exc)})
    observations = [{'target':target, 'evidence_source':'bounded_configuration_inspection',
        'reference_observation':'REFERENCE_FOUND' if any(r['target']==target for r in references)
          else 'NO_REFERENCE_FOUND_WITHIN_BOUNDED_SEARCH',
        'dependency_state':'UNKNOWN', 'exhaustive_domain_proof':False} for target in targets]
    return {'references':references,'checked':checked,'errors':errors,'scope_coverage':coverage,
            'target_observations':observations,
            'structured_candidates':structured,'dependency_state':'UNKNOWN',
            'dependency_clearance':False,
            'reason':'Bounded text search excludes registry, binary, dynamic and unregistered references; absence of matches is not clearance.',
            'bytes_read':max_bytes-remaining}
