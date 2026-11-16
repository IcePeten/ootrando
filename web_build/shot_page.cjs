const path = require("path");
const puppeteer = require("puppeteer-core");

(async () => {
  const width = Number(process.argv[2] || 1280);
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true, defaultViewport: { width, height: width < 700 ? 820 : 860, isMobile: width < 700, hasTouch: width < 700 },
  });
  const page = await browser.newPage();
  page.on("console", m => { if (m.type() === "error") console.log("console:", m.text()); });
  page.on("pageerror", e => console.log("pageerror:", e.message));
  await page.goto("http://localhost:8790/", { waitUntil: "networkidle0", timeout: 120000 });
  const out = name => path.join(__dirname, "shots", `${name}-${width}.png`);
  await page.click(".showcase .shots .shot:nth-child(2) a");
  await new Promise(r => setTimeout(r, 400));
  const state = () => page.evaluate(() => ({ open: !document.getElementById("lightbox").hidden, src: document.getElementById("lb-img").getAttribute("src") }));
  console.log("opened:", await state());
  await page.screenshot({ path: out("lightbox") });
  await page.keyboard.press("ArrowRight");
  console.log("right:", await state());
  await page.click("#lb-next");
  console.log("next:", await state());
  await page.click("#lb-next");
  console.log("wrap:", await state());
  await page.click("#lb-prev");
  console.log("prev:", await state());
  await page.keyboard.press("Escape");
  console.log("esc:", await state());
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
