const path = require("path");
const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true, defaultViewport: { width: 1280, height: 900 },
  });
  const page = await browser.newPage();
  page.on("pageerror", e => console.log("pageerror:", e.message));
  await page.goto("http://localhost:8790/", { waitUntil: "load" });
  await page.waitForFunction(() => document.getElementById("pick-game"), { timeout: 120000 });
  await page.screenshot({ path: path.join(__dirname, "shots", "5-top.png"), clip: { x: 0, y: 0, width: 1280, height: 360 } });
  console.log("donate href:", await page.$eval(".top-btn.donate", a => a.href));
  await page.click("#open-feedback");
  await page.type("textarea[name=message]", "Testing the feedback form.");
  await page.click("#fb-send");
  await page.waitForFunction(() => !document.getElementById("fb-send").disabled, { timeout: 20000 });
  console.log("status:", await page.$eval("#fb-status", e => e.innerText));
  await page.screenshot({ path: path.join(__dirname, "shots", "6-feedback.png") });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
