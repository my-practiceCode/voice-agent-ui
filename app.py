import base64
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from livekit import api
from config import settings
from clients import CLIENTS, LANGUAGES

# Put your logo image next to this file and name it logo.png
LOGO_PATH = Path(__file__).resolve().parent / "logo.png"

PAGE_CSS = """
<style>
  .stApp { background: #0D964D; }
  .stApp::before { content: ""; position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 999;
    background: linear-gradient(90deg, #00E676, #00C853, #BEF264); }
  [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #D6EEE3; box-shadow: 4px 0 24px rgba(16,120,85,.06); }
  [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span { color: #0B2E22; }
  [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] .stCaption * { color: #5C7A6D; }
  [data-testid="stSidebar"] button { background: #FFFFFF; color: #0B6B4B; border: 1px solid #00C853; border-radius: 12px; font-weight: 600; }
  [data-testid="stSidebar"] button:hover { background: linear-gradient(135deg, #00E676, #00C853); color: #04210F; border-color: transparent; }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stAppDeployButton"], [data-testid="stDecoration"], #MainMenu, footer { display: none; visibility: hidden; }
  .block-container, [data-testid="stMainBlockContainer"] { box-sizing: border-box; min-height: 100vh; max-width: 720px;
    padding-top: 1rem; padding-bottom: 1rem; display: flex; flex-direction: column; justify-content: center; }
  [data-testid="stVerticalBlock"] { width: 100%; align-items: stretch; }
  [data-testid="stElementContainer"]:has(.subtitle), .element-container:has(.subtitle),
  [data-testid="stMarkdown"]:has(.subtitle), [data-testid="stMarkdownContainer"]:has(.subtitle) { width: 100% !important; max-width: 100% !important; text-align: center; }
  p.subtitle { margin: 0 auto 4px !important; }
  .subtitle { display: table; max-width: 100%; margin: 0 auto 4px; padding: 8px 20px 8px 16px; border-radius: 999px; text-align: center;
    color: #0B4A35; font-size: 13px; font-weight: 600; letter-spacing: .02em;
    background: #FFFFFF; border: 1px solid #BFE8D4; box-shadow: 0 6px 20px rgba(16,150,100,.12); }
  .subtitle::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 9px; border-radius: 50%;
    background: #00E676; box-shadow: 0 0 0 4px rgba(0,230,118,.25); vertical-align: 1px; }
</style>
"""

