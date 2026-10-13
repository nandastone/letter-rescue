"""Validate Godot build identity and requirement-by-requirement completion evidence.

This gate validates provenance and declared coverage. Reviewing whether a proof
actually establishes its claim remains part of the final completion audit.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
SUITES = ('startup', 'room', 'objects', 'care', 'music', 'maze', 'theater',
          'nature', 'board', 'persistence', 'preferences', 'input', 'printing',
          'browser_audio', 'fresh_profile')
JOURNEYS = ('entrance_boy', 'entrance_girl', 'room_objects', 'room_return',
            'music_edit', 'maze_tutorial', 'maze_skip', 'maze_victory', 'theater',
            'nature_human', 'nature_robot', 'money_win', 'money_loss', 'chips')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sources(root=ROOT):
    project = root / 'treehouse-godot'
    paths = [project / name for name in ('project.godot', 'main.tscn', 'export_presets.cfg')]
    paths += sorted((project / 'scripts').rglob('*.gd'))
    paths += sorted((project / 'scripts').rglob('*.uid'))
    paths += [project / 'data/original.json']
    paths += sorted((project / 'data').glob('*.wav'))
    paths += sorted((project / 'data').glob('*.wav.import'))
    return {p.relative_to(root).as_posix():sha(p) for p in paths}


def web_files(directory):
    return {p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}


def reference(path, root=ROOT):
    return dict(path=path.resolve().relative_to(root.resolve()).as_posix(), sha256=sha(path))


def read_proof(ref, root=ROOT):
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
        raise ValueError('missing evidence reference')
    path = (root / ref['path']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('missing or external evidence file')
    if sha(path) != ref.get('sha256'):
        raise ValueError('changed evidence file')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('evidence must be an object')
    return value


def successful(result):
    if result.get('passed') is not True or result.get('errors'):
        return False
    checks = result.get('checks', [])
    return isinstance(checks, list) and all(isinstance(c, dict) and c.get('passed') is True for c in checks)


def evaluate(ledger, verification, root=ROOT):
    work = json.loads(ledger.read_text(encoding='utf-8'))
    index = json.loads(verification.read_text(encoding='utf-8'))
    checks, requirements = [], []
    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))
    check('Godot verification schema', index.get('schema') == 2 and index.get('runtime') == 'Godot')
    build, files = {}, {}
    try:
        build = read_proof(index.get('build'), root)
        directory = (root / build['web_directory']).resolve()
        assert directory.is_relative_to(root.resolve())
        files = web_files(directory)
        required = {'index.html', 'index.js', 'index.wasm', 'index.pck'}
        check('immutable Godot export and complete file inventory', successful(build) and build.get('runtime') == 'Godot'
              and required <= files.keys() and files == build.get('web_files')
              and fingerprint(files) == build.get('build_sha256'))
        current = sources(root)
        check('export source inventory matches current project', current == build.get('source_files')
              and fingerprint(current) == build.get('source_sha256'))
    except (OSError, ValueError, KeyError, AssertionError) as error:
        check('valid Godot build manifest', False, reason=str(error))

    def bound(ref, allowed, claims=()):
        try:
            envelope = read_proof(ref, root)
            result = read_proof(envelope.get('result'), root)
            valid = successful(envelope) and successful(result) and envelope.get('scope') in allowed
            valid = valid and bool(build.get('build_sha256')) and envelope.get('build_sha256') == build.get('build_sha256')
            valid = valid and envelope.get('source_sha256') == build.get('source_sha256')
            valid = valid and set(claims) <= set(envelope.get('claims', []))
            execution = envelope.get('execution', {})
            valid = valid and execution.get('exit_code') == 0 and bool(execution.get('command'))
            verifier_files = envelope.get('verifier_files', {})
            valid = valid and bool(verifier_files)
            for name, digest in verifier_files.items():
                path = (root / name).resolve()
                valid = valid and path.is_relative_to(root.resolve()) and path.is_file() and sha(path) == digest
            if envelope.get('scope') in ('web', 'native_journey', 'strict_timing', 'native_audio'):
                valid = valid and result.get('web_files', result.get('files')) == files
            if envelope.get('scope') == 'native_journey':
                valid = valid and result.get('complete_journey') is True and result.get('ordinary_inputs') is True
            if envelope.get('scope') == 'desktop':
                artifacts = result.get('desktop_files', {})
                valid = valid and bool(artifacts)
                for name, digest in artifacts.items():
                    path = (root / name).resolve()
                    valid = valid and path.is_relative_to(root.resolve()) and path.is_file() and sha(path) == digest
            return bool(valid), result
        except (OSError, ValueError, KeyError, TypeError):
            return False, {}

    issues = work['issues']
    ids = [i['id'] for i in issues]
    if not issues or len(ids) != len(set(ids)):
        raise ValueError('Empty or duplicate issue list')
    expected_requirements = set()
    issue_results = {}
    for issue in issues:
        if issue['status'] not in ('open', 'in_progress', 'closed'):
            raise ValueError('Unknown issue status')
        if any(d not in ids for d in issue.get('depends_on', [])):
            raise ValueError('Unknown dependency')
        accepted = issue['status'] == 'closed'
        for number, text in enumerate(issue['acceptance'], 1):
            ident = f"{issue['id']}:{number}"
            expected_requirements.add(ident)
            item = index.get('requirements', {}).get(ident, {})
            proofs = item.get('evidence', [])
            valid = item.get('text') == text and item.get('reviewed') is True and bool(proofs)
            for proof in proofs:
                if issue['id'] == 'TH-001':
                    try:
                        valid = valid and successful(read_proof(proof, root))
                    except (OSError, ValueError, KeyError):
                        valid = False
                else:
                    allowed = {'web', 'native_journey', 'strict_timing', 'native_audio', 'desktop'}
                    if ident == 'TH-007:1':
                        allowed.add('component')  # Gate rejection tests, not gameplay coverage.
                    valid = valid and bound(proof, allowed, [ident])[0]
            requirements.append(dict(id=ident, text=text, passed=bool(valid), evidence_count=len(proofs)))
            accepted = accepted and valid
        issue_results[issue['id']] = bool(accepted)
    check('all ledger acceptance rows represented exactly', set(index.get('requirements', {})) == expected_requirements)
    for issue in issues:
        accepted = issue_results[issue['id']] and all(issue_results[d] for d in issue.get('depends_on', []))
        check(issue['id'] + ' ' + issue['title'], accepted, status=issue['status'])
    for category, names, allowed in [('suites', SUITES, {'web'}), ('native_journeys', JOURNEYS, {'native_journey'})]:
        for name in names:
            check(category + ': ' + name, bound(index.get(category, {}).get(name), allowed)[0])
    valid, timing = bound(index.get('strict_timing'), {'strict_timing'})
    check('strict unshifted timing and complete presentation', valid and timing.get('strict_timing_parity') is True
          and timing.get('unrepresented_native_displays') == 0 and timing.get('shifted_frames') == 0
          and timing.get('excluded_frames') == 0)
    valid, audio = bound(index.get('native_audio'), {'native_audio'})
    check('actual Godot audio waveform and event timing', valid and audio.get('waveform_parity') is True
          and audio.get('event_timing_parity') is True)
    check('desktop export and controls on the same source', bound(index.get('desktop'), {'desktop'})[0])
    check('full fidelity audit explicitly accepted', index.get('full_clone_parity') is True)
    check('no unresolved strict failures', index.get('known_failures') == [])
    try:
        delivery = read_proof(index.get('delivery'), root)
        rows = delivery.get('checks', [])
        delivered = {r['name']:r['served_sha256'] for r in rows}
        check('every served export file matches verified build', successful(delivery) and bool(files)
              and len(rows) == len(files) and delivered == files
              and delivery.get('build_sha256') == build.get('build_sha256'))
    except (OSError, ValueError, KeyError, TypeError):
        check('every served export file matches verified build', False)
    return dict(runtime='Godot', build_sha256=build.get('build_sha256'), pck_sha256=files.get('index.pck'),
                checks=checks, requirements=requirements, remaining=[i['id'] for i in issues if not issue_results[i['id']]],
                known_failures=index.get('known_failures', []),
                passed=all(c['passed'] for c in checks) and all(r['passed'] for r in requirements))
