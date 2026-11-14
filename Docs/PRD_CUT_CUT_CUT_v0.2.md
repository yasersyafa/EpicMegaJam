# PRODUCT REQUIREMENTS DOCUMENT

# CUT! CUT! CUT!

**Version:** 0.2 — Draft for Review
**Engine:** Unreal Engine 5.x
**Development Approach:** Blueprint-first
**Platform:** Windows PC
**Genre:** First-Person Narrative Puzzle / Psychological Horror
**Target Playtime:** 10–15 minutes
**Scope:** 3 Levels + Ending Cinematic + Credits
**Art & Visual Development:** Out of scope for this document

---

## 1. PRODUCT OVERVIEW

### 1.1 Game Description

CUT! CUT! CUT! adalah game first-person di mana pemain berperan sebagai sutradara film bernama Surya.

Pemain harus mempersiapkan lokasi syuting dengan memindahkan properti dan mengatur pencahayaan. Setelah set siap, pemain memulai pengambilan gambar menggunakan perintah ACTION.

Seorang aktris bernama Maya akan menjalankan adegan berdasarkan naskah dan kondisi set yang telah dipersiapkan.

Jika penataan set menyebabkan Maya kesulitan berakting, pemain dapat menghentikan adegan menggunakan CUT, memperbaiki set, kemudian melakukan RETAKE.

Setelah tiga adegan selesai, cerita berakhir melalui cinematic yang mengungkap identitas sebenarnya dari karakter pemain.

### 1.2 Product Goals

- Memberikan pengalaman menjadi sutradara film dari perspektif first-person.
- Memiliki satu sistem interaksi utama yang mudah dipelajari.
- Memberikan feedback gameplay melalui perilaku dan dialog aktor.
- Menghasilkan pengalaman cinematic dengan camera shots seperti film.
- Menghubungkan tiga level menjadi satu cerita dengan ending yang kuat.
- Menghasilkan prototype yang playable dan stabil dalam empat hari pengembangan.

### 1.3 Non-Goals

Fitur berikut tidak direncanakan untuk MVP:

- AI aktor yang memiliki perilaku bebas.
- Sistem combat.
- Physics-based furniture placement.
- Free camera positioning atau manual cinematography.
- Timeline video editor yang dikendalikan pemain.
- Branching ending.
- Multiplayer.
- Sistem inventory.
- Sistem dialog bercabang.
- Real-time recording gameplay untuk final movie.
- Shader, material, dan visual effects khusus.

---

## 2. CORE GAMEPLAY

### 2.1 Core Mechanic

**Set Arrangement**

Pemain dapat mengambil dan menempatkan properti tertentu ke posisi yang telah disediakan.

Setiap posisi properti memengaruhi kondisi adegan dan respons Maya.

Sistem interaksi yang sama digunakan untuk furnitur, meja, lemari, dan standing lamp.

### 2.2 Core Loop

**PREPARE → ACTION → OBSERVE → CUT / COMPLETE**

| Phase    | Player Experience                                                 |
| -------- | ----------------------------------------------------------------- |
| PREPARE  | Pemain mengeksplorasi ruangan dan menata properti                 |
| ACTION   | Pemain memulai pengambilan gambar                                 |
| OBSERVE  | Maya menjalankan scripted performance melalui cinematic camera    |
| CUT      | Pemain menghentikan adegan untuk memperbaiki set                  |
| RETAKE   | Pemain memulai ulang adegan dengan setup terbaru                  |
| COMPLETE | Perfect Take otomatis diakhiri dengan CUT dan dialog keberhasilan |

### 2.3 Input Mapping

| Input       | Action                    | Availability                     |
| ----------- | ------------------------- | -------------------------------- |
| WASD        | Movement                  | Setup                            |
| Mouse       | Look                      | Setup                            |
| E           | Interact / Pickup / Place | Setup                            |
| F           | ACTION                    | Setup                            |
| F           | CUT                       | Take Playing / Awkward / Waiting |
| Right Mouse | Cancel Placement          | Holding Prop                     |
| Tab         | Director's Notes          | Setup                            |
| Esc         | Pause Menu                | Gameplay                         |

Implementasikan menggunakan Enhanced Input.

### 2.4 Player Controller

Gunakan Unreal First Person Template sebagai fondasi.

Player Character menggunakan `CharacterMovementComponent` untuk pergerakan dasar.

Kamera first-person aktif selama Setup Mode

Ketika ACTION dimulai:

1. Input movement dinonaktifkan.
2. Interaksi properti dinonaktifkan.
3. Kamera berpindah ke cinematic.
4. Input CUT tetap aktif.

Ketika CUT dipanggil:

1. Cinematic playback dihentikan.
2. Camera view dikembalikan ke player.
3. Maya dikembalikan ke starting position.
4. Player masuk ke Setup Mode.
5. Properti mempertahankan posisi terakhir.

Pemain tidak dapat mengubah properti ketika take sedang berlangsung.

---

## 3. PROP INTERACTION SYSTEM

### 3.1 Pickup System

Pemain mengarahkan crosshair ke properti interaktif.

Gunakan camera line trace untuk mendeteksi objek dalam interaction distance.

Ketika objek terdeteksi, UI memperlihatkan prompt:

`[E] PICK UP`

Setelah pemain menekan E, objek masuk ke Holding State.

### 3.2 Placement System

Properti hanya dapat diletakkan pada predefined snap points.

Alur:

1. Pemain mengambil properti.
2. Ghost preview mengikuti arah pandangan pemain.
3. Snap point yang tersedia terdeteksi.
4. Pemain menekan E untuk menempatkan properti.
5. Sistem memperbarui `CurrentSlotID`.

Jika posisi tidak valid, properti tidak dapat diletakkan.

Pemain dapat membatalkan perpindahan menggunakan Right Mouse dan mengembalikan objek ke posisi sebelumnya.

### 3.3 Placement Rules

