import express from "express";
import http from "http";
import path from "path";
import { WebSocketServer, WebSocket } from "ws";
import { GoogleGenAI, LiveServerMessage, Modality } from "@google/genai";
import dotenv from "dotenv";
import { createServer as createViteServer } from "vite";

dotenv.config();

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

// Create an HTTP server so that we can attach WebSocket (ws) to the same port
const server = http.createServer(app);

// Initialize a WebSocket server
const wss = new WebSocketServer({ noServer: true });

// Lazy initialization of Gemini client
let aiInstance: GoogleGenAI | null = null;
function getGeminiClient(): GoogleGenAI {
  if (!aiInstance) {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error("GEMINI_API_KEY environment variable is not defined. Please configure it in the Secrets panel.");
    }
    aiInstance = new GoogleGenAI({
      apiKey,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    });
  }
  return aiInstance;
}

// API endpoint to check health and configured environment variables
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    hasApiKey: !!process.env.GEMINI_API_KEY,
  });
});

// Setup WebSocket connection handling for Gemini Live connection
wss.on("connection", async (clientWs: WebSocket, request: http.IncomingMessage) => {
  console.log("Client connected to local voice WebSocket proxy");

  // Parse query parameters
  const requestUrl = new URL(request.url || "", `http://${request.headers.host}`);
  const modelName = requestUrl.searchParams.get("model") || "gemini-3.1-flash-live-preview";
  const voiceName = requestUrl.searchParams.get("voice") || "Zephyr";
  const systemInstruction = requestUrl.searchParams.get("systemInstruction") || 
    "You are a helpful, extremely polite real-time voice assistant. Respond concisely and conversationally. Do not use markdown and respond in a clear, spoken-friendly format.";

  console.log(`Setting up Live session on model: ${modelName} with voice: ${voiceName}`);

  let geminiConnector: any = null;

  try {
    const ai = getGeminiClient();
    
    // Connect to Gemini Live API
    geminiConnector = await ai.live.connect({
      model: modelName,
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: {
              voiceName: voiceName, // 'Puck', 'Charon', 'Kore', 'Fenrir', 'Zephyr'
            },
          },
        },
        systemInstruction: systemInstruction,
        // Optional additions for robust text transcribing of the stream to overlay on UI
        outputAudioTranscription: {},
        inputAudioTranscription: {},
      },
      callbacks: {
        onmessage: (message: LiveServerMessage) => {
          // Assert to any for flexible property access on standard Live API interfaces
          const serverContent = message.serverContent as any;
          if (!serverContent) return;

          // If the message contains audio, forward it directly to the client
          const audio = serverContent.modelTurn?.parts?.[0]?.inlineData?.data;
          const interrupted = serverContent.interrupted;
          const userTranscription = serverContent.inputTranscription?.text || serverContent.inputTranscription?.parts?.[0]?.text;
          const modelTranscription = serverContent.modelTurn?.parts?.[0]?.text;

          // Collect structural data
          const responsePayload: any = {};
          if (audio) {
            responsePayload.audio = audio;
          }
          if (interrupted) {
            responsePayload.interrupted = true;
          }
          if (userTranscription) {
            responsePayload.userTranscription = userTranscription;
          }
          if (modelTranscription) {
            responsePayload.modelTranscription = modelTranscription;
          }

          if (Object.keys(responsePayload).length > 0) {
            if (clientWs.readyState === WebSocket.OPEN) {
              clientWs.send(JSON.stringify(responsePayload));
            }
          }
        },
        onclose: () => {
          console.log("Gemini Session closed");
          clientWs.close();
        },
        onerror: (err: any) => {
          console.error("Gemini Session error:", err);
          if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ error: err?.toString() || "Gemini Session Error" }));
          }
        },
      },
    });

    console.log("Connected to Gemini Live session successfully");

  } catch (err: any) {
    console.error("Initialization of Gemini Live connection failed:", err);
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(JSON.stringify({ error: `Failed to initiate voice session: ${err.message}` }));
      clientWs.close();
    }
    return;
  }

  // Handle incoming audio stream chunk or text queries from the client browser
  clientWs.on("message", (rawBytes: Buffer) => {
    try {
      const parsed = JSON.parse(rawBytes.toString());
      if (!geminiConnector) return;

      if (parsed.audio) {
        // Send raw little-endian PCM sample block to Gemini Live session
        geminiConnector.sendRealtimeInput({
          audio: {
            data: parsed.audio, // base64 encoded PCM data
            mimeType: "audio/pcm;rate=16000",
          },
        });
      } else if (parsed.text) {
        // Support text-based user queries in parallel (if requested)
        geminiConnector.sendRealtimeInput({
          text: parsed.text,
        });
      }
    } catch (parseError) {
      console.error("Error parsing message block from client browser:", parseError);
    }
  });

  clientWs.on("close", () => {
    console.log("Client browser disconnected from proxy");
    if (geminiConnector) {
      try {
        geminiConnector.close();
      } catch (err) {
        // ignore double-close errors
      }
    }
  });

  clientWs.on("error", (err) => {
    console.error("WebSocket proxy error:", err);
  });
});

// Delegate WebSocket upgrades to our wss
server.on("upgrade", (request, socket, head) => {
  const url = new URL(request.url || "", `http://${request.headers.host}`);
  if (url.pathname === "/api/live-ws") {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit("connection", ws, request);
    });
  }
});

// Setup Vite and Static file configuration
async function initializeApp() {
  if (process.env.NODE_ENV !== "production") {
    // In development mode, mount Vite middleware to handle React/Vite assets
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
    console.log("Vite middleware mounted successfully for fullstack development");
  } else {
    // In production mode, serve the static assets from /dist
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
    console.log("Static production build configured.");
  }

  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Server fully booting. Listening on http://0.0.0.0:${PORT}`);
  });
}

initializeApp().catch((err) => {
  console.error("Failed to bootstrap server:", err);
});