ORB_WIDGET = """
<style>
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; padding: 0; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; color: #0B2E22; overflow: hidden; }
  body { background: #0D964D; }
  .stage { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .scene { --lvl: 0; position: relative; width: 300px; height: 300px; perspective: 900px; cursor: pointer; }
  .scene::after { content: ""; position: absolute; left: 50%; bottom: 10px; width: 170px; height: 20px; margin-left: -85px; border-radius: 50%;
    background: radial-gradient(ellipse at center, rgba(2,70,30,.5) 0%, rgba(2,70,30,.22) 45%, rgba(2,70,30,0) 72%); filter: blur(5px); }
  .ring { position: absolute; inset: 0; margin: auto; width: 250px; height: 250px; border-radius: 50%; border: 2px solid transparent; opacity: 0; }
  .scene.user .ring { border-color: #3B82F6; animation: pulse 2s ease-out infinite; }
  .scene.ai .ring { border-color: #FFFFFF; animation: pulse 2s ease-out infinite; }
  .ring.r2 { animation-delay: .65s !important; }
  .ring.r3 { animation-delay: 1.3s !important; }
  @keyframes pulse { 0% { transform: scale(1); opacity: .7; } 100% { transform: scale(1.2); opacity: 0; } }

  .float, .spin, .tilt { position: absolute; inset: 0; transform-style: preserve-3d; }
  .float { animation: float 4s ease-in-out infinite alternate; }
  @keyframes float { from { transform: translateY(3px); } to { transform: translateY(-5px); } }
  .scene.think .spin { animation: turn 2.6s linear infinite; }
  .scene.ai .spin { animation: sway 1.7s ease-in-out infinite alternate; }
  @keyframes turn { to { transform: rotateY(360deg); } }
  @keyframes sway { from { transform: rotateY(-14deg); } to { transform: rotateY(14deg); } }
  .tilt { transition: transform .15s ease-out; }

  .glass { position: absolute; left: 50%; top: 50%; width: 240px; height: 240px; margin: -120px 0 0 -120px; border-radius: 50%;
    transform: translateZ(-14px);
    background: radial-gradient(circle at 30% 25%, #17956B 0%, #0A4A36 42%, #04211A 100%);
    border: 3px solid #FFFFFF;
    box-shadow: inset 0 0 18px rgba(16,185,129,.25), 0 6px 14px rgba(4,60,40,.35), 0 0 calc(2px + var(--lvl) * 14px) rgba(4,60,40,.4); }
  .scene.user .glass { box-shadow: inset 0 0 18px rgba(59,130,246,.3), 0 6px 14px rgba(4,60,40,.35), 0 0 calc(2px + var(--lvl) * 14px) rgba(30,64,175,.4); }
  .stack { position: absolute; inset: 0; transform-style: preserve-3d; }
  .slice { position: absolute; left: 50%; top: 50%; width: 190px; height: 190px; margin: -95px 0 0 -95px; pointer-events: none; }
  .slice.front { filter: drop-shadow(0 0 6px rgba(0,230,118,.55)); }
  .gloss { position: absolute; left: 50%; top: 50%; width: 240px; height: 240px; margin: -120px 0 0 -120px; border-radius: 50%; transform: translateZ(14px);
    background: radial-gradient(circle at 28% 22%, rgba(255,255,255,.26) 0%, rgba(255,255,255,0) 40%); pointer-events: none; }

  #state { margin-top: 4px; font-size: 21px; font-weight: 700; letter-spacing: .01em;
    background: linear-gradient(90deg, #FFFFFF, #D9FBE8); -webkit-background-clip: text; background-clip: text; color: transparent; }
  #sub { margin-top: 3px; font-size: 13px; color: #D9FBE8; }
  .controls { position: relative; display: flex; justify-content: center; align-items: center; margin-top: 16px; }
  #mute { position: absolute; left: 100%; margin-left: 12px; }
  #toggle { min-width: 168px; text-align: center; border: 0; border-radius: 999px; padding: 13px 34px; font-size: 15px; font-weight: 700; color: #04210F; cursor: pointer;
    background: linear-gradient(135deg, #00E676, #00C853); box-shadow: 0 8px 20px rgba(0,60,25,.35), 0 0 0 2px rgba(255,255,255,.6); transition: transform .15s, box-shadow .15s; }
  #toggle:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(0,60,25,.4), 0 0 0 2px rgba(255,255,255,.85); }
  #toggle.end { background: linear-gradient(135deg, #F87171, #EF4444); box-shadow: 0 8px 22px rgba(239,68,68,.35); }
  #toggle:disabled { opacity: .6; cursor: default; }
  #mute { width: 46px; height: 46px; border-radius: 50%; border: 1px solid rgba(255,255,255,.55); background: rgba(255,255,255,.18); color: #fff; font-size: 18px; cursor: pointer;
    box-shadow: 0 4px 14px rgba(0,60,25,.25); transition: background .15s;
  #mute:hover:not(:disabled) { background: rgba(255,255,255,.32); }
  #mute:disabled { opacity: .45; cursor: default; }
  #mute.on { background: #EF4444; border-color: #EF4444; color: #fff; }
</style>

<div class="stage">
  <div class="scene" id="scene">
    <div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div>
    <div class="float"><div class="spin"><div class="tilt" id="tilt">
      <div class="glass"></div>
      <div class="stack" id="stack"></div>
      <div class="gloss"></div>
    </div></div></div>
  </div>
  <div id="state">Tap to start</div>
  <div id="sub"></div>
  <div class="controls">
    <button id="toggle">Start call</button>
    <button id="mute" disabled title="Mute microphone">&#127908;</button>
  </div>
  <div id="audio"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
<script>
  const { Room, RoomEvent, Track } = LivekitClient;
  const LANGS = __LANGS__;
  const current = __LANGUAGE__;
  const LOGO = "__LOGO__";
  const scene = document.getElementById("scene");
  const tilt = document.getElementById("tilt");
  const stack = document.getElementById("stack");
  const stateEl = document.getElementById("state");
  const subEl = document.getElementById("sub");
  const btn = document.getElementById("toggle");
  const muteBtn = document.getElementById("mute");
  let room = null, muted = false, last = "";

  subEl.textContent = "Speaking: " + (LANGS[current] || current);

  function setState(cls, text) {
    scene.className = "scene " + cls;
    stateEl.textContent = text;
  }

  // Turn the logo's white background into transparency and recolor it, so it can be stacked into a 3D extrusion.
  function buildLogo() {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const size = 400, c = document.createElement("canvas");
        c.width = c.height = size;
        const x = c.getContext("2d");
        x.drawImage(img, 0, 0, size, size);
        const d = x.getImageData(0, 0, size, size), p = d.data;
        for (let i = 0; i < p.length; i += 4) {
          const r = p[i], g = p[i + 1], a = p[i + 3];
          if (a < 250) continue;
          if (g > r + 40) { p[i] = 0; p[i + 1] = 230; p[i + 2] = 118; p[i + 3] = Math.max(0, Math.min(255, 255 - r)); }
          else p[i + 3] = 0;
        }
        x.putImageData(d, 0, 0);
        resolve(c.toDataURL("image/png"));
      };
      img.src = LOGO;
    });
  }

  buildLogo().then((url) => {
    const N = 12;
    for (let i = 0; i < N; i++) {
      const im = document.createElement("img");
      im.src = url;
      im.className = "slice" + (i === N - 1 ? " front" : "");
      im.style.transform = "translateZ(" + ((i - N / 2) * 2) + "px)";
      if (i < N - 1) im.style.filter = "brightness(" + (0.3 + 0.6 * i / (N - 1)) + ")";
      stack.appendChild(im);
    }
  });

  document.addEventListener("mousemove", (e) => {
    const x = e.clientX / window.innerWidth - 0.5, y = e.clientY / window.innerHeight - 0.5;
    tilt.style.transform = "rotateX(" + (-y * 10) + "deg) rotateY(" + (x * 12) + "deg)";
  });
  document.addEventListener("mouseleave", () => { tilt.style.transform = "rotateX(0deg) rotateY(0deg)"; });

  setInterval(() => {
    if (!room) { scene.style.setProperty("--lvl", 0); return; }
    let lvl = room.localParticipant.audioLevel || 0;
    room.remoteParticipants.forEach((p) => { lvl = Math.max(lvl, p.audioLevel || 0); });
    scene.style.setProperty("--lvl", Math.min(1, lvl * 2).toFixed(2));
  }, 80);

  scene.onclick = () => { if (!room) btn.click(); };

  muteBtn.onclick = async () => {
    if (!room) return;
    muted = !muted;
    await room.localParticipant.setMicrophoneEnabled(!muted);
    muteBtn.classList.toggle("on", muted);
  };

  btn.onclick = async () => {
    if (room) return room.disconnect();
    btn.disabled = true;
    setState("think", "Connecting...");
    try {
      room = new Room();
      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) document.getElementById("audio").appendChild(track.attach());
      });
      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        if (speakers.some((s) => !s.isLocal)) { last = "ai"; setState("ai live", "Speaking"); }
        else if (speakers.length) { last = "user"; setState("user live", "Listening to you"); }
        else if (last === "user") { setState("think live", "Thinking..."); }
        else setState("live", "Ready - say something");
      });
      room.on(RoomEvent.Disconnected, () => {
        room = null; last = ""; muted = false;
        btn.textContent = "Start call"; btn.className = "";
        muteBtn.disabled = true; muteBtn.classList.remove("on");
        setState("", "Call ended - tap to start again");
      });
      await room.connect(__URL__, __TOKEN__);
      await room.localParticipant.setMicrophoneEnabled(true);
      await room.localParticipant.setAttributes({ language: current });
      btn.textContent = "End call"; btn.className = "end";
      muteBtn.disabled = false;
      setState("live", "Ready - say something");
    } catch (error) {
      room = null;
      setState("", "Error: " + error.message);
    }
    btn.disabled = false;
  };
</script>
"""


