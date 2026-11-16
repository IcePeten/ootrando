const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const BUILD = (document.currentScript && new URL(document.currentScript.src).searchParams.get("v")) || "dev";

const reported = new Set();
function reportError(where, err, extra) {
  if (!window.OOT_ENGINE) return;
  const message = String((err && err.message) || err || "Unknown error").slice(0, 1000);
  const key = where + "|" + message;
  if (reported.has(key) || reported.size >= 25) return;
  reported.add(key);
  const field = id => ($(id) ? $(id).value : "");
  let info = null;
  try { info = state.gameInfo; } catch {}
  const body = JSON.stringify(Object.assign({
    where, message,
    detail: String((err && (err.detail || err.stack)) || "").slice(-12000),
    step: (err && err.step) || "",
    seed: field("seed"),
    settings: field("settings-string"),
    game: info ? `${info.version}, ${info.size_gb} GB` : "",
    build: BUILD,
    memory: navigator.deviceMemory || "",
    cores: navigator.hardwareConcurrency || "",
    screen: `${screen.width}x${screen.height}`,
  }, extra || {}));
  try {
    fetch("log.php", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: body.length < 60000 }).catch(() => {});
  } catch {}
}
window.OOT_REPORT = reportError;
window.addEventListener("error", e => {
  if (!e.error && (!e.filename || !e.filename.startsWith(location.origin))) return;
  reportError("page", e.error || e.message, { source: `${e.filename || ""}:${e.lineno || 0}:${e.colno || 0}` });
});
window.addEventListener("unhandledrejection", e => reportError("promise", e.reason));
document.addEventListener("securitypolicyviolation", e => reportError("blocked", `Blocked ${e.blockedURI || "inline"} by ${e.violatedDirective}`, { source: `${e.sourceFile || ""}:${e.lineNumber || 0}` }));

const api = window.OOT_ENGINE || {
  hosted: false,
  onStatus() {},
  defaults: async () => (await fetch("/api/defaults")).json(),
  randomSeed: async () => (await (await fetch("/api/random_seed")).json()).seed,
  openGame: async () => null,
  generate: async options => (await fetch("/api/generate", { method: "POST", body: JSON.stringify(options) })).json(),
};

const GROUPS = [
  ["main", "Main Rules", "How carefully items are placed, and which roadblocks are cleared before you start."],
  ["shuffle", "Shuffle", "Pick which kinds of places get a random item."],
  ["world", "Hidden Items", "Things lying on the ground, and anything you can break, cut or pick up. Anything Anywhere lets these hold real items too."],
  ["items", "Items & Traps", "What shows up, and whether some of it bites back."],
  ["time", "Timesavers", "Cut down on waiting so more of your time goes to exploring."],
  ["help", "Hints & Help", "Tools for when you get stuck."],
  ["cosmetics", "Cosmetics", "Colors and body swaps for Link."],
];

