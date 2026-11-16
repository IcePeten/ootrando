const fs = require("fs");
const path = require("path");
const { loadPyodide } = require("pyodide");

const SITE = path.resolve(__dirname, "..", "..", "ootrando-site");
const AstcModule = require(path.join(SITE, "astcenc.js"));
const NUP = fs.readdirSync(path.resolve(__dirname, "..", "..")).find(n => n.includes("Ocarina of Time") && n.endsWith(".nup"));
const options = JSON.parse(process.argv[2] || "{}");

(async () => {
  const t0 = Date.now();
  const lap = label => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${label}`);
  const astc = await AstcModule();
  const call = (fn, input, outLen) => {
    const i = astc._malloc(input.length), o = astc._malloc(outLen);
    try {
      astc.HEAPU8.set(input, i);
      const rc = fn(i, o);
      if (rc !== 0) throw new Error("astc " + rc);
      return astc.HEAPU8.slice(o, o + outLen);
    } finally { astc._free(i); astc._free(o); }
  };
  globalThis.astcDecode = (b, w, h, bw, bh, srgb) => call((i, o) => astc._astc_decode(i, b.length, o, w, h, bw, bh, srgb ? 1 : 0), b, w * h * 4);
  globalThis.astcEncode = (p, w, h, bw, bh, srgb, q) => {
    const size = Math.ceil(w / bw) * Math.ceil(h / bh) * 16;
    return call((i, o) => astc._astc_encode(i, o, size, w, h, bw, bh, srgb ? 1 : 0, q), p, size);
  };
  const py = await loadPyodide();
  await py.loadPackage(["numpy", "pillow", "zstandard", "mmh3"]);
  py.unpackArchive(new Uint8Array(fs.readFileSync(path.join(SITE, "engine.zip"))), "zip", { extractDir: "/home/pyodide/oot" });
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide/oot')");
  const entry = py.pyimport("webentry");
  lap("engine loaded");
  const defaults = JSON.parse(entry.defaults());
  lap(`defaults ok (${Object.keys(defaults).length} keys)`);
  const nupPath = path.resolve(__dirname, "..", "..", NUP);
  const fd = fs.openSync(nupPath, "r");
  const size = fs.fstatSync(fd).size;
  const reader = (pos, len) => { const b = Buffer.alloc(len); fs.readSync(fd, b, 0, len, pos); return new Uint8Array(b.buffer, b.byteOffset, len); };
  console.log(entry.open_game(reader, size, NUP));
  lap("game opened");
  const summary = entry.generate(JSON.stringify(Object.assign({ seed: "12345" }, options)), t => lap(t));
  lap("generated");
  console.log(summary);
  const zip = py.FS.readFile("/tmp/mod.zip");
  const out = path.join(__dirname, "node_mod.zip");
  fs.writeFileSync(out, zip);
  fs.writeFileSync(path.join(__dirname, "node_spoiler.txt"), py.FS.readFile("/tmp/spoiler.txt", { encoding: "utf8" }));
  lap(`zip ${(zip.length / 1e6).toFixed(1)} MB written to ${out}`);
})().catch(e => { console.error(e); process.exit(1); });
