# Panduan sistem gameplay mandiri

Implementasi untuk Unreal Engine 5.6.1, 14 November 2026.

## Mulai bermain

1. Buka Content Drawer dengan **Ctrl+Space**.
2. Masuk ke `Content/Game/Levels/Tests` dan buka `L_GameplaySystems`.
3. Klik **Play**. Klik viewport game apabila input belum masuk. Gunakan **Shift+F1** untuk melepaskan mouse dan **Esc** untuk mengakhiri PIE.
4. Kamu mulai di area Scene 1. Dekati balok sofa, arahkan pusat layar ke balok, lalu tekan **E** ketika prompt pickup muncul.
5. Setelah dipilih, prop tetap berada pada posisi terakhir yang dikonfirmasi. Berjalanlah ke slot tujuan dan arahkan pusat layar ke bola cyan. Ghost hijau dan prompt **PLACE** menandakan slot yang bisa dipakai.
6. Tekan **E** untuk mengonfirmasi. RMB membatalkan pemilihan. Ghost merah berarti target belum valid.

Level memakai GameMode override lokal `BP_GameplayTestMode`. Default map proyek tetap `SB_GrayBox`. Sistem runtime menggunakan Blueprint. Script Python digunakan untuk authoring dan pengujian editor.

## Kontrol

| Input | Perilaku |
| --- | --- |
| WASD dan mouse | Berjalan dan melihat |
| E | Memilih atau menempatkan prop. Saat objective final aktif, gunakan interkom dari jarak maksimal 300 cm |
| RMB | Membatalkan pemilihan prop |
| F | ACTION saat Setup. CUT saat TakeActive |
| Tab | Membuka atau menutup Notes tes |
| N | Melanjutkan setelah scene selesai |
| R | Memulai ulang scene aktif dan mengembalikan kedua prop ke slot A |
| 1, 2, 3 | Memilih scene untuk pengujian langsung |
| P | Pause dan resume |
| Esc | Mengakhiri sesi PIE |

Tombol pemilihan scene mengganti objective dan pasangan prop aktif. Pemain tetap berjalan ke area scene yang dipilih. Ketiga area berada dalam arena yang sama.

## Coba loop pertama

1. Biarkan sofa dan wardrobe di slot A, lalu tekan F. HUD menunjukkan masalah blocking. Gerak pemain terkunci, tetapi kamu masih dapat melihat ruangan dan menekan F.
2. Tunggu beberapa detik. Take gagal tetap aktif sampai kamu menekan CUT.
3. Tekan F untuk CUT. Pemain bisa bergerak kembali. Posisi prop dipertahankan.
4. Pindahkan sofa ke B, lalu tekan F lagi. HUD sekarang menunjukkan masalah komposisi pada prop kedua.
5. CUT, pindahkan wardrobe ke C, lalu tekan F.
6. Setelah dua detik, simulator tes menyelesaikan perfect take dan menampilkan AUTO CUT.
7. Tekan N untuk mengaktifkan Scene 2. Berjalan ke area Kitchen/Hollow Wall.

Solusi yang sengaja dibuat mudah untuk menguji sistem adalah sebagai berikut.

| Scene | Prop pertama | Prop kedua |
| --- | --- | --- |
| 1 — Arrival | Sofa B | Wardrobe C |
| 2 — Hollow Wall | Cabinet B | Lamp C |
| 3 — Last Scene | Chair B | Lamp C |

Slot A/B/C menerima placement yang sesuai jenis prop. Kebenaran puzzle dinilai terpisah dari validitas placement. Slot A dapat menerima sofa, tetapi menghasilkan take yang salah. Slot wardrobe menolak sofa.

Setelah Scene 3 selesai, tekan N. Objective berubah menjadi `CALL EVERYONE TO SET`. Dekati balok interkom di dekat sisi masuk arena, lalu tekan E. Pesan `EVERYONE CALLED` mengakhiri pengujian alur.

## CUT, restart, dan progres

- CUT mengembalikan fase ke Setup dan mempertahankan transform serta `CurrentSlotID` prop. ACTION berikutnya menjadi retake baru.
- Restart scene dengan R menghapus completion scene aktif dan mengembalikan kedua prop ke slot A. Scene lain yang sudah selesai tetap tercatat.
- Memilih scene yang sudah selesai menampilkan status selesai. Tekan R apabila ingin menguji scene tersebut dari awal.
- Stop lalu Play kembali memulai sesi baru dari Scene 1. Progres saat ini disimpan dalam sesi bermain.
- ACTION ditolak ketika masih ada prop yang dipilih. Tempatkan prop atau tekan RMB dahulu.

## Membaca Blueprint untuk pertama kali

Buka `Content/Game/Blueprints/Gameplay/Testing`. Terdapat empat aset.

| Aset | Tanggung jawab |
| --- | --- |
| `BP_GameplayTestManager` | Puzzle, take, retake, Notes, progression, interkom, restart, dan pause |
| `BP_GameplayPlayer` | Child dari player yang sudah ada. Memakai gerak dan mekanik penempatan proyek |
| `BP_TestHUD` | HUD mandiri untuk crosshair, prompt interaksi, status, kontrol, Notes, dan pause |
| `BP_GameplayTestMode` | Memilih player, controller, dan HUD khusus level tes |

