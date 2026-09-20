/* ============================================
   Health Dashboard — app.js
   Main application logic, data loading, charts
   ============================================ */

// ========== DOM References ==========
const navBtns = document.querySelectorAll('.nav-btn');
const panels = document.querySelectorAll('.panel');
const chatPanel = document.getElementById('chat-panel');
const toggleChatBtn = document.getElementById('toggle-chat');
const closeChatBtn = document.getElementById('chat-close');
const chatArea = document.getElementById('chat');
const orb = document.getElementById('orb');
const statusText = document.getElementById('statusText');
const headerDate = document.getElementById('header-date');
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.getElementById('sidebar');

// ========== State ==========
let profileData = null;
let vitalsData = null;
let sessionData = null;
let alertsData = null;
let chartsInitialized = false;

// ========== UI strings ==========
// Dynamically-inserted UI text (static text lives directly in index.html).
const STR = {
  'status.idle':       'Tap to start',
  'status.listening':  '🟢 Listening... go ahead',
  'status.thinking':   '🤔 Processing your answer...',
  'status.speaking':   '🔊 Assistant is replying...',
  'status.connectFail':'Cannot connect to Audio Agent (port 8000)',
  'status.connError':  'Audio Agent connection error',
  'status.micError':   'Microphone access error: ',
  'status.audioFail':  "Couldn't play audio (browser autoplay blocked?): ",
  'transcript.hint':   'Listening... say something',
  'transcript.you':    'You:',
  'gender.male':       'Male',
  'gender.female':     'Female',
  'gender.other':      'Other',
  'act.steps':         'Steps',
  'act.activeMin':     'Active min',
  'act.cal':           'Calories',
  'hyp.awake':         'Awake',
  'hyp.light':         'Light',
  'hyp.deep':          'Deep',
  'zone.warmUp':       'Warm-up',
  'zone.fatBurn':      'Fat burn',
  'unit.min':          'min',
  'chat.cleared':      'Conversation cleared. Tap the orb to talk again.',
};

function t(key) { return STR[key] ?? key; }

// ========== Init ==========
document.addEventListener('DOMContentLoaded', async () => {
  setHeaderDate();
  await loadAllData();
  setupNavigation();
  setupChat();
  setupSidebar();
  renderOverview();
  renderProfile();
  animateNumbers();
});

// ========== Date ==========
function setHeaderDate() {
  const now = new Date();
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  headerDate.textContent = now.toLocaleDateString('en-US', options);
}

// ========== AWS Cloud Configuration ==========
const AWS_API_ENDPOINT = window.AWS_API_ENDPOINT || localStorage.getItem('AWS_API_ENDPOINT') || '';

// ========== Data Loading ==========
async function loadAllData() {
  try {
    const [profile, vitals, session, alerts] = await Promise.all([
      fetch('data/user_profile.json').then(r => r.json()),
      fetch('data/daily_vitals.json').then(r => r.json()),
      fetch('data/active_session.json').then(r => r.json()),
      fetch('data/assistant_alerts.json').then(r => r.json())
    ]);
    profileData = profile;
    vitalsData = vitals;
    sessionData = session;
    alertsData = alerts;

    // Optional: Fetch live vitals if AWS API Gateway endpoint is provided
    if (AWS_API_ENDPOINT) {
      try {
        const liveRes = await fetch(`${AWS_API_ENDPOINT}/vitals/latest?user_id=${profile.metadata?.user_id || 'user-hdung-001'}`);
        if (liveRes.ok) {
          const liveJson = await liveRes.json();
          if (liveJson.data && liveJson.data.vitals) {
            console.log('Synchronized live data from AWS Cloud:', liveJson.data);
            if (liveJson.data.vitals.heart_rate) vitalsData.daily_summary.resting_heart_rate_bpm = liveJson.data.vitals.heart_rate;
            if (liveJson.data.vitals.spo2) vitalsData.daily_summary.average_blood_oxygen_pct = liveJson.data.vitals.spo2;
            document.getElementById('agent-status-text').textContent = 'ONLINE (AWS LIVE)';
          }
        }
      } catch (awsErr) {
        console.warn('AWS API Gateway connection notice:', awsErr.message);
      }
    } else {
      document.getElementById('agent-status-text').textContent = 'ONLINE';
    }

    document.getElementById('agent-status-dot').style.background = 'var(--success)';
  } catch (e) {
    console.error('Error loading data:', e);
    document.getElementById('agent-status-text').textContent = 'DATA ERROR';
    document.getElementById('agent-status-dot').style.background = 'var(--danger)';
  }
}


// ========== Navigation ==========
function setupNavigation() {
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.panel;
      navBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      panels.forEach(p => p.classList.remove('active'));
      document.getElementById(`panel-${target}`).classList.add('active');

      // Lazy render
      if (target === 'sleep' && !document.getElementById('chart-eeg')._rendered) renderSleep();
      if (target === 'vitals' && !document.getElementById('chart-spo2')._rendered) renderVitals();
      if (target === 'alerts' && !document.getElementById('alerts-container')._rendered) renderAlerts();

      // Close sidebar on mobile
      if (window.innerWidth <= 900) sidebar.classList.remove('open');
    });
  });
}

// ========== Sidebar ==========
function setupSidebar() {
  menuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  // Click outside to close on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 900 && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && e.target !== menuToggle && !menuToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    }
  });
}