const SETTINGS = [
  { key: "logic", group: "main", label: "Logic", type: "choice",
    options: [["safe", "Safe"], ["relaxed", "Relaxed"], ["none", "No Logic"]],
    desc: { safe: "The most forgiving option. Checks inside a dungeon or grotto expect you to have every tool that place uses.",
            relaxed: "Like Safe, except a dungeon's own big item only expects the tools you needed to get to it.",
            none: "Items go anywhere with no checks at all. Some seeds cannot be finished." } },
  { key: "open_forest", group: "main", label: "Kokiri Forest", type: "choice",
    options: [["open", "Open"], ["closed_deku", "Closed Deku"], ["closed", "Closed"]],
    desc: { open: "Nobody blocks the way. You can leave the forest or visit the Deku Tree immediately.",
            closed_deku: "You can leave the forest, but Mido still guards the Deku Tree until you have a sword and shield.",
            closed: "Mido and the bridge guard both keep you in until you've earned it, like the original game." } },
  { key: "kakariko_gate", group: "main", label: "Kakariko Gate", type: "choice",
    options: [["closed", "Open with Zelda's Letter"], ["open", "Open"]],
    desc: { closed: "Young Link needs to show Zelda's Letter before the guard lets him onto the mountain path.",
            open: "The guard waves young Link through from the start." } },
  { key: "door_of_time", group: "main", label: "Door of Time", type: "choice",
    options: [["closed", "Closed"], ["open", "Open"]],
    desc: { closed: "Opens the normal way, after collecting the three stones and playing the Song of Time.",
            open: "Already open, with the Master Sword waiting. The story steps for the door are skipped." } },
  { key: "zora_fountain", group: "main", label: "Zora's Fountain", type: "choice",
    options: [["closed", "Closed"], ["open", "Open"]],
    desc: { closed: "King Zora only shifts over after you give him Ruto's Letter.",
            open: "King Zora has already shifted over, so you can walk straight to the fountain." } },
  { key: "gerudo_fortress", group: "main", label: "Gerudo Fortress", type: "choice",
    options: [["vanilla", "Rescue All Carpenters"], ["fast", "Rescue One Carpenter"], ["open", "Open"]],
    desc: { vanilla: "Rescue all four carpenters to earn your membership card.",
            fast: "Only one carpenter is still locked up. Free him to earn the card.",
            open: "The carpenters are already home and the card is in your pocket." } },
  { key: "bridge", group: "main", label: "Rainbow Bridge", type: "choice",
    options: [["vanilla", "Shadow & Spirit Medallions"], ["open", "Always Open"]],
    desc: { vanilla: "The bridge to Ganon's Castle forms once you hold the Shadow and Spirit Medallions.",
            open: "The bridge is already there the first time you visit as an adult." } },
  { key: "ganon_boss_key", group: "main", label: "Ganon's Boss Key", type: "choice",
    options: [["vanilla", "In Ganon's Castle"], ["start", "Start With It"]],
    desc: { vanilla: "The key to Ganondorf's tower is somewhere inside his castle.",
            start: "You already carry the key to Ganondorf's tower." } },
  { key: "trials", group: "main", label: "Ganon's Trials", type: "choice",
    options: [["0", "None"], ["1", "One"], ["2", "Two"], ["3", "Three"], ["4", "Four"], ["5", "Five"], ["6", "All Six"]],
    desc: "How many of the six barrier rooms inside Ganon's Castle you must clear. Which ones are skipped is random, and the spoiler log says which." },
  { key: "shuffle_chests", group: "shuffle", label: "Chests", type: "toggle", desc: "Treasure chests anywhere in the world." },
  { key: "cutscene_chests", group: "shuffle", label: "Cutscene Chests", type: "toggle", desc: "The large chests that usually show a special scene when you open them." },
  { key: "shuffle_npcs", group: "shuffle", label: "Gifts & Rewards", type: "toggle", desc: "Items that characters hand you, such as Darunia, three Great Fairies, the fishing pond and the Skull Kid." },
  { key: "shuffle_shops", group: "shuffle", label: "Shop Stock", type: "toggle", desc: "Shop shelves stock different items." },
  { key: "shuffle_floor", group: "world", label: "Heart Pieces", type: "toggle", desc: "Heart Pieces sitting out in the open." },
  { key: "shuffle_rupees", group: "world", label: "Floor Rupees", type: "toggle", desc: "Rupees lying on the ground may turn into something else." },
  { key: "shuffle_hearts", group: "world", label: "Floor Hearts", type: "toggle", desc: "Hearts lying on the ground may turn into rupees, items or traps." },
  { key: "shuffle_pots", group: "world", label: "Pots & Jars", type: "toggle", desc: "Breaking a pot or jar may reveal an item." },
  { key: "shuffle_crates", group: "world", label: "Crates", type: "toggle", desc: "Breaking a wooden crate may reveal an item." },
  { key: "shuffle_beehives", group: "world", label: "Beehives", type: "toggle", desc: "Knocking down a beehive may drop an item." },
  { key: "shuffle_grass", group: "world", label: "Grass", type: "toggle", desc: "Cutting certain grass may uncover an item." },
  { key: "shuffle_rocks", group: "world", label: "Rocks & Boulders", type: "toggle",
    desc: "Any rock you can lift or boulder you can blow up may hide an item, and the ones that do are painted gold. Logic expects the Goron Bracelet or adult Link for lifting, and bombs or the Megaton Hammer for boulders." },
  { key: "small_anything", group: "world", label: "Anything Anywhere", type: "toggle", desc: "The hidden spots above can hold real equipment, like a sword or the Hookshot. Big items pop out and are collected just by walking into them." },
  { key: "shuffle_maps_compasses", group: "shuffle", label: "Maps & Compasses", type: "toggle", desc: "Each dungeon's map and compass move to a random chest in that same dungeon." },
  { key: "shuffle_songs", group: "shuffle", label: "Songs", type: "toggle",
    desc: "Ten songs swap teachers, so Saria, Malon, Sheik, the windmill and the Royal Tomb each teach a different song. Zelda's Lullaby and the Song of Time don't move." },
  { key: "tokens", group: "shuffle", label: "Gold Skulltula Tokens", type: "choice",
    options: [["off", "Off"], ["dungeons", "Dungeons"], ["overworld", "Overworld"], ["all", "All"]],
    desc: { off: "Every Gold Skulltula leaves its normal token.",
            dungeons: "Gold Skulltulas inside dungeons leave a random item, and their tokens are hidden elsewhere.",
            overworld: "Gold Skulltulas outside dungeons leave a random item, and their tokens are hidden elsewhere.",
            all: "Every Gold Skulltula leaves a random item, and all 100 tokens are hidden around the world." } },
  { key: "scrubs", group: "shuffle", label: "Deku Scrub Sales", type: "toggle",
    desc: "The five Deku Scrubs that sell a Heart Piece or a stick or nut upgrade sell a random item instead." },
  { key: "shuffle_gerudo_card", group: "shuffle", label: "Gerudo Card", type: "toggle",
    desc: "Freeing the carpenters gives a random item, and the membership card itself can be anywhere." },
  { key: "shuffle_frogs", group: "shuffle", label: "Frog Rewards", type: "toggle",
    desc: "Both Heart Pieces from the singing frogs on Zora's River become random items." },
  { key: "shuffle_minigames", group: "shuffle", label: "Minigame Prizes", type: "toggle",
    desc: "First-time prizes from both shooting galleries, the Lost Woods targets, horseback archery, the rolling Goron and Bombchu Bowling." },
  { key: "shuffle_sidequests", group: "shuffle", label: "Side Quest Rewards", type: "toggle",
    desc: "Rewards from the Cucco Lady, Talon, the dog lady, the Poe buyer, the potion shop and the Happy Mask Shop, plus the Forest Stage upgrades." },
  { key: "shuffle_skulltula_rewards", group: "shuffle", label: "Skulltula House", type: "toggle",
    desc: "The family's rewards for 10 through 50 tokens. These never hold anything required to finish." },
  { key: "shuffle_great_fairies", group: "shuffle", label: "Great Fairy Upgrades", type: "toggle",
    desc: "The magic meter, double magic and double defense can be anywhere. Logic makes sure you have magic before the final battle." },
  { key: "shuffle_story_gifts", group: "shuffle", label: "Story Gifts", type: "toggle",
    desc: "Malon's egg, Zelda's Letter and the Light Arrows become random items, and the real ones are hidden in the world." },
  { key: "shuffle_trade_rewards", group: "shuffle", label: "Trading Quest Reward", type: "toggle",
    desc: "The final reward from Biggoron is random. Every trade along the way works as normal." },
  { key: "small_keys", group: "shuffle", label: "Small Keys", type: "choice",
    options: [["vanilla", "Where They Were"], ["anywhere", "Keysanity"], ["keysy", "Doors Unlocked"]],
    desc: { vanilla: "Small keys sit in their normal chests.",
            anywhere: "Small keys from the temples, the well, the training ground and Ganon's Castle can be in any chest. Each key is labeled with its dungeon and counts there no matter where you find it, and logic never expects you to use a key you haven't found.",
            keysy: "Each dungeon starts with all of its keys, so locked doors open right away." } },
  { key: "boss_keys", group: "shuffle", label: "Boss Keys", type: "choice",
    options: [["vanilla", "Where They Were"], ["dungeon", "Own Dungeon"], ["anywhere", "Keysanity"], ["start", "Start With Them"]],
    desc: { vanilla: "Each boss key sits in its temple's big chest.",
            dungeon: "Each boss key is in a random chest inside its own temple.",
            anywhere: "Boss keys can be in any chest outside the other temples, and logic makes sure you have one before you face its boss.",
            start: "You begin with every temple's boss key." } },
  { key: "traps", group: "items", label: "Traps", type: "choice",
    options: [["off", "Off"], ["some", "Some"], ["lots", "Lots"]],
    desc: { off: "Nothing is a trap.", some: "Roughly 1 in 16 small items is a trap. It may freeze you, set you on fire, release a Keese, or cost you 10 rupees.",
            lots: "Roughly 1 in 5 small items is a trap. It may freeze you, set you on fire, release a Keese, or cost you 10 rupees." } },
  { key: "color_breakables", group: "items", label: "Gold Hidden Treasure", type: "toggle",
    desc: "Pots, rocks and crates with something worth having are painted gold. A few are decoys." },
  { key: "item_pool", group: "items", label: "Item Pool", type: "choice",
    options: [["balanced", "Balanced"], ["plentiful", "Plentiful"], ["scarce", "Scarce"]],
    desc: { balanced: "The same items as the original game, one of each.",
            plentiful: "An extra copy of each important item takes the place of some rupee chests.",
            scarce: "Half the Heart Pieces become rupees." } },
  { key: "starting_items", group: "items", label: "Starting Inventory", type: "multi",
    desc: "Equipment you start a new file with. Logic counts these as already found." },

  { key: "skip_intro", group: "time", label: "Skippable Opening", type: "toggle", desc: "Press the skip button during the opening movie, just like other cutscenes." },
  { key: "skip_area_intros", group: "time", label: "Skip Area Intros", type: "toggle", desc: "No camera tour or name banner the first time you enter an area." },
  { key: "skip_zelda", group: "time", label: "Skip Child Zelda", type: "toggle", desc: "Begin with Zelda's Letter and her lullaby, skipping the castle visit." },
  { key: "free_scarecrow", group: "time", label: "Free Scarecrow", type: "toggle", desc: "The scarecrow's song is already learned. Still experimental." },
  { key: "chest_size", group: "time", label: "Chest Size", type: "choice",
    options: [["match", "Matches Contents"], ["small", "All Small"], ["vanilla", "Original"]],
    desc: { match: "Large chests mean something important or a boss key. Everything else comes in a small, quick chest.",
            small: "Every chest is small and opens quickly.",
            vanilla: "Every chest keeps its normal size." } },
  { key: "mask_quest", group: "time", label: "Complete Mask Quest", type: "toggle", desc: "The Happy Mask Shop lends all eight masks from the start." },

  { key: "map_markers", group: "help", label: "Map Markers", type: "toggle", desc: "Every chest, and every important item outside a chest, gets a chest icon on the pause map that disappears once collected. Each area's name shows how many there are." },
  { key: "spoiler", group: "help", label: "Spoiler Log", type: "always", desc: "A file listing every item's location and one order you could collect them in." },
  { key: "places", group: "help", label: "Plain-English Locations", type: "always", desc: "Locations are described with nearby landmarks, like \"near the Kokiri Shop, on the west side\"." },
  { key: "hints", group: "help", label: "Gossip Stone Hints", type: "choice",
    options: [["balanced", "Balanced"], ["strong", "Strong"], ["very_strong", "Very Strong"], ["off", "Off"]],
    desc: { balanced: "Twenty hints, each repeated on two stones. They point to areas worth visiting, areas with nothing important, and where key items are.",
            strong: "The same as Balanced, but hints about items name the exact spot.",
            very_strong: "Forty different hints, nearly all naming the exact spot.",
            off: "Gossip Stones say what they normally say." } },
  { key: "logo", group: "cosmetics", label: "Randomizer Title Logo", type: "always", desc: "The word Randomizer appears under the title logo." },
];

