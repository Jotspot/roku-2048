#!/usr/bin/env python3
"""Generate the static pages for https://2048.mistr.uk into public/.

    python3 site/build.py && (cd site && npx wrangler deploy)

Shared header/footer live here; edit page content below. Keep the legal pages
accurate to what the app actually does: no network requests, no accounts, no
analytics, data only in the Roku device registry. If the app ever changes that,
update /privacy before shipping.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "public")

SITE = "https://2048.mistr.uk"
PUBLISHER = "Jamie Perry"
EMAIL = "support@mistr.uk"
REPO = "https://github.com/Jotspot/roku-2048"
UPDATED = "24 September 2026"
YEAR = "2026"

NAV = [("/", "Home"), ("/#how-to-play", "How to play"), ("/support", "Support"),
       ("/privacy", "Privacy"), ("/terms", "Terms"), (REPO, "GitHub")]


def page(path, title, description, body, current=None):
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{href}"{cur if href == current else ""}>{label}</a>' for href, label in NAV)
    full_title = title if title.startswith("2048") else f"{title} · 2048"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{SITE}{path}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{SITE}/img/og.jpg">
<meta property="og:url" content="{SITE}{path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FAF8EF">
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="/"><span class="mark"><i></i><i></i><i></i><i></i></span>2048</a>
  <nav aria-label="Main">{nav}</nav>
</div></header>
<main>
{body}
</main>
<footer><div class="wrap">
  <nav aria-label="Footer"><a href="{REPO}">Source code (MIT)</a><a href="/support">Support</a><a href="/privacy">Privacy Policy</a><a href="/terms">Terms of Service</a><a href="mailto:{EMAIL}">{EMAIL}</a></nav>
  <p>&copy; {YEAR} {PUBLISHER}. This 2048 app is independent and inspired by the original
  <a href="https://github.com/gabrielecirulli/2048">2048</a> by Gabriele Cirulli.</p>
  <p>Roku is a trademark of Roku, Inc. This app is not affiliated with, sponsored or endorsed by Roku, Inc.</p>
</div></footer>
</body>
</html>
"""
    out = os.path.join(PUB, "index.html" if path == "/" else path.strip("/") + ".html")
    open(out, "w").write(html)
    print("wrote", os.path.relpath(out, HERE))


def tile_logo():
    return ('<div class="logo" aria-hidden="true">'
            '<span style="background:var(--t2)">2</span><span style="background:var(--t0)">0</span>'
            '<span style="background:var(--t4)">4</span><span style="background:var(--t8)">8</span></div>')


# ---------------------------------------------------------------- home ----

