/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, useRef } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  Play,
  Square,
  Sparkles,
  RefreshCw,
  AlertCircle,
  Trash2,
  Settings,
  X,
  MessageSquare,
  HelpCircle,
  Activity,
  Cpu,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { downsampleBuffer, pcmToBase64 } from "./utils.ts";

interface TranscriptItem {
  id: string;
  role: "user" | "model";
  text: string;
  timestamp: number;
}

export default function App() {
  // UI Configuration State
  const [model, setModel] = useState("gemini-3.1-flash-live-preview");
  const [voice, setVoice] = useState("Zephyr");
  const [systemInstruction, setSystemInstruction] = useState(
    "You are a helpful, extremely polite real-time voice assistant. Respond concisely and conversationally. Do not use markdown and respond in a clear, spoken-friendly format."
  );

  // App & Connection State
  const [connectionStatus, setConnectionStatus] = useState<
    "disconnected" | "connecting" | "connected" | "error"
  >("disconnected");
  const [errorMessage, setErrorMessage] = useState("");
  const [hasApiKey, setHasApiKey] = useState<boolean | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Visualizer Volumes
  const [micVolume, setMicVolume] = useState(0);
  const [speakerVolume, setSpeakerVolume] = useState(0);

  // Conversation transcripts list
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([]);

  // Session Time State
  const [sessionTime, setSessionTime] = useState(0);

  // Refs for tracking WebSocket and Audio Contexts
  const wsRef = useRef<WebSocket | null>(null);
  const inputAudioCtxRef = useRef<AudioContext | null>(null);
  const outputAudioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const processorNodeRef = useRef<ScriptProcessorNode | null>(null);
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([]);
  const nextStartTimeRef = useRef<number>(0);

  // Helper refs to prevent closure stale problems in asynchronous callbacks
  const isMutedRef = useRef(isMuted);
  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  const transcriptScrollContainerRef = useRef<HTMLDivElement | null>(null);

  // Audio timer increment effect
  useEffect(() => {
    let timerId: any = null;
    if (connectionStatus === "connected") {
      timerId = setInterval(() => {
        setSessionTime((t) => t + 1);
      }, 1000);
    } else {
      setSessionTime(0);
    }
    return () => {
      if (timerId) clearInterval(timerId);
    };
  }, [connectionStatus]);

  // Format session timer duration
  const formatSessionTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins
      .toString()
      .padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Auto-scroll transcripts to bottom when new entries arrive
  useEffect(() => {
    if (transcriptScrollContainerRef.current) {
      transcriptScrollContainerRef.current.scrollTo({
        top: transcriptScrollContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [transcripts]);

  // Check server health/API key presence on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("/api/health");
        const data = await res.json();
        setHasApiKey(data.hasApiKey);
      } catch (err) {
        console.error("Health check endpoint unreachable:", err);
      }
    };
    checkHealth();
  }, []);

  // Flush and cancel active voice sources
  const flushAudioSources = () => {
    console.log("Flushing active audio sources");
    activeSourcesRef.current.forEach((src) => {
      try {
        src.stop();
      } catch (e) {
        // Source already terminated or not started
      }
    });
    activeSourcesRef.current = [];
    nextStartTimeRef.current = 0;
    setSpeakerVolume(0);
  };

  // Play incoming chunks of raw PCM audio (24kHz, 16-bit little-endian) from Gemini
  const playAudioChunk = (base64Audio: string) => {
    if (!outputAudioCtxRef.current) {
      outputAudioCtxRef.current = new (window.AudioContext ||
        (window as any).webkitAudioContext)({ sampleRate: 24000 });
    }
    const ctx = outputAudioCtxRef.current;

    // Direct resume if browser suspended output
    if (ctx.state === "suspended") {
      ctx.resume();
    }

    try {
      // Decode base64 to binary representation
      const raw = window.atob(base64Audio);
      const len = raw.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = raw.charCodeAt(i);
      }

      // 16-bit PCM equates to 2 bytes per sample point
      const numSamples = len / 2;
      const f32 = new Float32Array(numSamples);
      const view = new DataView(bytes.buffer);

      let peak = 0;
      for (let i = 0; i < numSamples; i++) {
        const val = view.getInt16(i * 2, true); // true = little-endian conversion
        f32[i] = val / 32768.0;
        const abs = Math.abs(f32[i]);
        if (abs > peak) peak = abs;
      }

      // Scale audio peak for visual feedback indicators
      setSpeakerVolume(peak * 100);

      const audioBuf = ctx.createBuffer(1, numSamples, 24000);
      audioBuf.copyToChannel(f32, 0);

      const source = ctx.createBufferSource();
      source.buffer = audioBuf;
      source.connect(ctx.destination);

      const now = ctx.currentTime;
      // Introduce an 80ms lookahead safety buffer to guarantee gapless playback over network jitter
      if (nextStartTimeRef.current < now) {
        nextStartTimeRef.current = now + 0.08;
      }

      source.start(nextStartTimeRef.current);
      activeSourcesRef.current.push(source);

      source.onended = () => {
        activeSourcesRef.current = activeSourcesRef.current.filter(
          (s) => s !== source
        );
        if (activeSourcesRef.current.length === 0) {
          setSpeakerVolume(0);
        }
      };

      // Push timeline marker forward by play duration
      nextStartTimeRef.current += audioBuf.duration;
    } catch (err) {
      console.error("Error decoding playback chunk:", err);
    }
  };

  // Start microphones stream and setup recording pipeline
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });

      micStreamRef.current = stream;

      // Construct a generic AudioContext at native device sample rate (highly safe config)
      const inputCtx = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      inputAudioCtxRef.current = inputCtx;

      const source = inputCtx.createMediaStreamSource(stream);

      // Create a script processor block (buffer size 4096)
      const processor = inputCtx.createScriptProcessor(4096, 1, 1);
      processorNodeRef.current = processor;

      source.connect(processor);
      // Connect to destination to activate the onaudioprocess callback in all standard browsers
      processor.connect(inputCtx.destination);

      processor.onaudioprocess = (e) => {
        if (isMutedRef.current) {
          setMicVolume(0);
          return;
        }

        const inputBuffer = e.inputBuffer.getChannelData(0);

        // Calculate voice amplitude (RMS) for green dynamic waveform visualizer
        let sum = 0;
        for (let i = 0; i < inputBuffer.length; i++) {
          sum += inputBuffer[i] * inputBuffer[i];
        }
        const rms = Math.sqrt(sum / inputBuffer.length);
        setMicVolume(rms * 100);

        // Downsample input from hardware device rate (typically 44.1/48kHz) down to 16kHz
        const pcm16 = downsampleBuffer(inputBuffer, inputCtx.sampleRate, 16000);
        const base64 = pcmToBase64(pcm16);

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ audio: base64 }));
        }
      };

      console.log("Microphone recording setup successfully");
    } catch (err: any) {
      console.error("Accessing mic failed:", err);
      setErrorMessage("Could not capture your microphone. Ensure page permissions are granted.");
      setConnectionStatus("error");
    }
  };

  // Tear down audio recording components
  const stopRecording = () => {
    if (processorNodeRef.current) {
      try {
        processorNodeRef.current.disconnect();
      } catch (e) {}
      processorNodeRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (inputAudioCtxRef.current) {
      try {
        inputAudioCtxRef.current.close();
      } catch (e) {}
      inputAudioCtxRef.current = null;
    }
    setMicVolume(0);
  };

  // Setup proxy WebSockets connections to node bridge server
  const connectVoiceAgent = async () => {
    if (connectionStatus !== "disconnected") return;

    setConnectionStatus("connecting");
    setErrorMessage("");

    // Initialize/resume output audio contexts to satisfy browser user gesture requirement
    if (!outputAudioCtxRef.current) {
      outputAudioCtxRef.current = new (window.AudioContext ||
        (window as any).webkitAudioContext)({ sampleRate: 24000 });
    }
    const outCtx = outputAudioCtxRef.current;
    if (outCtx.state === "suspended") {
      outCtx.resume();
    }

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/api/live-ws?model=${encodeURIComponent(
      model
    )}&voice=${encodeURIComponent(voice)}&systemInstruction=${encodeURIComponent(
      systemInstruction
    )}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = async () => {
        console.log("Local browser connected to websocket bridge proxy");
        setConnectionStatus("connected");
        // Start streaming mic audio directly to bridge
        await startRecording();
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          // 1. Play active model voice responses
          if (msg.audio) {
            playAudioChunk(msg.audio);
          }

          // 2. Clear speaker output on user barge-in / interruption signal
          if (msg.interrupted) {
            console.log("User interrupted Gemini. Stopping speaker playbacks.");
            flushAudioSources();
          }

          // 3. User transcribed text chunks
          if (msg.userTranscription) {
            setTranscripts((prev) => {
              const list = [...prev];
              if (list.length > 0 && list[list.length - 1].role === "user") {
                list[list.length - 1] = {
                  ...list[list.length - 1],
                  text: list[list.length - 1].text + msg.userTranscription,
                };
                return list;
              } else {
                return [
                  ...list,
                  {
                    id: Math.random().toString(),
                    role: "user",
                    text: msg.userTranscription,
                    timestamp: Date.now(),
                  },
                ];
              }
            });
          }

          // 4. Model transcribed response chunks
          if (msg.modelTranscription) {
            setTranscripts((prev) => {
              const list = [...prev];
              if (list.length > 0 && list[list.length - 1].role === "model") {
                list[list.length - 1] = {
                  ...list[list.length - 1],
                  text: list[list.length - 1].text + msg.modelTranscription,
                };
                return list;
              } else {
                return [
                  ...list,
                  {
                    id: Math.random().toString(),
                    role: "model",
                    text: msg.modelTranscription,
                    timestamp: Date.now(),
                  },
                ];
              }
            });
          }

          // 5. Connection Error payload
          if (msg.error) {
            setErrorMessage(msg.error);
            setConnectionStatus("error");
            disconnectVoiceAgent();
          }
        } catch (err) {
          console.error("Error reading JSON message packet:", err);
        }
      };

      ws.onclose = () => {
        console.log("Local browser disconnected from proxy");
        setConnectionStatus("disconnected");
        stopRecording();
        flushAudioSources();
      };

      ws.onerror = (err) => {
        console.error("Local WebSocket connection error:", err);
        setErrorMessage("Websocket connection failed. Check server logs.");
        setConnectionStatus("error");
      };
    } catch (err: any) {
      setErrorMessage(`Proxy connection failure: ${err?.message || err}`);
      setConnectionStatus("error");
    }
  };

  // Clean-up and disconnect voice session completely
  const disconnectVoiceAgent = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    stopRecording();
    flushAudioSources();
  };

  // Cleanup effect on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      stopRecording();
      flushAudioSources();
    };
  }, []);

  const clearTranscript = () => {
    setTranscripts([]);
  };

  // Determine current active animation state class
  const getPulseState = () => {
    if (connectionStatus === "connecting") return "connecting";
    if (connectionStatus === "connected") {
      if (speakerVolume > 1.5) return "speaking";
      if (micVolume > 1.5) return "listening";
      return "ready";
    }
    if (connectionStatus === "error") return "error";
    return "idle";
  };

  const pulseState = getPulseState();

  // Pick off the last relevant transcription as caption snippet
  const latestCaption = transcripts.length > 0 ? transcripts[transcripts.length - 1] : null;

  // Render reactive equalizing bars based on mic / speaker amplitude
  const amplitudeScaler = pulseState === "speaking" ? speakerVolume : micVolume;

  return (
    <div className="min-h-screen bg-[#050505] text-slate-100 flex flex-col font-sans relative overflow-hidden selection:bg-cyan-500/20">
      
      {/* Immersive Atmospheric Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[45%] h-[45%] bg-cyan-600/10 rounded-full blur-[140px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[45%] h-[45%] bg-purple-600/10 rounded-full blur-[140px] pointer-events-none"></div>

      {/* Top Header Navigation */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 md:py-8 flex justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.8)] animate-pulse"></div>
          <div>
            <span className="text-xs uppercase tracking-[0.2em] font-bold text-slate-400 block">
              Gemini Live
            </span>
            <span className="text-[10px] text-zinc-500 font-mono tracking-wider">
              {connectionStatus === "connected" ? "REAL-TIME PORT OPEN" : "IDLE STATE"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-6 md:gap-8">
          <div className="flex flex-col items-end">
            <span className="text-[9px] uppercase text-slate-500 tracking-wider">Latency</span>
            <span className="text-xs md:text-sm font-mono text-emerald-400 font-medium">
              {connectionStatus === "connected" ? "38ms" : "--"}
            </span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[9px] uppercase text-slate-500 tracking-wider">Model</span>
            <span className="text-xs md:text-sm font-mono text-slate-300">
              {model.replace("-live-preview", "")}
            </span>
          </div>
          <button
            onClick={() => setShowSettings(true)}
            disabled={connectionStatus === "connecting" || connectionStatus === "connected"}
            className={`p-2 rounded-lg border flex items-center justify-center transition-all ${
              connectionStatus === "connected"
                ? "bg-transparent text-slate-600 border-white/5 cursor-not-allowed"
                : "bg-white/5 hover:bg-white/10 text-slate-300 border-white/10 active:scale-95"
            }`}
            title="Configure model parameters"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch z-10">
        
        {/* Left Interactive Orb Panel */}
        <div className="lg:col-span-6 flex flex-col items-center justify-between bg-white/[0.02] border border-white/5 rounded-3xl p-6 md:p-8 backdrop-blur-md relative min-h-[420px]">
          
          <div className="w-full text-center mb-4">
            <span className="text-[10px] font-mono uppercase tracking-[0.15em] text-cyan-400/80 block">
              Direct PCM Streaming
            </span>
            <h2 className="text-sm text-slate-400 mt-1">Audio Visualizer Orb</h2>
          </div>

          {/* Central Immersive Concentric Circles & Real Waveform */}
          <div className="my-6 relative flex items-center justify-center w-full max-w-[280px] aspect-square">
            
            {/* Ambient Background blur sphere */}
            <div className={`absolute w-[220px] h-[220px] rounded-full blur-[50px] transition-all duration-500 ${
              pulseState === "speaking" ? "bg-rose-500/10" :
              pulseState === "listening" ? "bg-cyan-500/10" : "bg-cyan-500/2"
            }`} />

            {/* Glowing Rings */}
            <div className="absolute w-[280px] h-[280px] border border-white/5 rounded-full"></div>
            <div className="absolute w-[340px] h-[340px] border border-white/5 rounded-full pointer-events-none"></div>

            {/* Rotating border aura */}
            <AnimatePresence>
              {connectionStatus === "connecting" && (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
                  className="absolute inset-0 rounded-full border border-dashed border-cyan-400/25"
                />
              )}
            </AnimatePresence>

            {/* Inner responsive waveform visualization */}
            <div className="flex items-center gap-1.5 h-36 z-20">
              <div 
                className={`w-1.5 rounded-full transition-all duration-100 ${
                  pulseState === "speaking" ? "bg-rose-400" : "bg-cyan-400"
                }`}
                style={{ height: `${Math.max(12, 12 + amplitudeScaler * 0.4)}px` }}
              />
              <div 
                className={`w-1.5 rounded-full transition-all duration-100 ${
                  pulseState === "speaking" ? "bg-rose-400" : "bg-cyan-400"
                }`}
                style={{ height: `${Math.max(16, 16 + amplitudeScaler * 0.9)}px` }}
              />
              <div 
                className="w-1.5 bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.4)] transition-all duration-100"
                style={{ height: `${Math.max(20, 20 + amplitudeScaler * 1.5)}px` }}
              />
              <div 
                className={`w-1.5 rounded-full shadow-[0_0_15px_rgba(34,211,238,0.4)] transition-all duration-100 ${
                  pulseState === "speaking" ? "bg-rose-300" : "bg-cyan-300"
                }`}
                style={{ height: `${Math.max(24, 24 + amplitudeScaler * 1.8)}px` }}
              />
              <div 
                className="w-1.5 bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.4)] transition-all duration-100"
                style={{ height: `${Math.max(20, 20 + amplitudeScaler * 1.3)}px` }}
              />
              <div 
                className={`w-1.5 rounded-full transition-all duration-100 ${
                  pulseState === "speaking" ? "bg-rose-400" : "bg-cyan-400"
                }`}
                style={{ height: `${Math.max(16, 16 + amplitudeScaler * 0.8)}px` }}
              />
              <div 
                className={`w-1.5 rounded-full transition-all duration-100 ${
                  pulseState === "speaking" ? "bg-rose-400" : "bg-cyan-400"
                }`}
                style={{ height: `${Math.max(12, 12 + amplitudeScaler * 0.3)}px` }}
              />
            </div>

            {/* Small absolute indicator badge */}
            <div className="absolute -bottom-2 px-3 py-1 bg-zinc-900/90 border border-white/10 rounded-full text-[9px] font-mono uppercase tracking-wider text-slate-300 shadow-md">
              {pulseState === "speaking" ? "Agent Speaking" :
               pulseState === "listening" ? "Listening" :
               pulseState === "ready" ? "Channel Active" :
               pulseState === "connecting" ? "Linking" : "Offline Ready"}
            </div>
          </div>

          {/* Subtitle / Caption Snippet Overlay */}
          <div className="w-full text-center max-w-md my-4 px-2">
            <p className="text-base font-light text-slate-300 leading-relaxed italic min-h-[48px]">
              {latestCaption ? (
                `"${latestCaption.text.length > 120 ? latestCaption.text.substring(0, 120) + "..." : latestCaption.text}"`
              ) : (
                <span className="text-slate-500 text-sm italic">
                  "Say hello to the agent to begin low-latency audio transmission"
                </span>
              )}
            </p>
          </div>

          <div className="w-full flex flex-col gap-4">
            
            {/* Primary Action Buttons */}
            <div className="flex gap-4 items-center justify-center">
              {connectionStatus === "connected" && (
                <button
                  onClick={() => setIsMuted(!isMuted)}
                  className={`w-12 h-12 rounded-full border flex items-center justify-center transition-all ${
                    isMuted
                      ? "bg-amber-950/40 text-amber-400 border-amber-500/30"
                      : "bg-white/5 border-white/10 text-slate-300 hover:bg-white/10"
                  }`}
                  title={isMuted ? "Unmute Mic" : "Mute Mic"}
                >
                  {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>
              )}

              {connectionStatus === "disconnected" || connectionStatus === "error" ? (
                <button
                  onClick={connectVoiceAgent}
                  className="px-8 py-4 bg-white text-black hover:bg-slate-100 rounded-full font-bold uppercase tracking-widest text-xs flex items-center gap-3 shadow-[0_0_30px_rgba(255,255,255,0.15)] hover:shadow-[0_0_40px_rgba(255,255,255,0.25)] transition-all active:scale-95"
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                  Start Live Session
                </button>
              ) : (
                <button
                  onClick={disconnectVoiceAgent}
                  className="px-8 py-4 bg-rose-600 hover:bg-rose-500 text-white rounded-full font-bold uppercase tracking-widest text-xs flex items-center gap-3 shadow-[0_0_30px_rgba(239,68,68,0.15)] transition-all active:scale-95"
                >
                  <span className="w-2 h-2 rounded-full bg-red-100"></span>
                  End Session
                </button>
              )}
            </div>

            {errorMessage && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl flex items-start gap-2 max-w-md mx-auto">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span className="font-light">{errorMessage}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Active Transcripts Logs Terminal */}
        <div className="lg:col-span-6 flex flex-col bg-white/[0.01] border border-white/5 rounded-3xl overflow-hidden backdrop-blur-md relative">
          
          <div className="px-5 py-4 border-b border-white/5 bg-white/[0.02] flex justify-between items-center z-10">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Live Captioning Terminal
              </h3>
            </div>
            
            {transcripts.length > 0 && (
              <button
                onClick={clearTranscript}
                className="text-xs text-slate-500 hover:text-rose-400 flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-rose-500/5 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Reset Logs</span>
              </button>
            )}
          </div>

          <div
            ref={transcriptScrollContainerRef}
            className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 max-h-[460px] relative scrollbar-thin"
            style={{ minHeight: "350px" }}
          >
            {transcripts.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 my-auto">
                <div className="w-10 h-10 rounded-full border border-white/5 flex items-center justify-center bg-white/2 mb-3">
                  <Activity className="w-4 h-4 text-slate-400 animate-pulse" />
                </div>
                <h4 className="text-sm font-semibold text-slate-300">Waiting for Voice Inputs</h4>
                <p className="text-xs text-slate-500 max-w-xs mt-1 leading-relaxed">
                  Connect your voice agent stream and begin talking. The transcript window outputs live word-for-word audio decodes.
                </p>
              </div>
            ) : (
              transcripts.map((entry) => (
                <div
                  key={entry.id}
                  className={`flex flex-col max-w-[85%] ${
                    entry.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
                  }`}
                >
                  <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-1.5">
                    {entry.role === "user" ? "YOU / INPUT" : "GEMINI / OUTPUT"}
                  </span>
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      entry.role === "user"
                        ? "bg-zinc-800 text-slate-200 rounded-tr-none"
                        : "bg-cyan-950/20 border border-cyan-800/30 text-cyan-200 rounded-tl-none shadow-[0_0_15px_rgba(6,182,212,0.05)]"
                    }`}
                  >
                    {entry.text}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* User tips footer block */}
          <div className="p-4 bg-black/40 border-t border-white/5 text-[11px] text-slate-500 flex gap-3">
            <HelpCircle className="w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-400 block mb-0.5">Stream Transmission Controls</span>
              <p className="leading-relaxed">
                Enjoy seamless low-latency interaction. Simply start speaking in the middle of a model response to trigger immediate automatic interruption.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Immersive Dashboard Footer metadata bar */}
      <footer className="w-full max-w-7xl mx-auto px-6 py-8 border-t border-white/5 flex flex-col sm:flex-row gap-6 justify-between items-center z-10 text-slate-400">
        
        <div className="flex gap-8 md:gap-12 w-full justify-between sm:justify-start">
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-widest mb-1.5">
              Audio Buffers
            </span>
            <div className="flex gap-1">
              <div className={`w-1 h-3 rounded-sm ${connectionStatus === "connected" ? "bg-cyan-400 animate-pulse" : "bg-white/10"}`}></div>
              <div className={`w-1 h-3 rounded-sm ${connectionStatus === "connected" ? "bg-cyan-400 animate-pulse delay-75" : "bg-white/10"}`}></div>
              <div className={`w-1 h-3 rounded-sm ${connectionStatus === "connected" ? "bg-cyan-400" : "bg-white/10"}`}></div>
              <div className={`w-1 h-3 rounded-sm ${speakerVolume > 1.5 ? "bg-cyan-400 animate-pulse" : "bg-white/10"}`}></div>
              <div className="w-1 h-3 rounded-sm bg-white/10"></div>
            </div>
          </div>

          <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-widest mb-1">CPU Overhead</span>
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-slate-500" />
              i5-1135G7: {connectionStatus === "connected" ? "14%" : "1%"}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-widest mb-1 text-right sm:text-left">Session State</span>
            <span className="text-xs font-mono text-slate-400 text-right sm:text-left">
              {connectionStatus === "connected" ? formatSessionTime(sessionTime) : "00:00:00"}
            </span>
          </div>
        </div>

        {hasApiKey === false && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>Setup GEMINI_API_KEY in Secrets.</span>
          </div>
        )}
      </footer>

      {/* Floating full-screen Parameters Settings modal */}
      <AnimatePresence>
        {showSettings && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#0c0c0c] border border-white/10 rounded-3xl w-full max-w-lg p-6 md:p-8 relative shadow-2xl"
            >
              <button
                onClick={() => setShowSettings(false)}
                className="absolute top-5 right-5 p-2 text-slate-400 hover:text-white rounded-xl hover:bg-white/5 transition"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="mb-6">
                <h3 className="text-base font-semibold text-white flex items-center gap-2 font-sans tracking-wide">
                  <Settings className="w-4 h-4 text-cyan-400" />
                  Live Voice Assistant Configuration
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Tune model selection & setup instruction prompts. Parameters lock during live connection.
                </p>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                    Model Stream Target
                  </label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full bg-[#141414] border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
                  >
                    <option value="gemini-3.1-flash-live-preview">
                      gemini-3.1-flash-live-preview (Fast Live Audio Output)
                    </option>
                    <option value="gemini-3.5-live-translate-preview">
                      gemini-3.5-live-translate-preview (Fast Dynamic Audio Translation)
                    </option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                    Prebuilt Voice Tone
                  </label>
                  <select
                    value={voice}
                    onChange={(e) => setVoice(e.target.value)}
                    className="w-full bg-[#141414] border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
                  >
                    <option value="Zephyr">Zephyr (Deep, crisp Male)</option>
                    <option value="Kore">Kore (Warm, clear Female)</option>
                    <option value="Puck">Puck (Friendly, lively Male)</option>
                    <option value="Charon">Charon (Calm, wise Male)</option>
                    <option value="Fenrir">Fenrir (Deep, authoritative Male)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2">
                    Agent Persona / Instructions
                  </label>
                  <textarea
                    value={systemInstruction}
                    onChange={(e) => setSystemInstruction(e.target.value)}
                    rows={4}
                    className="w-full bg-[#141414] border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-sans leading-relaxed"
                  />
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button
                  onClick={() => setShowSettings(false)}
                  className="px-6 py-3 rounded-full bg-white text-black font-semibold uppercase tracking-wider text-xs transition hover:bg-slate-100 active:scale-95"
                >
                  Save Parameters
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