// ========== Chat Panel + Audio Agent Integration ==========
const AGENT_WS_URL = (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.host + '/ws';

// Audio Agent state
let agentWs = null;
let agentAudioCtx = null;
let agentMicStream = null;
let agentWorkletNode = null;
let agentRunning = false;
let outputAudioCtx = null;
let nextStartTime = 0;
let activeSources = [];
let shouldTransitionToListening = false;
let lastBubble = null;
let lastWho = null;

function setupChat() {
  toggleChatBtn.addEventListener('click', () => {
    chatPanel.classList.toggle('open');
    toggleChatBtn.classList.toggle('active');
  });
  closeChatBtn.addEventListener('click', () => {
    chatPanel.classList.remove('open');
    toggleChatBtn.classList.remove('active');
  });

  // Reset button
  const resetBtn = document.getElementById('chat-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      clearAgentHistory();
    });
  }

  // Orb: toggle voice agent
  orb.addEventListener('click', () => {
    agentRunning ? stopAgent() : startAgent();
  });
}

// Build the English system instruction with health context from loaded data.
function buildSystemInstruction() {
  let prompt = 'You are an extremely friendly, warm health assistant that answers briefly (at most 2-3 sentences). '
    + 'You answer questions about the user\'s vital signs and health. '
    + 'Always reply in English. No markdown, emoji or lists, since the reply will be read aloud.\n\n';

  // Inject health data context
  if (profileData) {
    const d = profileData.demographics;
    const bl = profileData.physiological_baselines;
    const gender = d.gender === 'male' ? 'male' : 'female';
    prompt += `User profile: ${d.age} years old, ${gender}, ${d.height_cm}cm, ${d.weight_kg}kg, `
      + `BMI=${d.calculated_metrics.bmi}, BMR=${d.calculated_metrics.bmr_kcal}kcal. `
      + `Average resting heart rate=${bl.resting_heart_rate.avg}bpm, max heart rate=${bl.max_heart_rate}bpm, `
      + `baseline blood pressure=${bl.blood_pressure_baseline.systolic}/${bl.blood_pressure_baseline.diastolic}mmHg.\n`;
  }

  if (vitalsData) {
    const s = vitalsData.daily_summary;
    prompt += `Today's vitals: resting heart rate=${s.resting_heart_rate_bpm}bpm, `
      + `average blood pressure=${s.average_blood_pressure.systolic}/${s.average_blood_pressure.diastolic}mmHg, `
      + `average SpO2=${s.average_blood_oxygen_pct}%, sleep score=${s.sleep_summary.sleep_score}/100, `
      + `sleep duration=${s.sleep_summary.total_sleep_hours}h. `
      + `Activity: ${vitalsData.activities.steps} steps, ${vitalsData.activities.active_minutes} min, `
      + `${vitalsData.activities.calories_burned_kcal}kcal.\n`;
  }

  if (sessionData && sessionData.summary_insights) {
    const insights = sessionData.summary_insights;
    if (insights.ai_summary_bullets && insights.ai_summary_bullets.length > 0) {
      prompt += 'AI analysis: ' + `${insights.ai_summary_bullets.join('. ')}.\n`;
    }
    if (insights.alerts && insights.alerts.length > 0) {
      prompt += 'Alerts: ' + `${insights.alerts.map(a => a.message).join('. ')}.\n`;
    }
  }

  if (alertsData && alertsData.proactive_alerts) {
    const active = alertsData.proactive_alerts.filter(a => a.call_status !== 'resolved');
    if (active.length > 0) {
      prompt += 'Proactive alerts: ' + `${active.map(a => a.alert_text).join('. ')}.\n`;
    }
  }

  return prompt;
}

// AudioWorklet processor: downsample mic audio to 16kHz PCM16
const WORKLET_CODE = `
class DS extends AudioWorkletProcessor {
  constructor(){ super(); this.ratio = sampleRate/16000; this.buf=[]; this.pos=0; }
  process(inputs){
    const ch = inputs[0][0]; if(!ch) return true;
    for(let i=0;i<ch.length;i++) this.buf.push(ch[i]);
    const out=[];
    while(Math.floor(this.pos) < this.buf.length){ out.push(this.buf[Math.floor(this.pos)]); this.pos+=this.ratio; }
    const consumed=Math.floor(this.pos); this.buf=this.buf.slice(consumed); this.pos-=consumed;
    if(out.length){
      const i16=new Int16Array(out.length);
      for(let i=0;i<out.length;i++){ let s=Math.max(-1,Math.min(1,out[i])); i16[i]=s<0?s*0x8000:s*0x7fff; }
      this.port.postMessage(i16.buffer,[i16.buffer]);
    }
    return true;
  }
}
registerProcessor('ds', DS);`;

async function startAgent() {
  // Stop any existing playback
  stopAgentPlayback();

  try {
    agentMicStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    });
  } catch (e) {
    statusText.textContent = t('status.micError') + e.message;
    return;
  }

  // Build the English system instruction with health context
  const systemInstruction = buildSystemInstruction();

  // Connect WebSocket to audio agent server
  agentWs = new WebSocket(AGENT_WS_URL
    + '?system_instruction=' + encodeURIComponent(systemInstruction));
  agentWs.binaryType = 'arraybuffer';
  agentWs.onmessage = onAgentMessage;
  agentWs.onclose = () => { if (agentRunning) stopAgent(); };
  agentWs.onerror = (e) => {
    console.error('WebSocket error:', e);
    statusText.textContent = t('status.connError');
    setConnectionBadge(false);
  };

  try {
    await new Promise((resolve, reject) => {
      agentWs.onopen = resolve;
      setTimeout(() => reject(new Error('timeout')), 5000);
    });
  } catch (e) {
    statusText.textContent = t('status.connectFail');
    if (agentMicStream) agentMicStream.getTracks().forEach(tr => tr.stop());
    return;
  }

  // Set up AudioWorklet for mic downsampling
  agentAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (agentAudioCtx.state === 'suspended') {
    await agentAudioCtx.resume();
  }
  const blobURL = URL.createObjectURL(new Blob([WORKLET_CODE], { type: 'application/javascript' }));
  await agentAudioCtx.audioWorklet.addModule(blobURL);

  const src = agentAudioCtx.createMediaStreamSource(agentMicStream);
  agentWorkletNode = new AudioWorkletNode(agentAudioCtx, 'ds');
  agentWorkletNode.port.onmessage = (e) => {
    if (agentWs && agentWs.readyState === 1) agentWs.send(e.data);
  };
  src.connect(agentWorkletNode);

  // Connect to silent sink to keep processing loop running
  const sink = agentAudioCtx.createGain();
  sink.gain.value = 0;
  agentWorkletNode.connect(sink);
  sink.connect(agentAudioCtx.destination);

  agentRunning = true;
  setConnectionBadge(true);
  setOrbState('listening');

  // Show live transcript box and set placeholder
  const transBox = document.getElementById('live-transcript');
  if (transBox) {
    transBox.style.display = 'flex';
    transBox.innerHTML = '<span style="opacity: 0.6;"><i class="fa-solid fa-ear-hearing" style="margin-right: 6px;"></i>' + t('transcript.hint') + '</span>';
  }
}