HOME = f"""
<section class="hero"><div class="wrap">
  <div>
    {tile_logo()}
    <h1>The classic puzzle, <em>made for your TV.</em></h1>
    <p class="lede">Slide the tiles, merge matching numbers and reach the 2048 tile, right from your couch.
    Available on Roku streaming devices and TVs.</p>
    <div class="pills"><span class="pill">Free</span><span class="pill">No ads</span>
      <span class="pill">No account</span><span class="pill">HD &amp; Full HD</span></div>
  </div>
  <div>
    <div class="tv"><img src="/img/hero_0.jpg" width="1600" height="900" alt="A 2048 game in progress on a TV, with 2048 and 1024 tiles on the board"></div>
    <div class="tv-stand"></div>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <h2>Made to feel <em>great.</em></h2>
  <p class="section-lede">Every detail is tuned for the big screen and a simple remote.</p>
  <div class="features">
    <div class="feature"><div class="dot" style="background:var(--t0)"></div><b>Snappy merges</b>
      <p>Tiles slide, squish and pop instantly, with sounds that climb as your tiles grow.</p></div>
    <div class="feature"><div class="dot" style="background:var(--t4)"></div><b>Undo a move</b>
      <p>Press Replay to take back your last move, even right after a game over.</p></div>
    <div class="feature"><div class="dot" style="background:var(--t8)"></div><b>Always saved</b>
      <p>Your game and best score are saved after every move. Pick up any time.</p></div>
    <div class="feature"><div class="dot" style="background:var(--t2)"></div><b>Crisp on any TV</b>
      <p>Pixel-perfect graphics in HD and Full HD, and it opens in about a second.</p></div>
  </div>
</div></section>

<section id="how-to-play"><div class="wrap howto">
  <div>
    <h2>How to <em>play</em></h2>
    <ol class="rules">
      <li>Press an arrow to slide every tile on the board in that direction.</li>
      <li>When two tiles with the same number touch, they merge into one: 2 + 2 = 4, 4 + 4 = 8, and so on.</li>
      <li>After every move a new 2 (or sometimes a 4) appears.</li>
      <li>Reach the <b>2048</b> tile to win, then keep going for a bigger one.</li>
      <li>The game ends when the board is full and nothing can merge.</li>
    </ol>
  </div>
  <div class="controls" aria-label="Remote controls">
    <div class="ctl"><div class="key"><img src="/img/ic_dpad.png" alt=""></div><div>Arrow pad <span>· slide tiles</span></div></div>
    <div class="ctl"><div class="key"><img src="/img/ic_replay.png" alt=""></div><div>Replay <span>· undo last move</span></div></div>
    <div class="ctl"><div class="key"><img src="/img/ic_options.png" alt=""></div><div>Options (*) <span>· new game</span></div></div>
    <div class="ctl"><div class="key"><img src="/img/ic_playpause.png" alt=""></div><div>Play/Pause <span>· sound on/off</span></div></div>
    <div class="ctl"><div class="key txt">OK</div><div>OK <span>· choose on the win / game-over screens</span></div></div>
    <div class="ctl"><div class="key txt">BACK</div><div>Back <span>· close a dialog or exit</span></div></div>
  </div>
</div></section>

<section class="alt"><div class="wrap">
  <h2>See it in <em>action</em></h2>
  <p class="section-lede">Real screenshots, captured on a Roku.</p>
  <div class="gallery">
    <figure><img src="/img/merge_1.jpg" width="1600" height="900" loading="lazy" alt="Tiles popping as they merge"><figcaption>Merges pop with a satisfying burst.</figcaption></figure>
    <figure><img src="/img/win_1.jpg" width="1600" height="900" loading="lazy" alt="The You win! screen"><figcaption>Reach 2048, then keep going.</figcaption></figure>
    <figure><img src="/img/over_0.jpg" width="1600" height="900" loading="lazy" alt="The Game over screen with an Undo option"><figcaption>Out of moves? Undo and try again.</figcaption></figure>
  </div>
</div></section>
"""

# ------------------------------------------------------------- support ----

SUPPORT = f"""
<div class="doc"><div class="wrap">
  <h1>Support</h1>
  <p class="meta">Questions, bugs or ideas? Email <a href="mailto:{EMAIL}">{EMAIL}</a>. We usually reply within a few days.</p>
  <p><a class="btn" href="mailto:{EMAIL}?subject=2048%20for%20Roku">Email support</a></p>

  <h2>Frequently asked questions</h2>
  <details><summary>How do I play?</summary>
    <p>Press an arrow on your remote to slide all tiles. Matching numbers merge. Reach the 2048 tile to win. See <a href="/#how-to-play">How to play</a>.</p></details>
  <details><summary>How do I undo a move?</summary>
    <p>Press <b>Replay</b> (the circular arrow button) to undo your last move. You can undo one move at a time, including right after a game over.</p></details>
  <details><summary>How do I start a new game?</summary>
    <p>Press <b>Options (*)</b>. If you have a game in progress you'll be asked to confirm; press OK to start over or Back to keep playing.</p></details>
  <details><summary>How do I turn the sound off?</summary>
    <p>Press <b>Play/Pause</b> to switch sound effects on or off. The setting is remembered.</p></details>
  <details><summary>Will I lose my game if I exit?</summary>
    <p>No. Your board, score and best score are saved on your Roku device after every move, and the game picks up where you left off next time you open it.</p></details>
  <details><summary>How do I reset my best score?</summary>
    <p>Your best score is stored only on your Roku device. Removing the app from your Roku home screen deletes it; reinstalling starts fresh.</p></details>
  <details><summary>Does the app need an account or internet connection to play?</summary>
    <p>No account is needed and the game itself makes no network requests. Your Roku needs to be online to install the app from the store.</p></details>

  <h2>Reporting a problem</h2>
  <p>Please include your Roku model (Settings → System → About) and what happened just before the problem. Thank you!</p>
</div></div>
"""

