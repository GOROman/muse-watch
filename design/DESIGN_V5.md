# Muse Watch v5 — design spec (decided 2026-11-18 by user)

Concept image: `design/concept_retro_v2.webp` (retro direction, revised)

## Look
- Retro-futuristic cradle like the concept: chunky ivory body, rounded edges,
  horizontal ribbed band around the lower body, ribbed backrest, ONE orange
  accent disc on the right side face.
- Pendant stands UPRIGHT, leaning slightly back against the backrest.
- Screen shows the Muse avatar (Muse Charm reference) — this is a display
  content note, not geometry; the model just must not cover the screen.

## User's explicit decisions
- Direction 2 (retro) chosen. Bottom/dangling cord loop in the first image:
  NOT needed — cord only goes UP from the pendant top; when docked it rises
  out of the dock (backrest top has a shallow center cord channel).
- The Pixel Watch 4 CROWN IS USED: it must stay exposed and operable both
  while worn (v3 side-module plunger already does this) and while docked —
  the dock's right side must have clearance around the crown (crown sits on
  the pendant's +X edge, mid height; in the concept it peeks at upper right).

## Mechanism (from Codex/Astra run, codex-out/)
- Upright side-contact docking: puck vertical inside the dock's left inner
  wall, face toward +X; pendant drops in upright, magnet pulls it 2.5 mm left.
- Reuse Codex geometry where sound: shell/liner cut left_cut_x=-17
  (codex-out/out/pendant_shell_codex.stl, pendant_liner_codex.stl),
  puck pocket 41.8 x 27.8 (+0.4/side), depth 7, parameters.json has the rest.
- KNOWN UNVERIFIED (carry over): puck contact-center Y offset on the real
  unit, slide-mate blind mating, shell retention with the -17 cut.
  puck_fit_test_codex.stl must be printed and tested before the full dock.

## v5 dock requirements
- Ivory retro body approx 92 x 64 footprint, chunky rounded (radius >= 6 corners),
  ribbed band (3 grooves) on the lower body, backrest behind the slot with
  vertical rib grooves and a top-center cord channel (14 wide x 8 deep).
- Slot: pendant lower arc cradled; lean-back angle ~8 deg; puck housing tilted
  to match so the puck face stays parallel to the watch's left edge plane.
- Crown clearance: no dock material within 6 mm of the crown envelope on +X.
- Orange accent: separate small disc STL (r 9, thickness 3) for the right face.
- Cable: from puck bottom, channel under the base, exits at the back.
- All meshes watertight; verify dock x docked-pendant interference ~ 0.
- Print orientation: base down, no supports target.

## Display content (user, 2026-11-18)
- Final concept: design/concept_final.webp (official Muse character, full body, black screen) + design/muse_charm_official.jpg
- When the watch shows the Muse official character/avatar, the watch-face
  background is BLACK (OLED black, avatar glowing in the center).

## CORRECTION (user photo, 2026-11-18 16:24) — charging orientation
- Real charging photo: design/charging_orientation.jpg. The puck lies FLAT
  (horizontal, as Google designed) and the watch stands with its left edge
  seated in the puck groove and the CROWN POINTING UP. Charging confirmed
  on screen (0%).
- Therefore the v5 mechanism is the Muse v4 orientation, NOT the Codex
  vertical-puck upright scheme: pendant rotated 90 deg CCW in its plane,
  crown up, tower + cord to the LEFT, puck horizontal in a saddle below.
- v5 = v4 mechanism (src/build_muse_watch.py numbers: chord cut -19.5,
  pocket 42.6 x 28.4, floor z 18.9, docked transform (x,y,z)->(-z,y,x)+(10,0,48))
  with the retro concept styling applied (ivory chunky body, ribbed band,
  orange accent disc, rounded forms).
- The Codex upright design stays in codex-out/ as a reference only.

## Puck fully embedded (user, 2026-11-18 16:26)
- The dock must EMBED the charger puck inside the body, not rest it in an
  open pocket: puck slides in from the bottom (or back) into an internal
  cavity, only its grooved top face exposed, flush with the seat the watch
  edge drops onto. Cable routes inside the body and exits the back.
- Puck must stay replaceable (slide-out), held by friction + a bottom cover
  plate or snap lip; no glue, no tape.
