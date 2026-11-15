# SB_GrayBox subtitle, CUT and L02 spotlight QA

Tested in Unreal Editor 5.6 PIE on `SB_GrayBox`. Editor remained open; PIE was stopped after testing. The scenario driver completed the arrival handoff event, moved the PIE pawn to the director marks, and moved puzzle props in PIE only. It accelerated game time to 3× after the intro. Evidence: `Saved/QA/FeedbackInvestigation/current/monitor.json` and `fail_fixed.png`.

| Scenario | Result |
| --- | --- |
| Arrival handoff | `WBP_Scene01Objective` left the viewport and `FilmSceneManager.bIntroDone` became true. |
| L01 BLOCKED | Intro and failure subtitles appeared. `[F] CUT` became visible in the same sampled state transition as `WAITING_FOR_CUT`; hint dialogue followed. |
| L01 PERFECT | Four performance lines, eight success lines, five interlude lines and scene advance to L02 were observed. `SCENE COMPLETE` appeared during post-take. |
| L02 OBSTRUCTED | Performance, failure and hint subtitles appeared; CUT prompt appeared at `WAITING_FOR_CUT`. |
| L02 DARK | Performance, failure and hint subtitles appeared; CUT prompt appeared at `WAITING_FOR_CUT`. |
| L02 PERFECT | The spotlight followed its puzzle actor to the reveal area. Four performance lines, twelve success lines, `TO BE CONTINUED`, credits and main-menu transition were observed. |

The revised subtitle box has fixed viewport width and the CUT prompt sits below it in the lower cinematic band. The gameplay subtitle rule still hides that band when the view target is the player. No Blueprint runtime errors were found in the editor log for this PIE run. The QA monitor itself stopped with `StopIteration` when PIE changed from `SB_GrayBox` to `L_MainMenu`; that exception is in the test harness, after the in-game credits state.

Follow-up visual QA: the spotlight actor had been authored with positional `Rotator` arguments, which produced a straight-up world forward vector. Its saved forward vector is now approximately `(0, 0.978, -0.208)`, aimed at the old doorway and slightly downward. `Saved/QA/FeedbackInvestigation/current/spot_forward_tuned.png` shows the beam on the wall. The HUD `LineText` and `SpeakerText` now fill the width of `SubtitleBox`, and `LineText` wraps at the available width. `Saved/QA/FeedbackInvestigation/current/hint_width_after.png` shows the director-mark hint on one line in gameplay.
