import json
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from livekit import api
from config import settings
from clients import CLIENTS , LANGUAGES


CALL_WIDGET = """
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 4px; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }
  .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 4px 16px rgba(15,23,42,.08); overflow: hidden; color: #0f172a; }
  .header { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid #e2e8f0; }
  .badge { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; color: #fff; font-weight: 700; font-size: 14px; background: linear-gradient(135deg, #6366f1, #8b5cf6); flex: none; }
  .title { font-weight: 600; font-size: 15px; }
  .state { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #64748b; margin-top: 2px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; }
  .dot.live { background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,.2); }
  .dot.busy { background: #f59e0b; }
  #toggle { margin-left: auto; border: 0; border-radius: 999px; padding: 10px 22px; font-size: 14px; font-weight: 600; color: #fff; cursor: pointer; background: #16a34a; }
  #toggle.end { background: #dc2626; }
  #toggle:disabled { opacity: .6; cursor: default; }
  .langs { display: flex; gap: 8px; padding: 10px 18px; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; }
  .lang { border: 1px solid #cbd5e1; background: #fff; color: #0f172a; border-radius: 999px; padding: 6px 14px; font-size: 13px; font-weight: 500; cursor: pointer; }
  .lang.on { background: #6366f1; color: #fff; border-color: #6366f1; }
  #chat { height: 400px; overflow-y: auto; padding: 18px; background: #f8fafc; display: flex; flex-direction: column; gap: 16px; }
  .empty { margin: auto; text-align: center; color: #94a3b8; font-size: 14px; line-height: 1.6; }
  .row { display: flex; gap: 10px; align-items: flex-end; max-width: 88%; }
  .row.user { align-self: flex-end; flex-direction: row-reverse; }
  .content { min-width: 0; }
  .avatar { width: 34px; height: 34px; border-radius: 50%; display: grid; place-items: center; color: #fff; font-size: 11px; font-weight: 700; flex: none; }
  .ai .avatar { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
  .user .avatar { background: #0f766e; }
  .name { font-size: 11px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; margin-bottom: 4px; }
  .ai .name { color: #6366f1; }
  .user .name { color: #0f766e; text-align: right; }
  .bubble { padding: 10px 14px; border-radius: 16px; font-size: 14.5px; line-height: 1.5; white-space: pre-wrap; }
  .ai .bubble { background: #fff; border: 1px solid #e2e8f0; border-bottom-left-radius: 4px; }
  .user .bubble { background: #0f766e; color: #fff; border-bottom-right-radius: 4px; }
</style>

<div class="card">
  <div class="header">
    <div class="badge">AI</div>
    <div>
      <div class="title">AI Assistant</div>
      <div class="state"><span class="dot" id="dot"></span><span id="statusText">Idle</span></div>
    </div>
    <button id="toggle">Start call</button>
  </div>
  <div class="langs" id="langs"></div>
  <div id="chat">
    <div class="empty" id="empty">Press <b>Start call</b> and say hello.<br>Your conversation will appear here.</div>
  </div>
  <div id="audio"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
<script>
  const { Room, RoomEvent, Track } = LivekitClient;
  const button = document.getElementById("toggle");
  const statusEl = document.getElementById("statusText");
  const dot = document.getElementById("dot");
  const chat = document.getElementById("chat");
  const empty = document.getElementById("empty");
  const bar = document.getElementById("langs");
  const LANGS = __LANGS__;
  const messages = {};
  let current = __LANGUAGE__;
  let room = null;

  Object.entries(LANGS).forEach(([code, label]) => {
    const langButton = document.createElement("button");
    langButton.className = "lang" + (code === current ? " on" : "");
    langButton.textContent = label;
    langButton.onclick = async () => {
      current = code;
      bar.querySelectorAll(".lang").forEach((other) => other.classList.toggle("on", other === langButton));
      if (room) await room.localParticipant.setAttributes({ language: code });
    };
    bar.appendChild(langButton);
  });

  function setState(text, mode) {
    statusEl.textContent = text;
    dot.className = "dot " + (mode || "");
  }

  function showMessage(id, isUser, text) {
    if (!text.trim()) return;
    empty.style.display = "none";
    if (!messages[id]) {
      const row = document.createElement("div");
      row.className = "row " + (isUser ? "user" : "ai");
      row.innerHTML = '<div class="avatar">' + (isUser ? "You" : "AI") + '</div>' +
        '<div class="content"><div class="name">' + (isUser ? "You" : "AI Assistant") + '</div><div class="bubble" dir="auto"></div></div>';
      chat.appendChild(row);
      messages[id] = row.querySelector(".bubble");
    }
    messages[id].textContent = text;
    chat.scrollTop = chat.scrollHeight;
  }

  button.onclick = async () => {
    if (room) return room.disconnect();
    button.disabled = true;
    setState("Connecting...", "busy");
    chat.querySelectorAll(".row").forEach((row) => row.remove());
    Object.keys(messages).forEach((key) => delete messages[key]);
    try {
      room = new Room();
      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) document.getElementById("audio").appendChild(track.attach());
      });
      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        if (speakers.some((speaker) => !speaker.isLocal)) setState("AI is speaking", "live");
        else if (speakers.length) setState("Listening to you", "live");
        else setState("Connected", "live");
      });
      room.on(RoomEvent.Disconnected, () => {
        room = null;
        button.textContent = "Start call";
        button.className = "";
        setState("Call ended", "");
      });
      room.registerTextStreamHandler("lk.transcription", async (reader, participantInfo) => {
        const isUser = participantInfo.identity === __IDENTITY__;
        const attributes = reader.info.attributes || {};
        const id = attributes["lk.segment_id"] || reader.info.id;
        let text = "";
        for await (const chunk of reader) {
          text += chunk;
          showMessage(id, isUser, text);
        }
      });
      await room.connect(__URL__, __TOKEN__);
      await room.localParticipant.setMicrophoneEnabled(true);
      await room.localParticipant.setAttributes({ language: current });
      button.textContent = "End call";
      button.className = "end";
      setState("Connected", "live");
    } catch (error) {
      room = null;
      setState("Error: " + error.message, "");
    }
    button.disabled = false;
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


st.set_page_config(page_title="AI Voice Assistant", layout="centered")

with st.sidebar:
    st.header("Settings")
    client_id = st.selectbox("Business", list(CLIENTS), format_func=CLIENTS.get)
    language = st.selectbox("Starting language", list(LANGUAGES), format_func=LANGUAGES.get)
    new_session = st.button("New session", width="stretch")

current = st.session_state.get("session", {})
if new_session or (current.get("client_id"), current.get("language")) != (client_id, language):
    st.session_state.session = create_session(client_id, language)
session = st.session_state.session

with st.sidebar:
    st.caption(f"Room: {session['room']}")

st.title("AI Voice Assistant")
st.caption(f"Talking to the assistant for {CLIENTS[client_id]}")
st.iframe(
    CALL_WIDGET.replace("__URL__", json.dumps(settings.livekit_url))
    .replace("__TOKEN__", json.dumps(session["token"]))
    .replace("__IDENTITY__", json.dumps(session["identity"]))
    .replace("__LANGS__", json.dumps(LANGUAGES))
    .replace("__LANGUAGE__", json.dumps(session["language"])),
    height=620,
)


=============================



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
  .stApp { background: radial-gradient(circle at 50% 0%, #1b0f45 0%, #0A0618 60%); }
  [data-testid="stSidebar"] { background: #120a2e; border-right: 1px solid #2b1a5e; }
  [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] span { color: #EDE9FE; }
  [data-testid="stHeader"] { background: transparent; }
  .block-container { padding-top: 1.5rem; }
  .subtitle { text-align: center; color: #A78BFA; font-size: 14px; margin: 0 0 4px; }
</style>
"""

