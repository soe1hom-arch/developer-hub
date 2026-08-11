# Cara Berkontribusi

Makasih udah mau berkontribusi! Repo ini bisa ada isinya karena bantuan dari berbagai pihak.

## Cara Nambah Resource Baru

1. **Fork** repo ini
2. **Buat branch**: `git checkout -b add/nama-project`
3. **Buat file JSON** di folder kategori yang sesuai (misal: `android/nama-project.json`)
4. **Pastikan JSON valid** — cek dulu: `python scripts/validate.py path/to/file.json`
5. **Commit & push**
6. **Buka Pull Request**

## Cara Update Resource yang Ada

1. Fork repo
2. Cari file JSON project tersebut
3. Update field yang perlu diubah
4. Update `last_checked` dan `last_updated`
5. Jalankan validasi: `python scripts/validate.py`
6. Submit Pull Request

## Lapor Masalah

- Pake template issue yang udah disediain
- Cek dulu apakah issue serupa sudah ada
- Kasih informasi selengkap mungkin

## Yang Perlu Diperhatikan

- **Konten ilegal tidak akan saya terima** — no malware, crack, hack, atau piracy
- Usahakan resource yang kamu tambahin adalah tools developer yang legitimate
- JSON pake indentasi 2 spasi
- Nama file pake huruf kecil dengan tanda hubung (contoh: `my-awesome-tool.json`)
- URL pake link absolut (lengkap dengan `https://`)
- Deskripsi yang jelas tapi padat

## Ada Pertanyaan?

Buka aja [diskusi atau issue](https://github.com/soe1hom-arch/developer-hub/issues).
