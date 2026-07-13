# Automation

Developer Hub uses GitHub Actions and Python scripts to automate maintenance tasks.

## GitHub Actions Workflows

| Workflow | Trigger | Tugas |
|---|---|---|
| **validate.yml** | Push + PR | Validasi JSON terhadap schema |
| **tests.yml** | Push + PR | Jalanin test suite |
| **duplicate-check.yml** | PR | Deteksi duplikat |
| **daily-update.yml** | Setiap hari 02:00 UTC | Update GitHub stats, discover & commit proposals, rebuild index |
| **weekly-maintenance.yml** | Setiap Minggu 08:00 UTC | Full validation, health check, release scan, report |

### daily-update.yml
Jalan tiap malam, ngelakuin:
1. Update stats GitHub (stars, forks, last update) untuk semua entry
2. Auto-discover proposal baru dari GitHub (max 5 per kategori)
3. Commit proposal yang lolos validasi
4. Validasi semua JSON
5. Rebuild `index.json`
6. Commit & push perubahan

### weekly-maintenance.yml
Jalan tiap Minggu, ngelakuin:
1. Validasi penuh semua JSON
2. Health check (cek link website, docs, GitHub)
3. Scan rilis baru dari F-Droid, Termux, GitHub releases
4. Discover & commit proposal baru (max 10 per kategori)
5. Rebuild index
6. Generate laporan kualitas
7. Commit & push perubahan

## Python Scripts

| Script | Fungsi |
|---|---|
| `auto_discover.py` | Auto-discover resource baru dari GitHub → simpan sebagai proposal |
| `auto_update.py` | Update stats GitHub semua entry |
| `auto_fix.py` | Fix placeholder entries, cari GH repo dari website |
| `scrape_external.py` | Scrape F-Droid, Termux packages, GitHub releases |
| `validate.py` | Validasi JSON terhadap schema |
| `build_index.py` | Generate `index.json` dan `index.csv` |
| `search_engine.py` | Intelligent fuzzy search engine |
| `relationships.py` | Project relationship graph |
| `recommendations.py` | Rekomendasi, trending, stacks |
| `scoring.py` | Quality scoring |
| `analytics.py` | Statistik & metrics |
| `health_check.py` | Cek link website, docs, GitHub |
| `generate_report.py` | Generate laporan kualitas |
| `ai_assistant.py` | CLI assistant rekomendasi stack |
| `ai_categorize.py` | AI categorization & enrichment |
| `ai_knowledge.py` | AI deskripsi & use cases |
| `cache.py` | Caching layer |

## Running Locally

```bash
pip install -r scripts/requirements.txt

# Validasi semua entry
python scripts/validate.py

# Build search index
python scripts/build_index.py

# Update stats
python scripts/auto_update.py

# Discover proposal baru
python scripts/auto_discover.py --dry-run          # Preview
python scripts/auto_discover.py --max-per-category 5
python scripts/auto_discover.py --commit            # Finalize proposals

# Health check
python scripts/health_check.py --quick
```