function stopAgent() {
  agentRunning = false;
  setOrbState('idle');
  setConnectionBadge(false);

  if (agentWorkletNode) agentWorkletNode.disconnect();
  if (agentAudioCtx) agentAudioCtx.close();
  if (agentMicStream) agentMicStream.getTracks().forEach(tr => tr.stop());
  if (agentWs && agentWs.readyState === 1) agentWs.close();

  stopAgentPlayback();
  agentWs = agentAudioCtx = agentMicStream = agentWorkletNode = null;
  lastWho = null;
  lastBubble = null;

  // Hide live transcript box
  const transBox = document.getElementById('live-transcript');
  if (transBox) {
    transBox.style.display = 'none';
    transBox.textContent = '';
  }
}

function stopAgentPlayback() {
  activeSources.forEach(src => {
    try { src.stop(); } catch (e) {}
  });
  activeSources = [];
  nextStartTime = 0;
  shouldTransitionToListening = false;
}

function playPCMChunk(base64Audio) {
  if (!agentAudioCtx) return;
  const ctx = agentAudioCtx;
  if (ctx.state === 'suspended') ctx.resume();

  try {
    const raw = window.atob(base64Audio);
    const len = raw.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = raw.charCodeAt(i);

    const numSamples = len / 2;
    const f32 = new Float32Array(numSamples);
    const view = new DataView(bytes.buffer);
    for (let i = 0; i < numSamples; i++) {
      f32[i] = view.getInt16(i * 2, true) / 32768.0;
    }

    const audioBuf = ctx.createBuffer(1, numSamples, 24000);
    audioBuf.copyToChannel(f32, 0);

    const source = ctx.createBufferSource();
    source.buffer = audioBuf;
    source.connect(ctx.destination);

    const now = ctx.currentTime;
    if (nextStartTime < now) nextStartTime = now + 0.01;
    source.start(nextStartTime);
    activeSources.push(source);

    source.onended = () => {
      activeSources = activeSources.filter(s => s !== source);
      if (activeSources.length === 0) {
        if (shouldTransitionToListening) {
          shouldTransitionToListening = false;
          setOrbState('listening');
        } else if (orb.classList.contains('speaking')) {
          // Fallback: if all audio finished playing and we are still in speaking state,
          // go back to listening after a tiny safety delay to allow any late chunks.
          setTimeout(() => {
            if (activeSources.length === 0 && orb.classList.contains('speaking')) {
              setOrbState('listening');
            }
          }, 150);
        }
      }
    };

    nextStartTime += audioBuf.duration;
  } catch (err) {
    console.error('Error playing audio chunk:', err);
  }
}

// Add chat bubble
function addAgentBubble(text, who) {
  const d = document.createElement('div');
  d.className = `chat-bubble ${who === 'user' ? 'user-bubble' : 'bot-bubble'}`;
  const icon = who === 'user'
    ? '<i class="fa-solid fa-user" style="margin-right:6px; opacity:0.7"></i>'
    : '<i class="fa-solid fa-robot" style="margin-right:6px; color:var(--primary)"></i>';
  d.innerHTML = `${icon}<span></span>`;
  d.querySelector('span').textContent = text;
  chatArea.appendChild(d);
  chatArea.scrollTop = chatArea.scrollHeight;
  return d;
}

// Handle streaming text chunks (append to existing bubble or create new)
function handleTextChunk(text, who) {
  if (lastWho === who && lastBubble) {
    const span = lastBubble.querySelector('span');
    span.textContent += text;
    chatArea.scrollTop = chatArea.scrollHeight;
  } else {
    lastBubble = addAgentBubble(text, who);
    lastWho = who;
  }
}

// Set orb visual state
function setOrbState(s) {
  orb.className = 'mic-orb';
  const transBox = document.getElementById('live-transcript');

  if (s === 'listening') {
    orb.classList.add('listening');
    orb.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    statusText.textContent = t('status.listening');
    
    // Automatically show/reset the transcript box for the next turn
    if (transBox && agentRunning) {
      transBox.style.display = 'flex';
      transBox.innerHTML = '<span style="opacity: 0.6;"><i class="fa-solid fa-ear-hearing" style="margin-right: 6px;"></i>' + t('transcript.hint') + '</span>';
    }
  } else if (s === 'thinking') {
    orb.classList.add('thinking');
    orb.innerHTML = '<i class="fa-solid fa-arrows-spin fa-spin"></i>';
    statusText.textContent = t('status.thinking');
  } else if (s === 'speaking') {
    orb.classList.add('speaking');
    orb.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
    statusText.textContent = t('status.speaking');
    
    // Hide transcript box when agent is talking
    if (transBox) transBox.style.display = 'none';
  } else {
    orb.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    statusText.textContent = t('status.idle');
    
    // Hide and clear transcript box on disconnect/idle
    if (transBox) {
      transBox.style.display = 'none';
      transBox.textContent = '';
    }
  }
}

