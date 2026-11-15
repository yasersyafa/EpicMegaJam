# Audit ketersediaan VO — SB_GrayBox

Audit 16 November 2026, UE 5.6.1. Pemeriksaan read-only terhadap aset yang dimuat dari disk, audio sections Sequencer, aktor map, konfigurasi scene, tabel dialog, graph Blueprint dan manifest rekaman. Tidak ada aset gameplay yang diubah. Belum merupakan listening test atau verifikasi playback baru.

## Ringkasan

- 23/23 WAV rekaman pada `Tools/Isolated/CampaignVO.json` tersedia di disk; folder audio campaign berisi 24 SoundWave termasuk turunan `S_VO_CutSofa`. Ada tambahan turunan pendek `S_Director_Cut` untuk map utama.
- 22 kelompok naratif dengan VO berhasil dimuat sebagai SoundWave berdurasi positif. Dua kelompok naratif tanpa VO adalah aftermath L01 dan L03. Rekaman ManualCut berada di manifest VO terpisah dari 22 kelompok tersebut.
- 10 sequence produksi memiliki 25 section VO aktif. Ini menggunakan delapan rekaman sumber; beberapa rekaman dibagi ke sequence opening dan perfect. Sound effect camera power terpisah dari jumlah VO.
- `FilmSceneManager` di map memiliki `CutShout = S_Director_Cut` dan hanya dua `SceneConfigs`: L01 dan L02.
- `DT_Dialogue` memiliki 62 baris; **62/62 VoiceSound = None**. Audio yang sudah terdengar pada take berasal dari Sequencer, bukan tabel ini.
- `BP_ArrivalDirector` mengatur intro melalui graph tersendiri; tidak ditemukan node pemutaran sound/audio pada EventGraph-nya. Tabel alternatif `DT_Scene01Dialogue` juga memiliki 34/34 Sound = None, tetapi tabel alternatif itu bukan bukti bahwa sistem tersebut dipakai map utama.

## Sudah terpasang

| Bagian | Aset sequence / jalur | Cakupan |
|---|---|---|
| Opening Maya | `Opening/LS_Opening_Maya` | Empat kalimat VO; camera-power SFX juga ada |
| L01 opening + perfect | `L01/LS_L01_Opening`, `LS_L01_Perfect` | Enam kalimat performance Maya |
| L01 blocked | `L01/LS_L01_Blocked` | Respons Maya; hint Surya belum |
| L01 missed clue | `L01/LS_L01_MissedClue` | Respons Maya; hint Surya belum |
| Interlude 01 | `Interludes/LS_Interlude01` | Lima kalimat Maya |
| L02 opening + perfect | `L02/LS_L02_Opening`, `LS_L02_Perfect` | Enam kalimat performance Maya |
| L02 obstructed | `L02/LS_L02_Obstructed` | Respons Maya; hint Surya belum |
| L02 dark | `L02/LS_L02_Dark` | Respons Maya; hint Surya belum |
| Manual CUT | Manager → `S_Director_Cut` | Hanya teriakan CUT sekitar 0,55 detik; bukan seluruh kalimat reset |

Path sequence di atas relatif terhadap `/Game/Game/Cinematics/`. Semua section yang dihitung aktif; audit tidak menjamin sinkronisasi subtitle, kualitas mixing, atau bahwa semua cabang berhasil dimainkan.

## Audio tersedia, belum terpasang pada dialog yang sudah ada

| Bagian / baris utama | Rekaman tersedia | Pekerjaan integrasi |
|---|---|---|
| Intro crew dan Maya, sembilan kalimat | `S_VO_Intro` | Hubungkan ke pergantian kalimat milik ArrivalDirector, bukan memutar satu file sekaligus tanpa mengikuti jeda tutorial |
| Crew transition sesudah L01: `L01_SUCCESS_06..08` | `S_VO_L01_CrewTransition` | Pasang tiga potongan sesuai baris dialog |
| Menuju dapur: `TR02_01..07` | `S_VO_KitchenApproach` | Pasang pada dialog yang dipicu `TR02_DialogueTrigger` |
| Aftermath L02: `L02_SUCCESS_01..07` | `S_VO_Aftermath` | Pasang tujuh potongan; rekaman ini khusus percakapan tentang knocking |
| Service transition: `L02_SUCCESS_08..12` | `S_VO_ServiceTransition` | Lima kalimat sudah tercantum di konfigurasi success L02, tetapi VoiceSound kosong |
| Hint pertama empat kegagalan: `L01_HINT_BLOCKED_1`, `L01_HINT_MISSED_1`, `L02_HINT_OBSTRUCTED_1`, `L02_HINT_DARK_1` | Bagian Surya pada empat file failure | Potong/pakai offset kalimat Surya, tanpa menggandakan respons Maya yang sudah dimainkan Sequencer |
| CUT awal L01/L02 | `S_VO_ManualCut` | File lengkap tersedia: “Cut! Hold on, I need to tidy up the scene.” Saat ini hanya teriakan pendek dipasang |
| CUT karena sofa: `L01_CUT_BLOCKED` | Ekor rekaman `S_VO_L01_FailBlocking`, turunan `S_VO_CutSofa` | Rekaman kalimat lengkap tersedia; map utama belum memakai cue lengkap ini |

