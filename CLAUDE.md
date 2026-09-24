# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A 2048 game as a Roku SceneGraph app (BrightScript + XML). Priorities, in order: snappy/satisfying feel, crisp rendering at HD and FHD, and a small, fast-launching package (~0.5–0.75 s launch on device).

## Commands

```sh
make assets                                     # regenerate images/ + sounds/ (python3, stdlib only)
make zip                                        # build out/roku2048.zip
make install ROKU_IP=<roku-ip> ROKU_PASS=<dev-pass>   # sideload to a dev-mode Roku
make console ROKU_IP=<roku-ip>                  # BrightScript debug console (port 8085)
make check SCA=path/to/sca-cmd                  # Roku Static Analysis (download: devtools.web.roku.com/static-channel-analysis/sca-cmd.zip, needs Java)
make package ROKU_IP=... ROKU_PASS=... PKG_PASS=<genkey pw>   # signed .pkg for the dashboard
```

There is no test suite. Verification is:

- **Lint/compile check** — BrighterScript compiler (catches syntax errors and reserved identifiers):
  `npx -p brighterscript bsc --rootDir . --files manifest "source/**/*" "components/**/*" --createPackage false --copyToStaging false`
- **Headless run** — `brs-node` (same engine as the lvcabral.com/brs web emulator):
  `npx brs-cli out/roku2048.zip -e -a 40` then send keys over ECP: `curl -X POST http://127.0.0.1:8060/keypress/Left` (Up/Down/Right/Select/InstantReplay/Info/Play/Back). Check output for `[2048]` / errors.
  Screenshots: run with `TERM_PROGRAM=iTerm.app npx brs-cli out/roku2048.zip -e -i 100 > log`, then base64-decode the `1337;File=...:<b64>` payloads in the log to PNGs. Frame capture in this mode is slow (~10 fps) and skips frames — don't judge animation timing from it; use `print` + `UpTime(0)` in a scratch copy instead.
- **On device** — `make install`, then `curl http://<ip>:8060/query/active-app` and watch `nc <ip> 8085`. The user's Roku has ECP in **limited** mode: `/keypress` returns 403 (only `/launch`, `/input`, `/query` work), so on-device input can't be scripted — staged builds must trigger moves themselves (see `tools/promo/capture.py`). Device screenshots: `POST /plugin_inspect mysubmit=Screenshot`, then GET `/pkgs/dev.jpg` (digest auth).

For debugging, copy the project to a scratch dir and instrument there (e.g. hardcode `saved` in `source/main.brs` to seed a board) rather than editing the real sources.

## Architecture

- `source/main.brs` — reads the saved JSON into `m.global.saved` before `CreateScene`, then only handles roInput / memory events. **It must not touch the scene node after `CreateScene()`**: on real devices the scene's `init()` is still running, so `scene.observeField` silently returns false and scene field access can deadlock with init's `m.global` reads. (This bug made saving a no-op on hardware while working in brs-engine.)
- `components/SaveTask` — Task thread that owns registry writes. GameScene creates it in `init()` (before `loadState`) and sets `m.saver.data = <json>` after every move/toggle; the task writes + flushes. Sideloading a new build wipes the dev app's registry (normal Roku behaviour), so test persistence by relaunching (`/launch/dev`), not reinstalling.
- `components/GameScene` — everything else: computes the layout, builds the board/panel nodes in code, owns the grid logic, input (`onKeyEvent`), sounds, and persistence. `init()` computes `layout()` and publishes it as `m.global.layout`; **Tile and Overlay read their geometry from `m.global.layout` in their own `init()`**, so they must be created *after* the scene's init (Overlay is created in code for this reason, not declared in XML).
- `components/Tile` — one pooled tile. `mover` group sits at the tile **centre** and art inside `popper` is offset by `-size/2`, so scaling popper grows around the middle without relying on `scaleRotateCenter` (which brs-engine ignores). API via `callFunc`: `spawn({x,y,v,d,kind})` (`kind` = `"merge"` pop or `"appear"` fade-in), `slide({x,y,die})`, `finish()`, `hide()`.
- `components/Overlay` — win / game-over / confirm modal sized to the board. Hints are `[key, action]`; key `"OK"` renders as text, anything else as an icon name (`images/ic_<name>_<res>.png`).
- `components/colors.brs` — tile palette, included by both Tile and GameScene.

### Game/animation model

