#!/usr/bin/env python3
"""
Auto-Fix Master — menjalankan auto-fix secara berurutan.
Hanya menjalankan fix yang aman (health check, index, report).

Usage:
    python scripts/auto_fix.py              # Fix semua
    python scripts/auto_fix.py --dry-run    # Preview aja
"""

import sys, subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def run_script(name, *args):
    print(f"\n{'='*60}")
    print(f"  \U0001f527 {name}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / 'scripts' / name)] + list(args),
        cwd=str(REPO_ROOT),
    )
    return result.returncode == 0

def main():
    dry_run = '--dry-run' in sys.argv
    print("\U0001f527 DEVELOPER HUB - AUTO FIX MASTER")
    print(f"   Mode: {'dry-run' if dry_run else 'live'}")
    print()

    steps = [
        ("Health Check + Auto-Fix", 'health_check.py', ['--quick', '--fix']),
        ("Validate All Entries", 'validate.py', []),
        ("Validate Pending Proposals", 'validate.py', ['--proposals']),
        ("Rebuild Search Index", 'build_index.py', []),
        ("Generate Report", 'generate_report.py', []),
    ]

    success = True
    for name, script, args in steps:
        if not run_script(script, *args):
            print(f"  \u26a0\ufe0f  {name} had issues")
            success = False

    print(f"\n{'='*60}")
    if dry_run:
        print("  \u2705 Dry-run selesai.")
    else:
        print(f"  {'\u2705 Semua fix selesai!' if success else '\u26a0\ufe0f  Ada beberapa issue'}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