Lima kelompok percakapan pertama berisi 31 kalimat yang rekamannya tersedia (9 + 3 + 7 + 7 + 5). Empat hint dan kalimat CUT merupakan kekurangan tambahan/parsial.

## Audio tersedia, alur cerita belum ada di map utama

Sembilan rekaman berikut ada pada campaign terisolasi, tetapi `SB_GrayBox` hanya mengonfigurasi L01/L02 dan graph manager masih memiliki `EndOfDemo`. Konfigurasi L02 tidak memiliki InterludeSequence atau InterludeDialogueIDs. Memasukkan semuanya membutuhkan integrasi progression/cutscene berikutnya, bukan sekadar menambah sound ke tabel:

1. `S_VO_Interlude02` — The Edit.
2. `S_VO_LastRoomApproach` — menuju ruang terakhir.
3. `S_VO_L03_FailChair` — kegagalan kursi.
4. `S_VO_L03_FailLight` — kegagalan lampu.
5. `S_VO_L03_Perfect` — take benar Scene 3.
6. `S_VO_Interlude03` — The Ending.
7. `S_VO_FinalPickup` — intercom/final pickup.
8. `S_VO_Confession` — pengakuan akhir.
9. `S_VO_Reveal` — final reveal.

Jangan menambahkan `BP_CampaignDirector` begitu saja bersama director utama: kedua sistem memiliki tanggung jawab flow, kamera, dialog, dan input yang tumpang tindih. Integrasi harus memakai handoff/ownership yang jelas.

## Rekaman belum tersedia / belum ditemukan padanannya

- **Aftermath L01:** lima kalimat `L01_SUCCESS_01..05`; manifest eksplisit `vo=false`.
- **Aftermath L03:** enam kalimat; manifest eksplisit `vo=false` dan alurnya juga belum ada di SB_GrayBox.
- **Empat hint alternatif** `L01_HINT_BLOCKED_2`, `L01_HINT_MISSED_2`, `L02_HINT_OBSTRUCTED_2`, `L02_HINT_DARK_2`: tidak ditemukan padanan dalam cue/transkrip sumber yang tersedia.
- **Tiga kalimat CUT khusus** `L01_CUT_MISSED`, `L02_CUT_OBSTRUCTED`, `L02_CUT_DARK`: tidak ditemukan rekaman lengkap dengan wording yang sama. Teriakan generik yang sudah ada tidak mencakup instruksi lanjutannya.

“Belum ditemukan” mengacu pada aset/manifest lokal yang diperiksa; tidak menyatakan rekaman tersebut tidak mungkin ada di folder eksternal lain. Original MPEG menunjuk lokasi mesin anggota tim lain; audit ini mengonfirmasi WAV lokal dan aset Unreal, bukan keberadaan MPEG di mesin tersebut.

## Urutan implementasi yang disarankan

1. Lengkapi 31 kalimat percakapan yang sudah punya alur di map, empat hint pertama, dan CUT yang sumbernya tersedia.
2. Pastikan player dialog memiliki AudioComponent yang dapat dihentikan pada CUT, reset, skip, pergantian dialog, dan EndPlay. Graph manager saat ini menggunakan `Play Sound 2D`; `StopDialogue` membersihkan timer/queue dan CutAudio, belum membuktikan kemampuan menghentikan VO dialog baru.
3. Pertahankan satu pemilik playback tiap kalimat: jangan memasukkan VO take ke tabel lalu memutarnya lagi melalui Sequencer. Sesuaikan durasi subtitle dengan potongan audio, sambil mempertahankan subtitle gameplay tanpa black band.
4. Integrasikan alur L03 hingga ending untuk sembilan rekaman lanjutan; baru setelah itu QA alur penuh.
5. Rekam/pasok dialog yang belum ada atau tetapkan fallback subtitle secara eksplisit.

## Bukti

- `Saved/GrayBoxAudio/AvailabilityAudit/assets.json`: sound duration, section aktif, waktu/offset, aktor map.
- `Saved/GrayBoxAudio/AvailabilityAudit/configs.json`: daftar dialog dan sequence L01/L02.
- `Saved/GrayBoxAudio/AvailabilityAudit/DT_Dialogue.json`: 62 baris tabel produksi.
- `Saved/GrayBoxAudio/AvailabilityAudit/DT_Scene01Dialogue.json`: tabel alternatif.
- Graph manager dan ArrivalDirector tersimpan di folder bukti yang sama.
- `Tools/Isolated/CampaignNarrative.json`, `CampaignVO.json`: cue dan asal rekaman.

Editor audit dijalankan tersembunyi, audio dimatikan, prioritas BelowNormal, tanpa input desktop. Tidak melakukan implementasi VO pada sesi audit ini.