// Set connection badge
function setConnectionBadge(connected) {
  const badge = document.getElementById('chat-connection-badge');
  const text = document.getElementById('chat-connection-text');
  if (!badge || !text) return;
  if (connected) {
    badge.className = 'chat-connection-badge connected';
    text.textContent = 'Live';
  } else {
    badge.className = 'chat-connection-badge disconnected';
    text.textContent = 'Offline';
  }
}

// Handle messages from audio agent WebSocket
function onAgentMessage(ev) {
  const m = JSON.parse(ev.data);

  if (m.type === 'state') {
    if (m.value === 'listening') {
      if (activeSources.length > 0) {
        shouldTransitionToListening = true;
      } else {
        setOrbState('listening');
      }
    } else {
      setOrbState(m.value);
    }
  } else if (m.type === 'user') {
    addAgentBubble(m.text, 'user');
    lastWho = null;
    lastBubble = null;
  } else if (m.type === 'bot') {
    addAgentBubble(m.text, 'bot');
    lastWho = null;
    lastBubble = null;
  } else if (m.type === 'user_chunk') {
    handleTextChunk(m.text, 'user');
    setOrbState('listening');
    shouldTransitionToListening = false;

    // Update live transcript box
    const transBox = document.getElementById('live-transcript');
    if (transBox) {
      transBox.style.display = 'flex';
      transBox.innerHTML = `<span style="font-weight: 600; color: var(--primary-light);"><i class="fa-solid fa-microphone" style="margin-right: 6px; color: var(--success)"></i>${t('transcript.you')}</span> <span style="margin-left: 5px;">"${m.text}"</span>`;
    }
  } else if (m.type === 'bot_chunk') {
    handleTextChunk(m.text, 'bot');
    setOrbState('speaking');

    // Hide live transcript box when agent starts speaking
    const transBox = document.getElementById('live-transcript');
    if (transBox) transBox.style.display = 'none';
  } else if (m.type === 'interrupt') {
    stopAgentPlayback();
    lastWho = null;
    lastBubble = null;
    setOrbState('listening');

    // Hide live transcript box on interrupt
    const transBox = document.getElementById('live-transcript');
    if (transBox) transBox.style.display = 'none';
  } else if (m.type === 'audio') {
    // Full audio response (non-realtime mode)
    stopAgentPlayback();
    const player = new Audio(`data:${m.mime};base64,${m.data}`);
    player.play().catch(e => {
      console.warn('Audio playback error:', e);
      statusText.textContent = t('status.audioFail') + e.message;
    });
  } else if (m.type === 'audio_chunk') {
    // Realtime PCM audio chunk from Gemini Live
    playPCMChunk(m.data);
    setOrbState('speaking');

    // Hide live transcript box when agent starts speaking
    const transBox = document.getElementById('live-transcript');
    if (transBox) transBox.style.display = 'none';
  } else if (m.type === 'error') {
    addAgentBubble('Lỗi: ' + m.text, 'bot');
    setOrbState('idle');

    // Hide live transcript box on error
    const transBox = document.getElementById('live-transcript');
    if (transBox) transBox.style.display = 'none';
  }
}

// Clear chat history and reset WebSocket
function clearAgentHistory() {
  stopAgentPlayback();
  if (agentWs && agentWs.readyState === 1) {
    agentWs.send('reset');
  }
  chatArea.innerHTML = '<div class="meta-info"><i class="fa-solid fa-clock-rotate-left" style="margin-right:6px"></i> ' + t('chat.cleared') + '</div>';
  lastWho = null;
  lastBubble = null;
}

// ========== Render Profile ==========
function renderProfile() {
  if (!profileData) return;
  const d = profileData.demographics;
  const genderText = d.gender === 'male' ? t('gender.male') : d.gender === 'female' ? t('gender.female') : t('gender.other');
  document.getElementById('profile-name').textContent = `User ${profileData.metadata.user_id.split('-').pop()}`;
  document.getElementById('profile-meta').textContent = `${d.age} tuổi · ${genderText} · ${d.height_cm}cm / ${d.weight_kg}kg`;
  document.getElementById('stat-bmi').textContent = d.calculated_metrics.bmi.toFixed(1);
  document.getElementById('stat-bmr').textContent = `${d.calculated_metrics.bmr_kcal} kcal`;
  document.getElementById('stat-maxhr').textContent = `${profileData.physiological_baselines.max_heart_rate} bpm`;
  const bp = profileData.physiological_baselines.blood_pressure_baseline;
  document.getElementById('stat-bp').textContent = `${bp.systolic}/${bp.diastolic}`;
}

// ========== Render Overview ==========
function renderOverview() {
  if (!vitalsData || !sessionData) return;

  // Quick stats
  const hrLog = vitalsData.heart_rate_log;
  const latestHR = hrLog[hrLog.length - 1].bpm;
  document.getElementById('ov-hr').textContent = latestHR;

  const bp = vitalsData.daily_summary.average_blood_pressure;
  document.getElementById('ov-bp').textContent = `${bp.systolic}/${bp.diastolic}`;

  document.getElementById('ov-spo2').textContent = vitalsData.daily_summary.average_blood_oxygen_pct;
  document.getElementById('ov-sleep').textContent = vitalsData.daily_summary.sleep_summary.sleep_score;

  // HR Daily Chart
  renderHRDailyChart();

  // Activity Doughnut
  renderActivityChart();

  // AI Insights
  renderInsights();
}

