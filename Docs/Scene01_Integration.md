# Integrasi Scene 01

Map: `/Game/Game/Levels/Tests/L_Scene01`.
Engine: Unreal Engine 5.6.1. Authoring: 15 November 2026.

## Hasil dan batas verifikasi

Level baru memuat rumah, opening Maya, tutorial kedatangan, percakapan duduk,
free placement sofa/wardrobe, ACTION/CUT/retake, performance Scene 01, serta
aftermath dan perpindahan kru menuju hall utara. Scene 02, interlude berikutnya,
finale, facial animation, dan lip-sync belum termasuk. Karakter memakai animasi
blocking yang tersedia, bukan performance final.

**Unit test, functional test, PIE/playmode, Simulate, Standalone Game, preview
interaktif, dan packaging TIDAK dijalankan.** Tidak ada input keyboard/mouse atau
perintah untuk mengambil fokus jendela. Pemeriksaan hanya inspeksi aset/referensi,
compile/save Blueprint, dan perbandingan hash paket sumber. Compile berhasil
bukan bukti bahwa gameplay, framing, blocking, atau playback VO sudah lolos uji.

Sembilan Blueprint/widget integrasi dikompilasi dengan nol error dan warning.
235 file sumber/config dibandingkan dengan baseline dan tidak berubah.
Detail tercatat di `Docs/Scene01_AuthoringReport.json`; receipt lokal tambahan
ada di `Saved/Scene01Build/` dan tidak untuk commit.

`SB_GrayBox`, `L_GameplaySystems`, Blueprint sumber dan konfigurasi default map
tetap dipertahankan. Aset yang perlu diubah dibuat sebagai salinan khusus Scene01.
Mesh/material, Blueprint prop, dan evaluator area solusi dipakai sebagai
dependency bersama yang tidak diedit. Salinan awal L_Scene01 disimpan di
`Saved/Scene01Build/L_Scene01.before-integration.umap`.

## Alur dan kontrol

Opening menahan kamera close-up saat dialog berjalan, lalu melanjutkan fade/title.
Space hanya melakukan skip ketika fase Opening masih aktif. Skip menghentikan
VO/subtitle, menghentikan sequence, dan menyerahkan kontrol ke tutorial.

Arrival mempertahankan tutorial berjalan, melihat, pintu depan, Notes, serta
trigger masuk ruang tamu. Percakapan kru/Maya menggunakan durasi VO atau fallback;
gerakan kru dan approach/return Maya tidak lagi bergantung pada delay subtitle
lama. Kursi dan kamera seated conversation tetap dipakai.

| Input | Fungsi |
| --- | --- |
| WASD / Mouse | Berjalan / melihat saat kontrol tidak dikunci |
| E | Membuka pintu saat tutorial; memilih/menempatkan prop saat Setup |
| RMB | Membatalkan placement; posisi terakhir tetap dipertahankan |
| Tab | Notes dan clipboard; tidak tersedia saat opening/take |
| F | ACTION pada director mark, CUT saat take |
| Space | Skip opening |
| P | Pause/resume, termasuk audio dialog |

Tombol arena tes 1/2/3/N/R/F6 tidak terhubung pada level ini. API `RestartScene`
tersedia pada flow director untuk me-reload level dari awal, tanpa debug key.

ACTION memerlukan fase Setup, tangan kosong, serta jarak XY <=100 cm dari marker
director, dengan toleransi tinggi 120 cm. Marker director berada di sisi utara
ruang tamu. Solusi puzzle tidak ditampilkan sebagai lingkaran biru.

- Sofa salah: Maya mencoba mendekat ke jalur, berhenti sebelum sofa, lalu memberi
  feedback. Take menunggu CUT manual, termasuk setelah VO selesai.
- Sofa benar, wardrobe salah: Maya mencapai titik inspeksi, menghadap clue, lalu
  memberi feedback dan menunggu CUT manual.
- Kedua prop benar: performance dan dialog selesai sebelum auto-CUT.
- CUT cepat tidak memberi penalti. Kamera/input dan Maya dipulihkan; posisi prop
  terakhir dipertahankan. Identitas take lama tidak dapat menyelesaikan retake baru.
- Perfect take menjalankan aftermath dan transisi kru sekali, kemudian mengirim
  custom event `OnScene01Completed`. Event ini adalah titik ekstensi graph;
  bukan multicast dispatcher. Scene 02 belum dibuka.

Untuk mengubah staging, pilih `SYSTEM_Scene01Flow` dan marker `MARK_Scene01_*`.
Sofa dan wardrobe memakai `BP_InteractableProp`; area `AREA_Scene01_*` menilai
identitas prop dan jarak XY pusat bounds, radius 35 cm. Acuan awal actor sofa
sekitar (145,0,0) dan wardrobe (-30,290,0), dengan rotasi intro dipertahankan.
Perubahan layout memerlukan pemeriksaan manual ulang atas jalur dan sightline.
Satu sofa dekoratif, side table, dan desk lamp dihapus hanya dari salinan level
untuk memberi ruang puzzle/performance.

## Memasang voice over nanti

