# Store listing: 2048

Everything to paste or upload in the Roku Developer Dashboard (Manage apps → your app).

## Artwork

| Dashboard field | File | Spec |
|---|---|---|
| App poster (FHD) | `poster_540x405.png` | 540×405 PNG, opaque, broadcast-safe colors |
| App poster (HD, if asked) | `poster_290x218.png` | 290×218 PNG |
| Screenshots (up to 6) | `screenshots/01_hero.png` … `06_resume.png` | 1920×1080 PNG. Gameplay is real device captures |

Regenerate: `python3 tools/promo/make_slides.py` (re-captures: `tools/promo/capture.py`, needs the Roku).

## Text

**App name** (max 30): `2048`

**On-device description** (228 / 300):

> The classic number puzzle, made for your TV. Slide tiles with your remote, merge matching numbers and reach 2048. Snappy animations, satisfying sounds, one-press undo, and your game saves automatically. Free, no ads, no account.

**Online description** (531 / 1500):

> 2048 is the addictive number-sliding puzzle, rebuilt for the big screen.
>
> Press the arrows on your remote to slide every tile. When two matching numbers touch, they merge: 2 + 2 = 4, 4 + 4 = 8, and so on. Keep combining to reach the 2048 tile, then keep going for a new best.
>
> - Snappy, satisfying animations and sound effects
> - Undo your last move with the Replay button
> - Your game and best score save automatically
> - Crisp graphics in HD and Full HD
> - Free, with no ads, accounts or in-app purchases
>
> Learn more at 2048.mistr.uk

## URLs (live at https://2048.mistr.uk, source in `site/`)

| Dashboard field | URL |
|---|---|
| Privacy policy | https://2048.mistr.uk/privacy |
| Terms of service | https://2048.mistr.uk/terms |
| Website / Learn more | https://2048.mistr.uk |
| Customer support URL | https://2048.mistr.uk/support |
| Support email | support@mistr.uk |

**Category:** Games (Puzzle). **Made for kids:** your call. There is no data collection, ads or chat, so either is fine. **Age rating:** choose the "all ages" option the dashboard offers.

## Still needed from you (dashboard-only, can't be done in code)

- [x] **Signing key:** created on the maintainer's Roku. The password and DevID are kept privately (never in this repo).
- [ ] **Upload the package:** `out/roku2048-1.2.1.pkg` (signed). The dashboard rejects the plain zip ("invalid header"). For each update, bump `build_version`, then run `make package ROKU_IP=<keyed-roku-ip> ROKU_PASS=<dev-pass> PKG_PASS=<password>`.
- [ ] **Create the support@mistr.uk address:** mistr.uk mail runs through iCloud, so add it at icloud.com → Settings → Custom Email Domain → mistr.uk → Add address. The site and listing already use it.
- [ ] **Support phone and the admin/technical contacts** in the dashboard (the URLs are above).
- [ ] **Countries, domestic region, pricing** (free).
- [ ] **Bump the version** (`build_version` in `manifest`) for every build you submit (cert 6.1).
