# To-do: optimasi lighting `SB_GrayBox` (jangan bake)

**Konteks**
- Project memakai lighting dinamis penuh: `r.AllowStaticLighting=False`, Lumen GI + Lumen Reflections, dan Virtual Shadow Maps (`Config/DefaultEngine.ini`). Jangan aktifkan static lighting dan jangan build lighting. Lightmap tidak dipakai kalau Lumen menyala, dan mengubah setting itu memaksa recompile semua shader.
- Pada 15 Nov, `Cast Shadows` dinyalakan di 18 lampu `LIGHT_House_*` dan `EXT_House_Light_*` untuk menghentikan cahaya yang tembus dinding. Contohnya `LIGHT_House_Living_Practical_435` yang bocor ke dapur.
- Lampu `CINE_*` (sinematik) **jangan disentuh**.

## 1. Benchmark baseline
- Editor harus fokus (tidak minimized) dan tidak ada yang sedang mengedit.
- Jalankan PIE `SB_GrayBox` dan ukur FPS / frame time GPU di tiga titik:
  - ruang tamu dekat `L01_DirectorMark` (240, −220)
  - dapur dekat `L02_DirectorMark` (1250, −300)
  - koridor servis (710, 800)
- Catat hasilnya sebagai angka pembanding.

## 2. Kecilkan radius lampu agar pas dengan ruangannya
- Target: lampu taman `EXT_House_Light_Garden_0..3` (radius 1000), `LIGHT_House_Remaster_Garage` (radius 1071), dan lampu plafon `Remaster_*` (radius 650–880).
- Atur `AttenuationRadius` supaya kira-kira hanya menutup ruangannya sendiri. Lampu taman cukup menyinari halaman, tidak perlu menembus rumah.
- Cek tiap ruangan dengan screenshot sebelum dan sesudah. Tidak boleh ada sudut ruangan yang jadi gelap.

## 3. Matikan shadow yang tidak perlu
- Lampu praktikal kecil (radius 260) yang jaraknya lebih dari 260 cm dari dinding mana pun boleh `Cast Shadows = false` lagi.
- Pertahankan shadow di lampu yang bisa menembus dinding, terutama:
  - `Practical_435`
  - `Remaster_HiddenRoom` (jangan sampai menyinari dapur atau koridor, karena ruang rahasianya jadi ketahuan)
  - `Remaster_Kitchen`
  - `Remaster_Service`
- Lampu yang shadow-nya dimatikan harus punya radius yang tidak melewati dinding (lanjutan dari task 2).

## 4. Cek kebocoran setelah perubahan
- Ruang rahasia (sekitar (1230, 1030)) harus gelap jika dilihat dari dapur dan koridor sebelum L02 selesai.
- Kaki dinding barat dapur, di kiri kulkas sekitar (550, 0..300), tidak boleh ada bercak hangat dari ruang tamu.
- Interior rumah tidak boleh tersinari lampu taman.

## 5. Benchmark ulang dan laporkan
- Ulangi pengukuran di tiga titik yang sama, lalu laporkan perbandingannya.
- Kalau selisihnya di bawah sekitar 5%, kembalikan perubahan yang mengorbankan tampilan.

## 6. Opsional: cek build
- Package Windows Development, lalu cek FPS di build hasil package. Angka di PIE editor lebih rendah dari aslinya.

## Batasan
- Jangan ubah `BP_StandingLampProp`. Light lampu prop (`LampLight`, intensitas 8000, radius 750) sengaja dibuat terang untuk puzzle L02.
- Simpan level setelah selesai, dan jangan commit sebelum user mengecek.
