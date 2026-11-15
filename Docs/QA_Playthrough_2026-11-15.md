# QA Playthrough: 15 November 2026

**Branch:** `dev/falih` (belum di-commit: interlude + transition) · **Engine:** UE 5.6 · **Map:** `L_MainMenu` → `SB_GrayBox`

Satu playthrough penuh dari main menu sampai habis konten, pakai input asli (WASD, mouse, E, Tab, F, Space) lewat PIE. Screenshot ada di `Saved/Screenshots/Screenshot_20261115_0748*.png` s/d `0756*.png`.

Yang **di-shortcut** (bukan dimainkan manual): jalan lobby → living room dan dining → kitchen (teleport), memindah props (teleport; pickup manual sudah lulus di QA sebelumnya), dan sebagian dialog sukses/interlude dipercepat dengan `slomo`. Audio, pause menu dan build packaged tidak dites di run ini.

---

## 1. Bug yang dilaporkan: "Play dan ACTION beda"

**Status: CONFIRMED.** Akar masalahnya: ada **dua setup Scene 1 yang jalan bareng** di `SB_GrayBox`, dan keduanya tidak saling tahu.

| | Intro Ibra (`BP_ArrivalDirector`) | Take system (`BP_FilmSceneManager`) |
|---|---|---|
| Maya | `MAYA_Scene01` (follow `SET_Scene01_Maya_StandIn`), akhir intro berdiri di **tengah ruangan** (-190, -260) pegang skrip | `MAYA_Take`, mulai di **pintu** (`L01_MayaStart` -90, 380) |
| Lemari | `PROP_Scene01_Wardrobe` (220, -470), dibawa Crew A, **statis** (tidak bisa diangkat), persis di sebelah director mark | `L01_Prop_Wardrobe` (-490, -440), yang **dinilai rule** |
| Sofa | sofa dekorasi rumah | `L01_Prop_Sofa` (-140, 140), yang dinilai rule |
| Crew | Crew B berhenti di (-280, -210), Crew A di samping lemari statis | tidak diatur |

Yang dilihat player:

1. **Sebelum ACTION pertama:** Maya + Crew B di tengah ruangan, Maya pegang naskah.
2. **Saat ACTION:** stand-in Maya hilang, `MAYA_Take` muncul di pintu. Kertas naskah (`PROP_Intro_Maya_Script`, `PROP_Intro_ScriptLine_0..3`) **tertinggal melayang** di samping Crew B.
3. **Setelah CUT:** Maya tetap di pintu. Jadi SETUP sesudah take pertama beda dengan SETUP sebelum take pertama.
4. **Shot dinding (PERFECT):** Crew B berdiri persis di titik inspeksi Maya → **Maya dan Crew B tumpang tindih** di frame.
5. Lemari yang diceritakan intro (dibawa crew, di sebelah mark) bukan lemari yang menentukan hasil take. Ada dua lemari di ruangan.
6. Kamera duduk percakapan intro (`CINE_Arrival_Director_Seated`) setengahnya ketutup `L01_Prop_Sofa` di posisi awalnya.

**Usulan perbaikan (satu sumber kebenaran untuk staging Scene 1):**

- Saat intro Ibra selesai (stage 8), manager langsung serah-terima: sembunyikan stand-in + kertas naskah, tampilkan `MAYA_Take` di `L01_MayaStart`. Atau ubah target `FinishIntroduction` supaya stand-in jalan ke pintu (mark awal Laras), bukan ke tengah ruangan.
- Pakai **satu** lemari: jadikan lemari yang dibawa crew = `L01_Prop_Wardrobe` (atau hapus `PROP_Scene01_Wardrobe`).
- Pindahkan titik akhir Crew B dan Crew A keluar dari jalur dan frame take.
- Tambahkan `PROP_Intro_Maya_Script` + `PROP_Intro_ScriptLine_*` ke `StandInsToHide`.
- Geser posisi awal `L01_Prop_Sofa` supaya tidak menutup kamera duduk, tapi tetap menghalangi jalur.

Ini menyentuh BP Ibra (`BP_ArrivalDirector`), jadi perlu disepakati dulu sama Ibra.

---

## 2. Temuan lain (urut dari paling parah)

### Blocker

| # | Temuan | Detail |
|---|---|---|
| B1 | **Dead end setelah L02** | Setelah dialog sukses L02: `CurrentSceneIndex` 2, `CurrentSceneID` None, objective kosong, F tidak melakukan apa-apa (cuma Print String dev "No scene config is active"). Tidak ada L03, intercom, ending atau credits. Player terjebak tanpa petunjuk. Minimal untuk build jam: layar "To be continued" → credits → main menu. |