ORB_WIDGET = """
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; background: #0A0618; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; color: #EDE9FE; overflow: hidden; }
  .stage { display: flex; flex-direction: column; align-items: center; padding-top: 8px; }
  .scene { --lvl: 0; position: relative; width: 340px; height: 340px; perspective: 900px; cursor: pointer; }
  .ring { position: absolute; inset: 0; margin: auto; width: 290px; height: 290px; border-radius: 50%; border: 2px solid transparent; opacity: 0; }
  .scene.user .ring { border-color: #FF3D9A; animation: pulse 1.8s ease-out infinite; }
  .scene.ai .ring { border-color: #00E676; animation: pulse 1.8s ease-out infinite; }
  .ring.r2 { animation-delay: .6s !important; }
  .ring.r3 { animation-delay: 1.2s !important; }
  @keyframes pulse { 0% { transform: scale(1); opacity: .75; } 100% { transform: scale(1.65); opacity: 0; } }

  .float, .spin, .tilt { position: absolute; inset: 0; transform-style: preserve-3d; }
  .float { animation: float 4s ease-in-out infinite alternate; }
  @keyframes float { from { transform: translateY(6px); } to { transform: translateY(-10px); } }
  .scene.think .spin { animation: turn 2.6s linear infinite; }
  .scene.ai .spin { animation: sway 1.7s ease-in-out infinite alternate; }
  @keyframes turn { to { transform: rotateY(360deg); } }
  @keyframes sway { from { transform: rotateY(-16deg); } to { transform: rotateY(16deg); } }
  .tilt { transition: transform .15s ease-out; }

  .glass { position: absolute; left: 50%; top: 50%; width: 300px; height: 300px; margin: -150px 0 0 -150px; border-radius: 50%;
    transform: translateZ(-34px);
    background: radial-gradient(circle at 32% 28%, #5b34c9 0%, #2a1470 45%, #12082f 100%);
    box-shadow: inset 0 0 40px rgba(255,61,154,.35), 0 0 calc(40px + var(--lvl) * 110px) rgba(124,58,237,.75), 0 30px 60px rgba(0,0,0,.55); }
  .scene.ai .glass { box-shadow: inset 0 0 40px rgba(0,230,118,.25), 0 0 calc(40px + var(--lvl) * 110px) rgba(124,58,237,.8), 0 30px 60px rgba(0,0,0,.55); }
  .stack { position: absolute; inset: 0; transform-style: preserve-3d; }
  .slice { position: absolute; left: 50%; top: 50%; width: 230px; height: 230px; margin: -115px 0 0 -115px; pointer-events: none; }
  .slice.front { filter: drop-shadow(0 0 14px rgba(0,230,118,.75)); }
  .gloss { position: absolute; left: 50%; top: 50%; width: 300px; height: 300px; margin: -150px 0 0 -150px; border-radius: 50%; transform: translateZ(46px);
    background: radial-gradient(circle at 28% 22%, rgba(255,255,255,.22) 0%, rgba(255,255,255,0) 42%); pointer-events: none; }

  #state { margin-top: 6px; font-size: 20px; font-weight: 600; letter-spacing: .02em; }
  #sub { margin-top: 4px; font-size: 13px; color: #A78BFA; }
  .controls { display: flex; gap: 14px; margin-top: 18px; align-items: center; }
  #toggle { border: 0; border-radius: 999px; padding: 14px 34px; font-size: 15px; font-weight: 700; color: #fff; cursor: pointer;
    background: linear-gradient(135deg, #7C3AED, #FF3D9A); box-shadow: 0 8px 24px rgba(124,58,237,.45); }
  #toggle.end { background: #E5484D; box-shadow: 0 8px 24px rgba(229,72,77,.4); }
  #toggle:disabled { opacity: .6; cursor: default; }
  #mute { width: 48px; height: 48px; border-radius: 50%; border: 1px solid #4c2fa3; background: #1a0f40; color: #EDE9FE; font-size: 18px; cursor: pointer; }
  #mute:disabled { opacity: .35; cursor: default; }
  #mute.on { background: #FF3D9A; border-color: #FF3D9A; }
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
      im.style.transform = "translateZ(" + ((i - N / 2) * 3) + "px)";
      if (i < N - 1) im.style.filter = "brightness(" + (0.3 + 0.6 * i / (N - 1)) + ")";
      stack.appendChild(im);
    }
  });

  document.addEventListener("mousemove", (e) => {
    const x = e.clientX / window.innerWidth - 0.5, y = e.clientY / window.innerHeight - 0.5;
    tilt.style.transform = "rotateX(" + (-y * 26) + "deg) rotateY(" + (x * 34) + "deg)";
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
    height=640,
)