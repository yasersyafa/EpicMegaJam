import json,hashlib
from pathlib import Path
baseline=json.loads(Path('Saved/GameplaySystemsBuild/protected_hashes.json').read_text())
changed=[name for name,digest in baseline.items() if not Path(name).exists() or hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
print('PROTECTED_PACKAGES_CHANGED',changed)
Path('Saved/GameplaySystemsIsolation.json').write_text(json.dumps({'protected_files':len(baseline),'changed':changed},indent=2))
assert not changed