const PRESETS = [
  ["Beginner", "Forgiving logic, no traps", { logic: "safe", traps: "off", small_anything: false, shuffle_pots: false, shuffle_crates: false, shuffle_beehives: false, shuffle_grass: false, shuffle_rocks: false, shuffle_rupees: false, open_forest: "open" }],
  ["Standard", "What I usually play", null],
  ["Full Randomizer", "Everything shuffled, with logic", { logic: "relaxed", traps: "some", small_anything: true,
    shuffle_chests: true, cutscene_chests: true, shuffle_npcs: true, shuffle_shops: true, shuffle_floor: true,
    shuffle_rupees: true, shuffle_hearts: true, shuffle_pots: true, shuffle_crates: true, shuffle_beehives: true,
    shuffle_grass: true, shuffle_rocks: true, shuffle_maps_compasses: true, shuffle_songs: true, tokens: "all",
    scrubs: true, shuffle_gerudo_card: true, shuffle_frogs: true, small_keys: "anywhere", boss_keys: "anywhere",
    shuffle_minigames: true, shuffle_sidequests: true, shuffle_skulltula_rewards: true, shuffle_great_fairies: true,
    shuffle_story_gifts: true, shuffle_trade_rewards: true,
    color_breakables: true, map_markers: true, hints: "balanced" }],
  ["Chaos", "No logic, everything shuffled, many traps", { logic: "none", traps: "lots", small_anything: true,
    shuffle_pots: true, shuffle_crates: true, shuffle_beehives: true, shuffle_grass: true, shuffle_rocks: true, shuffle_rupees: true, shuffle_hearts: true, shuffle_floor: true, open_forest: "open", shuffle_songs: true,
    tokens: "all", scrubs: true, small_keys: "anywhere", boss_keys: "anywhere", chest_size: "match", hints: "balanced",
    shuffle_gerudo_card: true, shuffle_frogs: true, shuffle_minigames: true, shuffle_sidequests: true,
    shuffle_skulltula_rewards: true, shuffle_great_fairies: true, shuffle_story_gifts: true,
    shuffle_trade_rewards: true }],
];

