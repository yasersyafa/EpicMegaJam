# Dev Log: 15 November 2026 (01:30 – 03:54)

**Developer:** Falih (dibantu Claude Code)
**Branch:** `dev/falih`
**Engine:** UE 5.6, Blueprint-only

---

## Ringkasan

Sesi ini fokus mengganti karakter placeholder (mannequin) dengan model **Tripo** untuk Maya dan crew, merapikan pose tangan crew, lalu menguji core loop. Hasil akhirnya:

- Maya dan semua crew sudah memakai model Tripo dan satu skeleton bersama.
- Pose crew yang memegang prop (kamera, boom, clipboard) sudah natural.
- Core loop ACTION/CUT di `SB_GrayBox` berjalan benar.
- Validasi gameplay Yaser (`L_GameplaySystems`) lulus 85/85.

Perubahan sesi ini **belum di-commit**.

---

## Timeline

### 01:30: Sinkronisasi branch
- `dev/falih` di-push ke remote (`e638f6c`). Isinya sudah termasuk `main` terbaru dengan PR #2 Yaser (free placement dan director mark).
- Dicek ulang bahwa tidak ada commit `main` yang tertinggal.

### ~01:35: Persiapan animasi dari Tripo
- Dibahas apa saja yang perlu di-download dari Tripo: FBX ber-rig dengan skin, T/A-pose, dan tekstur.
- Disusun daftar animasi minimum: 5 untuk Maya (idle, walk, look around, hesitate, inspect) dan 4 untuk crew (idle, arms crossed, talking, clipboard).

### ~01:40: Import karakter Tripo
- Sumber: `Downloads/Characters`, berisi Maya plus 5 animasi dan 3 crew ber-rig (salah satunya membawa 3 animasi).
- Rig Tripo ternyata memakai **nama tulang yang sama dengan UE5 Manny**.
- Semua karakter diimpor ke **satu skeleton bersama** `SK_Tripo_Humanoid`, jadi animasi bisa dipakai bersama oleh Maya dan crew.
- Skala diperbaiki karena tinggi asli Tripo sekitar 100 cm:
  - Maya 166 cm
  - Crew A 178 cm
  - Crew B 181 cm
  - Crew Utility 175 cm
- Tekstur crew tidak ikut di FBX ber-rig. Setelah file `.jpg` ditambahkan, dibuat master material `M_Tripo_Character` dan `MI_Crew_A/B/Utility`.
- Animasi yang tersedia:
  - `A_Tripo_Idle`, `Walk`, `Wait`, `LookAround`, `FoldArms`, `Agree`
  - `A_Tripo_Crew_Idle`, `A_Tripo_Crew_FoldArms`

### ~01:55: Crew memakai model Tripo
- `ABP_Crew` dipindah ke skeleton Tripo (asset aslinya yang diubah, bukan duplikat).
- `BP_CrewMember` default memakai mesh `SKM_Crew_A`. Mesh per aktor:

  | Aktor | Mesh |
  |---|---|
  | `Crew_Camera` | `SKM_Crew_A` |
  | `Crew_Boom` | `SKM_Crew_B` |
  | `Crew_Script` | `SKM_Crew_B` |
  | `Crew_Gaffer` | `SKM_Crew_Utility` |

### 02:07: Feedback: crew "tidak seperti manusia", tangan tidak pas dengan prop
Hasil investigasi lewat pengukuran tulang di PIE:
1. **Animasi idle Tripo bergoyang sampai 30 cm ke samping** (weight shift). Tangan yang dikunci IK tertinggal, sehingga lengan menyilang.
2. **Lengan Tripo lebih pendek** (sekitar 36 cm dibanding Manny). Target tangan untuk boom (z 194) tidak terjangkau.
3. Rotasi tangan (`HandRot`) masih hasil tuning tulang Manny, sehingga pergelangan terpelintir.

Perbaikan:
- Pose dasar crew diganti ke `A_Tripo_Wait`, yang pinggulnya diam di tengah.
- Target tangan, siku, dan posisi prop dihitung ulang dari posisi bahu yang diukur. Hasil di PIE:
  - **Boom** memegang tiang dengan dua tangan di atas kepala. Tiang dihitung supaya lewat tepat di kedua tangan.
  - **Camera** memegang kamera dengan dua tangan di depan wajah.
  - **Script** memegang clipboard dengan dua tangan di depan dada.
  - **Gaffer** tanpa IK, memakai pose natural.
- `HandRot` dinolkan.

### ~02:30: Maya dipasang di level
- Dites apakah animasi Manny (dipakai `BP_ArrivalDirector` dan `LS_Opening_Maya` milik Ibra) bisa jalan di model Tripo:
  - Lewat compatible skeleton: **mesh kolaps**.
  - Lewat retarget IK (`IK_Tripo` + `RTG_Manny_To_Tripo`): **mesh juga kolaps**, kemungkinan karena bind pose bawaan Tripo.
