const path = require("path");
const puppeteer = require("puppeteer-core");

const FIX = path.join(__dirname, "fixtures");
const t0 = Date.now();
const log = (...a) => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s]`, ...a);

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true, defaultViewport: { width: 1280, height: 1000 },
  });
  const page = await browser.newPage();
  await page.evaluateOnNewDocument(() => { delete window.showDirectoryPicker; });
  page.on("pageerror", e => log("pageerror:", e.message));
  page.on("response", r => { if (r.url().includes("log.php")) log("log.php ->", r.status()); });
  await page.goto("http://localhost:8791/", { waitUntil: "load" });
  await page.waitForFunction(() => document.getElementById("status").innerText.startsWith("Ready"), { timeout: 180000 });
  log("ready");

  const status = () => page.$eval("#status", e => e.innerText);
  const waitStatus = re => page.waitForFunction(r => new RegExp(r).test(document.getElementById("status").innerText), { timeout: 600000 }, re);

  for (const name of ["Ocarina of Time [0400486024DEC000].nsp", "Ocarina of Time [0400486024DEC000].xci", "random.bin"]) {
    const [input] = await page.$$("#game-box input[type=file]");
    await input.uploadFile(path.join(FIX, name));
    await waitStatus("isn't supported|not supported");
    log(name, "->", await page.$eval(".pick-error", e => e.innerText));
  }

  const [chooser] = await Promise.all([page.waitForFileChooser(), page.click("#pick-folder")]);
  await chooser.accept([path.join(FIX, "Ocarina dump")]);
  await waitStatus("Game found|error|Couldn't|doesn't");
  log("folder status:", await status());
  log("folder meta:", await page.$eval("#game-box", e => e.innerText.replace(/\s+/g, " ")));
  await page.screenshot({ path: path.join(__dirname, "shots", "folder-picked.png"), clip: { x: 0, y: 560, width: 1280, height: 420 } });

  await page.click("#generate");
  await waitStatus("is ready|error|failed|stopped");
  log("generate:", await status());
  log("download:", await page.$eval("#r-download", a => a.href.slice(0, 30)));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