const TITLE_ID = "0400486024DEC000";
const EMULATORS = [
  ["Lichii", "Tested", `%APPDATA%\\lichii\\load\\${TITLE_ID}\\`, `~/.local/share/lichii/load/${TITLE_ID}/`],
  ["Eden", "yuzu family", `%APPDATA%\\eden\\load\\${TITLE_ID}\\`, `~/.local/share/eden/load/${TITLE_ID}/`],
  ["Citron", "yuzu family", `%APPDATA%\\citron\\load\\${TITLE_ID}\\`, `~/.local/share/citron/load/${TITLE_ID}/`],
  ["Sudachi", "yuzu family", `%APPDATA%\\sudachi\\load\\${TITLE_ID}\\`, `~/.local/share/sudachi/load/${TITLE_ID}/`],
  ["Suyu", "yuzu family", `%APPDATA%\\suyu\\load\\${TITLE_ID}\\`, `~/.local/share/suyu/load/${TITLE_ID}/`],
  ["yuzu", "yuzu family", `%APPDATA%\\yuzu\\load\\${TITLE_ID}\\`, `~/.local/share/yuzu/load/${TITLE_ID}/`],
  ["Ryujinx / Ryubing", "Ryujinx family", `%APPDATA%\\Ryujinx\\mods\\contents\\${TITLE_ID}\\`,
    `~/.config/Ryujinx/mods/contents/${TITLE_ID}/ (macOS: ~/Library/Application Support/Ryujinx/mods/contents/${TITLE_ID}/)`],
];

function renderInstall() {
  const html = `
    <ol class="install-steps">
      <li>Download the mod zip above.</li>
      <li>Open your emulator's mod folder for Ocarina of Time. The quickest way is to right-click the game in the emulator's game list and choose <b>Open Mod Data Location</b> (yuzu family) or <b>Open Mods Directory</b> (Ryujinx family). The folders are listed below.</li>
      <li>Unzip the download into that folder. You should end up with <code>${TITLE_ID}/OoT Randomizer/romfs/</code>. If an older seed is there, replace it.</li>
      <li>Start the game and begin a <b>new save file</b>.</li>
    </ol>
    <div class="emu-table">
      <div class="emu-row head"><span>Emulator</span><span>Windows</span><span>Linux</span></div>
      ${EMULATORS.map(([name, tag, win, linux]) => `
        <div class="emu-row">
          <span class="emu-name">${esc(name)}<i class="badge ${tag === "Tested" ? "works" : "planned"}">${esc(tag)}</i></span>
          <code>${esc(win)}</code>
          <code>${esc(linux)}</code>
        </div>`).join("")}
    </div>
    <p class="note">Lichii is the emulator this randomizer is tested on. Other emulators need to support Nintendo Switch 2 games to run it. On Android, use the emulator's mod or add-on option for the game and point it at the unzipped folder.</p>`;
  document.querySelectorAll("[data-install]").forEach(el => el.innerHTML = html);
}

const SPECIAL = ["Default", "Random Choice", "Completely Random", "Custom"];
const state = { defaults: null, options: {}, group: "main", gameReady: !api.hosted, busy: false };

const hex = rgb => "#" + rgb.map(c => c.toString(16).padStart(2, "0")).join("").toUpperCase();
const descFor = (s, v) => typeof s.desc === "string" ? s.desc : s.desc[v] || "";

function switchEl(on, disabled, onToggle) {
  const b = document.createElement("button");
  b.className = "switch" + (on ? " on" : "");
  b.disabled = !!disabled;
  if (!disabled) b.onclick = onToggle;
  return b;
}

function renderGroups() {
  const nav = $("groups");
  nav.innerHTML = GROUPS.map(([id, name]) => `<button data-g="${id}" class="${id === state.group ? "on" : ""}">${name}</button>`).join("");
  nav.querySelectorAll("button").forEach(b => b.onclick = () => { state.group = b.dataset.g; renderGroups(); renderSettings(); });
  $("group-desc").textContent = GROUPS.find(g => g[0] === state.group)[2];
}

