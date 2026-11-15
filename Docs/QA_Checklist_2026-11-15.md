# QA Checklist: 15 November 2026

**Branch:** `dev/falih` (`9805368`) · **Engine:** UE 5.6

Isinya hal-hal yang sudah dites dev di sesi 15 Nov (lihat `DevLog_2026-11-15_Falih.md`). QA tinggal ulangi manual di PIE dan isi kolom hasil.

Legend sumber: **AUTO** = sudah lulus lewat script, **MANUAL** = dites dev manual di PIE.

Cara isi: tulis `PASS` / `FAIL` + catatan singkat. Kalau FAIL, sertakan langkah reproduksi dan screenshot (`Saved/Screenshots/`).

---

## A. Core loop ACTION/CUT: `SB_GrayBox`

**Setup:** buka `Content/Game/Levels/SB_GrayBox`, Play, klik viewport.

> Take di map ini **berakhir otomatis sekitar 8 detik**. Itu bukan bug (lihat Known Issues). Kalau mau tes CUT manual, tekan F sebelum 8 detik.

| # | Langkah | Expected | Sumber | Hasil |
|---|---|---|---|---|
| A1 | Tekan F di SETUP | State masuk TAKE_PLAYING, kamera pindah ke cine cam (letterbox 2.39:1), crosshair hilang | MANUAL | |
| A2 | Coba WASD, mouse, E, RMB selama take | Player gak bisa gerak, look, atau interaksi | MANUAL | |
| A3 | Amati crew selama take | Crew jadi Focused (diam, menghadap set) | MANUAL | |
| A4 | Tekan F lagi (sebelum 8 detik) | CUT: state balik ke SETUP, kamera first-person dan kontrol pulih | MANUAL | |
| A5 | Amati crew setelah CUT | Crew balik ke Relaxed | MANUAL | |
| A6 | Ulangi A1–A4 dua kali berturut-turut | Tiap siklus bersih, gak ada kamera nyangkut atau input terkunci | MANUAL | |
| A7 | Tekan F lalu tunggu sampai lebih dari 8 detik tanpa input | Take selesai sendiri, balik ke SETUP, kamera dan kontrol pulih | MANUAL | |
| A8 | Langsung gerak setelah CUT | Gak ada sisa velocity (player gak meluncur) | MANUAL | |
| A9 | Shot pertama tiap take baru | Selalu mulai dari opening shot | MANUAL | |

## B. Karakter Tripo dan crew: `SB_GrayBox`

| # | Cek | Expected | Sumber | Hasil |
|---|---|---|---|---|
| B1 | Mesh crew per aktor | `Crew_Camera` = Crew A, `Crew_Boom` = Crew B, `Crew_Script` = Crew B, `Crew_Gaffer` = Crew Utility | MANUAL | |
| B2 | Tekstur crew | Gak ada material abu-abu default atau checker | MANUAL | |
| B3 | Skala | Tinggi masuk akal (Maya sekitar 166 cm, crew 175–181 cm), gak ada yang mini atau raksasa | MANUAL | |
| B4 | Pose Boom | Dua tangan di atas kepala, tiang boom lewat tepat di kedua tangan | MANUAL | |
| B5 | Pose Camera | Dua tangan pegang kamera di depan wajah | MANUAL | |
| B6 | Pose Script | Dua tangan pegang clipboard di depan dada | MANUAL | |
| B7 | Pose Gaffer | Pose natural, tanpa IK | MANUAL | |
| B8 | Lengan dan pergelangan semua crew | Lengan gak menyilang, pergelangan gak terpelintir, tangan gak tembus prop | MANUAL | |
| B9 | Idle crew | Pinggul diam di tengah, gak goyang ke samping | MANUAL | |
| B10 | `MAYA_Opening`, `MAYA_Scene01` | Model Tripo Maya ikut stand-in: walk saat bergerak, idle saat diam | MANUAL | |
| B11 | `CREW_Intro_PropMaster`, `CREW_Intro_SetDresser`, `CREW_Intro_Lobby` | Model Tripo ikut stand-in intro | MANUAL | |
| B12 | Stand-in Quinn/Manny | **Gak kelihatan** sepanjang opening dan Scene 01 | MANUAL | |
| B13 | Mesh Tripo saat animasi | Gak ada mesh kolaps atau melar | MANUAL | |

## C. Sistem gameplay: `L_GameplaySystems` (level tes Yaser)

