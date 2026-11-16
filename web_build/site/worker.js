const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
importScripts(PYODIDE + "pyodide.js", "astcenc.js");

let pyodide = null;
let entry = null;
let astc = null;
let ready = null;
let step = "";

const say = text => { step = text; postMessage({ type: "status", text }); };

function astcCall(fn, input, outLen, args) {
  const inPtr = astc._malloc(input.length);
  const outPtr = astc._malloc(outLen);
  try {
    astc.HEAPU8.set(input, inPtr);
    const rc = fn(inPtr, outPtr, ...args);
    if (rc !== 0) throw new Error("ASTC texture conversion failed (" + rc + ")");
    return astc.HEAPU8.slice(outPtr, outPtr + outLen);
  } finally {
    astc._free(inPtr);
    astc._free(outPtr);
  }
}

self.astcDecode = (blocks, w, h, bw, bh, srgb) =>
  astcCall((i, o) => astc._astc_decode(i, blocks.length, o, w, h, bw, bh, srgb ? 1 : 0), blocks, w * h * 4, []);

self.astcEncode = (rgba, w, h, bw, bh, srgb, quality) => {
  const size = Math.ceil(w / bw) * Math.ceil(h / bh) * 16;
  return astcCall((i, o) => astc._astc_encode(i, o, size, w, h, bw, bh, srgb ? 1 : 0, quality), rgba, size, []);
};

function pyError(e) {
  const text = String(e && e.message || e);
  const lines = text.trim().split("\n").filter(Boolean);
  const last = lines[lines.length - 1] || text;
  return last.replace(/^\w+(Error|Exception): /, "");
}

async function boot() {
  say("Loading the randomizer engine");
  pyodide = await loadPyodide({ indexURL: PYODIDE });
  say("Loading image and compression tools");
  await pyodide.loadPackage(["numpy", "pillow", "zstandard", "mmh3"]);
  astc = await AstcModule();
  say("Unpacking the randomizer");
  const zip = await (await fetch("engine.zip", { cache: "no-cache" })).arrayBuffer();
  pyodide.unpackArchive(zip, "zip", { extractDir: "/home/pyodide/oot" });
  pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide/oot')");
  entry = pyodide.pyimport("webentry");
  return JSON.parse(entry.defaults());
}

onmessage = async ({ data }) => {
  step = "";
  try {
    if (data.type === "init") {
      ready = ready || boot();
      postMessage({ type: "ready", defaults: await ready });
    } else if (data.type === "seed") {
      await ready;
      postMessage({ type: "seed", id: data.id, seed: entry.random_seed() });
    } else if (data.type === "game") {
      await ready;
      say("Reading your game file");
      const file = data.file;
      const reader = (pos, len) => new Uint8Array(new FileReaderSync().readAsArrayBuffer(file.slice(pos, pos + len)));
      const info = JSON.parse(entry.open_game(reader, file.size, file.name));
      postMessage({ type: "game", info });
    } else if (data.type === "folder") {
      await ready;
      say("Checking the extracted game files");
      const files = new Map(data.entries);
      const sizes = {};
      files.forEach((file, path) => { sizes[path] = file.size; });
      const reader = path => new Uint8Array(new FileReaderSync().readAsArrayBuffer(files.get(path)));
      const info = JSON.parse(entry.open_folder(JSON.stringify(sizes), reader));
      postMessage({ type: "game", info });
    } else if (data.type === "generate") {
      await ready;
      const summary = JSON.parse(entry.generate(JSON.stringify(data.options), say));
      const zip = pyodide.FS.readFile("/tmp/mod.zip");
      const spoiler = pyodide.FS.readFile("/tmp/spoiler.txt", { encoding: "utf8" });
      pyodide.FS.unlink("/tmp/mod.zip");
      postMessage({ type: "done", summary, zip, spoiler }, [zip.buffer]);
    }
  } catch (e) {
    const detail = String(e && (e.message || e) || "") + (e && e.stack && !String(e.message).includes("Traceback") ? "\n" + e.stack : "");
    postMessage({ type: "error", stage: data.type, text: pyError(e), detail: detail.slice(-12000), step });
  }
};