### Major (bikin player bingung)

| # | Temuan | Detail |
|---|---|---|
| M1 | Objective take muncul terlalu cepat | "SCENE 1 - THE ARRIVAL … [F] ACTION" sudah tampil di atas opening cinematic dan selama tutorial Ibra ("WASD — Walk toward the house"). Instruksinya bertabrakan. Sebaiknya objective take baru muncul setelah intro selesai. |
| M2 | Dua Director's Notes sekaligus | Tab membuka teks notes Ibra (kiri atas, numpuk dengan baris objective) **dan** papan notes 3D "[TAB] lower notes". |
| M3 | Director's mark tidak dijelaskan | Lingkaran oranye tanpa label/prompt. Player baru tahu harus berdiri di situ setelah menekan F di luar mark. Tidak ada hint "cari tanda oranye". |
| M4 | "Laras" tidak pernah dikenalkan | Objective dan speaker subtitle pakai "LARAS", sementara intro hanya menyebut Maya. Player baru tidak tahu Laras = karakter yang diperankan Maya. Contoh: "MAYA (as LARAS)" atau satu baris intro. |
| M5 | Outcome BLOCKED L01 tidak terbaca | Shot `CINE_L01_Wide` menampilkan Maya kecil di pintu kiri, sofa penghalang tidak jelas di frame. Player tidak paham apa yang salah tanpa hint. Bandingkan L02 OBSTRUCTED yang jelas (lemari tepat di depan kamera). |
| M6 | Petunjuk visual dinding tidak ada | L01 ("Wasn't there a doorway here?") dan L02 (outline pintu lama) sama-sama dinding polos. Clue yang jadi inti cerita tidak terlihat. Perlu decal/mesh tambalan atau outline pintu. |
| M7 | Props movable vs dekorasi tidak bisa dibedakan | Ruang tamu penuh sofa; yang bisa diangkat cuma ketahuan dari prompt "[E] PICK UP" saat diarahkan. Perlu outline/highlight atau hint di notes. |
| M8 | Tidak ada arahan ke L02 | Setelah interlude, objective berganti tapi tidak bilang "pergi ke dapur" atau di mana mark-nya. Dapur gelap. |
| M9 | Set opening/interlude ada di dalam secret room | Set meja (`CINE_Opening_*`, juga `LS_Interlude01`) berada di balik gate L02 (ruang rahasia). Secara cerita, ruangan yang "ditemukan" di L02 sudah dipakai syuting sejak opening. Perlu diputuskan tim: memang foreshadowing, atau set-nya dipindah. |

### Minor / polish

| # | Temuan | Detail |
|---|---|---|
| m1 | Maya teleport balik saat dialog sukses | Setelah PERFECT, `ResetTake` langsung mengembalikan Maya ke pintu (L01) selagi Surya memuji takenya. |
| m2 | Crew lobby menghalangi pintu masuk | `Crew_Camera`/`Crew_Gaffer` berdiri di jalur pintu depan, player menabrak mereka. |
| m3 | Wajah Maya gelap saat percakapan intro | Backlit, wajah hampir hitam di kamera duduk. |
| m4 | Transisi bisa terpotong | Kalau player menekan ACTION sebelum 7 baris `TR02_*` selesai, intro take menggantikan antreannya. Wajar, tapi baris Surya/Maya hilang. |
| m5 | Opening lambat, skip tidak jelas | Opening ±30 detik; prompt "SPACE Skip opening" ada tapi kecil. OK. |
| m6 | Main menu polos | Background datar tanpa scene. |
| m7 | Objective tetap tampil saat cinematic | Baris objective tetap di atas letterbox selama take dan interlude. |

---

## 3. Yang sudah jalan baik

- Main menu → PLAY → opening → tutorial (jalan, lihat, E pintu, Tab notes) → percakapan crew → kontrol balik.
- Gate ACTION di director mark + pesan "Stand on the director's mark…".
- L01: BLOCKED → hint → CUT line → layout benar → PERFECT → SCENE COMPLETE → dialog sukses.
- Interlude 01 (close-up Maya + 5 baris) → L02 SETUP, kamera balik ke player.
- Transition 07 terpicu di pintu dapur, Maya menunggu di dining.
- L02: OBSTRUCTED terbaca jelas, hint eksplisit ("The cabinet's getting in the way…"), PERFECT → gate ruang rahasia terbuka.

---

## 4. Dari sudut pandang player baru