function renderSettings() {
  const box = $("settings");
  box.innerHTML = "";
  const list = SETTINGS.filter(s => s.group === state.group);
  if (state.group === "cosmetics") renderColors(box);
  for (const s of list) {
    const el = document.createElement("div");
    el.className = "setting" + (s.soon ? " planned" : "");
    const value = s.soon ? (s.options ? s.options[0][0] : false) : state.options[s.key];
    el.innerHTML = `<div class="head"><span class="label">${esc(s.label)}</span>${s.soon ? '<i class="badge planned">Coming Soon</i>' : ""}</div>`;
    if (s.type === "choice") {
      const sel = document.createElement("select");
      sel.innerHTML = s.options.map(([v, l]) => `<option value="${v}"${String(v) === String(value) ? " selected" : ""}>${esc(l)}</option>`).join("");
      sel.disabled = !!s.soon;
      sel.onchange = () => { state.options[s.key] = sel.value; renderSettings(); updateString(); };
      el.appendChild(sel);
    } else if (s.type === "multi") {
      const chosen = state.options[s.key] || [];
      const grid = document.createElement("div");
      grid.className = "checks";
      for (const [k, label] of Object.entries(state.defaults.starting_choices)) {
        const lab = document.createElement("label");
        lab.innerHTML = `<input type="checkbox"${chosen.includes(k) ? " checked" : ""}>${esc(label)}`;
        lab.querySelector("input").onchange = e => {
          const cur = new Set(state.options[s.key] || []);
          e.target.checked ? cur.add(k) : cur.delete(k);
          state.options[s.key] = [...cur];
          updateString();
        };
        grid.appendChild(lab);
      }
      el.appendChild(grid);
      const actions = document.createElement("div");
      actions.className = "check-actions";
      actions.innerHTML = `<button type="button" data-a="all">Select All</button><button type="button" data-a="none">Clear</button>`;
      actions.querySelectorAll("button").forEach(b => b.onclick = () => {
        state.options[s.key] = b.dataset.a === "all" ? Object.keys(state.defaults.starting_choices) : [];
        renderSettings();
        updateString();
      });
      el.appendChild(actions);
    } else if (s.type === "toggle") {
      el.appendChild(switchEl(value, s.soon, () => { state.options[s.key] = !state.options[s.key]; renderSettings(); updateString(); }));
    } else {
      el.insertAdjacentHTML("beforeend", `<span class="always">Always on</span>`);
    }
    el.insertAdjacentHTML("beforeend", `<div class="desc">${esc(descFor(s, value))}</div>`);
    box.appendChild(el);
  }
}

function renderModels(box) {
  for (const [key, slot] of Object.entries(state.defaults.model_slots || {})) {
    const el = document.createElement("div");
    el.className = "setting";
    const current = state.options.cosmetics[key] || slot.default;
    el.innerHTML = `<div class="head"><span class="label">${esc(slot.label)}</span></div>
      <select>${slot.choices.map(n => `<option${n === current ? " selected" : ""}>${esc(n)}</option>`).join("")}</select>
      <div class="desc">Lunk puts adult Link's body on young Link. Lank stretches young Link's body over adult Link. Purely cosmetic.</div>`;
    el.querySelector("select").onchange = e => { state.options.cosmetics[key] = e.target.value; updateString(); };
    box.appendChild(el);
  }
}

function renderColors(box) {
  const slots = state.defaults.cosmetic_slots;
  state.options.cosmetics = state.options.cosmetics || {};
  renderModels(box);
  for (const [key, slot] of Object.entries(slots)) {
    const el = document.createElement("div");
    el.className = "setting";
    const fallback = slot.match ? "Contrast" : "Default";
    if (!state.options.cosmetics[key]) state.options.cosmetics[key] = fallback;
    const current = state.options.cosmetics[key];
    const isCustom = current.startsWith("#");
    const specials = slot.match ? ["Contrast", "Match Tunic", ...SPECIAL] : SPECIAL;
    el.innerHTML = `<div class="head"><span class="label">${esc(slot.label)}</span></div>
      <div class="color-row"><div class="swatch"></div><select>${
        [...specials, ...Object.keys(slot.palette)].map(n => `<option${(isCustom ? n === "Custom" : n === current) ? " selected" : ""}>${esc(n)}</option>`).join("")
      }</select><input type="color" style="display:none"></div>
      <div class="desc">${slot.match ? "Contrast picks a complementary trim color for the chosen tunic." : "Classic color names, a random pick tied to the seed, or any color you like."}</div>`;
    const sel = el.querySelector("select"), pick = el.querySelector("input"), swatch = el.querySelector(".swatch");
    const paint = () => {
      const v = state.options.cosmetics[key] || "Default";
      pick.style.display = sel.value === "Custom" ? "block" : "none";
      if (v.startsWith("#")) swatch.style.background = v;
      else if (v === "Contrast") swatch.style.background = "linear-gradient(135deg, #1E691B 50%, #95308A 50%)";
      else if (v === "Match Tunic") swatch.style.background = "linear-gradient(135deg, #1E691B 50%, #2a3a33 50%)";
      else if (v === "Default") swatch.style.background = hex(slot.palette[slot.default]);
      else if (slot.palette[v]) swatch.style.background = hex(slot.palette[v]);
      else swatch.style.background = "conic-gradient(red, yellow, lime, cyan, blue, magenta, red)";
    };
    pick.value = isCustom ? current : hex(slot.palette[slot.default]);
    sel.onchange = () => { state.options.cosmetics[key] = sel.value === "Custom" ? pick.value.toUpperCase() : sel.value; paint(); updateString(); };
    pick.oninput = () => { state.options.cosmetics[key] = pick.value.toUpperCase(); paint(); updateString(); };
    paint();
    box.appendChild(el);
  }
}

function liveKeys() {
  return SETTINGS.filter(s => !s.soon && s.type !== "always").map(s => s.key);
}

function updateString() {
  const out = {};
  for (const k of liveKeys()) out[k] = state.options[k];
  out.cosmetics = state.options.cosmetics;
  $("settings-string").value = btoa(unescape(encodeURIComponent(JSON.stringify(out)))).replace(/=+$/, "");
}