- Satu properti hanya boleh menempati satu slot.
- Satu slot hanya boleh ditempati satu properti.
- Player hanya dapat memegang satu objek.
- Posisi properti menggunakan predefined transforms.
- Collision properti diatur sesuai posisi final.
- Posisi objek tetap tersimpan selama retake.
- Posisi awal dipulihkan hanya ketika level di-reset secara eksplisit.

### 3.4 Lighting Interaction

Standing lamp menggunakan sistem pickup dan placement yang sama.

Setiap snap point menentukan posisi dan rotasi lampu.

Tidak ada kontrol manual untuk intensitas, color temperature, atau rotasi bebas.

Status pencahayaan dihitung berdasarkan slot lampu yang dipilih pemain.

Contoh:

`LampSlot = RevealWall` menghasilkan `bClueLit = true`.

---

## 4. TAKE MANAGEMENT SYSTEM

### 4.1 Gameplay States

Gunakan sebuah enum `E_TakeState`.

| State           | Description                                |
| --------------- | ------------------------------------------ |
| SETUP           | Player bebas menata set                    |
| TAKE_PLAYING    | Cinematic dan performance Maya berlangsung |
| AWKWARD         | Maya mengalami kesulitan saat performance  |
| WAITING_FOR_CUT | Maya menunggu arahan sutradara             |
| CUTTING         | Proses menghentikan take dan reset Maya    |
| PERFECT_TAKE    | Adegan berhasil diselesaikan               |
| POST_TAKE       | Dialog setelah take berhasil               |
| FINALE          | Ending cinematic berlangsung               |
| CREDITS         | Credit scene aktif                         |

### 4.2 ACTION

Saat F ditekan dalam SETUP:

- Periksa apakah player masih memegang properti.
- Jika tidak, mulai pengambilan gambar.
- Simpan snapshot posisi semua properti.
- Evaluasi konfigurasi set.
- Pilih outcome take berdasarkan konfigurasi.
- Nonaktifkan kontrol movement dan interaction.
- Jalankan cinematic sequence.
- Perbarui `TakeCount`.

Evaluasi boleh dilakukan saat ACTION ditekan, tetapi outcome baru diperlihatkan ketika Maya mencapai bagian adegan yang relevan.

Evaluasi bersifat data-driven dan deterministik: slot → flag → outcome. Detail per level di Section 8, schema dan algoritma di Section 11.4.

### 4.3 Awkward Take

Jika konfigurasi set tidak memenuhi persyaratan adegan:

- Maya menjalankan respons kebingungan yang sesuai.
- Maya dapat berhenti, ragu, melihat sekitar, atau mencari arahan.
- Adegan tidak dihentikan otomatis.
- Tidak ada layar BAD TAKE.
- Setelah jeda, sistem memainkan hint monolog Surya (eskalasi: take gagal pertama → hint samar, berikutnya → hint eksplisit; lihat 11.4).
- Maya masuk ke Waiting State sampai pemain menekan CUT.

Contoh internal dialogue:

*"The blocking feels off. I should cut and adjust the set."*

Jika pemain tidak menekan CUT, Maya tetap berada dalam waiting animation.

Setelah beberapa detik, UI boleh memperlihatkan hint ringan:

`[F] CUT`

Hint tidak boleh menghentikan cinematic secara otomatis.

### 4.4 Manual CUT

CUT harus bisa ditekan kapan saja selama TAKE_PLAYING, AWKWARD, atau WAITING_FOR_CUT.

Jika pemain menekan CUT sebelum masalah muncul, sistem tetap menerima input tersebut.

Contoh dialog early CUT:

*"CUT! Hold on, I need to tidy up the scene."*

Jika CUT dilakukan setelah Maya mengalami kesulitan, gunakan dialog sesuai masalahnya.

Contoh:

*"CUT! Let's clear some space and try again."*

Setelah CUT, Maya di-reset dan pemain kembali ke SETUP.

### 4.5 Perfect Take

Perfect Take terjadi ketika seluruh kondisi keberhasilan scene terpenuhi dan sequence sukses telah mencapai akhir.

Sistem kemudian:

1. Memicu dialog CUT otomatis dari Surya.
2. Menghentikan take.
3. Memainkan dialog behind-the-scenes.
4. Menandai scene selesai.
5. Menyimpan progression state.
6. Membuka area atau objective berikutnya.

Manual CUT yang terjadi sebelum sequence sukses selesai membatalkan take tersebut. Scene hanya dianggap complete setelah momen sukses benar-benar ditampilkan.

### 4.6 RETAKE Rules

- Retake tidak dibatasi.
- Take counter terus meningkat.
- Tidak ada lives atau health system.
- Tidak ada Game Over akibat salah penataan.
- Properti tidak otomatis kembali ke posisi awal.
- Maya selalu kembali ke titik awal take.
- Cinematic dimulai kembali dari shot pembuka.
- Dialog intro yang sudah pernah dilihat boleh di-skip pada retake.

---

## 5. MAYA PERFORMANCE SYSTEM

### 5.1 Technical Approach

Maya tidak menggunakan AI decision-making yang kompleks.

Gunakan **Scripted Performance + Conditional Outcomes**.

Setiap level memiliki:

- Start Position.
- Scripted movement path.
- Inspection Point.
- Success Reaction.
- Failure Reactions.
- Waiting Animation.

Untuk MVP, outcome dipilih berdasarkan konfigurasi set. Kemudian sistem memainkan rangkaian gerakan dan animasi Maya yang sesuai.

Pergerakan dapat menggunakan predefined waypoints atau transform animation yang telah dibuat di Sequencer.

### 5.2 Maya States

| State      | Behavior                              |
| ---------- | ------------------------------------- |
| READY      | Menunggu ACTION                       |
| PERFORMING | Menjalankan adegan                    |
| CONFUSED   | Menunjukkan kebingungan               |
| HESITATING | Berhenti dan mencoba memahami situasi |
| WAITING    | Menunggu CUT pemain                   |
| SUCCESS    | Menyelesaikan performance             |
| RESETTING  | Kembali ke posisi awal                |

