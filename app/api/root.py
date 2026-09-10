from fastapi import APIRouter
from fastapi import Response
from fastapi.responses import HTMLResponse

router = APIRouter()

_TAGLINE_ROOT = "There is nothing here. That is the point."
_TAGLINE_DATABASE = (
    "You have reached the database. It is not a database. It is a ghost wearing "
    "a database costume."
)

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poltergeist</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    background: radial-gradient(ellipse at 50% 120%, #2a0f3f 0%, #0b0716 55%, #050308 100%);
    color: #e8ddff; overflow: hidden; cursor: none;
    display: flex; align-items: center; justify-content: center; text-align: center;
    padding: 0 16px;
  }
  .fog {
    position: fixed; inset: -20%; pointer-events: none; opacity: .35;
    background: repeating-radial-gradient(circle at 30% 40%, transparent 0 60px, rgba(180,140,255,.06) 60px 120px),
                repeating-radial-gradient(circle at 70% 60%, transparent 0 80px, rgba(120,200,255,.05) 80px 160px);
    animation: drift 40s linear infinite alternate;
  }
  @keyframes drift { from { transform: translate(-3%, -2%) rotate(0deg); } to { transform: translate(3%, 2%) rotate(3deg); } }
  main { position: relative; z-index: 2; max-width: 720px; }
  h1 {
    font-size: clamp(3rem, 12vw, 8rem); letter-spacing: .12em; margin: 0;
    font-weight: 900; color: #f3ecff;
    text-shadow: 0 0 12px #b48cff, 0 0 40px #7b3fe4, 0 0 80px #4a1d8f;
    animation: flicker 6s infinite;
  }
  @keyframes flicker {
    0%, 18%, 22%, 25%, 53%, 57%, 100% { opacity: 1; }
    20%, 24%, 55% { opacity: .35; text-shadow: none; }
  }
  .tag { font-size: 1.15rem; opacity: .85; margin: 1rem 0 2rem; }
  .whisper {
    min-height: 3.2em; font-style: italic; color: #b9a6e6; font-size: 1.05rem;
    transition: opacity .6s;
  }
  .bar { width: min(420px, 90%); height: 10px; margin: 2rem auto 0; border-radius: 999px;
    background: rgba(255,255,255,.08); overflow: hidden; box-shadow: inset 0 0 8px #000; }
  .bar > i { display: block; height: 100%; width: 0; border-radius: 999px;
    background: linear-gradient(90deg, #7b3fe4, #c58cff); box-shadow: 0 0 14px #b48cff;
    animation: almost 9s ease-in-out infinite; }
  @keyframes almost { 0% { width: 0 } 85% { width: 99% } 100% { width: 99% } }
  .label { font-size: .8rem; letter-spacing: .3em; text-transform: uppercase; opacity: .55; margin-top: .6rem; }
  footer { position: fixed; bottom: 14px; left: 0; right: 0; font-size: .75rem; opacity: .45; letter-spacing: .05em; }
  #ghost { position: fixed; left: 0; top: 0; width: 64px; height: 72px; z-index: 5;
    pointer-events: none; will-change: transform; filter: drop-shadow(0 0 16px rgba(196,160,255,.7)); }
  .boo { position: fixed; z-index: 4; pointer-events: none; font-weight: 800; color: #d9c8ff;
    text-shadow: 0 0 10px #8f5cff; animation: rise 1.6s ease-out forwards; }
  @keyframes rise { to { transform: translateY(-140px) rotate(var(--r)); opacity: 0; } }
  @media (pointer: coarse) { body { cursor: auto; } }
</style>
</head>
<body>
<div class="fog"></div>
<svg id="ghost" viewBox="0 0 64 72" aria-hidden="true">
  <path d="M32 4C17 4 8 16 8 30v34l8-6 8 6 8-6 8 6 8-6 8 6V30C56 16 47 4 32 4z" fill="#f4efff" opacity=".95"/>
  <circle cx="24" cy="30" r="4" fill="#2a1a4a"/><circle cx="40" cy="30" r="4" fill="#2a1a4a"/>
  <path id="mouth" d="M27 42q5 5 10 0" stroke="#2a1a4a" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>
<main>
  <h1>POLTERGEIST</h1>
  <p class="tag">__TAGLINE__</p>
  <p class="whisper" id="whisper"></p>
  <div class="bar"><i></i></div>
  <div class="label">contacting the other side</div>
</main>
<footer>a Geometry Dash server &middot; haunted since 2026 &middot; the real frontend lives elsewhere</footer>
<script>
  const whispers = [
    "the daily level was scheduled by something that is not a moderator.",
    "your gjp2 has been consumed. it was delicious.",
    "-1",
    "somebody rated a level 11 stars and the server just sighed.",
    "the weekly demon is watching you from inside the leaderboard.",
    "this page is 99% loaded. it will stay that way.",
    "no, the vault code is not 'backstreetboy' here either.",
    "a friend request arrived from an account that does not exist.",
    "the level string was fine. the level was not.",
    "please stop clicking. the ghost is ticklish.",
    "creator points are stored in a jar. the jar is haunted.",
    "the chest cooldown is measured in ghost minutes. they are longer.",
  ];
  const whisper = document.getElementById("whisper");
  let index = Math.floor(Math.random() * whispers.length);
  function speak() {
    whisper.style.opacity = 0;
    setTimeout(() => { whisper.textContent = whispers[index++ % whispers.length]; whisper.style.opacity = 1; }, 600);
  }
  speak(); setInterval(speak, 4200);

  const ghost = document.getElementById("ghost");
  let target = { x: innerWidth / 2, y: innerHeight * 0.7 }, pos = { ...target }, phase = 0;
  addEventListener("pointermove", e => target = { x: e.clientX, y: e.clientY });
  addEventListener("pointerdown", e => {
    target = { x: e.clientX, y: e.clientY };
    const boo = document.createElement("div");
    boo.className = "boo";
    boo.textContent = ["boo", "BOO", "no", "-1", "spooky", "oh no"][Math.floor(Math.random() * 6)];
    boo.style.left = e.clientX - 20 + "px"; boo.style.top = e.clientY - 30 + "px";
    boo.style.setProperty("--r", (Math.random() * 60 - 30) + "deg");
    boo.style.fontSize = 14 + Math.random() * 22 + "px";
    document.body.appendChild(boo); setTimeout(() => boo.remove(), 1600);
    document.getElementById("mouth").setAttribute("d", "M26 40q6 -6 12 0");
    setTimeout(() => document.getElementById("mouth").setAttribute("d", "M27 42q5 5 10 0"), 500);
  });
  function float() {
    phase += 0.04;
    pos.x += (target.x - pos.x) * 0.06; pos.y += (target.y - pos.y) * 0.06;
    const bob = Math.sin(phase) * 8, tilt = (target.x - pos.x) * 0.04;
    ghost.style.transform = `translate(${pos.x - 32 + 40}px, ${pos.y - 36 + bob}px) rotate(${tilt}deg)`;
    requestAnimationFrame(float);
  }
  float();
</script>
</body>
</html>
"""


def _page(tagline: str) -> Response:
    return HTMLResponse(_PAGE.replace("__TAGLINE__", tagline))


@router.get("/", include_in_schema=False)
async def root() -> Response:
    return _page(_TAGLINE_ROOT)


@router.get("/database", include_in_schema=False)
async def database() -> Response:
    return _page(_TAGLINE_DATABASE)