function loadString() {
  try {
    const data = JSON.parse(decodeURIComponent(escape(atob($("settings-string").value.trim()))));
    for (const k of liveKeys()) if (k in data) state.options[k] = data[k];
    if (data.cosmetics) state.options.cosmetics = data.cosmetics;
    renderSettings();
    setStatus("Settings loaded.");
  } catch (e) {
    reportError("settings-string", e, { input: $("settings-string").value.slice(0, 2000) });
    setStatus("That settings string could not be read.", "error");
  }
}

function applyPreset(values) {
  for (const k of liveKeys()) state.options[k] = state.defaults[k];
  Object.assign(state.options, values || {});
  renderSettings();
  updateString();
}

function renderPresets() {
  const box = $("presets");
  box.innerHTML = "";
  for (const [name, desc, values] of PRESETS) {
    const b = document.createElement("button");
    b.className = "preset";
    b.innerHTML = `<div class="name">${name}</div><div class="desc">${desc}</div>`;
    b.onclick = () => { applyPreset(values); setStatus(`${name} settings applied.`); };
    box.appendChild(b);
  }
}

function renderPicker(info, error, warning) {
  const box = $("game-box");
  box.className = "game-box picker" + (info ? "" : " missing");
  const meta = info && [info.size_gb ? `${info.size_gb} GB` : info.source, `Title ${info.title_id}`, info.version].filter(Boolean).map(esc).join(" &middot; ");
  box.innerHTML = info
    ? `<div class="name"><span class="ok-dot"></span>${esc(info.name)}</div>
       <div class="meta">${meta}</div>
       ${warning ? `<div class="pick-warn">${esc(warning)}</div>` : ""}
       <div class="pick-buttons">
         <button class="ghost" id="pick-game">Choose a Different File</button>
         <button class="ghost" id="pick-folder">Choose a Different Folder</button>
       </div>`
    : `<div class="name">Choose your game</div>
       <div class="meta">Your game is read on your computer and never uploaded.</div>
       <div class="pick-buttons">
         <button class="primary" id="pick-game">Choose Game File</button>
         <button class="ghost" id="pick-folder">Choose Extracted Folder</button>
       </div>
       <div class="meta">Fully supported: <b>.nup</b> files and extracted <b>RomFS folders</b>.</div>
       <div class="meta">NSP, XCI and similar files: it will try. If it can't read one, it sends me a short note about how the file is laid out so I can add support. No game data is ever sent.</div>
       ${error ? `<div class="pick-error">${esc(error)}</div>` : ""}`;
  const input = document.createElement("input");
  input.type = "file";
  input.hidden = true;
  const folderInput = document.createElement("input");
  folderInput.type = "file";
  folderInput.webkitdirectory = true;
  folderInput.hidden = true;
  box.append(input, folderInput);
  $("pick-game").onclick = () => input.click();
  $("pick-folder").onclick = async () => {
    if (!window.showDirectoryPicker) return folderInput.click();
    let dir;
    try {
      dir = await window.showDirectoryPicker({ id: "oot-romfs", mode: "read" });
    } catch (e) {
      if (e.name !== "AbortError") reportError("folder-picker", e);
      return;
    }
    loadGame("folder", () => folderFromHandle(dir));
  };
  folderInput.onchange = () => {
    if (folderInput.files.length) loadGame("folder", () => folderFromList(folderInput.files));
  };
  input.onchange = () => {
    const file = input.files[0];
    if (file) loadGame("file", () => file, file);
  };
}

async function loadGame(kind, getSource, file) {
  state.gameReady = false;
  state.gameInfo = null;
  updateGenerate();
  setStatus(kind === "file" ? "Reading your game file" : "Looking through the folder", "busy");
  try {
    const source = await getSource();
    const info = kind === "file" ? await api.openGame(source) : await api.openFolder(source);
    state.gameReady = true;
    state.gameInfo = info;
    let warning = "";
    if (info.known_version === false) {
      warning = "I couldn't recognise this game version. The mod may not match it, so if anything goes wrong, try a .nup file instead. A short report was sent to me so I can look into it.";
      reportError("folder-version", "Unknown RomFS folder version", { detail: JSON.stringify({ hashes: info.hashes, missing: info.missing }) });
    } else if (info.missing && info.missing.length) {
      reportError("folder-missing", `RomFS folder is missing ${info.missing.length} files`, { detail: info.missing.join("\n") });
    }
    renderPicker(info, null, warning);
    setStatus("Game found. Pick your settings and generate a seed.");
  } catch (e) {
    const what = file ? { file: `${file.name.includes(".") ? file.name.split(".").pop() : "no extension"} file, ${(file.size / 1e9).toFixed(2)} GB` } : {};
    if (e.unsupported) {
      reportError("unsupported-format", e, what);
      const known = e.format !== "unknown";
      const message = (known
        ? `This looks like an ${e.format} file (${e.contents}). It is encrypted, so it can't be read in the browser yet. `
        : "This isn't a game format we recognise yet. ") +
        `A short report about how the file is laid out (${known ? "file names and sizes only, " : ""}no game data) was sent to me so I can add support. ` +
        "For now, please use a .nup file or an extracted RomFS folder.";
      renderPicker(null, message);
      setStatus("This game format isn't supported yet.", "error");
    } else {
      reportError(kind === "file" ? "open-game" : "open-folder", e, what);
      renderPicker(null, e.message);
      setStatus(e.message, "error");
    }
  }
  updateGenerate();
}

let neededFiles = null;
async function needed() {
  neededFiles = neededFiles || (await (await fetch("romfs-files.json")).json());
  return neededFiles;
}

const MARKER = "Pack/ZsDic.pack.zs";

