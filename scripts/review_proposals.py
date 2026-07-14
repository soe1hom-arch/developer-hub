#!/usr/bin/env python3
"""
Review Proposals — CLI tool untuk review manual proposal yang butuh verifikasi.

Fitur:
  - List semua proposal dengan quality score & confidence
  - Approve/reject dengan satu klik
  - Lihat detail lengkap (semua signals)
  - Batch approve quality >= threshold

Usage:
    python scripts/review_proposals.py list              # List semua proposal
    python scripts/review_proposals.py show <id>         # Detail proposal
    python scripts/review_proposals.py approve <id>      # Approve satu
    python scripts/review_proposals.py reject <id>       # Reject satu
    python scripts/review_proposals.py approve-all --min-quality 70  # Batch approve
"""

import json, os, sys, shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES
from scripts.quality_check import check_schema, check_github, check_description, check_category, check_duplicate

PROPOSALS_DIR = REPO_ROOT / ".proposals"


def list_proposals():
    """List semua proposal dengan score."""
    if not PROPOSALS_DIR.exists():
        print("No proposals directory found.")
        return []
    
    proposals = []
    for f in sorted(PROPOSALS_DIR.glob('*.json')):
        try:
            data = json.loads(f.read_text())
            quality = data.get('quality_score', 0)
            cat = data.get('category', '?')
            name = data.get('name', f.stem)
            gh = data.get('github_repository', '')[:50]
            proposals.append((f, name, cat, quality, gh))
        except:
            pass
    
    return proposals


def show_proposal(proposal_id):
    """Show detail lengkap proposal."""
    f = PROPOSALS_DIR / f"{proposal_id}.json"
    if not f.exists():
        print(f"Proposal '{proposal_id}' not found.")
        return
    
    data = json.loads(f.read_text())
    quality = data.get('quality_score', 0)
    
    print(f"\n{'='*60}")
    print(f"  📄 Proposal: {data.get('name', '?')}")
    print(f"{'='*60}")
    print(f"  Category:    {data.get('category', '?')}")
    print(f"  Quality:     {quality}/100")
    print(f"  GitHub:      {data.get('github_repository', '?')}")
    print(f"  Website:     {data.get('official_website', '?')}")
    print(f"  License:     {data.get('license', '?')}")
    print(f"  Lang:        {', '.join(data.get('programming_languages', []))}")
    print(f"  Tags:        {', '.join(data.get('tags', []))}")
    print(f"  Description: {data.get('description', '')[:100]}...")
    print()
    
    # Jalankan quality checks
    print(f"{'─'*40}")
    print(f"  QUALITY CHECKS:")
    print(f"{'─'*40}")
    
    ok, issues = check_schema(data)
    print(f"  {'✅' if ok else '❌'} Schema: {len(issues)} issues")
    for i in issues[:3]:
        print(f"       • {i}")
    
    ok, issues, _ = check_github(data.get('github_repository', ''))
    print(f"  {'✅' if ok else '❌'} GitHub: {len(issues)} issues")
    for i in issues[:3]:
        print(f"       • {i}")
    
    ok, issues = check_description(data)
    print(f"  {'✅' if ok else '❌'} Description: {len(issues)} issues")
    for i in issues[:3]:
        print(f"       • {i}")
    
    ok, issues, confidence = check_category(data)
    print(f"  {'✅' if ok else '❌'} Category (confidence: {confidence:.0%}): {len(issues)} issues")
    for i in issues[:3]:
        print(f"       • {i}")
    
    print()
    print(f"  Commands: approve {proposal_id} | reject {proposal_id}")


def approve_proposal(proposal_id):
    """Approve dan commit proposal."""
    f = PROPOSALS_DIR / f"{proposal_id}.json"
    if not f.exists():
        print(f"Proposal '{proposal_id}' not found.")
        return False
    
    data = json.loads(f.read_text())
    cat = data.get('category', 'tools')
    cat_dir = REPO_ROOT / cat
    cat_dir.mkdir(exist_ok=True)
    dst = cat_dir / f.name
    
    if dst.exists():
        print(f"❌ Target already exists: {dst}")
        return False
    
    # Update fields
    data['auto_discovered'] = True
    from scripts.auto_discover import calculate_quality_score
    data['quality_score'] = calculate_quality_score(data)
    data['last_checked'] = __import__('time').strftime('%Y-%m-%d')
    data['last_updated'] = data['last_checked']
    
    with open(dst, 'w') as f:
        json.dump(data, f, indent=2)
    
    f.unlink()  # Remove proposal
    print(f"✅ Approved & committed: {data['name']} → {cat}/")
    return True


def reject_proposal(proposal_id):
    """Reject dan hapus proposal."""
    f = PROPOSALS_DIR / f"{proposal_id}.json"
    if not f.exists():
        print(f"Proposal '{proposal_id}' not found.")
        return False
    
    data = json.loads(f.read_text())
    name = data.get('name', f.stem)
    f.unlink()
    print(f"🗑️  Rejected & deleted: {name}")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        proposals = list_proposals()
        if not proposals:
            print("No proposals pending review.")
            return
        print(f"\n{'='*60}")
        print(f"  Proposals Pending Review ({len(proposals)})")
        print(f"{'='*60}")
        print(f"  {'ID':25s} {'Name':25s} {'Cat':15s} {'Quality':>8s}")
        print(f"  {'─'*25} {'─'*25} {'─'*15} {'─'*8}")
        for f, name, cat, quality, gh in proposals:
            print(f"  {f.stem:25s} {name:25s} {cat:15s} {quality:3d}/100")
        
        high_q = sum(1 for _, _, _, q, _ in proposals if q >= 70)
        print(f"\n  {high_q} ready to auto-approve (quality >= 70)")
        print(f"  Run: python scripts/review_proposals.py approve-all --min-quality 70")
    
    elif cmd == 'show' and len(sys.argv) > 2:
        show_proposal(sys.argv[2])
    
    elif cmd == 'approve' and len(sys.argv) > 2:
        approve_proposal(sys.argv[2])
    
    elif cmd == 'reject' and len(sys.argv) > 2:
        reject_proposal(sys.argv[2])
    
    elif cmd == 'approve-all':
        min_quality = 70
        for a in sys.argv:
            if a.startswith('--min-quality='):
                min_quality = int(a.split('=')[1])
        
        proposals = list_proposals()
        approved = 0
        for f, name, cat, quality, gh in proposals:
            if quality >= min_quality:
                if approve_proposal(f.stem):
                    approved += 1
        print(f"\nApproved {approved}/{len(proposals)} proposals")
    
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
