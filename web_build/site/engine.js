(() => {
  const worker = new Worker("worker.js");
  const waiting = {};
  let statusHandler = () => {};
  let seedId = 0;

  const once = type => new Promise((resolve, reject) => { waiting[type] = { resolve, reject }; });

  worker.onmessage = ({ data }) => {
    if (data.type === "status") return statusHandler(data.text);
    if (data.type === "error") {
      const key = data.stage === "init" ? "ready" : data.stage === "game" || data.stage === "folder" ? "game" : data.stage === "generate" ? "done" : data.stage;
      const err = Object.assign(new Error(data.text), { detail: data.detail, step: data.step, stage: data.stage });
      const w = waiting[key];
      if (w) { delete waiting[key]; w.reject(err); } else if (window.OOT_REPORT) window.OOT_REPORT("engine-" + data.stage, err);
      return;
    }
    if (data.type === "seed") return waiting["seed" + data.id] && waiting["seed" + data.id].resolve(data.seed);
    const w = waiting[data.type];
    if (w) { delete waiting[data.type]; w.resolve(data); }
  };

  const crash = (detail) => {
    const err = Object.assign(new Error("The randomizer engine stopped unexpectedly. Reload the page and try again."), { detail, stage: "worker" });
    const pending = Object.keys(waiting);
    pending.forEach(k => { const w = waiting[k]; delete waiting[k]; w.reject(err); });
    if (!pending.length && window.OOT_REPORT) window.OOT_REPORT("engine-crash", err);
  };
  worker.onerror = e => { e.preventDefault(); crash(`${e.message || "worker error"} (${e.filename || "worker"}:${e.lineno || 0})`); };
  worker.onmessageerror = () => crash("A message from the engine could not be read.");

  let urls = [];

  window.OOT_ENGINE = {
    hosted: true,
    onStatus(fn) { statusHandler = fn; },
    async defaults() {
      const p = once("ready");
      worker.postMessage({ type: "init" });
      const { defaults } = await p;
      defaults.game = { picker: true };
      return defaults;
    },
    async randomSeed() {
      const id = ++seedId;
      const p = new Promise(resolve => { waiting["seed" + id] = { resolve, reject: resolve }; });
      worker.postMessage({ type: "seed", id });
      return p;
    },
    async openGame(file) {
      const p = once("game");
      worker.postMessage({ type: "game", file });
      const { info } = await p;
      if (info.unsupported) {
        throw Object.assign(new Error(`Unsupported ${info.format}`), {
          unsupported: true, format: info.format, contents: info.contents, detail: JSON.stringify(info.diagnostics),
        });
      }
      return info;
    },
    async openFolder(entries) {
      const p = once("game");
      worker.postMessage({ type: "folder", entries });
      return (await p).info;
    },
    async generate(options) {
      const p = once("done");
      worker.postMessage({ type: "generate", options });
      const { summary, zip, spoiler } = await p;
      urls.forEach(URL.revokeObjectURL);
      const zipUrl = URL.createObjectURL(new Blob([zip], { type: "application/zip" }));
      const spoilerUrl = URL.createObjectURL(new Blob([spoiler], { type: "text/plain;charset=utf-8" }));
      urls = [zipUrl, spoilerUrl];
      return Object.assign(summary, {
        download: zipUrl, download_name: `OoT-Randomizer-${summary.seed}.zip`,
        spoiler_url: spoilerUrl, spoiler_name: `OoT-Randomizer-${summary.seed}-spoiler.txt`,
      });
    },
  };
})();