### 5.3 Reusable Reactions

Untuk mengurangi jumlah animasi, gunakan respons umum yang dapat dipakai ulang:

- Looking Around
- Looking at Director
- Hesitating
- Inspecting Object
- Idle Waiting
- Walking
- Turning
- Reacting / Surprised

Animasi dan voice lines spesifik dapat dipasangkan berdasarkan level dan kondisi kegagalan.

### 5.4 Reset Requirements

Setiap CUT harus menghentikan movement, animasi, dan sequence yang sedang berjalan.

Sistem harus membersihkan state sebelumnya sebelum Maya dipindahkan kembali ke starting position.

Tidak boleh ada animasi, timer, atau event dari take lama yang masih memengaruhi take baru.

### 5.5 Film Crew (Ambient)

Kru adalah karakter latar yang membuat set terasa hidup. Kru **bukan** AI bebas (lihat Non-Goals): tidak ada navigasi, keputusan, atau interaksi dengan player, dan tidak memengaruhi evaluasi take.

**Roster default per scene (4 kru, mannequin sebagai placeholder):**

| Role (`E_CrewRole`) | Pos di set                    | Pose / idle                         |
| ------------------- | ----------------------------- | ----------------------------------- |
| CAMERA              | Di belakang kamera film       | Berdiri, tangan setinggi kepala     |
| BOOM                | Di sisi set, di luar frame    | Kedua tangan terangkat memegang boom |
| GAFFER              | Dekat lampu standing          | Berdiri santai, tangan di pinggang  |
| SCRIPT              | Dekat sutradara               | Memegang catatan di depan dada      |

**Reaksi terhadap `E_TakeState`:**

| Take state                                            | Perilaku kru                              |
| ----------------------------------------------------- | ----------------------------------------- |
| SETUP, POST_TAKE                                      | Relaxed: idle santai                      |
| TAKE_PLAYING, AWKWARD, WAITING_FOR_CUT, PERFECT_TAKE  | Focused: diam, menghadap set, tanpa suara |
| CUTTING                                               | Kembali ke Relaxed                        |
| FINALE, CREDITS                                       | Disembunyikan atau tetap Relaxed (ditentukan per cinematic) |

**Aturan teknis:**

- Kru tidak memiliki state game sendiri. `BP_FilmSceneManager` memanggil `SetCrewFocus(bool)` pada semua kru di scene aktif saat state berubah (atau kru bind ke dispatcher `OnTakeStateChanged`).
- Semua kru memakai **satu Anim Blueprint bersama** (`ABP_Crew`). Role dipilih lewat variabel, bukan ABP terpisah.
- Optimasi animasi: Update Rate Optimization (URO) aktif, `VisibilityBasedAnimTickOption = OnlyTickPoseWhenRendered`, multi-threaded animation update, tanpa physics/collision kompleks.
- Kru tidak boleh menghalangi jalur Maya atau slot prop.

---

## 6. CINEMATIC CAMERA SYSTEM

### 6.1 Camera Architecture

Gunakan:

- Unreal Level Sequencer.
- Cine Camera Actors.
- Camera Cut Track.
- Level Sequence Player.

Semua shot kamera dibuat oleh developer.

Pemain tidak dapat menentukan posisi kamera atau urutan shot pada MVP.

### 6.2 Shot Structure

Tiap level menggunakan cinematic dengan pola:

1. Opening Shot.
2. Movement / Blocking Shot.
3. Inspection Shot.
4. Conditional Outcome Shot.

Opening Shot dapat digunakan ulang oleh beberapa outcome.

### 6.3 Cinematic Branching

Gunakan satu shared opening sequence dan beberapa outcome sequence.

Contoh untuk Level 1:

- `LS_L01_Opening`
- `LS_L01_Blocked`
- `LS_L01_MissedClue`
- `LS_L01_Perfect`

Ketika opening selesai, Scene Manager memainkan outcome sequence yang telah dipilih.

Jika pemain menekan CUT di tengah sequence, playback langsung dihentikan dan tidak boleh memicu event kesuksesan.

### 6.4 Camera Restoration

Sebelum ACTION, simpan view target dan player setup transform yang diperlukan.

Setelah CUT:

- Stop active sequence.
- Restore first-person camera.
- Restore movement input.
- Restore interaction input.
- Reset Maya.
- Enter SETUP.

Setelah Perfect Take, dialog pascatake dijalankan sebelum progression berikutnya dibuka.

---

## 7. DIALOGUE SYSTEM

### 7.1 Dialogue Categories

| Type             | Function                                   |
| ---------------- | ------------------------------------------ |
| IN_FILM          | Dialog karakter Laras yang diperankan Maya |
| BEHIND_SCENES    | Percakapan Maya, Surya, dan kru            |
| INTERNAL_HINT    | Petunjuk berupa monolog Surya              |
| CUT_DIALOGUE     | Respons Surya saat menghentikan adegan     |
| SUCCESS_DIALOGUE | Dialog setelah Perfect Take                |
| ENDING_DIALOGUE  | Dialog final cinematic                     |

### 7.2 Requirements

- Dialog dikendalikan oleh Scene Manager atau Dialogue Manager.
- Mendukung voice audio dan subtitle.
- Setiap dialog memiliki ID unik.
- Subtitle menampilkan speaker name sesuai konteks.
- Dialog tidak boleh saling tumpang tindih tanpa disengaja.
- CUT menghentikan dialog IN_FILM yang sedang berjalan.
- Dialog hint tidak diputar berulang kali secara terus-menerus.
- Semua dialog Surya pada Level 1–3 tetap profesional dan tidak membocorkan identitasnya sebelum ending.

### 7.3 Dialogue Data

Gunakan Data Table atau Data Asset sederhana dengan field:

- DialogueID
- Speaker
- SubtitleText
- VoiceSound
- DialogueCategory
- SceneID

Untuk prototype, sistem juga harus dapat bekerja menggunakan subtitle tanpa voice recording final.

---

## 8. LEVEL REQUIREMENTS

### LEVEL 1 — THE ARRIVAL

**Area:** Living Room
**Gameplay Focus:** Blocking dan visibility
**Interactive Props:** Sofa, Wardrobe

**Director Objective:** Siapkan adegan Laras memasuki rumah dan menyadari kejanggalan dinding.

#### Required Conditions

- `bPathClear`
- `bWallVisible`

#### Conditional Outcomes

| Condition                 | Maya Behavior             | Outcome      |
| ------------------------- | ------------------------- | ------------ |
| Path blocked              | Berhenti dan kebingungan  | Awkward Take |
| Wall hidden               | Mencari fokus adegan      | Awkward Take |
| Path clear + wall visible | Memperhatikan kejanggalan | Perfect Take |

#### Blocking

Maya masuk dari pintu depan → berjalan ke Inspection Point di tengah ruangan → menoleh ke dinding janggal.

#### Slot Table

| SlotID      | Prop     | Posisi                                  | Efek                                   | Start |
| ----------- | -------- | --------------------------------------- | -------------------------------------- | ----- |
| SOFA_Entry  | Sofa     | Tengah jalur dari pintu masuk           | Path blocked                           | Yes   |
| SOFA_Window | Sofa     | Bawah jendela                           | —                                      |       |
| SOFA_TV     | Sofa     | Menghadap TV, sisi kanan ruangan        | —                                      |       |
| WARD_Wall   | Wardrobe | Menempel di depan dinding janggal       | Wall hidden                            | Yes   |
| WARD_Corner | Wardrobe | Sudut kiri belakang                     | —                                      |       |
| WARD_Entry  | Wardrobe | Samping pintu masuk, memakan jalur      | Path blocked (decoy: dinding terlihat) |       |

#### Flag Rules

| Flag           | RuleType  | Placements                                    |
| -------------- | --------- | --------------------------------------------- |
| `bPathClear`   | ForbidAny | `Sofa@SOFA_Entry`, `Wardrobe@WARD_Entry`      |
| `bWallVisible` | ForbidAny | `Wardrobe@WARD_Wall`                          |

#### Outcome Rules (urutan = priority)

| #   | OutcomeID   | TriggerIfAnyFalse | Sequence            | Maya Reaction                    | Hint 1 (samar)                        | Hint 2 (eksplisit)                                                   |
| --- | ----------- | ----------------- | ------------------- | -------------------------------- | ------------------------------------- | -------------------------------------------------------------------- |
| 1   | BLOCKED     | `bPathClear`      | `LS_L01_Blocked`    | Hesitating → Looking at Director | *"She can't even get through the room."* | *"Something's in her way. I need to clear the path from the door."* |
| 2   | MISSED_CLUE | `bWallVisible`    | `LS_L01_MissedClue` | Looking Around                   | *"She has nothing to react to."*      | *"The wall is the whole point of this scene. It has to be seen."*   |
| 3   | PERFECT     | —                 | `LS_L01_Perfect`    | Inspecting Object                | —                                     | —                                                                    |

#### Start & Solution

- Start: `Sofa@SOFA_Entry`, `Wardrobe@WARD_Wall`. Kedua flag gagal → take pertama pasti BLOCKED (tutorial CUT).
- Solusi valid: `Sofa@SOFA_Window` atau `Sofa@SOFA_TV`, + `Wardrobe@WARD_Corner`.
- Total kombinasi: 9. Solusi: 2.

#### Success Event

- Mainkan automatic CUT.
- Putar dialog success Level 1.
- Tandai Level 1 Complete.
- Buka akses menuju koridor dan dapur.

### LEVEL 2 — THE HOLLOW WALL

**Area:** Kitchen & Corridor
**Gameplay Focus:** Visibility dan lighting
**Interactive Props:** Small Cabinet, Standing Lamp

**Director Objective:** Siapkan adegan Laras menemukan bekas pintu yang tersembunyi.

#### Required Conditions

- `bPathClear`
- `bDoorVisible`
- `bClueLit`

#### Conditional Outcomes

| Condition              | Maya Behavior                               | Outcome      |
| ---------------------- | ------------------------------------------- | ------------ |
| Path / clue obstructed | Kesulitan menemukan area yang harus diamati | Awkward Take |
| Lighting incorrect     | Tidak dapat melihat detail dinding          | Awkward Take |
| All valid              | Menemukan bekas pintu                       | Perfect Take |

#### Blocking

Maya berjalan dari ujung koridor → masuk area dapur → berhenti di depan hollow wall → meraba bekas kusen pintu.

#### Slot Table

| SlotID              | Prop          | Posisi                                       | Efek                                  | Start |
| ------------------- | ------------- | -------------------------------------------- | ------------------------------------- | ----- |
| CAB_Corridor        | Small Cabinet | Tengah koridor                               | Path blocked                          | Yes   |
| CAB_HollowWall      | Small Cabinet | Menempel di bekas pintu                      | Door hidden                           |       |
| CAB_Kitchen         | Small Cabinet | Samping kulkas                               | —                                     |       |
| LAMP_Kitchen        | Standing Lamp | Pojok dapur, jauh dari dinding               | — (dinding gelap)                     | Yes   |
| LAMP_CorridorCenter | Standing Lamp | Tengah koridor, menyorot dinding             | Clue lit + Path blocked (trap)        |       |
| LAMP_RevealWall     | Standing Lamp | Diagonal depan dinding, cahaya grazing angle | Clue lit                              |       |

#### Flag Rules

