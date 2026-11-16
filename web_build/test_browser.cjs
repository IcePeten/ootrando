const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const URL_ = process.argv[2] || "http://localhost:8790/";
const NUP_DIR = path.resolve(__dirname, "..", "..");
const NUP = path.join(NUP_DIR, fs.readdirSync(NUP_DIR).find(n => n.includes("Ocarina of Time") && n.endsWith(".nup")));
const SHOTS = path.join(__dirname, "shots");

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true, args: ["--window-size=1280,1000"], defaultViewport: { width: 1280, height: 1000 },
  });
  const page = await browser.newPage();
  const t0 = Date.now();
  const lap = s => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${s}`);
  page.on("console", m => console.log("console:", m.text()));
  page.on("pageerror", e => console.log("pageerror:", e.message));
  const client = await page.createCDPSession();
  await client.send("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: SHOTS }).catch(() => {});
  await page.goto(URL_, { waitUntil: "load" });
  await page.screenshot({ path: path.join(SHOTS, "1-loading.png") });
  await page.waitForFunction(() => document.getElementById("pick-game"), { timeout: 180000 });
  lap("engine ready: " + await page.$eval("#status", e => e.textContent));
  await page.screenshot({ path: path.join(SHOTS, "2-ready.png"), fullPage: true });
  const input = await page.$("#game-box input[type=file]");
  await input.uploadFile(NUP);
  await page.waitForFunction(() => document.querySelector("#game-box .ok-dot") || document.querySelector(".pick-error"), { timeout: 120000 });
  lap("game: " + await page.$eval("#game-box", e => e.innerText.replace(/\s+/g, " ")));
  await page.evaluate(() => {
    const b = [...document.querySelectorAll("#groups button")].find(b => b.dataset.g === "cosmetics");
    b.click();
  });
  await page.evaluate(() => {
    const sel = document.querySelector("#settings select");
    sel.value = "Purple";
    sel.dispatchEvent(new Event("change"));
  });
  await page.screenshot({ path: path.join(SHOTS, "3-game.png"), fullPage: true });
  await page.click("#generate");
  let last = "";
  const timer = setInterval(async () => {
    const s = await page.$eval("#status", e => e.textContent).catch(() => "");
    if (s !== last) { last = s; lap("status: " + s); }
  }, 500);
  await page.waitForFunction(() => !document.getElementById("result").hidden || document.querySelector("#status.error"), { timeout: 600000 });
  clearInterval(timer);
  lap("finished: " + await page.$eval("#status", e => e.textContent));
  const info = await page.evaluate(() => ({
    title: document.getElementById("r-title").textContent,
    stats: document.getElementById("r-stats").innerText.replace(/\s+/g, " "),
    href: document.getElementById("r-download").href, name: document.getElementById("r-download").download,
    note: document.getElementById("r-installed").textContent,
  }));
  console.log(info);
  const size = await page.evaluate(async href => (await (await fetch(href)).blob()).size, info.href);
  lap(`zip blob ${(size / 1e6).toFixed(1)} MB`);
  await page.screenshot({ path: path.join(SHOTS, "4-result.png"), fullPage: true });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