- Solusi tanpa mengubah kerjaan Ibra: **`BP_TripoFollower`**.
  - Menempel ke stand-in Ibra dan menyembunyikan mesh Quinn/Manny-nya.
  - Memakai `ABP_TripoFollower`, yang otomatis memutar walk saat stand-in bergerak dan idle saat diam.
- Aktor yang dipasang:

  | Aktor | Menempel ke | Mesh |
  |---|---|---|
  | `MAYA_Opening` | `CINE_Opening_Maya_StandIn` | `SKM_Maya` |
  | `MAYA_Scene01` | `SET_Scene01_Maya_StandIn` | `SKM_Maya` |
  | `CREW_Intro_PropMaster` | `NPC_Intro_CrewA_PropMaster` | `SKM_Crew_Utility` |
  | `CREW_Intro_SetDresser` | `NPC_Intro_CrewB_SetDresser` | `SKM_Crew_A` |
  | `CREW_Intro_Lobby` | `NPC_Intro_CrewC_Lobby` | `SKM_Crew_B` |

- Masalah: stand-in masih terlihat karena `SetActorHiddenInGame` dibuka lagi oleh director Ibra. Diperbaiki dengan mematikan visibility komponen mesh-nya.

### ~03:00: Testing core loop dan level
- **`SB_GrayBox`:**
  - ACTION: state TAKE_PLAYING, kamera pindah ke cine cam, gerak pemain terkunci, crew fokus.
  - CUT: state SETUP, kamera dan kontrol kembali, crew rileks.
  - Dua siklus berturut-turut bersih.
- **`L_GameplaySystems` (Yaser):** `Tools/ValidateGameplaySystems.py` lulus **85/85 check**, mencakup:
  - outcome di 3 scene
  - CUT mempertahankan posisi prop
  - 20 siklus retake
  - completion basi diabaikan
  - progress 3 scene dan interkom
- Sempat terlihat seperti bug double-trigger tombol F. Ternyata take di `SB_GrayBox` **berakhir otomatis setelah sekitar 8 detik** (`LS_TakePreview` OnFinished → `EndTake`), dan tes CUT jatuh setelahnya. Debounce yang sempat ditambahkan ke `BP_FilmSceneManager` **dibatalkan**, jadi file Yaser tidak berubah.

### 03:54: Ringkasan dan dev log

---

## Aset baru / berubah (belum di-commit)

**Baru**
- `Content/Characters/Tripo/`
  - `SK_Tripo_Humanoid`, `M_Tripo_Character`, `ABP_TripoFollower`
  - `Maya/`: `SKM_Maya`, `M_Maya`, `T_Maya_BC`, `T_Maya_N`
  - `Crew/`: `SKM_Crew_A`, `SKM_Crew_B`, `SKM_Crew_Utility`, `MI_Crew_*`, `T_Crew_*_BC`
  - `Anims/`: 8 animasi `A_Tripo_*`
  - `Rig/`: `IK_Tripo`, `RTG_Manny_To_Tripo` (belum terpakai)
- `Content/Game/Blueprints/Characters/BP_TripoFollower`

**Berubah**
- `Content/Game/Blueprints/Crew/ABP_Crew`: skeleton Tripo, pose dasar `A_Tripo_Wait`.
- `Content/Game/Blueprints/Crew/BP_CrewMember`: mesh default, target IK, dan posisi prop baru.
- `Content/Game/Levels/SB_GrayBox.umap`: mesh crew per aktor dan 5 aktor `BP_TripoFollower`.

---

## Catatan untuk tim

1. **Bertentangan dengan PRD:** take di `SB_GrayBox` berakhir otomatis sekitar 8 detik, padahal take gagal seharusnya menunggu CUT. Perlu dibahas dengan Yaser.
2. ACTION di `SB_GrayBox` belum ada gating. Director mark baru ada di level tes Yaser, dan prop/slot puzzle belum ada di level utama.
3. Branch `ibra` (commit "cb") belum masuk `main` dan bentrok di 4 file: `BP_ArrivalDirector`, `WBP_OpeningOverlay`, `WBP_Scene01Objective`, `VerifySeatedConversation.py`. Biar Ibra yang resolve.
4. **Ibra:** pull dulu sebelum menyimpan `SB_GrayBox`, supaya crew dan `FilmSceneManager` tidak hilang lagi seperti sebelumnya.
5. Animasi Manny tidak bisa dipakai di model Tripo. Kalau sequence Ibra butuh pose khusus Maya (duduk, berdiri, dan sebagainya), animasinya perlu dibuat atau di-download langsung untuk rig Tripo.
6. Ukuran folder Tripo sekitar 40 MB (tekstur 4K, di-cap 2048 saat runtime), sedangkan repo tanpa LFS.
7. Saat tes di PIE dengan editor tidak fokus, waktu game bisa melompat sekitar 10 detik antar-aksi. CUT manual perlu ditekan sebelum 8 detik.

## Langkah berikutnya
- Commit + push: `feat(characters): add Tripo Maya and crew with shared skeleton`.
- Tunggu keputusan tim soal auto-end take dan integrasi puzzle ke `SB_GrayBox`.