// ========== Chart: HR Daily ==========
function renderHRDailyChart() {
  const ctx = document.getElementById('chart-hr-daily').getContext('2d');
  const hrLog = vitalsData.heart_rate_log;
  const labels = hrLog.map(d => {
    const t = new Date(d.timestamp);
    return `${t.getHours()}:${String(t.getMinutes()).padStart(2, '0')}`;
  });
  const data = hrLog.map(d => d.bpm);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'BPM',
        data,
        borderColor: '#f87171',
        backgroundColor: (ctx) => {
          const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.height);
          gradient.addColorStop(0, 'rgba(248, 113, 113, 0.3)');
          gradient.addColorStop(1, 'rgba(248, 113, 113, 0)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#f87171',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 20, 35, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          titleFont: { family: 'Plus Jakarta Sans', weight: '600' },
          bodyFont: { family: 'Plus Jakarta Sans' }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' }, maxTicksLimit: 12 }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' } },
          min: 40,
          suggestedMax: 100
        }
      }
    }
  });
}

// ========== Chart: Activity Doughnut ==========
function renderActivityChart() {
  const ctx = document.getElementById('chart-activity').getContext('2d');
  const a = vitalsData.activities;
  const goalSteps = 10000;
  const goalMinutes = 60;
  const goalCal = 2500;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: [t('act.steps'), t('act.activeMin'), t('act.cal')],
      datasets: [{
        data: [
          Math.min((a.steps / goalSteps) * 100, 100),
          Math.min((a.active_minutes / goalMinutes) * 100, 100),
          Math.min((a.calories_burned_kcal / goalCal) * 100, 100)
        ],
        backgroundColor: ['#6366f1', '#10b981', '#f59e0b'],
        borderWidth: 0,
        borderRadius: 6,
        spacing: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 20, 35, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.raw.toFixed(0)}%`
          }
        }
      }
    }
  });

  // Activity stats below chart
  const statsEl = document.getElementById('activity-stats');
  statsEl.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="display:flex;align-items:center;gap:6px"><span style="width:8px;height:8px;border-radius:50%;background:#6366f1;display:inline-block"></span> ${t('act.steps')}</span>
      <span style="font-weight:700">${a.steps.toLocaleString()} / ${goalSteps.toLocaleString()}</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="display:flex;align-items:center;gap:6px"><span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block"></span> ${t('act.activeMin')}</span>
      <span style="font-weight:700">${a.active_minutes} / ${goalMinutes}</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="display:flex;align-items:center;gap:6px"><span style="width:8px;height:8px;border-radius:50%;background:#f59e0b;display:inline-block"></span> ${t('act.cal')}</span>
      <span style="font-weight:700">${a.calories_burned_kcal.toLocaleString()} / ${goalCal.toLocaleString()}</span>
    </div>
  `;
}

// ========== AI Insights ==========
function renderInsights() {
  const list = document.getElementById('insight-list');
  if (!sessionData) return;
  sessionData.summary_insights.ai_summary_bullets.forEach(text => {
    const li = document.createElement('li');
    li.innerHTML = `<i class="fa-solid fa-sparkles"></i><span>${text}</span>`;
    list.appendChild(li);
  });
}

// ========== Render Sleep Panel ==========
function renderSleep() {
  document.getElementById('chart-eeg')._rendered = true;

  // EEG Chart
  const ctx = document.getElementById('chart-eeg').getContext('2d');
  const eeg = sessionData.eeg_series;
  const labels = eeg.map(d => d.timestamp);

  const makeDataset = (label, key, color) => ({
    label,
    data: eeg.map(d => d[key]),
    borderColor: color,
    backgroundColor: 'transparent',
    tension: 0.4,
    borderWidth: 2,
    pointRadius: 3,
    pointBackgroundColor: color,
    pointHoverRadius: 6
  });

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        makeDataset('Alpha', 'alpha', '#10b981'),
        makeDataset('Beta', 'beta', '#f59e0b'),
        makeDataset('Theta', 'theta', '#6366f1'),
        makeDataset('Delta', 'delta', '#8b5cf6')
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: {
            color: '#9ca3af',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 20, 35, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' } },
          min: 0,
          max: 0.7
        }
      }
    }
  });

  // Sleep Distribution Doughnut
  const distCtx = document.getElementById('chart-sleep-dist').getContext('2d');
  const dist = sessionData.cognitive_states.state_distribution;

  new Chart(distCtx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(dist),
      datasets: [{
        data: Object.values(dist).map(v => (v * 100).toFixed(1)),
        backgroundColor: ['#ef4444', '#3b82f6', '#6366f1', '#8b5cf6'],
        borderWidth: 0,
        borderRadius: 6,
        spacing: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#9ca3af',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 12
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 20, 35, 0.95)',
          callbacks: { label: (c) => `${c.label}: ${c.raw}%` }
        }
      }
    }
  });

  // Sleep Timeline
  renderHypnogram();

  // Sleep Vitals Chart
  renderSleepVitals();
}