**Setup:** buka `Content/Game/Levels/Tests/L_GameplaySystems`, Play. Kontrol lengkap ada di `GameplaySystems_TestGuide.md`.

Semua item di bawah sudah lulus otomatis lewat `Tools/ValidateGameplaySystems.py` (**85/85**, hasilnya di `Saved/GameplaySystemsValidation.json`). QA tinggal ulangi lewat input asli.

### C1. Outcome per scene (ulangi untuk Scene 1, 2, 3, pakai tombol 1/2/3)

Prop 1 / Prop 2 per scene: Scene 1 = Sofa / Wardrobe, Scene 2 = Cabinet / Lamp, Scene 3 = Chair / Lamp.

| # | Prop 1 di area | Prop 2 di area | Expected outcome | Hasil S1 | Hasil S2 | Hasil S3 |
|---|---|---|---|---|---|---|
| C1.1 | Tidak | Tidak | Error prop 1, nunggu CUT | | | |
| C1.2 | Ya | Tidak | Error prop 2, nunggu CUT | | | |
| C1.3 | Tidak | Ya | Error prop 1 (prop 1 dicek duluan) | | | |
| C1.4 | Ya | Ya | Perfect, auto-CUT sekitar 2 detik | | | |

Di tiap kombinasi juga cek:

- [ ] Gerak terkunci selama take.
- [ ] Setelah CUT, posisi prop tetap di tempat terakhir.
- [ ] Setelah CUT, gerak pulih dan state SETUP.

### C2. Rules take

| # | Langkah | Expected | Hasil |
|---|---|---|---|
| C2.1 | Pegang prop, tekan F di director mark | ACTION ditolak, TakeCount gak naik | |
| C2.2 | Tekan F di luar director mark | ACTION ditolak | |
| C2.3 | ACTION/CUT berulang 20 kali | Tiap siklus balik ke SETUP, gerak pulih, gak ada softlock | |
| C2.4 | ACTION → CUT cepat → ACTION lagi (setup perfect) | Completion dari take lama gak bikin scene selesai | |
| C2.5 | Perfect take selesai | Scene complete tepat **sekali** | |
| C2.6 | Perfect take, lalu spam input | Completion gak dobel | |

### C3. Restart, Notes, Pause

| # | Langkah | Expected | Hasil |
|---|---|---|---|
| C3.1 | R setelah scene selesai | Completion scene aktif ke-reset, state SETUP | |
| C3.2 | R | Posisi dan rotasi prop balik ke awal, preview bersih | |
| C3.3 | Tab | Notes buka, teks sesuai scene (mis. "SCENE 1"). Tab lagi untuk tutup | |
| C3.4 | P | Game pause, P lagi untuk resume | |

### C4. Progression dan interkom

| # | Langkah | Expected | Hasil |
|---|---|---|---|
| C4.1 | Selesaikan Scene 1 → N → Scene 2 → N → Scene 3 | Tiap scene complete, berurutan | |
| C4.2 | Setelah Scene 3 + N | Objective final interkom aktif | |
| C4.3 | Tekan E jauh dari interkom | Ditolak, gak ada yang terjadi | |
| C4.4 | Tekan E dekat interkom | Systems run selesai (state akhir) | |
| C4.5 | Tekan E lagi di interkom | Aman, gak error dan gak trigger ulang | |

---

## Known issues (jangan di-report sebagai bug baru)

1. Take di `SB_GrayBox` auto-end sekitar 8 detik (`LS_TakePreview` OnFinished → `EndTake`). Ini bentrok sama PRD §4.3 dan masih nunggu keputusan tim.
2. ACTION di `SB_GrayBox` belum ada gating director mark. Prop/slot puzzle juga belum ada di map ini.
3. Maya belum ada performance atau reaction, masih stand-in plus follower.
4. Kalau editor gak fokus saat PIE, waktu game bisa lompat sekitar 10 detik antar-aksi. Klik viewport dulu sebelum tes timing.
5. Placement di `L_GameplaySystems` pakai free placement + radius area, belum pakai slot sesuai PRD.

## Belum dites (di luar cakupan checklist ini)

- Pickup/placement prop di `SB_GrayBox`.
- HeldProp ditolak di `SB_GrayBox` (graph-nya ada, tapi belum dites runtime).
- Race input F tepat di akhir take, resize viewport.
- Windows packaged build.
