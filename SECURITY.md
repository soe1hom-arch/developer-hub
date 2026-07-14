# Security Policy

## Reporting a Vulnerability

Jika kamu menemukan celah keamanan di repository atau website ini, harap laporkan dengan cara:

1. **Jangan** buka issue publik — laporkan langsung ke email: (isi email kamu)
2. Atau buka **issue privat** lewat GitHub Security tab
3. Saya akan merespon dalam 48 jam

## Scope

Yang dilindungi:
- Data di repository ini (JSON files)
- API endpoint
- Website frontend

## Branch Protection

- `main` branch **dilindungi** — tidak bisa force push
-Semua perubahan ke `main` harus melewati **Validate JSON** dan **Run Tests** workflow.
- Push langsung hanya dari GitHub Actions automation (daily update, weekly maintenance)
- Semua kontribusi luar harus lewat **Pull Request**

## Data Integrity

Data entry di repo ini:
- Auto-validated setiap ada perubahan
- Quality gate: minimal skor 50/100 & confidence 60%
- Duplikat terdeteksi otomatis