// ========== Samsung Health-Style Hypnogram ==========
function renderHypnogram() {
  const canvas = document.getElementById('canvas-hypnogram');
  const wrapper = document.getElementById('hypnogram-wrapper');
  const dpr = window.devicePixelRatio || 1;

  // Size canvas to wrapper
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;
  const padTop = 16;
  const padBottom = 32; // room for time labels
  const padLeft = 4;
  const padRight = 12;
  const chartW = W - padLeft - padRight;
  const chartH = H - padTop - padBottom;

  const blocks = sessionData.cognitive_states.state_blocks;
  const totalDuration = blocks.reduce((s, b) => s + b.duration_seconds, 0);

  // Map states to Y levels: Awake=0, REM=1, Light=2, Deep=3
  const stateLevel = { 'Awake': 0, 'REM': 1, 'Light': 2, 'Deep': 3 };
  const stateColors = {
    'Awake': '#fb923c',  // orange
    'REM':   '#a78bfa',  // purple
    'Light': '#60a5fa',  // blue
    'Deep':  '#6366f1'   // indigo
  };
  const stateFillColors = {
    'Awake': 'rgba(251, 146, 60, 0.25)',
    'REM':   'rgba(167, 139, 250, 0.35)',
    'Light': 'rgba(96, 165, 250, 0.30)',
    'Deep':  'rgba(99, 102, 241, 0.45)'
  };

  const levelCount = 4;
  const levelH = chartH / (levelCount - 1); // height per level step

  function yForLevel(level) {
    return padTop + level * levelH;
  }

  function xForTime(elapsedSec) {
    return padLeft + (elapsedSec / totalDuration) * chartW;
  }

  // Draw horizontal grid lines (one per level)
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
  ctx.lineWidth = 1;
  for (let i = 0; i < levelCount; i++) {
    const y = yForLevel(i);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(W - padRight, y);
    ctx.stroke();
  }

  // Build step points: each block has a start-x/y and end-x/y (horizontal flat)
  let elapsed = 0;
  const steps = []; // { x1, x2, y, state }

  blocks.forEach(block => {
    const level = stateLevel[block.state] ?? 2;
    const x1 = xForTime(elapsed);
    const x2 = xForTime(elapsed + block.duration_seconds);
    const y = yForLevel(level);
    steps.push({ x1, x2, y, state: block.state });
    elapsed += block.duration_seconds;
  });

  const bottomY = yForLevel(3) + 4;
  const R = 8; // corner radius for softened transitions

  // Helper: trace the step path with rounded corners using arcTo
  function traceStepPath(c) {
    c.moveTo(steps[0].x1, steps[0].y);
    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      if (i === 0) {
        // First block: just go horizontal
        c.lineTo(s.x2, s.y);
      } else {
        const prev = steps[i - 1];
        // Vertical transition from prev.y to s.y at x = s.x1, then horizontal
        // Use arcTo for rounded corner at top and bottom of the vertical
        c.arcTo(s.x1, prev.y, s.x1, s.y, R);
        c.arcTo(s.x1, s.y, s.x2, s.y, R);
        c.lineTo(s.x2, s.y);
      }
    }
  }

  // 1. Draw per-segment colored fills under the step line
  elapsed = 0;
  steps.forEach(s => {
    const segGrad = ctx.createLinearGradient(0, s.y, 0, bottomY);
    segGrad.addColorStop(0, stateFillColors[s.state] || 'rgba(255,255,255,0.03)');
    segGrad.addColorStop(1, 'transparent');

    ctx.fillStyle = segGrad;
    ctx.globalAlpha = 0.5;
    ctx.beginPath();
    ctx.moveTo(s.x1, s.y);
    ctx.lineTo(s.x2, s.y);
    ctx.lineTo(s.x2, bottomY);
    ctx.lineTo(s.x1, bottomY);
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 1.0;
  });

  // 2. Draw unified gradient fill under the entire step path
  const fillGrad = ctx.createLinearGradient(0, padTop, 0, bottomY);
  fillGrad.addColorStop(0, 'rgba(99, 102, 241, 0.20)');
  fillGrad.addColorStop(0.5, 'rgba(96, 165, 250, 0.12)');
  fillGrad.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

  ctx.fillStyle = fillGrad;
  ctx.beginPath();
  traceStepPath(ctx);
  // Close down to bottom
  const lastStep = steps[steps.length - 1];
  ctx.lineTo(lastStep.x2, bottomY);
  ctx.lineTo(steps[0].x1, bottomY);
  ctx.closePath();
  ctx.fill();

  // 3. Draw glow line (wider, transparent — behind the main line)
  ctx.lineWidth = 10;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.globalAlpha = 0.12;

  // Draw glow per segment for color
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    ctx.strokeStyle = stateColors[s.state] || '#60a5fa';

    if (i === 0) {
      ctx.beginPath();
      ctx.moveTo(s.x1, s.y);
      ctx.lineTo(s.x2, s.y);
      ctx.stroke();
    } else {
      const prev = steps[i - 1];
      // Transition glow
      ctx.beginPath();
      ctx.moveTo(prev.x2, prev.y);
      ctx.arcTo(s.x1, prev.y, s.x1, s.y, R);
      ctx.arcTo(s.x1, s.y, s.x2, s.y, R);
      ctx.lineTo(s.x2, s.y);
      ctx.stroke();
    }
  }
  ctx.globalAlpha = 1.0;

  // 4. Draw the main step line as one continuous path with rounded corners
  ctx.lineWidth = 2.5;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  // Build corner points: each transition has 2 corners
  // We draw: start → flat → arcTo(end corner) → arcTo(start of next) → flat → ...
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    const next = steps[i + 1];
    ctx.strokeStyle = stateColors[s.state] || '#60a5fa';
    ctx.beginPath();

    if (i === 0) {
      ctx.moveTo(s.x1, s.y);
    } else {
      // Start from slightly before to overlap with previous transition
      ctx.moveTo(s.x1, s.y);
    }

    if (next) {
      // Draw horizontal up to the end, then round into the vertical
      ctx.arcTo(s.x2, s.y, s.x2, next.y, R);
      ctx.arcTo(s.x2, next.y, next.x2, next.y, R);
    } else {
      // Last block: just draw to the end
      ctx.lineTo(s.x2, s.y);
    }
    ctx.stroke();
  }

  // Draw awakening markers (orange bars at top for Awake blocks)
  blocks.forEach(block => {
    if (block.state === 'Awake') {
      let blockStart = 0;
      for (const b of blocks) {
        if (b === block) break;
        blockStart += b.duration_seconds;
      }
      const x1 = xForTime(blockStart);
      const x2 = xForTime(blockStart + block.duration_seconds);
      const barW = Math.max(x2 - x1, 3);

      // Orange bar markers
      ctx.fillStyle = '#fb923c';
      ctx.fillRect(x1, padTop - 8, barW, 6);

      // Glow effect
      ctx.shadowColor = 'rgba(251, 146, 60, 0.5)';
      ctx.shadowBlur = 6;
      ctx.fillRect(x1, padTop - 8, barW, 6);
      ctx.shadowBlur = 0;
    }
  });

  // Draw time labels on X axis
  ctx.fillStyle = '#6b7280';
  ctx.font = '10px "Plus Jakarta Sans", sans-serif';
  ctx.textAlign = 'center';

  const startTime = new Date(blocks[0].start_time);
  const endTime = new Date(blocks[blocks.length - 1].end_time);
  const totalMs = endTime - startTime;

  // Show ~5 time labels
  const labelCount = 5;
  for (let i = 0; i <= labelCount; i++) {
    const frac = i / labelCount;
    const x = padLeft + frac * chartW;
    const time = new Date(startTime.getTime() + frac * totalMs);
    const h = time.getHours();
    const m = time.getMinutes();
    const label = `${h}:${String(m).padStart(2, '0')}`;
    ctx.fillText(label, x, H - 6);
  }

  // Draw small tick marks
  for (let i = 0; i <= labelCount; i++) {
    const x = padLeft + (i / labelCount) * chartW;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, yForLevel(3) + 2);
    ctx.lineTo(x, yForLevel(3) + 6);
    ctx.stroke();
  }

  // Render summary below
  renderHypnogramSummary();
}