| Flag           | RuleType   | Placements                                                         |
| -------------- | ---------- | ------------------------------------------------------------------ |
| `bPathClear`   | ForbidAny  | `SmallCabinet@CAB_Corridor`, `StandingLamp@LAMP_CorridorCenter`   |
| `bDoorVisible` | ForbidAny  | `SmallCabinet@CAB_HollowWall`                                      |
| `bClueLit`     | RequireAny | `StandingLamp@LAMP_RevealWall`, `StandingLamp@LAMP_CorridorCenter` |

#### Outcome Rules (urutan = priority)

| #   | OutcomeID  | TriggerIfAnyFalse              | Sequence             | Maya Reaction                     | Hint 1 (samar)                                   | Hint 2 (eksplisit)                                                |
| --- | ---------- | ------------------------------ | -------------------- | --------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------- |
| 1   | OBSTRUCTED | `bPathClear`, `bDoorVisible`   | `LS_L02_Obstructed`  | Looking Around → Looking at Director | *"She's looking for something she can't reach."* | *"Clear the corridor, and keep the old doorway uncovered."*       |
| 2   | DARK       | `bClueLit`                     | `LS_L02_Dark`        | Inspecting Object (meraba dinding) | *"She can't see what she's supposed to find."*   | *"The wall needs light. The lamp has to face it directly."*      |
| 3   | PERFECT    | —                              | `LS_L02_Perfect`     | Reacting / Surprised              | —                                                | —                                                                 |

#### Start & Solution

- Start: `SmallCabinet@CAB_Corridor`, `StandingLamp@LAMP_Kitchen` → OBSTRUCTED.
- Trap: `StandingLamp@LAMP_CorridorCenter` menerangi dinding tapi menutup jalur → tetap OBSTRUCTED. Mengajarkan bahwa satu prop bisa memengaruhi dua kondisi.
- Solusi: `SmallCabinet@CAB_Kitchen` + `StandingLamp@LAMP_RevealWall`.
- Total kombinasi: 9. Solusi: 1.

#### Success Event

- Mainkan automatic CUT.
- Putar dialog success Level 2.
- Mainkan dialog Maya tentang suara misterius.
- Tandai Level 2 Complete.
- Buka akses menuju secret room.

### LEVEL 3 — THE FINAL TAKE

**Area:** Secret Room
**Gameplay Focus:** Reconstruction dan kombinasi kondisi
**Interactive Props:** Chair, Photo Table, Standing Lamp

**Director Objective:** Rekonstruksi ruangan sesuai foto referensi untuk adegan pengungkapan terakhir.

#### Required Conditions

- `bChairCorrect`
- `bPhotoVisible`
- `bLightingCorrect`

#### Conditional Outcomes

| Condition                  | Maya Behavior                               | Outcome      |
| -------------------------- | ------------------------------------------- | ------------ |
| Reconstruction incorrect   | Tidak dapat mencocokkan ruangan dengan foto | Awkward Take |
| Photo / lighting incorrect | Kesulitan mengenali bukti                   | Awkward Take |
| All valid                  | Mengenali hubungan ruangan dan foto         | Perfect Take |

#### Reference Photo

- Foto lama ruangan ditampilkan di `WBP_DirectorNotes` (Tab) melalui field `ReferenceImage` pada `DA_SceneConfig_L03`.
- Opsional: prop foto statis di meja naskah dekat pintu secret room, prompt `[E] VIEW PHOTO` membuka Director's Notes langsung ke halaman foto.
- Isi foto (harus terbaca jelas tanpa teks): kursi di tengah ruangan menghadap pintu, meja foto menempel dinding kanan, cahaya datang dari kiri (bayangan jatuh ke kanan).
- Hint Level 3 selalu mengarahkan pemain kembali ke foto.

#### Blocking

Maya masuk dari pintu secret room → berhenti di ambang pintu membandingkan ruangan dengan foto → berjalan ke meja foto → mengambil/menatap foto bukti.

#### Slot Table

| SlotID       | Prop          | Posisi                                     | Efek                                 | Start |
| ------------ | ------------- | ------------------------------------------ | ------------------------------------ | ----- |
| CHAIR_Corner | Chair         | Sudut, menghadap dinding                   | —                                    | Yes   |
| CHAIR_Center | Chair         | Tengah ruangan, menghadap pintu            | Sesuai foto                          |       |
| CHAIR_Door   | Chair         | Dekat pintu                                | —                                    |       |
| TABLE_Shadow | Photo Table   | Belakang rak, area gelap                   | —                                    | Yes   |
| TABLE_Wall   | Photo Table   | Menempel dinding kanan                     | Sesuai foto                          |       |
| TABLE_Door   | Photo Table   | Samping pintu                              | — (decoy: terlihat, tapi beda foto)  |       |
| LAMP_Entry   | Standing Lamp | Dekat pintu, cahaya dari depan             | —                                    | Yes   |
| LAMP_Left    | Standing Lamp | Kiri meja, bayangan sesuai foto            | Sesuai foto                          |       |
| LAMP_Right   | Standing Lamp | Kanan meja, bayangan terbalik              | —                                    |       |

#### Flag Rules

| Flag               | RuleType   | Placements                  |
| ------------------ | ---------- | --------------------------- |
| `bChairCorrect`    | RequireAll | `Chair@CHAIR_Center`        |
| `bPhotoVisible`    | RequireAll | `PhotoTable@TABLE_Wall`     |
| `bLightingCorrect` | RequireAll | `StandingLamp@LAMP_Left`    |

#### Outcome Rules (urutan = priority)

| #   | OutcomeID | TriggerIfAnyFalse                       | Sequence           | Maya Reaction                       | Hint 1 (samar)                           | Hint 2 (eksplisit)                                                       |
| --- | --------- | --------------------------------------- | ------------------ | ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| 1   | MISMATCH  | `bChairCorrect`                         | `LS_L03_Mismatch`  | Looking Around (membandingkan foto) | *"This isn't the room in the photo."*    | *"Start with the chair. It's the first thing anyone would notice."*     |
| 2   | EVIDENCE  | `bPhotoVisible`, `bLightingCorrect`     | `LS_L03_Evidence`  | Hesitating → Looking at Director    | *"She can't find the evidence."*         | *"Match the table and the light to the reference. Light from the left."* |
| 3   | PERFECT   | —                                       | `LS_L03_Perfect`   | Inspecting Object → Reacting        | —                                        | —                                                                        |

