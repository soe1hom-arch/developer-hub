# Developer Hub

> Sebuah database open-source yang berisi **703 sumber daya developer** — API, SDK, library, framework, tools, dan bahasa pemrograman.  
> Saya buat karena saya sendiri sering kesusahan mencari referensi tools yang terpercaya dan terorganisir dalam satu tempat.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![JSON Validation](https://github.com/soe1hom-arch/developer-hub/actions/workflows/validate.yml/badge.svg)](.github/workflows/validate.yml)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Railway-0B0D0E?logo=railway&logoColor=white)](https://developer-hub-production.up.railway.app)

**[🌐 Kunjungi Website](https://developer-hub-production.up.railway.app) · [📖 Baca Dokumentasi](docs/) · [🤝 Berkontribusi](CONTRIBUTING.md)**

---

## Tentang Project Ini

Halo! Saya **Wandi** — seorang Android firmware enthusiast dari Indonesia. Project ini saya buat karena saya ingin ada satu tempat yang mudah dicari, terstruktur, dan bisa dipakai siapa saja untuk menemukan tools developer berkualitas. Baik itu buat Android, web, backend, IoT, Termux, atau binary tools — semuanya ada di sini.

**Yang saya jaga di repo ini:**
- Semua data resource developer yang legitimate dan legal
- Tools yang betul-betul dipakai developer, bukan untuk kegiatan ilegal
- Informasi yang akurat, terbuka, dan bisa diverifikasi
- Tidak ada konten yang melanggar hukum — no malware, no crack, no piracy

## 📊 Statistik Saat Ini

| Metrik | Jumlah |
|---|---|
| **Total Resource** | 703 |
| **Kategori** | 33 |
| **Bahasa Pemrograman** | 80 |
| **Open Source** | 674 (96%) |
| **Terawat** | 697 (99%) |
| **Punya GitHub** | 703 (100%) |
| **Punya Alternatif** | 197 |
| **Lisensi Terbanyak** | MIT (404), Apache-2.0 (131) |

## ✨ Yang Bisa Kamu Lakukan

- **Cari resource** — pake search atau filter kategori/bahasa
- **Lihat detail** — deskripsi, lisensi, link resmi, GitHub, dokumentasi
- **Temukan alternatif** — setiap project punya rekomendasi project serupa
- **Lihat tech stacks** — kumpulan tools yang biasa dipakai bareng (Android Development, Python Backend, dll)
- **Trending & terbaru** — lihat project yang lagi populer atau baru diupdate
- **Akses via API** — semua data bisa diambil lewat REST API

## 📂 Kategori

| Kategori | Ikon | Jumlah | Kategori | Ikon | Jumlah |
|---|---|---|---|---|---|
| AI | 🤖 | 78 | Android | 📱 | 53 |
| Frontend | 🎨 | 48 | Backend | ⚙️ | 44 |
| Tools | 🔧 | 44 | Database | 🗄️ | 43 |
| Libraries | 📦 | 41 | Security | 🔒 | 36 |
| DevOps | 🚀 | 35 | Cloud | ☁️ | 32 |
| Languages | 💻 | 29 | Frameworks | 🏗️ | 21 |
| Blockchain | ⛓️ | 17 | Game Development | 🎮 | 17 |
| Network | 🌐 | 17 | Containers | 🐳 | 17 |
| Mobile | 📲 | 15 | macOS | 🍎 | 11 |
| Machine Learning | 🧠 | 10 | Android Tools | 📱 | 10 |
| CLI Tools | 📁 | 10 | IoT | 📡 | 10 |
| Termux | 📱 | 10 | Binary | 💾 | 10 |
| Desktop | 🖥️ | 7 | Linux | 🐧 | 7 |
| Web | 🌐 | 5 | Operating Systems | 💿 | 5 |
| Windows | 🪟 | 5 | Firmware | ⚡ | 4 |
| API | 🔗 | 4 | Embedded | 🔌 | 4 |
| Robotics | 🦾 | 4 | | | |

## 🔌 REST API

Semua data bisa diakses via API.  
**Base URL:** `https://developer-hub-production.up.railway.app`

| Endpoint | Fungsi |
|---|---|
| `GET /stats` | Statistik overview |
| `GET /projects` | Daftar project (bisa difilter per kategori) |
| `GET /projects/{id}` | Detail project + skor kualitas |
| `GET /search?q=` | Pencarian fuzzy |
| `GET /suggest?q=` | Autocomplete saran pencarian |
| `GET /trending` | Project yang lagi tren |
| `GET /stacks` | Tech stacks yang dikurasi |
| `GET /stacks/{id}` | Project dalam stack tertentu |
| `GET /recent` | Project yang baru diupdate |
| `GET /recommendations/{id}` | Rekomendasi project serupa |

Dokumentasi API lengkap: `/docs` (Swagger UI) atau `/redoc` (ReDoc).

## 🚀 Cara Pakai

```bash
# Clone repo
git clone https://github.com/soe1hom-arch/developer-hub.git
cd developer-hub

# Install
pip install -r scripts/requirements.txt

# Validasi data
python scripts/validate.py

# Jalankan server
uvicorn api_server.main:app --reload --host 0.0.0.0 --port 8000

# Buka website
open http://localhost:8000
```

## 🌐 Website

Website-nya single-page application, udah termasuk dark theme, search, filter, trending, tech stacks, dan detail project. Tinggal akses:

**[https://developer-hub-production.up.railway.app](https://developer-hub-production.up.railway.app)**

## 🤖 Otomatisasi

Saya pake GitHub Actions buat jaga kualitas data:

- **Tiap push** — validasi JSON, cek schema
- **Harian** — deteksi rilis baru, verifikasi link, update metadata
- **Mingguan** — scan penuh, deteksi project yang diarsipkan/ditinggalkan

## 🤝 Ikut Berkontribusi

Kamu boleh bantu nambahin resource atau laporin kalau ada yang salah:

- [Panduan Kontribusi](CONTRIBUTING.md)
- [Kode Etik](CODE_OF_CONDUCT.md)
- [Dokumentasi Lengkap](docs/)

## 📄 Lisensi

MIT License — silakan pakai, modifikasi, dan sebarkan. Lihat [LICENSE](LICENSE).

---

## 👤 Tentang Saya

Halo, saya **Wandi** (@soe1hom-arch). Saya bikin project ini di waktu luang, karena hobi saya di Android, firmware, dan open-source tools.

- 🔭 Sehari-hari saya berkutat dengan Android development dan firmware
- 🌟 Saya juga bikin tools lain kayak [AFFT](https://github.com/soe1hom-arch/AFFT) dan [CalcDuo](https://github.com/soe1hom-arch/calcduo)
- 💬 Kalau ada pertanyaan atau feedback, [buka issue aja](https://github.com/soe1hom-arch/developer-hub/issues)

## ⚖️ Hal yang Perlu Kamu Tahu

**Yang saya jamin:**
- Semua resource di sini adalah tools developer yang legitimate
- Tidak ada malware, crack, hack, atau konten ilegal
- Semua data diambil dari sumber publik (GitHub, website resmi, dokumentasi)
- Saya selalu berusaha menjaga akurasi dan kepatuhan hukum

**Yang perlu kamu catat:**
- Nama produk, logo, dan merek dagang adalah milik pemiliknya masing-masing
- Saya tidak terafiliasi dengan project atau perusahaan yang tercantum
- Data ini saya sediakan "apa adanya" — selalu verifikasi informasi penting dari sumber resmi
- Kalau ada resource yang melanggar hak kamu, [laporkan ke sini](https://github.com/soe1hom-arch/developer-hub/issues) — akan saya review dan hapus kalau perlu