# ------------------------------------------------------------- privacy ----

PRIVACY = f"""
<div class="doc"><div class="wrap">
  <h1>Privacy Policy</h1>
  <p class="meta">Last updated {UPDATED}</p>

  <div class="callout"><p><b>In short:</b> 2048 doesn't collect, store or share any personal information.
  There are no accounts, ads, analytics or trackers, and the app makes no network requests.
  Your game progress stays on your Roku device.</p></div>

  <p>This policy explains how the 2048 app for Roku devices (the "App") and this website,
  {SITE.replace("https://", "")} (the "Site"), handle information. The App and Site are published by {PUBLISHER}
  ("we", "us"). If you have any questions, contact <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>

  <h2>Information the App collects</h2>
  <p>None. The App does not collect, transmit, sell or share any personal information. It has no user accounts,
  no advertising, no analytics or crash-reporting services and no third-party SDKs, and it does not connect to the internet.</p>

  <h2>Information stored on your device</h2>
  <p>To let you continue where you left off, the App saves the following <b>only on your Roku device</b>, in the
  storage the Roku operating system provides for each app:</p>
  <ul>
    <li>the current game board and score,</li>
    <li>your best score, and</li>
    <li>whether sound effects are on or off.</li>
  </ul>
  <p>This data is never sent to us or anyone else. It is deleted when you remove the App from your Roku device.</p>

  <h2>Roku</h2>
  <p>The App runs on the Roku platform. Roku, Inc. may collect information about your device and how you use it,
  including which apps you install and use, under its own policies. We don't receive that information. See the
  <a href="https://docs.roku.com/published/userprivacypolicy/en/us">Roku Privacy Policy</a> for details.</p>

  <h2>This website</h2>
  <p>The Site uses no cookies, analytics or tracking, and loads no third-party scripts or fonts. It is hosted by
  Cloudflare, which processes technical information such as IP addresses to deliver and protect the Site.
  See <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare's Privacy Policy</a>.
  If you email us, we use your email address and message only to reply to you, and we don't share them.</p>

  <h2>Children</h2>
  <p>The App is suitable for all ages. Because it collects no personal information, it collects none from children,
  including children under 13.</p>

  <h2>Your rights</h2>
  <p>Depending on where you live (for example under Singapore's Personal Data Protection Act, the GDPR in the UK and EU,
  or US state laws such as the CCPA), you may have rights to access or delete personal data about you. As the App holds
  no personal data about you, there is nothing for us to access or delete. For any support emails you've sent, contact
  <a href="mailto:{EMAIL}">{EMAIL}</a> and we'll delete them on request.</p>

  <h2>Changes</h2>
  <p>If this policy changes, we'll update this page and the "Last updated" date above. If the App ever starts collecting
  personal information, we will update this policy before that change is released.</p>

  <h2>Contact</h2>
  <p>{PUBLISHER} · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div></div>
"""

# --------------------------------------------------------------- terms ----

