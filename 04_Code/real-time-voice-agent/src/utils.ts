/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Highly optimized downsampling buffer utility.
 * Convers any input sample rate (e.g., 44100Hz, 48000Hz) efficiently down to 16000Hz (16kHz).
 * This ensures low-latency and maximum compatibility with Gemini Live's audio requirements.
 */
export function downsampleBuffer(
  buffer: Float32Array,
  inputSampleRate: number,
  outputSampleRate: number = 16000
): Int16Array {
  if (inputSampleRate === outputSampleRate) {
    const pcm = new Int16Array(buffer.length);
    for (let i = 0; i < buffer.length; i++) {
      const val = Math.floor(buffer[i] * 0x7fff);
      pcm[i] = Math.max(-32768, Math.min(32767, val));
    }
    return pcm;
  }

  const sampleRateRatio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(buffer.length / sampleRateRatio);
  const result = new Int16Array(newLength);
  let offsetResult = 0;
  let offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
    let accum = 0;
    let count = 0;
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }
    const val = count > 0 ? (accum / count) * 0x7fff : 0;
    result[offsetResult] = Math.max(-32768, Math.min(32767, Math.floor(val)));
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }
  return result;
}

/**
 * Safely converts Int16Array PCM buffer to a base64 encoded string.
 */
export function pcmToBase64(int16Array: Int16Array): string {
  const buffer = int16Array.buffer;
  const bytes = new Uint8Array(buffer);
  let binary = "";
  // High-speed block string generation
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