#### Start & Solution

- Start: `Chair@CHAIR_Corner`, `PhotoTable@TABLE_Shadow`, `StandingLamp@LAMP_Entry` → MISMATCH.
- Solusi: `Chair@CHAIR_Center` + `PhotoTable@TABLE_Wall` + `StandingLamp@LAMP_Left`.
- Total kombinasi: 27. Solusi: 1.

#### Success Event

- Mainkan automatic CUT.
- Putar dialog success Level 3.
- Munculkan objective `CALL EVERYONE TO SET`.
- Aktifkan interkom.
- Tunggu interaksi pemain.

Ketika interkom digunakan:

- Nonaktifkan interaksi gameplay.
- Mulai ending cinematic.
- Ungkap identitas Surya sebagai pembunuh.
- Setelah cinematic selesai, mainkan final movie dan credits.

---

## 9. NARRATIVE PROGRESSION SYSTEM

### 9.1 Level Progression

Gunakan satu persistent house map untuk ketiga level.

Level disusun dalam area terpisah:

- Living Room
- Kitchen & Corridor
- Secret Room

Akses antarruang dikontrol oleh Scene Manager menggunakan progression flags.

### 9.2 Progression Variables

- `CurrentSceneID`
- `CurrentTakeCount`
- `bLevel1Complete`
- `bLevel2Complete`
- `bLevel3Complete`
- `bEndingTriggered`

### 9.3 Story Restrictions

- Pemain tidak dapat mengakses secret room sebelum Level 2 selesai.
- Story-critical events hanya dipicu setelah Perfect Take.
- Ending hanya dapat dipicu setelah Level 3 selesai dan interkom diaktifkan.
- Surya tidak mengungkap identitasnya sebelum final cinematic.
- Setelah ending dimulai, gameplay tidak kembali ke Setup Mode.

---

## 10. ENDING & CREDITS SYSTEM

### 10.1 Ending Cinematic

Gunakan Level Sequence terpisah untuk ending.

Ending dapat menggunakan kamera third-person sinematik untuk pertama kalinya memperlihatkan karakter Surya secara penuh.

Jika gameplay hanya menggunakan first-person arms, gunakan cinematic character actor tersendiri untuk menampilkan tubuh dan wajah Surya pada ending.

### 10.2 Final Movie

Setelah ending, mainkan montage singkat yang menggabungkan shot-shot terpilih dari Level 1, 2, dan 3.

Tidak diperlukan sistem gameplay recording.

Gunakan Sequencer dengan cinematic shots yang telah dibuat sebelumnya.

### 10.3 Credits

Credits dibuat menggunakan UMG Widget.

Requirements:

- Teks credits dapat di-scroll otomatis.
- Nama karakter dan tim produksi dapat ditampilkan.
- Background dan audio sederhana.
- Setelah credits, tampilkan post-credits sting bila tersedia.
- Kemudian kembali ke Main Menu.

---

## 11. UNREAL BLUEPRINT ARCHITECTURE

### 11.1 Required Blueprint Classes

| Blueprint / Asset      | Responsibility                                       |
| ---------------------- | ---------------------------------------------------- |
| `BP_DirectorCharacter` | First-person movement dan input interaksi            |
| `BP_FilmSceneManager`  | Scene state, take lifecycle, evaluation, progression |
| `BP_InteractableProp`  | Pickup, placement, `PropID`, `SceneID`, `StartSlotID`, `CurrentSlotID` |
| `BP_PropSlot`          | Snap transform, `SlotID`, `SceneID`, `AllowedPropID`, occupancy |
| `BP_Maya`              | Maya actor reference dan animation state             |
| `BP_CrewMember`        | Kru ambient: `Role`, `SetCrewFocus` (Section 5.5)    |
| `ABP_Crew`             | Anim Blueprint bersama untuk semua kru               |
| `E_CrewRole`           | CAMERA / BOOM / GAFFER / SCRIPT                      |
| `BP_Intercom`          | Final objective trigger                              |
| `WBP_GameHUD`          | Interaction prompts, subtitles, objective            |
| `WBP_DirectorNotes`    | Scene instructions                                   |
| `WBP_MainMenu`         | Main menu                                            |
| `WBP_Credits`          | Credit screen                                        |
| `E_TakeState`          | Gameplay state enum                                  |
| `E_FlagRuleType`       | RequireAll / RequireAny / ForbidAny                  |
| `E_MayaReaction`       | Reusable reactions (Section 5.3)                     |
| `F_Placement`          | Pasangan PropID + SlotID                             |
| `F_FlagRule`           | Aturan slot → flag                                   |
| `F_OutcomeRule`        | Aturan flag → outcome, sequence, hint                |
| `F_SceneLevelRefs`     | Referensi actor di level per scene                   |
| `PDA_SceneConfig`      | Primary Data Asset class untuk config scene          |
| `DA_SceneConfig_L01–03`| Instance data per level                              |

### 11.2 Primary Event Flow

**Interaction**

`Interact Input → Trace → Interactable Prop → Pickup / Placement → Update Slot State`

**ACTION**

`Action Input → Scene Manager → Evaluate Setup → Select Outcome → Play Cinematic`

**Awkward Take**

`Outcome Sequence → Maya Confusion → Internal Hint → Waiting for CUT`

**Manual CUT**

`Cut Input → Stop Sequence → Reset Maya → Restore Camera → Setup State`

**Perfect Take**

`Perfect Sequence Finished → Automatic CUT → Success Dialogue → Progression`

**Finale**

`Level 3 Complete → Intercom Interaction → Ending Sequence → Final Movie → Credits`