function renderHypnogramSummary() {
  const container = document.getElementById('hypnogram-summary');
  const dist = sessionData.cognitive_states.state_distribution;
  const totalSec = sessionData.metadata.duration_seconds;

  const stageConfig = [
    { key: 'Awake', label: t('hyp.awake'), cssClass: 'awake' },
    { key: 'REM',   label: 'REM',          cssClass: 'rem' },
    { key: 'Light', label: t('hyp.light'), cssClass: 'light' },
    { key: 'Deep',  label: t('hyp.deep'),  cssClass: 'deep' }
  ];

  stageConfig.forEach(s => {
    const pct = dist[s.key] || 0;
    const minutes = Math.round(pct * totalSec / 60);
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    const timeStr = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;

    const el = document.createElement('div');
    el.className = 'hyp-summary-item';
    el.innerHTML = `
      <div class="hyp-summary-dot ${s.cssClass}"></div>
      <div class="hyp-summary-text">
        <span class="hyp-summary-label">${s.label}</span>
        <span class="hyp-summary-value">${timeStr} <span style="font-size:11px;font-weight:500;color:var(--text-muted)">(${(pct * 100).toFixed(0)}%)</span></span>
      </div>
    `;
    container.appendChild(el);
  });
}

function renderSleepVitals() {
  const ctx = document.getElementById('chart-sleep-vitals').getContext('2d');
  const vs = sessionData.vitals_series;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: vs.map(d => d.timestamp),
      datasets: [
        {
          label: 'Heart Rate (bpm)',
          data: vs.map(d => d.heart_rate),
          borderColor: '#f87171',
          backgroundColor: 'transparent',
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#f87171',
          yAxisID: 'y'
        },
        {
          label: 'HRV (ms)',
          data: vs.map(d => d.hrv),
          borderColor: '#60a5fa',
          backgroundColor: 'transparent',
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#60a5fa',
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: {
            color: '#9ca3af',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 20, 35, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' } }
        },
        y: {
          type: 'linear',
          position: 'left',
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#f87171', font: { size: 10, family: 'Plus Jakarta Sans' } },
          title: { display: true, text: 'HR (bpm)', color: '#f87171', font: { size: 11 } }
        },
        y1: {
          type: 'linear',
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: '#60a5fa', font: { size: 10, family: 'Plus Jakarta Sans' } },
          title: { display: true, text: 'HRV (ms)', color: '#60a5fa', font: { size: 11 } }
        }
      }
    }
  });
}

// ========== Render Vitals Panel ==========
function renderVitals() {
  document.getElementById('chart-spo2')._rendered = true;

  // Quick stats
  document.getElementById('vt-rhr').textContent = vitalsData.daily_summary.resting_heart_rate_bpm;
  document.getElementById('vt-hrv').textContent = sessionData.summary_insights.average_vitals.hrv_ms;
  document.getElementById('vt-steps').textContent = vitalsData.activities.steps.toLocaleString();
  document.getElementById('vt-cal').textContent = vitalsData.activities.calories_burned_kcal.toLocaleString();

  // HR Zones
  renderHRZones();

  // SpO2 Chart
  renderSpO2Chart();

  // Workouts
  renderWorkouts();
}

function renderHRZones() {
  const zones = profileData.physiological_baselines.target_heart_rate_zones;
  const maxHR = profileData.physiological_baselines.max_heart_rate;
  const container = document.getElementById('hr-zones');

  const zoneConfig = [
    { key: 'warm_up', label: t('zone.warmUp'), color: '#60a5fa' },
    { key: 'fat_burn', label: t('zone.fatBurn'), color: '#10b981' },
    { key: 'aerobic', label: 'Aerobic', color: '#f59e0b' },
    { key: 'anaerobic', label: 'Anaerobic', color: '#ef4444' }
  ];

  zoneConfig.forEach(z => {
    const zone = zones[z.key];
    const pct = ((zone.max - zone.min) / maxHR) * 100 * 2.5; // scale up for visual
    const row = document.createElement('div');
    row.className = 'hr-zone-row';
    row.innerHTML = `
      <span class="hr-zone-label" style="color:${z.color}">${z.label}</span>
      <div class="hr-zone-bar-wrap">
        <div class="hr-zone-bar" style="width: 0%; background: linear-gradient(90deg, ${z.color}, ${z.color}88)"
             data-target-width="${Math.min(pct, 95)}%"></div>
      </div>
      <span class="hr-zone-range">${zone.min} – ${zone.max} bpm</span>
    `;
    container.appendChild(row);
  });

  // Animate bars
  setTimeout(() => {
    container.querySelectorAll('.hr-zone-bar').forEach(bar => {
      bar.style.width = bar.dataset.targetWidth;
    });
  }, 100);
}