> Opening-nya atmosferik: close-up Maya bicara soal kamera dan kebenaran, langsung kena mood-nya. Tapi dari detik pertama sudah ada tulisan "[F] ACTION" di atas, padahal aku bahkan belum di rumah. Tutorial jalan/lihat/pintu/notes jelas, cuma Tab memunculkan dua catatan sekaligus dan saling tumpuk.
>
> Di ruang tamu crew bilang "beberapa barang masih perlu ditempatkan", dan aku lihat crew menaruh lemari di dekat lingkaran oranye. Jadi aku kira lemari itu yang harus diurus. Ternyata tidak bisa diangkat. Aku tekan F dan disuruh berdiri di "director's mark", baru sadar lingkaran oranye itu mark-nya.
>
> Waktu ACTION, Maya tiba-tiba pindah ke pintu dan kertas naskahnya melayang sendiri di udara. Siapa Laras? Take pertama gagal, tapi dari kamera aku tidak lihat apa yang menghalangi. Baru dari hint suara aku tahu soal "walkway". Pas take berhasil, Maya mengamati dinding, tapi dindingnya polos, dan crew berdiri menembus badannya.
>
> Interlude-nya bagus. Scene 2 lebih jelas: lemari kelihatan menghalangi dan hint-nya langsung. Tapi setelah Scene 2 selesai, tidak ada apa-apa lagi. Aku jalan-jalan, tekan F, tidak terjadi apa-apa, dan tidak tahu game-nya sudah habis atau rusak.

**Kesimpulan:** loop inti (atur set → ACTION → lihat hasil → CUT) sudah terasa, dan L02 contoh yang bagus. Yang paling merusak pengalaman: (1) dua setup Scene 1 yang bertabrakan, (2) clue visual yang tidak ada padahal itu inti cerita, (3) game berhenti tanpa penutup setelah L02.

---

## 5. Status perbaikan (15 Nov, sesi siang)

| Temuan | Status | Catatan |
|---|---|---|
| Bagian 1: play vs ACTION beda | **FIXED, dites PIE** | Serah-terima di akhir intro Ibra (`FilmSceneManager.OnIntroFinished`). Maya Ibra berhenti di luar sofa L01 lalu jalan ke luar frame dekat pintu hall; `MAYA_Take` muncul di start L01. Kertas naskah, Crew B dan lemari duplikat disembunyikan. Kamera duduk dinaikkan. Ruangan dari director mark sama sebelum ACTION, saat take dan setelah CUT. |
| B1: dead end setelah L02 | **FIXED, dites PIE** | `EndOfDemo`: "TO BE CONTINUED..." 4 detik → `WBP_Credits` → main menu. F diabaikan (state `CREDITS`). |
| M1–M9, minor | Belum | Lihat prioritas di bawah. |

Perubahan di BP Ibra (`BP_ArrivalDirector`): dua target `MoveComponentTo` Maya diganti dan satu panggilan `OnIntroFinished` ditambah di akhir `FinishIntroduction`. Tidak ada logika tutorial yang diubah.

## 6. Prioritas yang disarankan

1. **Satukan staging Scene 1** (bagian 1). Perlu koordinasi dengan Ibra.
2. **Penutup sementara setelah L02**: layar "To be continued" → `WBP_Credits` → main menu, sampai L03 jadi.
3. **Objective & notes**: sembunyikan objective take sampai intro selesai, satu sistem notes saja, sebut director's mark di notes/objective.
4. **Clue dinding** L01 + L02 (decal/mesh tambalan, outline pintu).
5. **Framing BLOCKED L01** supaya sofa penghalang kelihatan.
6. Sisanya (minor) kalau waktu cukup.

## 7. Status perbaikan (15 Nov, sesi sore)

Dites di PIE (`SB_GrayBox`) dengan input asli (Space, Tab, F, N, T). Props di-teleport untuk mengecek PERFECT.

