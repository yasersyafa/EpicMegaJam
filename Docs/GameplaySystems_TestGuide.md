# Panduan sistem gameplay mandiri

Unreal Engine 5.6.1. Pembaruan mekanik placement bebas, 15 November 2026.

## Mulai bermain

1. Buka Content Drawer dengan **Ctrl+Space**.
2. Masuk ke `Content/Game/Levels/Tests`, lalu buka `L_GameplaySystems`.
3. Klik **Play**, kemudian klik viewport agar input masuk ke game. **Shift+F1** melepaskan mouse. **Esc** mengakhiri PIE.
4. Dekati benda dan arahkan pusat layar sampai prompt **PICK UP** muncul. Tekan **E** untuk memilihnya.
5. Berjalan ke lokasi yang diinginkan dan bidik permukaan. Ghost hijau menandakan posisi yang dapat ditempati. Tekan **E** untuk mengonfirmasi penempatan.
6. Ghost merah menunjukkan permukaan belum valid atau terdapat benturan. **RMB** membatalkan pemilihan dan mempertahankan posisi terakhir yang sudah dikonfirmasi.

Penempatan mengikuti titik bidik pada permukaan. Pemain dapat menempatkan benda di berbagai posisi lantai, termasuk di luar area solusi. Rotasi yang sudah dimiliki benda dipertahankan selama pemindahan. Posisi asli tetap tersimpan sampai pemain mengonfirmasi placement.

## Area solusi puzzle

Lingkaran biru menunjukkan area solusi di arena tes. Setiap area memiliki prop yang dituju dan radius sendiri. Radius awal adalah **125 cm**.

Saat ACTION dimulai, evaluator membandingkan jarak horizontal antara **pusat bounds benda** dan pusat area pada bidang XY. Jarak yang sama dengan radius masih diterima. Posisi dalam area menentukan kondisi puzzle. Metadata `CurrentSlotID` milik prop lama tidak dipakai untuk menilai puzzle.

| Scene | Prop pertama | Prop kedua |
| --- | --- | --- |
| 1 — Arrival | Sofa di area sofa | Wardrobe di area wardrobe |
| 2 — Hollow Wall | Cabinet di area cabinet | Lamp di area lamp |
| 3 — Last Scene | Chair di area chair | Lamp di area lamp |

Preview hijau menunjukkan bahwa benda dapat diletakkan secara fisik. Pemain masih perlu mengatur komposisi set agar kedua kondisi puzzle terpenuhi. Evaluator memeriksa prop pertama lebih dahulu, kemudian prop kedua.

Panduan slot A/B/C lama disembunyikan saat bermain dan collision-nya dinonaktifkan. Marker posisi awal tetap tersedia untuk restart scene.

## Kontrol

| Input | Perilaku |
| --- | --- |
| WASD dan mouse | Berjalan dan melihat |
| E | Memilih atau menempatkan benda. Menggunakan interkom ketika objective final aktif |
| RMB | Membatalkan pemilihan benda |
| F | ACTION dari director mark scene aktif. CUT selama take |
| Tab | Membuka atau menutup Notes tes |
| N | Melanjutkan setelah scene selesai |
| R | Memulai ulang scene aktif, membersihkan preview, serta memulihkan posisi dan rotasi awal kedua prop |
| 1, 2, 3 | Memilih scene untuk pengujian langsung |
| P | Pause dan resume |
| F6 | Menjalankan seluruh native FunctionalTest yang tersedia di level tes |
| Esc | Mengakhiri sesi PIE |

Tombol 1/2/3 mengganti scene aktif. Pemain berjalan sendiri menuju area scene tersebut.

## Coba loop pertama

1. Mulai di Scene 1 dan biarkan kedua prop pada posisi awal.
2. Berdiri pada lingkaran kuning `DIRECTOR MARK — SCENE 01`, lalu tekan F. Take menunjukkan kesalahan prop pertama dan menunggu CUT.
3. Tekan F untuk CUT. Gerak pemain pulih dan posisi prop dipertahankan.
4. Pindahkan sofa ke salah satu posisi dalam area sofa. Kembali ke director mark dan mulai take berikutnya. Kesalahan prop kedua sekarang dapat terlihat.
5. CUT, pindahkan wardrobe ke area wardrobe, lalu kembali ke director mark.
6. Tekan F. Simulator tes menyelesaikan perfect take setelah dua detik dan memicu auto-CUT.
7. Tekan N untuk mengaktifkan scene berikutnya.

ACTION membutuhkan tangan kosong dan posisi di director mark scene aktif. Radius mark awal adalah **100 cm**, dengan toleransi ketinggian **120 cm** terhadap marker lantai agar pusat capsule pemain diterima. Arah pandang bebas. CUT tetap tersedia selama take, termasuk jika pemain berpindah keluar mark melalui debug atau sistem lain.

Setelah Scene 3 selesai, tekan N. Objective berubah menjadi `CALL EVERYONE TO SET`. Dekati interkom sampai jaraknya maksimal 300 cm, lalu tekan E. Pesan `EVERYONE CALLED` mengakhiri alur sistem tes.

CUT mempertahankan seluruh penempatan yang sudah dikonfirmasi. R mengulang scene aktif dari susunan awal dan menghapus completion scene tersebut. Stop lalu Play memulai sesi baru dari Scene 1.

## Konfigurasi area dan placement