function renderSpO2Chart() {
  const ctx = document.getElementById('chart-spo2').getContext('2d');
  const log = vitalsData.blood_oxygen_log;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: log.map(d => {
        const t = new Date(d.timestamp);
        return `${t.getHours()}:${String(t.getMinutes()).padStart(2, '0')}`;
      }),
      datasets: [{
        label: 'SpO₂ (%)',
        data: log.map(d => d.spo2_pct),
        borderColor: '#60a5fa',
        backgroundColor: (ctx) => {
          const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.height);
          gradient.addColorStop(0, 'rgba(96, 165, 250, 0.25)');
          gradient.addColorStop(1, 'rgba(96, 165, 250, 0)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: '#60a5fa',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointHoverRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 20, 35, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af'
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 10, family: 'Plus Jakarta Sans' } },
          min: 90,
          max: 100
        }
      }
    }
  });
}

function renderWorkouts() {
  const container = document.getElementById('workout-list');
  const workouts = vitalsData.workout_sessions;

  const typeIcons = {
    'Running': 'fa-person-running',
    'Yoga': 'fa-spa',
    'Swimming': 'fa-person-swimming',
    'Cycling': 'fa-bicycle'
  };

  workouts.forEach(w => {
    const start = new Date(w.timestamp_start);
    const end = new Date(w.timestamp_end);
    const timeStr = `${start.getHours()}:${String(start.getMinutes()).padStart(2, '0')} – ${end.getHours()}:${String(end.getMinutes()).padStart(2, '0')}`;
    const durationMin = Math.round(w.duration_seconds / 60);

    const el = document.createElement('div');
    el.className = 'workout-item';
    el.innerHTML = `
      <div class="workout-icon">
        <i class="fa-solid ${typeIcons[w.type] || 'fa-dumbbell'}"></i>
      </div>
      <div class="workout-details">
        <div class="workout-name">${w.type}</div>
        <div class="workout-time">${timeStr} · ${durationMin} ${t('unit.min')}</div>
      </div>
      <div class="workout-stats">
        <div class="workout-stat">
          <span class="workout-stat-val" style="color: #f87171">${w.average_heart_rate}</span>
          <span class="workout-stat-label">Avg HR</span>
        </div>
        <div class="workout-stat">
          <span class="workout-stat-val" style="color: #ef4444">${w.max_heart_rate}</span>
          <span class="workout-stat-label">Max HR</span>
        </div>
        <div class="workout-stat">
          <span class="workout-stat-val" style="color: #f59e0b">${w.calories_burned_kcal}</span>
          <span class="workout-stat-label">kcal</span>
        </div>
      </div>
    `;
    container.appendChild(el);
  });
}

// ========== Render Alerts Panel ==========
function renderAlerts() {
  document.getElementById('alerts-container')._rendered = true;

  // Proactive Alerts
  const container = document.getElementById('alerts-container');
  const allAlerts = [
    ...sessionData.summary_insights.alerts.map(a => ({ ...a, timestamp: sessionData.metadata.timestamp_start, source: 'session' })),
    ...alertsData.proactive_alerts.map(a => ({
      type: a.vital_type,
      severity: a.value >= a.threshold ? 'warning' : 'info',
      message: a.alert_text,
      timestamp: a.timestamp,
      call_status: a.call_status,
      source: 'proactive'
    }))
  ];

  const severityIcons = {
    info: 'fa-circle-info',
    warning: 'fa-triangle-exclamation',
    critical: 'fa-circle-exclamation'
  };

  allAlerts.forEach((alert, i) => {
    const el = document.createElement('div');
    el.className = `alert-item severity-${alert.severity}`;
    el.style.animationDelay = `${i * 0.1}s`;
    el.innerHTML = `
      <div class="alert-icon">
        <i class="fa-solid ${severityIcons[alert.severity] || 'fa-circle-info'}"></i>
      </div>
      <div class="alert-body">
        <div class="alert-title">${alert.type.replace(/_/g, ' ').toUpperCase()}</div>
        <div class="alert-message">${alert.message}</div>
        <div class="alert-meta">
          <span><i class="fa-solid fa-clock" style="margin-right:4px"></i>${new Date(alert.timestamp).toLocaleTimeString('en-US')}</span>
          ${alert.call_status ? `<span class="alert-status-tag ${alert.call_status}">${alert.call_status}</span>` : ''}
        </div>
      </div>
    `;
    container.appendChild(el);
  });

  // Health Logs
  const logsContainer = document.getElementById('health-logs');
  const categoryIcons = {
    exercise: 'fa-person-running',
    diet: 'fa-utensils',
    symptom: 'fa-stethoscope',
    medication: 'fa-pills',
    sleep_comment: 'fa-moon'
  };

  alertsData.voice_health_logs.forEach(log => {
    const el = document.createElement('div');
    el.className = 'health-log-item';
    el.innerHTML = `
      <i class="fa-solid ${categoryIcons[log.category] || 'fa-clipboard'}"></i>
      <span class="health-log-category">${log.category}</span>
      <span class="health-log-text">${log.raw_statement}</span>
    `;
    logsContainer.appendChild(el);
  });
}

// ========== Number Animation ==========
function animateNumbers() {
  const statValues = document.querySelectorAll('.stat-value');
  statValues.forEach(el => {
    const finalText = el.textContent;
    if (finalText === '—' || !finalText) return;

    // Check if it's a fraction like "120/78"
    if (finalText.includes('/')) return;

    const finalNum = parseFloat(finalText.replace(/,/g, ''));
    if (isNaN(finalNum)) return;

    let current = 0;
    const increment = finalNum / 30;
    const timer = setInterval(() => {
      current += increment;
      if (current >= finalNum) {
        el.textContent = finalText;
        clearInterval(timer);
      } else {
        el.textContent = Math.round(current);
      }
    }, 30);
  });
}
