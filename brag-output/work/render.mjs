// Render video.html frame by frame over the Chrome DevTools Protocol (Node's built-in WebSocket).
// Usage: node render.mjs frames          -> work/frames/f00000.jpg … (30 fps, 48 s)
//        node render.mjs stills 2.4 10.6 -> work/stills/t2.40.jpg …
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const [mode, ...rest] = process.argv.slice(2);
const FPS = 30, DUR = +(process.env.DUR || 48), HTML = process.env.HTML || "video.html", FRAMES = process.env.FRAMES || "frames";
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn("google-chrome", ["--headless=new", "--disable-gpu", "--hide-scrollbars", `--remote-debugging-port=${port}`,
  "--window-size=1920,1080", "--allow-file-access-from-files", `--user-data-dir=${join(here, ".chrome")}`, "about:blank"], { stdio: "ignore" });

let ws, id = 0; const waits = new Map();
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; waits.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
try {
  let target;
  for (let k = 0; k < 50 && !target; k++) {
    await new Promise(r => setTimeout(r, 200));
    try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === "page"); } catch {}
  }
  if (!target) throw new Error("Chrome did not start");
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = e => { const m = JSON.parse(e.data); const w = waits.get(m.id); if (w) { waits.delete(m.id); m.error ? w.rej(new Error(m.error.message)) : w.res(m.result); } };
  await send("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
  await send("Page.enable");
  await send("Page.navigate", { url: "file://" + join(here, HTML) });
  for (let k = 0; ; k++) {   // wait for fonts + data
    await new Promise(r => setTimeout(r, 250));
    const r = await send("Runtime.evaluate", { expression: "window.ready ? window.ready.then(()=>1) : 0", awaitPromise: true, returnByValue: true }).catch(() => ({}));
    if (r.result?.value === 1) break;
    if (k > 120) throw new Error("page never became ready");
  }
  const times = mode === "stills" ? rest.map(Number) : Array.from({ length: FPS * DUR }, (_, i) => i / FPS);
  const outDir = join(here, mode === "stills" ? "stills" : FRAMES); mkdirSync(outDir, { recursive: true });
  for (const [i, t] of times.entries()) {
    const r = await send("Runtime.evaluate", { expression: `seek(${t}); 1`, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`seek(${t}) failed: ${r.exceptionDetails.exception?.description}`);
    const shot = await send("Page.captureScreenshot", { format: "jpeg", quality: 92, captureBeyondViewport: false });
    const name = mode === "stills" ? `t${t.toFixed(2)}.jpg` : `f${String(i).padStart(5, "0")}.jpg`;
    writeFileSync(join(outDir, name), Buffer.from(shot.data, "base64"));
    if (mode !== "stills" && i % 150 === 0) console.log(`frame ${i}/${times.length}`);
  }
  console.log(`done: ${times.length} images → ${outDir}`);
} finally { ws?.close(); chrome.kill("SIGKILL"); }
