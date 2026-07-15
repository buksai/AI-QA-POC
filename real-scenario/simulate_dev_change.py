"""Simulates a developer refactoring the API (the kind of change that breaks tests).
Makes a REAL code change and a REAL git commit."""
import subprocess
import sys

PATH = "shop_api.py"

with open(PATH) as f:
    src = f.read()

if '"grandTotal"' in src:
    print("App already refactored. To reset the demo: git reset --hard origin/main")
    sys.exit(1)

src = src.replace('"total": total,', '"grandTotal": total,')
src = src.replace('"status": "created",', '"status": "CREATED",')

with open(PATH, "w") as f:
    f.write(src)

subprocess.run(["git", "add", PATH])
subprocess.run([
    "git", "-c", "user.email=dev@example.com", "-c", "user.name=Dev Team",
    "commit", "-m",
    "refactor(api): rename 'total' -> 'grandTotal', status enum uppercase"
])
print("\n>> Developer change applied and committed.")
print(">> Fields renamed: total -> grandTotal, status 'created' -> 'CREATED'")
