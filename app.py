import json

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="IICI Voice Assistant",
    page_icon="💚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

TOKEN_ENDPOINT = "https://voice-bot-demo-kdk2.onrender.com/token"

st.markdown(
    """
    <style>
      #MainMenu, footer, header { visibility: hidden; }
      .block-container { max-width: 850px; padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

APP_HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 680px; color: #effcf5;
    background: radial-gradient(ellipse at 50% 20%, #20ed8b20, transparent 42%), #07100d;
    font: 15px/1.5 Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  .card {
    min-height: 660px; padding: 28px 20px; margin: auto;
    display: flex; flex-direction: column; align-items: center; text-align: center;
    border: 1px solid #a6dcbf24; border-radius: 26px;
    background: linear-gradient(160deg, #11231bf5, #070f0bf5);
    box-shadow: 0 24px 80px #0006;
  }
  .brand { display:flex; align-items:center; gap:10px; margin-bottom:22px; }
  .brand svg { width:38px; color:#20ed8b; filter:drop-shadow(0 0 10px #20ed8b66); }
  .brand-title { text-align:left; font-size:12px; font-weight:800; letter-spacing:.18em; }
  .brand-sub { text-align:left; color:#91a99c; font-size:11px; }
  .eyebrow { color:#a4ffd0; font-size:11px; font-weight:750; letter-spacing:.16em; text-transform:uppercase; }
  h1 { margin:9px 0; font-size:clamp(29px, 6vw, 44px); letter-spacing:-.045em; line-height:1.08; }
  .intro { max-width:430px; margin:4px 0; color:#91a99c; }

  .orb { position:relative; isolation:isolate; display:grid; place-items:center;
         width:min(330px, 74vw); aspect-ratio:1; margin:14px 0 2px; perspective:900px; }
  .glow { position:absolute; inset:18%; border-radius:50%; background:#12b8662b; filter:blur(38px); transition:.4s; }
  .shell {
    position:absolute; inset:14%; border-radius:50%;
    background:radial-gradient(circle at 34% 26%, #16452f, #0c2118 46%, #050c09);
    box-shadow:inset -15px -18px 34px #000b, inset 8px 9px 24px #51ffa41f, 0 0 55px #20ed8b24;
  }
  .ring { position:absolute; inset:7%; border:1px solid #20ed8b66; border-radius:50%; opacity:0; transform:scale(.8); }
  .ring.second { inset:0; }
  .logo3d { position:relative; width:65%; aspect-ratio:400/380; transform-style:preserve-3d; animation:float 5s ease-in-out infinite; }
  .logo3d svg {
    position:absolute; inset:0; width:100%; height:100%; fill:none; stroke:currentColor;
    stroke-width:18; stroke-linejoin:miter; stroke-linecap:butt;
  }
  .logo3d svg:nth-child(1) { color:#075332; transform:translateZ(-20px); }
  .logo3d svg:nth-child(2) { color:#087343; transform:translateZ(-15px); }
  .logo3d svg:nth-child(3) { color:#0a9254; transform:translateZ(-10px); }
  .logo3d svg:nth-child(4) { color:#0db765; transform:translateZ(-5px); }
  .logo3d svg:nth-child(5) { color:#18d77c; }
  .logo3d svg:nth-child(6) { color:#47ff9d; transform:translateZ(5px); filter:drop-shadow(0 0 9px #20ed8b99); }
  .orb[data-state="connecting"] .logo3d { animation:spin 3s linear infinite; }
  .orb[data-state="listening"] .ring, .orb[data-state="speaking"] .ring { animation:pulse 2s ease-out infinite; }
  .orb[data-state="speaking"] .ring.second { animation-delay:1s; }
  .orb[data-state="speaking"] .logo3d { animation:beat .55s ease-in-out infinite alternate; }
  .orb[data-state="speaking"] .glow { transform:scale(1.3); }
  @keyframes float { 50% { transform:translateY(-7px) rotateY(5deg); } }
  @keyframes spin { to { transform:rotateY(360deg); } }
  @keyframes beat { to { transform:scale(1.08) rotateY(8deg); } }
  @keyframes pulse { to { opacity:0; transform:scale(1.35); } }

  .language { display:grid; gap:6px; margin:0 0 13px; text-align:left; }
  .language label { color:#91a99c; font-size:11px; font-weight:750; letter-spacing:.12em; text-transform:uppercase; }
  select {
    min-width:215px; padding:10px 13px; color:#effcf5; background:#102019;
    border:1px solid #a6dcbf26; border-radius:12px; font:inherit;
  }
  .status { min-height:28px; display:flex; align-items:center; gap:9px; color:#a4ffd0; font-weight:650; }
  .dot { width:8px; height:8px; border-radius:50%; background:#718078; }
  .dot.connected, .dot.listening, .dot.speaking { background:#20ed8b; box-shadow:0 0 0 5px #20ed8b20; }
  .dot.connecting { background:#ffc96b; }
  .dot.error { background:#ff7575; }
  button {
    min-width:220px; margin-top:15px; padding:13px 22px; border:0; border-radius:999px;
    color:#032012; font:inherit; font-weight:800; cursor:pointer;
    background:linear-gradient(135deg,#5dffad,#16cf73); box-shadow:0 10px 32px #20ed8b33;
  }
  button.end { color:white; background:linear-gradient(135deg,#ef7777,#c73e4e); }
  button:disabled { opacity:.65; cursor:wait; }
  .hint { max-width:390px; margin:12px 0 0; color:#91a99c; font-size:12px; }
  #audio { position:fixed; left:-10px; width:1px; height:1px; overflow:hidden; }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation:none !important; } }
</style>
</head>
<body>
<svg aria-hidden="true" style="position:absolute;width:0;height:0">
  <symbol id="mark" viewBox="0 0 400 380">
    <path d="M162 48V90H200 M192 56H240V92H272 M90 92H132V125H172 M302 92V135H268
      M92 120V168 M232 122V165H195 M125 160H165V195 M340 160H300V190H265
      M55 160V200H100 M135 195H92 M232 195V235H275 M338 195V235H300V268
      M55 232H100 M125 232V275H90V300 M160 232H200V268 M195 262V300H232
      M232 262H265V300H305 M125 300H165V335H200"/>
  </symbol>
</svg>

<main class="card">
  <div class="brand">
    <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
    <div><div class="brand-title">IICI VOICE</div><div class="brand-sub">A thoughtful clinic assistant</div></div>
  </div>
  <div class="eyebrow">IICI Clinic · Islamabad</div>
  <h1>Care, in your language.</h1>
  <p class="intro">Talk naturally with the clinic’s voice assistant.</p>

  <div class="orb" id="orb" data-state="idle" aria-hidden="true">
    <span class="glow"></span><span class="ring"></span><span class="ring second"></span><span class="shell"></span>
    <div class="logo3d">
      <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
      <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
      <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
      <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
      <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
      <svg viewBox="0 0 400 380"><use href="#mark"></use></svg>
    </div>
  </div>

  <div class="language">
    <label for="language">Conversation language</label>
    <select id="language">
      <option value="en">English</option>
      <option value="ur">اردو (Urdu)</option>
      <option value="id">Bahasa Indonesia</option>
    </select>
  </div>
  <div class="status" aria-live="polite">
    <span class="dot" id="dot"></span><span id="status">Ready to connect</span>
  </div>
  <button id="call" type="button">Start conversation</button>
  <p class="hint">Allow microphone access when prompted. You can ask the assistant to switch languages during the call.</p>
  <div id="audio"></div>
</main>

<script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
<script>
  const TOKEN_ENDPOINT = __TOKEN_ENDPOINT__;
  const { Room, RoomEvent, Track } = LivekitClient;
  const button = document.getElementById("call");
  const language = document.getElementById("language");
  const statusText = document.getElementById("status");
  const dot = document.getElementById("dot");
  const orb = document.getElementById("orb");
  const audio = document.getElementById("audio");
  let room = null;

  function setStatus(text, state) {
    statusText.textContent = text;
    dot.className = "dot " + state;
    orb.dataset.state = state;
  }

  function resetCall(text) {
    room = null;
    audio.replaceChildren();
    button.disabled = false;
    button.textContent = "Start conversation";
    button.classList.remove("end");
    language.disabled = false;
    setStatus(text, "idle");
  }

  button.addEventListener("click", async () => {
    if (room) {
      const currentRoom = room;
      button.disabled = true;
      setStatus("Ending conversation…", "connecting");
      await currentRoom.disconnect();
      resetCall("Call ended");
      return;
    }

    button.disabled = true;
    language.disabled = true;
    button.textContent = "Connecting…";
    setStatus("Connecting to the assistant…", "connecting");

    let newRoom = null;
    try {
      const query = new URLSearchParams({ client_id: "iici", language: language.value });
      const response = await fetch(TOKEN_ENDPOINT + "?" + query.toString());
      if (!response.ok) throw new Error("Token service returned HTTP " + response.status);

      const session = await response.json();
      if (!session.token || !session.url) throw new Error("Token response is missing the LiveKit URL or token.");

      newRoom = new Room({ adaptiveStream: true, dynacast: true });
      room = newRoom;

      newRoom.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          const element = track.attach();
          element.autoplay = true;
          element.playsInline = true;
          audio.appendChild(element);
        }
      });
      newRoom.on(RoomEvent.TrackUnsubscribed, (track) => track.detach().forEach((element) => element.remove()));

      newRoom.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const agentSpeaking = speakers.some((speaker) => speaker.identity !== newRoom.localParticipant.identity);
        const userSpeaking = speakers.some((speaker) => speaker.identity === newRoom.localParticipant.identity);
        if (agentSpeaking) setStatus("Assistant speaking", "speaking");
        else if (userSpeaking) setStatus("Listening to you", "listening");
        else setStatus("Connected · speak when ready", "connected");
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        if (room === newRoom) resetCall("Call ended");
      });

      await newRoom.connect(session.url, session.token);
      await newRoom.localParticipant.setMicrophoneEnabled(true);
      button.disabled = false;
      button.textContent = "End conversation";
      button.classList.add("end");
      setStatus("Connected · speak when ready", "connected");
    } catch (error) {
      if (newRoom) {
        room = null;
        try { await newRoom.disconnect(); }
        catch (disconnectError) { console.error("Disconnect failed:", disconnectError); }
      }
      resetCall(error instanceof Error ? error.message : "Could not connect.");
    }
  });
</script>
</body>
</html>
"""

APP_HTML = APP_HTML.replace("__TOKEN_ENDPOINT__", json.dumps(TOKEN_ENDPOINT))
components.html(APP_HTML, height=720, scrolling=False)