Mulailah dari `BP_GameplayTestManager`.

1. Double-click aset, lalu pilih **EventGraph** pada panel My Blueprint.
2. Cari node F. Ikuti kabel eksekusi putih menuju `RequestActionCut`.
3. Double-click pemanggilan fungsi untuk membuka isinya. Fungsi ini memilih antara `StartTake` dan `CancelTake`.
4. Buka `StartTake`. Ikuti pemeriksaan fase, pemeriksaan HeldProp, evaluasi puzzle, pemberian TakeID, dan penguncian gerak.
5. Buka `EvaluatePuzzle`. Fungsi membaca slot yang sudah dikonfirmasi. Prop pertama diperiksa lebih dahulu, kemudian prop kedua.
6. Buka `NotifyTakeFinished`. Perhatikan pemeriksaan ID, fase, dan Outcome sebelum completion diterima.
7. Buka `RestartScene` untuk melihat perbedaan reset eksplisit dengan CUT.

Graph baru sudah diberi komentar. **Compile** memeriksa graph, sedangkan **Save** menyimpan perubahan. Saat mengedit child Blueprint, perhatikan nama aset pada tab agar perubahan tetap berada pada aset tes.

Untuk melihat nilai selama bermain, mulai PIE, buka manager, lalu pilih instance `BP_GameplayTestManager` pada **Debug Filter**. Perhatikan nilai berikut.

| Variabel | Nilai |
| --- | --- |
| `SceneIndex` | 1, 2, atau 3 |
| `State` | 0 Setup, 1 TakeActive, 2 SceneComplete, 3 FinalObjective, 4 SystemsComplete |
| `Outcome` | 0 Perfect, 1 kesalahan prop pertama, 2 kesalahan prop kedua |
| `TakeID` | ID baru untuk setiap ACTION yang diterima |
| `TakeCount` | Jumlah ACTION yang diterima dalam sesi |
| `CompletedCount` | Jumlah scene selesai yang masih tercatat |
| `Completed1/2/3` | Status completion tiap scene |

## Konfigurasi yang bisa diubah

Pilih actor `SYSTEM_GameplayTestManager` melalui Outliner. Details menyediakan referensi prop, marker awal, nama slot solusi, serta pengaturan simulator.

- `S1Prop1` dan `S1Prop2` menunjuk pasangan prop Scene 1. Prefix S2 dan S3 berlaku untuk scene berikutnya.
- `S1Start1` dan `S1Start2` menunjuk marker yang digunakan oleh restart.
- `S1Correct1` dan `S1Correct2` berisi nama SlotID solusi, misalnya `S1_P1_B` dan `S1_P2_C`.
- `SimulatorEnabled` mengaktifkan penyelesaian take sempurna secara otomatis di arena tes.
- `SimulatorSeconds` menentukan durasi simulator. Nilai awal adalah 2 detik.

Konfigurasi ini menguji kondisi berbasis slot. Feedback blocking, pandangan, dan pencahayaan ditampilkan sebagai teks tes. Foto referensi Scene 3 dan penampilan Maya akan membutuhkan pekerjaan presentasi pada tahap integrasi.

## Titik sambung untuk tahap berikutnya

`RequestActionCut`, `StartTake`, `CancelTake`, `NotifyTakeFinished(FinishedTakeID)`, dan `AdvanceScene` tersedia sebagai fungsi Blueprint. Penyelesaian eksternal nantinya harus mengirim ID take yang mulai dimainkan. ID lama ditolak setelah CUT dan retake. Penyelesaian berulang juga diabaikan.

Pada tahap ini, Tick manager hanya mensimulasikan akhir perfect take. Fase SceneComplete menunggu N sebagai pengganti transisi antarscene. Penyambungan Sequencer, reaksi Maya, dialog, perpindahan kru, dan dispatcher presentasi dilakukan setelah ada permintaan integrasi.

## Validasi

Pengujian dilakukan dalam PIE pada `L_GameplaySystems` di UE 5.6.1.

- 85 pemeriksaan logika mencakup kombinasi solusi tiga scene, 20 retake, preservasi prop, reset, callback ID lama, completion ganda, Notes, pause, progression, dan interkom.
- 31 pemeriksaan interaksi menggunakan jalur Enhanced Input. Keenam prop berhasil dipilih, dipindahkan ke slot solusi, dan menghasilkan auto-CUT. Slot terisi serta slot salah tipe ditolak. Input interkom berhasil menutup alur tiga scene.
- Empat Blueprint baru dikompilasi dengan nol error dan nol warning. HUD, feedback take, dan pause diperiksa di preview game.
- Pemeriksaan hash terhadap 22 file konfigurasi dan aset produksi tidak menemukan perubahan. Pemeriksaan ini mencakup `SB_GrayBox` dan Blueprint produksi yang dipakai sebagai parent atau referensi.

Bukti pengujian sesi tersimpan di `Saved/GameplaySystemsValidation.json`, `Saved/GameplayInteractionValidation.json`, `Saved/GameplaySystemsFinalCompile.json`, dan `Saved/GameplaySystemsIsolation.json`. Folder Saved merupakan output lokal yang diabaikan Git. Packaging Windows belum diuji.