### 11.3 Technical Constraints

- Scene Manager merupakan single source of truth untuk game state.
- Hanya satu take sequence yang boleh aktif pada waktu yang sama.
- Semua take harus memiliki reset behavior yang konsisten.
- Jangan menggunakan Tick untuk mengevaluasi seluruh objective secara terus-menerus.
- Evaluasi setup dilakukan ketika ACTION dimulai atau ketika ada perubahan prop yang relevan.
- Semua timing hint dan dialog harus dapat dibatalkan ketika pemain menekan CUT.
- Keberhasilan diproses satu kali, meskipun event cinematic terpanggil lebih dari sekali.

### 11.4 Scene Config Data Schema

`E_TakeOutcome` dari v0.1 dihapus. Outcome kini didefinisikan per scene sebagai `OutcomeID` (Name) di dalam `DA_SceneConfig`, sehingga Level 1–3 memakai satu fungsi evaluasi yang sama.

#### Enum & Struct

```
E_FlagRuleType
  RequireAll    // true jika SEMUA placement cocok
  RequireAny    // true jika MINIMAL SATU placement cocok
  ForbidAny     // true jika TIDAK ADA placement yang cocok

F_Placement
  PropID              : Name
  SlotID              : Name

F_FlagRule
  FlagName            : Name
  RuleType            : E_FlagRuleType
  Placements          : Array<F_Placement>

F_OutcomeRule
  OutcomeID           : Name
  bIsPerfect          : Bool
  TriggerIfAnyFalse   : Array<Name>              // outcome terpilih jika salah satu flag ini false
  OutcomeSequence     : Soft Object Ref <LevelSequence>
  MayaReaction        : E_MayaReaction
  HintDialogueIDs     : Array<Name>              // [0] samar, [1] eksplisit
  CutDialogueID       : Name

F_SceneLevelRefs                                  // di-set pada instance BP_FilmSceneManager di level
  MayaStartPoint      : Actor
  GateActor           : Actor                    // pintu/area yang dibuka setelah scene complete
  ExtraActors         : Array<Actor>             // contoh: BP_Intercom untuk L03

PDA_SceneConfig (Primary Data Asset)
  SceneID             : Name                     // L01 / L02 / L03
  DisplayName         : Text
  ObjectiveText       : Text
  DirectorNotesText   : Text
  ReferenceImage      : Texture2D                // opsional, dipakai L03
  OpeningSequence     : Soft Object Ref <LevelSequence>
  IntroDialogueIDs    : Array<Name>
  EarlyCutDialogueID  : Name
  SuccessDialogueIDs  : Array<Name>
  FlagRules           : Array<F_FlagRule>
  OutcomeRules        : Array<F_OutcomeRule>     // urutan array = priority, PERFECT di akhir
  NextSceneID         : Name
```

Data Asset tidak dapat mereferensikan actor di level. Karena itu referensi actor disimpan di `BP_FilmSceneManager` sebagai `Map<Name, F_SceneLevelRefs>` (key = SceneID).

#### Algoritma Evaluasi

Dijalankan sekali saat ACTION, setelah snapshot prop.

```
BuildPlacementMap():
  PlacementMap = {}
  for Prop in all BP_InteractableProp where Prop.SceneID == CurrentSceneID:
      PlacementMap[Prop.PropID] = Prop.CurrentSlotID

EvaluateRule(Rule) -> Bool:
  Matches = count p in Rule.Placements where PlacementMap[p.PropID] == p.SlotID
  RequireAll → Matches == Rule.Placements.Length
  RequireAny → Matches > 0
  ForbidAny  → Matches == 0

EvaluateFlags() -> Map<Name, Bool>:
  Flags = {}
  for Rule in Config.FlagRules:
      Prev = Flags.Contains(Rule.FlagName) ? Flags[Rule.FlagName] : true
      Flags[Rule.FlagName] = Prev AND EvaluateRule(Rule)    // beberapa rule untuk flag sama → AND
  return Flags

SelectOutcome(Flags) -> F_OutcomeRule:
  for Rule in Config.OutcomeRules:                           // urutan = priority
      if Rule.bIsPerfect: return Rule
      for F in Rule.TriggerIfAnyFalse:
          if Flags[F] == false: return Rule
```

#### Hint Escalation

- Scene Manager menyimpan `FailCountByOutcome : Map<Name, Int>` untuk scene aktif.
- Counter bertambah ketika outcome non-perfect mencapai fase hint.
- Index hint = `Min(FailCount - 1, HintDialogueIDs.Length - 1)`.
- Hint hanya diputar satu kali per take.
- Counter di-reset saat scene complete.

#### Validation Checklist (per DA)

- [ ] Setiap `PropID` unik dalam satu scene dan memiliki tepat satu `StartSlotID`. Standing Lamp L02 dan L03 adalah dua actor terpisah dengan `SceneID` berbeda.
- [ ] Setiap `SlotID` unik secara global.
- [ ] `OutcomeRules` memiliki tepat satu `bIsPerfect = true` di posisi terakhir.
- [ ] Semua flag di `TriggerIfAnyFalse` didefinisikan di `FlagRules`.
- [ ] Konfigurasi start bukan solusi.
- [ ] Minimal satu kombinasi solusi tercapai.
- [ ] Semua kombinasi slot sudah diuji: tidak ada yang menutup jalur player (softlock).
- [ ] Development build mencetak `Flags` dan `OutcomeID` di setiap ACTION untuk debugging.

---

## 12. UI / UX REQUIREMENTS

UI gameplay harus minimal.

### Setup Mode

Tampilkan:

- Crosshair.
- Interaction Prompt.
- Current Objective.
- Director's Notes melalui Tab.
- ACTION prompt saat siap.

### Take Mode

Tampilkan:

- Subtitle dialog.
- CUT hint bila diperlukan.

Sembunyikan:

- Interaction Prompt.
- Crosshair.
- Director's Notes.

### Awkward Take