| Temuan / permintaan | Status | Catatan |
|---|---|---|
| Director's Notes (Tab) masih Scene 1 di Scene 2 | **FIXED, dites** | Clipboard `WBP_DirectorNotes` diisi dari `DA_SceneConfig_L0x` (`DisplayName`, `DirectorNotesText`) lewat `FilmSceneManager.RefreshDirectorNotes` (dipanggil di `ConfigureScene` dan setiap Tab). Overlay teks Ibra tidak dibuka lagi oleh Tab (`BP_ArrivalDirector.HandleNotes` cuma memajukan tutorial stage 4→5). |
| M2: dua notes sekaligus | **FIXED, dites** | Satu sistem notes: clipboard. |
| M3: director's mark tidak dijelaskan | **FIXED** | Baris notes "Stand on the orange director's mark, then [F] ACTION" + label lantai `L0x_DirectorMarkLabel`. |
| M4: Laras tidak dikenalkan | **FIXED, dites** | Notes L01: "Laras (played by Maya)". Speaker 12 baris `DT_Dialogue` jadi "MAYA (as LARAS)". |
| M6: clue dinding L01/L02 | **FIXED, dites** | L01: tambalan + kusen pintu lama di dinding barat (`Gameplay/Scene01/L01/Clue`), ketutup wardrobe di start (= MISSED_CLUE). L02: garis pintu tersegel + engsel + lubang kunci (`Gameplay/Scene02/L02/Clue`), kebaca jelas di PERFECT saat lampu di reveal zone. |
| Crew masih di lobby | **FIXED, dites** | `BP_CrewMember.SceneSpots` (SceneID → `CrewSpot_<Scene>_<Role>`), dipindah oleh `FilmSceneManager.StageCrew` di `ConfigureScene`. Posisi di luar frame semua kamera take, di luar jalur Maya dan area prop (PRD §5.5). |
| Animasi idle/walk error | **FIXED, dites** | `MAYA_Take` pakai `SKM_Quinn_Simple` + `MM_Idle`/`MF_Unarmed_Walk_Fwd` (9 sequence di-remap, yaw −90 untuk arah mesh). Follower Tripo intro disembunyikan, stand-in Manny/Quinn Ibra yang tampil. `TR02_Crew_B/C` pakai Manny. `BP_CrewMember` tetap Tripo (pose IK). |
| Shortcut testing | **BARU** | `N` = skip ke scene berikut (selesaikan intro, reset take, buka gate, teleport ke mark). `T` = toggle kecepatan ×4. Mati di build Shipping (`IsPackagedForDistribution`). |
| M1 objective terlalu cepat | **FIXED, dites** | `FilmSceneManager.ApplyObjective`: objective kosong selama intro Ibra, muncul di `OnIntroFinished` (`bIntroDone`). Tanpa `BP_ArrivalDirector` langsung tampil. |
| M5 framing BLOCKED L01 | **FIXED, dites** | Kamera baru `CINE_L01_Blocked` (over-the-shoulder dari pintu hall, -60, 540) untuk `LS_L01_Blocked`: sofa terlihat memotong jalur Maya. |
| M7 movable vs dekorasi | **FIXED (notes)** | Notes tiap scene menyebut prop yang bisa dipindah ("Movable: ..."). Tidak ada outline (custom shader = non-goal PRD). |
| M8 arahan ke L02 | **FIXED, dites** | Objective L02: "go to the kitchen...". Belum ada penunjuk arah di dunia. |
| Baru: objek gelap di bawah wide shot L01 | **FIXED, dites** | Bukan Surya (pawn sudah hidden), tapi sandaran sofa dekor `PROP_House_Living_Sofa_TwoSeat_01`. `CINE_L01_Wide` dinaikkan ke z 230, pitch -12. |
| Baru: hint tutorial Ibra tetap jalan kalau intro tidak dimainkan | Info | Hanya kalau prop/pemain di-teleport; `N` menutup intro dengan `FinishIntroduction`. |
| Clue L01 ketutup sofa dekor | **FIXED, dites** | Clue digeser ke y -490; sofa 3-seat + armchair dekor +120 y, pot tanaman ke (-477, 357). Masih di belakang wardrobe start. |
| Crew Tripo (`BP_CrewMember`) | Tetap | Pose IK di-tuning untuk Tripo. |

### 7b. Feedback setelah tes (15 Nov, sore)

| Temuan | Status | Catatan |
|---|---|---|
| Crew L02 nembus counter dapur | **FIXED** | Spot L02 dipindah ke barat counter (x ≤ 1410). Dicek tanpa interseksi. Juga tidak di jalur mark → lampu. |
| Standing lamp L02 tidak bisa di-interact | **FIXED, dites** | `SM_House_Lamp_Floor` tidak punya collision yang kena line trace. `BP_StandingLampProp` dapat `InteractBox` (BoxComponent, profile `InteractableProp`, 60×60×172). PIE: `FocusProp` → lampu, E → `HeldProp` = lampu. Penempatan belum dites manual. |
| Sofa intro menghalangi player | **FIXED** | `BP_ArrivalDirector.InitializeArrival` menyembunyikan `Scene1Sofa` (`PROP_House_Living_Sofa_ThreeSeat_01`) dan mematikan collision-nya. |
| Crew "mendorong" barang di cutscene awal | **FIXED** | Cabang Crew B (dorong sofa) dan Crew A (bawa wardrobe) di `StartConversation` dihapus. Crew diam di posisi awal; Maya tetap jalan ke kursi. |
