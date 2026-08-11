# Panduan Deploy

## Menjalankan di Lokal

```bash
git clone https://github.com/soe1hom-arch/developer-hub.git
cd developer-hub

pip install -r scripts/requirements.txt

# Cek validasi
python scripts/validate.py

# Jalankan API server
uvicorn api_server.main:app --reload --host 0.0.0.0 --port 8000

# Buka di browser
open http://localhost:8000
```

Website (`website/index.html`) udah otomatis diserve sama backend FastAPI — gak perlu server statis terpisah.

## Deploy ke Railway (Paling Gampang)

Repo ini udah include `Dockerfile` dan `railway.json`. Tinggal:

1. Fork/clone repo ke GitHub kamu
2. Buka [Railway](https://railway.app) → New Project → Deploy from GitHub
3. Railway bakal auto-detect Dockerfile
4. Selesai. Domain langsung aktif.

## Deploy pake Docker

```bash
docker build -t developer-hub .
docker run -d -p 8000:8000 developer-hub
```

## Deploy ke VPS

```bash
apt install python3 python3-pip python3-venv
cd /opt
git clone https://github.com/soe1hom-arch/developer-hub.git
cd developer-hub

python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
pip install gunicorn uvicorn

gunicorn api_server.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

Bisa juga pake nginx sebagai reverse proxy.

## Environment Variables

| Variable | Default | Keterangan |
|---|---|---|
| `PORT` | `8000` | Port server (Railway set otomatis) |
| `HOST` | `0.0.0.0` | Alamat bind |
| `WORKERS` | `4` | Jumlah worker Gunicorn |

## CI/CD

GitHub Actions otomatis jalanin:

- **Tiap push** — validasi JSON, cek schema, build index
- **Harian** — verifikasi link, deteksi rilis baru
- **Mingguan** — maintenance penuh, deteksi project yang ditinggalkan

Railway auto-deploy tiap ada push ke branch `main`.