- Jangan menampilkan BAD TAKE.
- Jangan menampilkan Game Over.
- Perlihatkan ekspresi dan gerakan Maya.
- Putar internal hint Surya.
- Tampilkan prompt CUT hanya setelah diperlukan.

### Perfect Take

- Automatic CUT.
- Dialog keberhasilan.
- Optional small text `SCENE COMPLETE`.
- Progression ke area berikutnya.

---

## 13. MVP ACCEPTANCE CRITERIA

Sebuah build dianggap memenuhi kebutuhan MVP jika:

- [ ] Pemain dapat memulai game dari Main Menu.
- [ ] Pemain dapat bergerak dan berinteraksi dalam first-person.
- [ ] Properti bisa dipindahkan ke predefined snap points.
- [ ] Prop placement memengaruhi hasil take.
- [ ] Pemain dapat memulai ACTION.
- [ ] Cinematic menggunakan perpindahan shot yang telah ditentukan.
- [ ] Maya menjalankan respons berbeda berdasarkan kondisi set.
- [ ] Maya dapat masuk ke Awkward / Waiting State.
- [ ] Pemain dapat menekan CUT kapan saja selama take berlangsung.
- [ ] Manual CUT tidak memunculkan layar kegagalan.
- [ ] Maya kembali ke starting position setelah CUT.
- [ ] Properti mempertahankan posisi setelah RETAKE.
- [ ] Perfect Take memicu automatic CUT.
- [ ] Ketiga level dapat diselesaikan berurutan.
- [ ] Ending cinematic berjalan setelah interkom diaktifkan.
- [ ] Credits dapat dimainkan sampai selesai.
- [ ] Game dapat kembali ke Main Menu.
- [ ] Tidak ada softlock saat repeated CUT / RETAKE.

---

## 14. TECHNICAL RISKS

| Risk                                                  | Severity | Mitigation                                            |
| ----------------------------------------------------- | -------- | ----------------------------------------------------- |
| Sequencer tidak berhenti bersih saat CUT              | High     | Satu pengelola sequence, explicit stop & reset        |
| Maya tidak kembali ke starting position               | High     | Centralized ResetTake function                        |
| Shot sinematik tidak sinkron dengan actor performance | High     | Authored sequence segments dan fixed blocking         |
| Outcome tak sesuai kondisi prop                       | High     | Slot-based deterministic evaluation                   |
| CUT menimbulkan event lama yang masih berjalan        | High     | Cancel timer, dialogue, dan pending sequence callback |
| Terlalu banyak cinematic assets                       | Medium   | Reuse opening dan shared camera setups                |
| Terlalu banyak dialog                                 | Medium   | Prioritaskan subtitle serta voice lines penting       |
| Player tidak mengerti alasan take bermasalah          | Medium   | Gestur Maya + hint Surya yang spesifik                |

---

## 15. DEVELOPMENT PLAN — 4 DAYS

### Day 1 — Core Interaction

- First Person Template.
- BP_InteractableProp.
- Snap Placement.
- Basic HUD.
- Scene Manager prototype.
- Level 1 blockout.

**Deliverable:** Player dapat memindahkan properti, memulai ACTION, dan menghasilkan outcome berbeda.

### Day 2 — Take & Cinematic System

- Cinematic camera switching.
- Maya scripted performance.
- Manual CUT.
- Early CUT behavior.
- Awkward Take.
- Automatic CUT untuk success.
- Dialogue & subtitle events.

**Deliverable:** Level 1 playable dengan loop lengkap.

### Day 3 — Content & Progression

- Implementasi Level 2.
- Implementasi Level 3.
- Scene gating.
- Objective progression.
- Level dialogue dan cinematic outcome.

**Deliverable:** Ketiga level dapat dimainkan hingga final objective.

### Day 4 — Ending & Build

- Ending cinematic.
- Final movie montage.
- Credits.
- Audio integration.
- Gameplay testing.
- Bug fixing.
- Windows packaged build.

**Deliverable:** Playable game dari Start sampai Credits.

---

## 16. OPEN DESIGN DECISIONS

Bagian berikut belum dikunci dan perlu ditinjau sebelum implementasi penuh.

**D-01 — Interaction Method**
Apakah pickup dan snap placement sudah cukup menyenangkan, atau diperlukan perubahan UX agar pemain lebih merasa sedang melakukan set dressing?

**D-02 — Player Position During ACTION**
Apakah kamera langsung berpindah ke full-screen cinematic, atau gameplay ditampilkan melalui monitor sutradara terlebih dahulu?

**D-03 — CUT Presentation**
Apakah setiap CUT langsung menghentikan playback, atau menggunakan jeda singkat dengan audio CUT sebelum kembali ke first-person?

**D-04 — Maya Movement**
Apakah seluruh movement dikeyframe melalui Sequencer, atau sebagian menggunakan movement Blueprint berbasis waypoint?

**D-05 — Director Dialogue**
Apakah Surya menggunakan full voice acting, subtitle-only, atau kombinasi keduanya?

**D-06 — Progress Persistence**
Apakah build game jam cukup mendukung satu playthrough, atau perlu Save/Continue ketika pemain keluar dari game?

---

## 17. CHANGELOG

**v0.2**

- Tambah Blocking, Slot Table, Flag Rules, Outcome Rules, Start & Solution untuk Level 1–3.
- Tambah spesifikasi Reference Photo Level 3.
- Hapus `E_TakeOutcome`; ganti dengan outcome per scene berbasis data (Section 11.4).
- Tambah schema `PDA_SceneConfig`, struct pendukung, algoritma evaluasi, hint escalation, validation checklist.
- Tambah Section 5.5 Film Crew (ambient, reaksi ke take state, satu ABP bersama).

---

**Document Status:** DRAFT v0.2 — Awaiting Design Review

**Core principle:** Player changes the set. Maya performs the consequences. The director decides when to CUT, except when the perfect take is complete.