async function folderFromHandle(dir) {
  const list = await needed();
  const dirs = new Map();
  const dirFor = async (root, parts) => {
    let handle = root, key = "";
    for (const part of parts) {
      key += part + "/";
      if (!dirs.has(key)) dirs.set(key, handle.getDirectoryHandle(part));
      handle = await dirs.get(key);
    }
    return handle;
  };
  const fileAt = async (root, path) => {
    const parts = path.split("/");
    const name = parts.pop();
    return (await (await dirFor(root, parts)).getFileHandle(name)).getFile();
  };
  let root = null;
  for (const candidate of ["", "romfs", "RomFS"]) {
    try {
      const sub = candidate ? await dir.getDirectoryHandle(candidate) : dir;
      await (await sub.getDirectoryHandle("Pack")).getFileHandle("ZsDic.pack.zs");
      root = sub;
      break;
    } catch {}
  }
  if (!root) throw new Error("Couldn't find the game files in that folder. Choose the romfs folder you extracted from Ocarina of Time.");
  dirs.clear();
  const found = new Map();
  for (const folder of list.dirs) {
    setStatus(`Finding game files in ${folder}`, "busy");
    try {
      const handle = await dirFor(root, folder.split("/"));
      const pending = [];
      for await (const [name, h] of handle.entries()) {
        if (h.kind === "file") pending.push(h.getFile().then(f => found.set(`${folder}/${name}`, f)));
      }
      await Promise.all(pending);
    } catch {}
  }
  const rest = list.files.filter(path => !found.has(path));
  for (let i = 0; i < rest.length; i += 48) {
    setStatus(`Finding game files (${Math.min(i + 48, rest.length)} of ${rest.length})`, "busy");
    await Promise.all(rest.slice(i, i + 48).map(path => fileAt(root, path).then(f => found.set(path, f), () => null)));
  }
  return [...found];
}

async function folderFromList(fileList) {
  const list = await needed();
  const wanted = new Set(list.files), folders = new Set(list.dirs);
  const files = [...fileList];
  const marker = files.find(f => (f.webkitRelativePath || f.name).endsWith("/" + MARKER));
  if (!marker) throw new Error("Couldn't find the game files in that folder. Choose the romfs folder you extracted from Ocarina of Time.");
  const prefix = marker.webkitRelativePath.slice(0, -MARKER.length);
  const entries = [];
  for (const f of files) {
    const rel = f.webkitRelativePath;
    if (!rel.startsWith(prefix)) continue;
    const path = rel.slice(prefix.length);
    if (wanted.has(path) || folders.has(path.slice(0, path.lastIndexOf("/")))) entries.push([path, f]);
  }
  return entries;
}

function updateGenerate() {
  $("generate").disabled = state.busy || !state.gameReady || !state.defaults;
}

function renderGame(g) {
  if (g.picker) return renderPicker(null);
  const box = $("game-box");
  if (!g.found) {
    box.className = "game-box missing";
    box.innerHTML = `<div class="name">No game found</div><div class="meta">Place your Ocarina of Time .nup next to the OoT Studio folder.</div>`;
    return;
  }
  box.className = "game-box";
  box.innerHTML = `<div class="name"><span class="ok-dot"></span>${esc(g.name)}</div>
    <div class="meta">${g.size_gb} GB &middot; Title ${esc(g.title_id)} &middot; ${esc(g.version)}</div>`;
}

function setStatus(text, kind) {
  const el = $("status");
  el.className = "status" + (kind === "error" ? " error" : "");
  el.innerHTML = kind === "busy" ? `<span class="spinner"></span>${esc(text)}` : esc(text);
}

function renderResult(r) {
  $("result").hidden = false;
  $("r-title").textContent = `Seed ${r.seed}`;
  const noLogic = state.options.logic === "none";
  const stats = [[r.locations, "Locations"], [r.moved, "Items Moved"], [r.hidden, "Gold Treasures"], [r.traps, "Traps"]];
  if (!noLogic) stats.push([r.rounds.length, "Rounds"]);
  $("r-stats").innerHTML = stats.map(([n, l]) => `<div class="stat"><div class="n">${n}</div><div class="l">${l}</div></div>`).join("");
  $("r-download").href = r.download;
  $("r-spoiler").href = r.spoiler_url;
  if (r.download_name) $("r-download").download = r.download_name;
  if (r.spoiler_name) $("r-spoiler").download = r.spoiler_name;
  $("r-installed").textContent = r.mods_dir
    ? `Already installed for Lichii in ${r.mods_dir}. Start a new save file to play.`
    : noLogic ? "No Logic seeds have no guaranteed route, so this seed may not be beatable." : "";
  $("r-installed").hidden = !$("r-installed").textContent;
  $("result").scrollIntoView({ behavior: "smooth" });
}

async function generate() {
  state.busy = true;
  updateGenerate();
  setStatus("Placing items, checking the playthrough and building the mod. This takes a minute or two.", "busy");
  const options = { cosmetics: state.options.cosmetics, seed: $("seed").value };
  for (const k of liveKeys()) options[k] = state.options[k];
  try {
    const r = await api.generate(options);
    if (!r.ok) { setStatus(r.error, "error"); return; }
    $("seed").value = r.seed;
    setStatus(`Seed ${r.seed} is ready.`);
    renderResult(r);
  } catch (e) {
    reportError("generate", e);
    setStatus(api.hosted ? e.message : "The generator stopped responding. Is the OoT Website window still open?", "error");
  } finally {
    state.busy = false;
    updateGenerate();
  }
}

const CONTACT = "IcePeten@gmail.com";

