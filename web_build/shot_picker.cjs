const path = require("path");
const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true, defaultViewport: { width: Number(process.argv[2] || 1280), height: 1000 },
  });
  const page = await browser.newPage();
  await page.goto("http://localhost:8790/", { waitUntil: "load" });
  await page.waitForFunction(() => document.getElementById("status").innerText.startsWith("Ready"), { timeout: 180000 });
  const card = await page.evaluateHandle(() => document.getElementById("game-box").closest(".card"));
  await card.screenshot({ path: path.join(__dirname, "shots", `picker-${process.argv[2] || 1280}.png`) });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
