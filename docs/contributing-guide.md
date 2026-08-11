# Panduan Kontribusi

Terima kasih sudah mau ikut serta! Berikut cara-caranya.

## Menambahkan Resource Baru

1. Fork repo ini ke akun GitHub kamu
2. Buat branch baru: `git checkout -b add/nama-project`
3. Buat file JSON di folder kategori yang sesuai
4. Ikuti schema yang udah ditentukan di `schemas/project.schema.json`
5. Validasi: `python scripts/validate.py path/to/file.json`
6. Commit, push, lalu buka Pull Request

## Memperbarui Resource

1. Fork repo
2. Temukan file JSON project tersebut
3. Update field yang diperlukan
4. Perbarui timestamp `last_checked` dan `last_updated`
5. Validasi dengan `python scripts/validate.py`
6. Submit Pull Request

## Kategori yang Tersedia

Lihat [README.md](../README.md#-kategori) untuk daftar kategori lengkap.

## Yang Tidak Boleh Dimasukkan

- ❌ Malware, virus, atau tools berbahaya
- ❌ Hacking, cracking, atau exploitation tools
- ❌ Konten yang melanggar hak cipta
- ❌ Tools ilegal yang melanggar hukum