- Input is never blocked. On each key the logical grid updates immediately; `finishAll()` first snaps in-flight slides (`Tile.finish`) and returns last move's dying tiles to the pool. Pops/fades only touch scale/opacity so they keep running across moves.
- `doMove` builds per-tile commands. Merge: both source tiles slide into the target with `die=true` (shrinking to 80%), and a **new** tile from the pool is spawned there with `kind:"merge"` and brought to front via `appendChild`. Merge rings are a separate pool in `fxLayer` (above `tileLayer`) animated by poster width/height/translation, not scale.
- All tile animations are `easeFunction="linear"` over precomputed keyframes (ease-out cubic for slides, explicit overshoot keys for pops) so curves are identical on every renderer. Current timings: slide 100 ms, pop/appear 150 ms starting at 70 ms. The user explicitly prefers these snappy timings over longer spring-based ones.
- Sounds (`SoundEffect` nodes) and pool warm-up are created in a 50 ms one-shot timer after the first frame to keep launch fast.

### Resolution handling

`manifest` declares `ui_resolutions=hd,fhd`. `layout()` derives every size from the design height (720 or 1080) in whole pixels; FHD-authored numbers go through `s(v)` to scale. Tile/cell/ring/icon PNGs are **pre-rendered at exact pixel sizes per resolution** — sizes in `tools/gen_assets.py` (`TILE_PX`, `ICON_PX`, `PANEL_RADIUS`) must match `layout()` (tile = round(200·k), icon = round(44·k)).

### Assets

Everything in `images/` and `sounds/` is generated by `tools/gen_assets.py` (no PIL/numpy — hand-rolled PNG writer, 44.1 kHz WAV synth). The home-screen posters (`poster_*`, Roku spec FHD 540×405, HD 290×218) and splash screens (`splash_*`, 1920×1080 / 1280×720) are also generated; if the user supplies their own, remove the corresponding `make_art(...)` calls so `make assets` doesn't overwrite them.

## Certification & store

The dashboard only accepts the **signed `.pkg`**; a plain zip fails with "invalid header". The signing key lives on the maintainer's keyed Roku (`genkey` was run there); its password and DevID are in `out/SIGNING-KEY.txt` (never commit or print it). Build with `make package ROKU_IP=<keyed-roku-ip> ROKU_PASS=<dev-pass> PKG_PASS=<password>`. To sign from another Roku, `rekey` it with a signed .pkg plus the password.

Static Analysis must stay clean (the only accepted warning is the AppDialog beacon one — there is no pre-home dialog). Cert-relevant wiring: `AppLaunchComplete` beacon fires in `onDeferredInit` (first frame); `source/main.brs` handles `roInput` (+ `supports_input_launch=1`) and launch deep links (logged, board shown), and enables memory-monitor events; Back closes confirm/win modals, otherwise exits (cert 4.6); `rsg_version=1.3`. Bump `build_version` for every submission. Poster/splash art is written as opaque RGB in broadcast-safe 16–235 range (`legal()` in gen_assets); `splash_color` must match that remapped background.

`store/` holds the dashboard deliverables (posters, six 1920×1080 screenshots, `listing.md` with copy + remaining manual steps). Screenshots: `tools/promo/capture.py` stages boards on the real Roku (scratch builds with a hardcoded save and no registry writes; run `make install` afterwards), `tools/promo/make_slides.py` composes them in HTML and renders with headless Chrome.

## Website

`site/` is the public site at https://2048.mistr.uk (landing/learn-more, `/privacy`, `/terms`, `/support`), a static-assets Cloudflare Worker (`site/wrangler.jsonc`, custom domain). Pages are generated from `site/build.py` (shared header/footer + content): `python3 site/build.py && (cd site && npx wrangler deploy)`. The privacy policy states the app makes no network requests and stores data only in the Roku registry — update it before shipping anything that changes that. Publisher: Jamie Perry; contact support@mistr.uk (an iCloud Custom Email Domain alias — mistr.uk MX is iCloud, don't enable Cloudflare Email Routing); terms governed by Singapore law.

## Gotchas

- brs-engine is not proof something works on hardware (scene creation there is synchronous, hiding the save deadlock). Verify device behaviour via the 8085 console; the maintainer's Rokus have ECP in limited mode, so staged debug builds must act on their own (Timers) and can quit themselves (`wait(timeout)` + `return` in main) to test relaunch.
- BrightScript identifiers are **case-insensitive**: a local `l` clobbers `L` (the layout). Don't name locals after functions either (e.g. `s` collides with `s()`); `box` is reserved.
- brs-engine (web emulator) quirks, not device bugs: ignores `scaleRotateCenter`; draws a node with scale `[0,0]` as unscaled (start pops at ≥0.01); ignores a static Group `scale` on some subtrees; `font:BoldSystemFontFile` URIs render no text — use `label.font = "font:MediumBoldSystemFont"` then set `label.font.size`. It also picks the *first* `ui_resolutions` entry and runs slower than real hardware, so perceived choppiness there isn't representative.
