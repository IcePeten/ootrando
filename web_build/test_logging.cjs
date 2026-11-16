const fs = require("fs");
const os = require("os");
const path = require("path");
const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true, defaultViewport: { width: 1280, height: 900 },
  });
  const page = await browser.newPage();
  page.on("response", r => { if (r.url().includes("log.php")) console.log("log.php ->", r.status()); });
  await page.goto(process.argv[2] || "http://localhost:8791/", { waitUntil: "load" });
  await page.waitForFunction(() => document.getElementById("status").innerText.startsWith("Ready"), { timeout: 180000 });
  const fake = path.join(os.tmpdir(), "Not A Real Game.nup");
  fs.writeFileSync(fake, Buffer.alloc(4096, 7));
  const input = await page.$("#game-box input[type=file]");
  await input.uploadFile(fake);
  await page.waitForFunction(() => document.getElementById("status").className.includes("error"), { timeout: 60000 });
  console.log("status:", await page.$eval("#status", e => e.innerText));
  await page.evaluate(() => setTimeout(() => { throw new Error("Test crash from the logging check"); }, 0));
  await new Promise(r => setTimeout(r, 3000));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