def create_session(client_id: str, language: str) -> dict:
    session_id = uuid.uuid4().hex[:8]
    room = f"{client_id}__{language}__{session_id}"
    identity = f"user-{session_id}"
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_attributes({"language": language})
        .with_grants(api.VideoGrants(room_join=True, room=room, can_update_own_metadata=True))
        .to_jwt()
    )
    return {"client_id": client_id, "language": language, "room": room, "token": token, "identity": identity}


st.set_page_config(page_title="AI Voice Assistant", layout="centered", initial_sidebar_state="expanded")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

if not LOGO_PATH.exists():
    st.error(f"Save your logo image as {LOGO_PATH} and reload.")
    st.stop()
logo_uri = "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()

with st.sidebar:
    st.header("Voice settings")
    client_id = st.selectbox("Business", list(CLIENTS), format_func=CLIENTS.get)
    language = st.radio("Speaking language", list(LANGUAGES), format_func=LANGUAGES.get)
    new_session = st.button("New session", width="stretch")

current = st.session_state.get("session", {})
if new_session or (current.get("client_id"), current.get("language")) != (client_id, language):
    st.session_state.session = create_session(client_id, language)
session = st.session_state.session

with st.sidebar:
    st.caption(f"Room: {session['room']}")

st.markdown(f"<p class='subtitle'>Talking to the assistant for {CLIENTS[client_id]}</p>", unsafe_allow_html=True)
st.iframe(
    ORB_WIDGET.replace("__URL__", json.dumps(settings.livekit_url))
    .replace("__TOKEN__", json.dumps(session["token"]))
    .replace("__LANGS__", json.dumps(LANGUAGES))
    .replace("__LANGUAGE__", json.dumps(session["language"]))
    .replace("__LOGO__", logo_uri),
    height=500,
)