Pilih actor seperti `S01_Sofa_SolutionArea` melalui Outliner. Actor tersebut memakai `BP_PlacementArea`.

- `AllowedProp` menunjuk instance benda yang dinilai oleh area.
- `Radius` menentukan jangkauan dalam cm. Ukuran preview lingkaran mengikuti radius melalui Construction Script.
- Pindahkan actor area untuk memindahkan pusat solusi. Preview dan label mengikuti actor tersebut.

Pilih `SYSTEM_GameplayTestManager` untuk mengganti referensi `S1Area1`, `S1Area2`, dan pasangan area scene berikutnya. Referensi prop, marker posisi awal, dan director mark tetap diatur pada manager.

Placement memerlukan permukaan dengan normal Z minimal **0.85**. Pemeriksaan overlap mencegah penempatan menembus benda lain atau capsule pemain. Jangkauan bidik placement awal adalah **600 cm**. Pengaturan ini berada pada `BP_FreePlacementPlayerBase`.

## Membaca Blueprint

Aset sistem berada di `Content/Game/Blueprints/Gameplay/Testing`.

| Aset | Tanggung jawab |
| --- | --- |
| `BP_GameplayTestManager` | Take, evaluasi puzzle, objective, progression, interkom, pause, dan restart |
| `BP_PlacementArea` | Validasi prop berdasarkan identitas dan radius horizontal |
| `BP_GameplayPlayer` | Player yang dipakai GameMode tes |
| `BP_FreePlacementPlayerBase` | Gerak, camera look, pemilihan prop, free placement, ghost, dan cancel |
| `ABP_FreePlacementPlayer` | Salinan animasi untuk kontrak player tes, termasuk gerak tangan dan Notes |
| `BP_TestHUD` | Status, crosshair, prompt placement, Notes, dan pause |
| `BP_GameplayTestMode` | Pemilihan player dan HUD khusus level tes |

Urutan fungsi yang disarankan untuk dipelajari adalah sebagai berikut.

1. `RefreshFreePlacement` membaca target bidikan dan memperbarui preview.
2. `ValidateFreePlacement` memeriksa permukaan serta overlap kandidat posisi.
3. `TryFreeInteract` menangani pemilihan dan konfirmasi posisi. Kondisi placement diperiksa ulang saat E ditekan.
4. `CancelFreePlacement` membersihkan pemilihan dan menyembunyikan ghost.
5. `BP_PlacementArea.ContainsProp` memeriksa pusat benda terhadap radius.
6. `BP_GameplayTestManager.EvaluatePuzzle` memakai dua area aktif untuk menentukan hasil take.
7. `StartTake`, `CancelTake`, dan `NotifyTakeFinished` mengatur lifecycle take. `TakeID` mencegah callback take lama menyelesaikan retake baru.

Level tes menggunakan GameMode override lokal. Default map proyek tetap `SB_GrayBox`. Blueprint, animasi, dan map produksi dipertahankan. Integrasi cutscene tetap menunggu permintaan terpisah. Sistem runtime memakai Blueprint, sedangkan Python dipakai untuk authoring editor dan harness validasi manual.

## Functional test manual

**Agen hanya membuat, mengompilasi, dan menyimpan perubahan ini. PIE serta functional test belum dijalankan untuk mekanik placement bebas.**

1. Buka `L_GameplaySystems` dan mulai sesi PIE baru.
2. Tetap pada Setup, tanpa memegang prop dan sebelum menyelesaikan scene.
3. Klik viewport, lalu tekan **F6** sekali.
4. Buka panel **Output Log** di editor. Cari `Free placement` atau `Director mark`. Hasil akhir berasal dari native Unreal FunctionalTest.
5. Stop lalu Play jika ingin mencoba game dari awal lagi.

Terdapat dua suite yang berjalan ketika diminta melalui F6.

- `BP_DirectorMarkFunctionalTest` berisi sepuluh kasus untuk penerimaan ACTION, batas mark, scene aktif, prop yang masih dipegang, dan CUT di luar mark.
- `BP_FreePlacementFunctionalTest` berisi sembilan kasus yang mencakup pusat area, posisi berbeda dalam radius, batas radius, posisi di luar radius, prop salah, referensi kosong, keenam area scene, hasil puzzle, dan alur placement.

Alur placement dalam suite baru mencakup handler pickup, placement di luar solusi, benturan dengan furnitur/pemain, permukaan miring, bidikan tanpa permukaan, cancel, serta preservasi posisi setelah CUT. Test memulihkan posisi/rotasi prop, metadata kompatibilitas, pose pemain, scene aktif, counter take, dan konfigurasi simulator ketika selesai.

F6 memulai test secara eksplisit. Play biasa memberi kesempatan untuk mencoba mekanik secara manual.

## Batas verifikasi

Blueprint perubahan ini berhasil dikompilasi dengan nol error dan warning. Pemeriksaan hash terhadap 22 file produksi/configuration tidak menemukan perubahan. Catatan authoring berada pada `Saved/FreePlacementAuthoring.json`, dengan `tests_run` bernilai `false`.

Hasil 85 pemeriksaan state dan 31 pemeriksaan interaksi dari implementasi snap sebelumnya merupakan catatan historis. Script validasi terkait sudah diperbarui untuk area radius, tetapi belum dijalankan ulang. Packaging Windows belum diuji.