TERMS = f"""
<div class="doc"><div class="wrap">
  <h1>Terms of Service</h1>
  <p class="meta">Last updated {UPDATED}</p>

  <p>These terms apply to the 2048 app for Roku devices (the "App") and this website (the "Site"), published by
  {PUBLISHER} ("we", "us"). By installing or using the App or Site you agree to these terms. If you don't agree,
  please don't use them.</p>

  <h2>1. Using the App</h2>
  <p>The App is free to install and use on Roku devices you own or control.</p>
  <p>The App is also open source. Its source code is published at <a href="{REPO}">{REPO.replace("https://", "")}</a>
  under the <a href="{REPO}/blob/main/LICENSE">MIT License</a>, which lets you use, copy, modify and distribute the
  code. That licence, not these terms, governs what you can do with the source code. These terms cover your use of the
  App as published on the Roku Streaming Store and of this Site.</p>

  <h2>2. Roku</h2>
  <p>You get the App through the Roku platform, and your use of Roku devices and services is also covered by Roku's
  own terms. Roku, Inc. is not a party to these terms and is not responsible for the App or its content.</p>

  <h2>3. Ownership and open-source licences</h2>
  <p>The App's code, artwork, sounds and this Site are &copy; {YEAR} {PUBLISHER} and released under the MIT License
  (see above). The gameplay concept is inspired by the open-source game
  <a href="https://github.com/gabrielecirulli/2048">2048</a> by Gabriele Cirulli. The Outfit font used on this Site is
  licensed under the <a href="/assets/OFL-Outfit.txt">SIL Open Font License</a>. Roku is a trademark of Roku, Inc.
  We are not affiliated with or endorsed by Roku, Inc. If you publish your own version of the App, please use your own
  name and artwork so it isn't confused with this one.</p>

  <h2>4. Your data</h2>
  <p>The App stores your game progress only on your device and collects no personal information. See our
  <a href="/privacy">Privacy Policy</a>.</p>

  <h2>5. Updates and availability</h2>
  <p>We may update, change or stop offering the App or Site at any time. We don't guarantee the App will always be
  available or work on every device.</p>

  <h2>6. No warranty</h2>
  <p>This section applies to the App, the Site and the source code alike.</p>
  <p>The App and Site are provided "as is" and "as available", without warranties of any kind, express or implied,
  including warranties of merchantability, fitness for a particular purpose and non-infringement, to the fullest
  extent permitted by law.</p>

  <h2>7. Limitation of liability</h2>
  <p>To the fullest extent permitted by law, we are not liable for any indirect, incidental, special or consequential
  damages, or for any loss of data (including game progress or scores), arising from your use of the App or Site.
  Our total liability for any claim relating to the App or Site is limited to the amount you paid for it, which is zero.
  Nothing in these terms limits liability that cannot be limited by law.</p>

  <h2>8. Governing law</h2>
  <p>These terms are governed by the laws of Singapore. Any dispute will be subject to the jurisdiction of the courts
  of Singapore, without affecting any mandatory consumer protections of the country where you live.</p>

  <h2>9. Changes to these terms</h2>
  <p>We may update these terms from time to time. The "Last updated" date shows when they last changed. Continuing to
  use the App after a change means you accept the updated terms.</p>

  <h2>10. Contact</h2>
  <p>{PUBLISHER} · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div></div>
"""

NOT_FOUND = """
<div class="doc"><div class="wrap">
  <h1>Page not found</h1>
  <p class="meta">That tile slid off the board.</p>
  <p><a class="btn" href="/">Back to home</a></p>
</div></div>
"""

if __name__ == "__main__":
    page("/", "2048: the classic puzzle, made for your TV",
         "Slide, merge and reach the 2048 tile on your Roku. Free, no ads, no account.", HOME, "/")
    page("/support", "Support", "Help and FAQ for 2048 on Roku, plus how to contact support.", SUPPORT, "/support")
    page("/privacy", "Privacy Policy", "2048 collects no personal information. Game progress stays on your Roku device.", PRIVACY, "/privacy")
    page("/terms", "Terms of Service", "Terms of Service for the 2048 app for Roku devices.", TERMS, "/terms")
    page("/404", "Page not found", "Page not found.", NOT_FOUND)
