# Document subtitles

Current runtime flow is documented in ArrivalFlow.md.
Opening: four English Maya lines from page 3, at the existing 30-second editorial timings.
Arrival: three crew lines start only after mandatory tutorial and entering the living room.
Maya approaches next, then her six lines play. Both conversations clear afterward.
Speaker labels, wrapping and a dark shadow improve readability. No VO was provided.

DialogueCatalog.en.json is the source-page-indexed production reference. It is not an autoplay
list; later scenes and failed takes require their own gameplay-state triggers.
Scene01SubtitleGraph.json is a HISTORICAL authoring receipt for the superseded auto-start
prototype; do not replay it. The current asset has explicit StartCrewDialogue and
StartMayaDialogue events, plus SetHint, ToggleNotes and SetDirectorNotes functions.
