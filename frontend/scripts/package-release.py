#!/usr/bin/env python3
"""Create a private Next runtime and a separate, allowlisted CDN tree.
Run after npm ci && npm run build on the intended host OS/architecture.
Never point a web server or bucket at the package root or private-runtime.
"""
from pathlib import Path
import argparse, csv, hashlib, json, platform, re, shutil, subprocess

PUBLIC_FILES = {'trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson'}
PRIVATE_RESOURCES = [
    'generated/trace-exploration-v2/production-read-model.json',
    'generated/trace-exploration-v3/CHECKSUMS.sha256',
    'generated/trace-exploration-v3/manifest.json',
    'generated/trace-exploration-v3/read-model.json',
]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def copy_tree(src, dst, ignore=None):
    # node_modules has legitimate executable symlinks; application assets must not.
    for p in src.rglob('*'):
        if p.is_symlink():
            raise ValueError(f'Symlink in application artifacts: {p}')
    shutil.copytree(src, dst, ignore=ignore)

def copy_build(source, destination):
    copy_tree(source, destination, lambda directory, names: [n for n in names if n in {'cache', 'trace'}] if Path(directory) == source else [])

def check_public(public, held):
    files = []
    for p in sorted(public.rglob('*')):
        if p.is_symlink():
            raise ValueError('Public symlink rejected')
        if not p.is_file():
            continue
        rel = p.relative_to(public).as_posix()
        if rel not in PUBLIC_FILES and not rel.startswith('_next/static/'):
            raise ValueError(f'Unexpected public resource: {rel}')
        if rel.startswith('_next/static/') and p.suffix not in {'.js', '.css', '.woff', '.woff2', '.ttf', '.otf', '.png', '.jpg', '.jpeg', '.webp', '.avif', '.svg', '.ico'}:
            raise ValueError(f'Unexpected client artifact: {rel}')
        if set(re.findall(rb'SURF-[A-Z0-9_-]+', p.read_bytes())) & held:
            raise ValueError(f'Held identifier in public resource: {rel}')
        files.append({'path': rel, 'sha256': digest(p), 'bytes': p.stat().st_size})
    if not files:
        raise ValueError('Empty public artifact')
    return files

def package(frontend, repository, output):
    if output.exists():
        raise ValueError('Output must be a new directory; never overwrite an earlier release')
    if not (frontend / '.next/BUILD_ID').is_file():
        raise ValueError('Completed production build required')
    config = (frontend / 'next.config.ts').read_text()
    if 'NormalModuleReplacementPlugin' not in config or 'ProductionUnavailablePage.tsx' not in config:
        raise ValueError('Audited production legacy-page exclusion is missing')
    for p in (frontend / 'public').rglob('*'):
        if p.is_symlink():
            raise ValueError('Public source symlink rejected')
        if p.is_file():
            rel = p.relative_to(frontend / 'public').as_posix()
            if rel not in PUBLIC_FILES and not rel.startswith('data/trace-v48/') and rel != 'data/public_surface_mock_v0.json':
                raise ValueError(f'Unreviewed public source: {rel}')
    ledger = repository / 'docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv'
    with ledger.open() as f:
        held = {row['surface_id_exact'].encode() for row in csv.DictReader(f, delimiter='\t') if row['research_disposition'] == 'held'}
    if not held:
        raise ValueError('Authoritative held ledger is empty')
    output.mkdir(parents=True)
    private = output / 'private-runtime'
    private.mkdir()
    copy_build(frontend / '.next', private / '.next')
    for rel in ['package.json', 'package-lock.json', 'next.config.ts', *PRIVATE_RESOURCES]:
        src = frontend / rel
        if src.is_symlink() or not src.is_file():
            raise ValueError(f'Missing or linked runtime input: {rel}')
        dst = private / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    # Dependencies are private and OS-specific. Rebuild on the eventual target;
    # keeping the full locked install also supplies TypeScript for next.config.ts.
    shutil.copytree(frontend / 'node_modules', private / 'node_modules', symlinks=True)
    public = output / 'cdn-public'
    public.mkdir()
    for rel in PUBLIC_FILES:
        dst = public / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(frontend / 'public' / rel, dst)
    copy_tree(frontend / '.next/static', public / '_next/static')
    public_inventory = check_public(public, held)
    shutil.copytree(public, private / 'public', ignore=shutil.ignore_patterns('_next'))
    runtime_inventory = []
    for p in sorted(private.rglob('*')):
        if p.is_file() and 'node_modules' not in p.relative_to(private).parts:
            runtime_inventory.append({'path': p.relative_to(private).as_posix(), 'sha256': digest(p), 'bytes': p.stat().st_size})
    manifest = {
        'schema': 1, 'build_id': (frontend / '.next/BUILD_ID').read_text().strip(),
        'os': platform.system(), 'architecture': platform.machine(),
        'node': subprocess.check_output(['node', '--version'], text=True).strip(),
        'lock_sha256': digest(frontend / 'package-lock.json'),
        'public_files': public_inventory, 'private_files': runtime_inventory,
        'dependencies': 'private-runtime/node_modules: complete locked installation; never publish; target OS rebuild required',
        'held_id_count_checked': len(held),
        'excluded': ['public/data/trace-v48/**', 'public/data/public_surface_mock_v0.json', '.env*', 'source fixtures', 'QA services and evidence', '.git', '.next/cache'],
        'result': 'PASS',
    }
    (output / 'release-artifact-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'result': 'PASS', 'build_id': manifest['build_id'], 'public_files': len(public_inventory), 'private_files': len(runtime_inventory), 'held_ids_checked': len(held)}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.frontend.resolve(), args.repository.resolve(), args.output.resolve())
