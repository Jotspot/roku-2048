# Release notes

## 1.2.1: first release

**Store / user-facing** (paste into the dashboard):

> Welcome to 2048 on Roku! Slide tiles with your remote, merge matching numbers and reach the 2048 tile.
> - Snappy, satisfying animations and sound effects
> - Undo your last move with the Replay button
> - Your game and best score save automatically
> - Crisp graphics in HD and Full HD
> - Free, with no ads or account needed

**Internal changelog** (for your records):

- Gameplay: classic 4×4 rules, one-step undo, win screen with "keep going", game-over detection.
- Feel: 100 ms slides, merge pop with ring burst, fade-in for new tiles, glow on 128+ tiles, 44.1 kHz sound effects that rise in pitch with tile value, mute toggle.
- Display: native HD (720p) and FHD (1080p) layouts in whole pixels; images pre-rendered per resolution.
- Saving: the game auto-saves after every move via a background task (fixes saves being lost on real devices).
- Certification: AppLaunchComplete beacon, roInput / deep-link handling, memory monitoring, rsg_version 1.3, Back closes dialogs before exiting, broadcast-safe poster and splash. Roku Static Analysis is clean.
- Launch: about 0.5–1 s on test devices; package about 570 KB.