function setupFeedback() {
  const modal = $("feedback"), form = $("feedback-form"), status = $("fb-status"), send = $("fb-send");
  const say = (html, error) => { status.className = "status" + (error ? " error" : ""); status.innerHTML = html; };
  const open = () => { modal.hidden = false; say(""); form.message.focus(); };
  const close = () => { modal.hidden = true; };
  $("open-feedback").onclick = open;
  document.querySelectorAll("[data-report-logic]").forEach(a => a.onclick = e => {
    e.preventDefault();
    form.kind.value = "Logic Problem";
    if (!form.message.value) form.message.value = "Where I got stuck, and the item I expected to reach:\n";
    open();
  });
  document.querySelectorAll("[data-goto]").forEach(a => a.onclick = e => {
    e.preventDefault();
    showView(a.dataset.goto);
    $("views").scrollIntoView({ behavior: "smooth" });
  });
  $("close-feedback").onclick = close;
  modal.onclick = e => { if (e.target === modal) close(); };
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !modal.hidden) close(); });
  form.onsubmit = async e => {
    e.preventDefault();
    if (form.message.value.trim().length < 5) return say("Please write a little more before sending.", true);
    const data = new FormData(form);
    if ($("fb-attach").checked) {
      data.append("seed", $("seed").value);
      data.append("settings", $("settings-string").value);
    }
    send.disabled = true;
    say(`<span class="spinner"></span>Sending`);
    const fallback = `You can also email <a href="mailto:${CONTACT}?subject=${encodeURIComponent("OoT Randomizer " + data.get("kind"))}">${CONTACT}</a> directly.`;
    try {
      const res = await fetch("feedback.php", { method: "POST", body: data });
      const r = await res.json();
      if (!r.ok) {
        if (res.status >= 500) reportError("feedback", r.error, { status: res.status });
        return say(`${esc(r.error)} ${fallback}`, true);
      }
      form.message.value = "";
      say("Thanks, I got it. I'll read it soon.");
    } catch (e) {
      reportError("feedback", e);
      say(`The message could not be sent from here. ${fallback}`, true);
    } finally {
      send.disabled = false;
    }
  };
}

function setupGallery() {
  const shots = [...document.querySelectorAll(".showcase .shot")];
  const box = $("lightbox");
  if (!shots.length || !box) return;
  const items = shots.map(f => ({
    src: f.querySelector("a").getAttribute("href"),
    alt: f.querySelector("img").alt,
    title: f.querySelector("figcaption b").textContent,
    text: f.querySelector("figcaption").lastChild.textContent.trim(),
  }));
  const img = $("lb-img"), cap = $("lb-caption"), dots = $("lb-dots");
  let index = 0;
  dots.innerHTML = items.map((it, i) => `<button type="button" aria-label="Screenshot ${i + 1}: ${esc(it.title)}"></button>`).join("");
  const show = i => {
    index = (i + items.length) % items.length;
    const it = items[index];
    img.src = it.src;
    img.alt = it.alt;
    cap.innerHTML = `<b>${esc(it.title)}</b>${esc(it.text)}`;
    [...dots.children].forEach((d, n) => d.classList.toggle("on", n === index));
    [index - 1, index + 1].forEach(n => { new Image().src = items[(n + items.length) % items.length].src; });
  };
  const open = i => { show(i); box.hidden = false; document.body.style.overflow = "hidden"; $("lb-next").focus(); };
  const close = () => { box.hidden = true; document.body.style.overflow = ""; };
  shots.forEach((f, i) => { f.querySelector("a").onclick = e => { e.preventDefault(); open(i); }; });
  [...dots.children].forEach((d, i) => { d.onclick = () => show(i); });
  $("lb-prev").onclick = () => show(index - 1);
  $("lb-next").onclick = () => show(index + 1);
  $("lb-close").onclick = close;
  box.onclick = e => { if (e.target === box || e.target.classList.contains("lb-stage")) close(); };
  document.addEventListener("keydown", e => {
    if (box.hidden) return;
    if (e.key === "ArrowLeft") show(index - 1);
    else if (e.key === "ArrowRight") show(index + 1);
    else if (e.key === "Escape") close();
  });
  let startX = null;
  box.addEventListener("touchstart", e => { startX = e.touches[0].clientX; }, { passive: true });
  box.addEventListener("touchend", e => {
    if (startX === null) return;
    const dx = e.changedTouches[0].clientX - startX;
    startX = null;
    if (Math.abs(dx) > 45) show(index + (dx < 0 ? 1 : -1));
  });
}

function showView(name) {
  document.querySelectorAll("#views button").forEach(b => b.classList.toggle("on", b.dataset.view === name));
  document.querySelectorAll(".view").forEach(v => v.hidden = v.id !== `view-${name}`);
}

async function init() {
  renderInstall();
  setupFeedback();
  setupGallery();
  document.querySelectorAll("#views button").forEach(b => b.onclick = () => showView(b.dataset.view));
  api.onStatus(text => setStatus(text, "busy"));
  $("generate").disabled = true;
  if (api.hosted) setStatus("Loading the randomizer engine. The first visit downloads about 15 MB.", "busy");
  let d;
  try {
    d = await api.defaults();
  } catch (e) {
    reportError("engine-load", e);
    setStatus("The randomizer engine could not load: " + e.message, "error");
    return;
  }
  state.defaults = d;
  for (const k of liveKeys()) state.options[k] = d[k];
  state.options.cosmetics = {};
  $("seed").value = d.seed;
  renderGame(d.game);
  renderPresets();
  renderGroups();
  renderSettings();
  updateString();
  $("reroll").onclick = async () => { $("seed").value = await api.randomSeed(); };
  $("copy-string").onclick = () => { navigator.clipboard.writeText($("settings-string").value); setStatus("Settings string copied."); };
  $("load-string").onclick = loadString;
  $("generate").onclick = generate;
  updateGenerate();
  setStatus(api.hosted ? "Ready. Choose your game file to begin." : "");
}

init();