1. Impor **satu WAV per baris** ke `/Game/Game/Audio/Scene01/VO/`. Folder akan
   muncul di Content Browser setelah aset pertama diimpor. File dialog sebaiknya
   tidak looping. Nama audio boleh mengikuti LineID agar mudah dicocokkan.
2. Buka `/Game/Game/Audio/Scene01/DT_Scene01Dialogue`.
3. Pilih row yang cocok, lalu isi kolom **Sound** dengan SoundWave/SoundCue
   hasil impor. Row yang belum memiliki rekaman boleh tetap `None`.
4. Simpan tabel dan audio. Tidak perlu mengubah Blueprint untuk memasang VO.

Tabel berisi 34 row. `LineID` dan row name harus tetap sama. `NextLine` mengatur
urutan dalam satu kelompok; jangan membuat siklus. `FallbackSeconds` digunakan
ketika Sound kosong, tidak dapat di-resolve, atau bukan SoundBase yang valid.
Audio valid mengatur akhir baris melalui status playback AudioComponent; nilai
fallback bukan batas durasi audio. Subtitle mengikuti baris aktif.

`Speaker` dan `Subtitle` dapat diedit. Pertahankan label speaker `CREW A` dan
`CREW B` agar attachment suara mengarah ke actor yang benar. `MAYA` dan
`LARAS (MAYA)` mengarah ke Maya. `SURYA` serta `SURYA (INTERNAL)` memakai audio
2D. Opening memakai audio 2D; dialog Maya/kru dalam ruangan memakai audio attached
pada tinggi kepala dan `SA_Scene01Dialogue` (radius penuh 600 cm, falloff 1800 cm).
Volume keseluruhan VO dapat diubah melalui `Volume` pada `SYSTEM_Scene01Dialogue`.

| Kelompok row | Pemakaian |
| --- | --- |
| `Opening_01` - `Opening_04` | Monolog opening Maya |
| `Intro_Crew_01` - `Intro_Crew_03` | Percakapan kru dan Surya |
| `Intro_Maya_01` - `Intro_Maya_06` | Percakapan Maya dan Surya |
| `Take_Entry_01`, `Take_Walk_01` | Awal performance Laras |
| `Take_Clue_01` - `Take_Clue_02` | Penemuan clue |
| `Take_Perfect_01` - `Take_Perfect_02` | Penutup perfect take |
| `Fail_Sofa_01` - `Fail_Sofa_02` | Feedback blocking |
| `Fail_Wardrobe_01` - `Fail_Wardrobe_02` | Feedback sightline |
| `Cut_Sofa_01`, `Cut_Wardrobe_01`, `Cut_Early_01` | Respons CUT Surya |
| `Aftermath_01` - `Aftermath_05` | Percakapan setelah perfect take |
| `Transition_01` - `Transition_03` | Dialog perpindahan kru |

Dialog memakai satu jalur playback sehingga baris sebelumnya dihentikan saat
diganti, skip, CUT, restart, atau EndPlay. Pause menghentikan kemajuan game dan
menjeda komponen VO. `SessionID` membedakan sesi, dan tidak ada callback latent
dialog yang dapat menyalakan kembali caption setelah pembatalan. `OnDialogueFinished`
adalah hook fungsi Blueprint dengan ID sesi selesai.

## Checklist manual untuk nanti (BELUM dijalankan)

- Opening selesai normal dan skip; kamera, subtitle, title, dan input pulih.
- Menunggu di luar tidak memulai percakapan; pintu dan Notes bekerja; seated POV
  dan gerakan kru/Maya selesai sebelum Setup.
- Pickup, placement pada permukaan, overlap furniture/pemain, dan RMB cancel.
- ACTION ditolak di luar mark atau saat memegang prop; keyboard F sekali per tekan.
- Sofa salah, wardrobe salah, CUT cepat, CUT menjelang akhir take, dan retake berulang.
- Props tetap pada posisi terakhir setelah CUT; Maya dan kamera kembali dengan benar.
- Perfect take selesai setelah performance/dialog; aftermath/transisi hanya sekali.
- VO kosong, VO lebih panjang/pendek dari fallback, pause/resume, dan skip/CUT
  di tengah audio; tidak ada subtitle/audio lama yang tertinggal.
- Periksa framing ketiga kamera, keterbacaan clue, dan jalur karakter/props.
- Periksa Output Log. Packaging Windows menjadi langkah terpisah ketika diminta.

## Authoring

Runtime memakai Blueprint/Level Sequence/DataTable; Python dan editor bridge
tidak dibutuhkan saat game dijalankan. Jangan menjalankan ulang staging sumber
`StageOpeningFlow.py` atau `StageArrivalFlow.py` ke map integrasi.

Script authoring khusus: `BuildScene01Assets.py`, `BuildScene01Dialogue.py`,
`BuildScene01Arrival.py`, `BuildScene01Flow.py`, `BuildScene01Presentation.py`,
serta `Tools/Scene01/StageScene01.py` dan `FinalizeScene01.py`. Script prepare
adalah operasi sekali jalan dan menolak jika flow director integrasi sudah ada.
Gunakan recovery point sebelum membangun ulang; script authoring bukan pipeline
reset aman untuk level yang sudah diedit manual. `ReviewScene01Authoring.py`
hanya melakukan compile/inspeksi statis, tidak menjalankan runtime testing.
