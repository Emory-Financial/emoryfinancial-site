// Render a 1200x630 branded cover (JPEG) for each article that doesn't have one yet.
// Usage: node covers.js <manifest.json> <out_dir>
//   manifest: [{slug, title, topic, topicSlug}]
// Covers are cached in out_dir (src/covers); delete a file to re-render it.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const [, , manifestPath, outDir] = process.argv;
const items = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const fontDir = path.join(__dirname, 'node_modules', '@fontsource');
const font = (pkg, file) => 'data:font/woff2;base64,' + fs.readFileSync(path.join(fontDir, pkg, 'files', file)).toString('base64');

// Simple gold line-art motif per topic (drawn in a 420x420 box).
const MOTIFS = {
  'jobs-and-income': `<rect x="70" y="140" width="280" height="190" rx="22"/><path d="M160 140v-34a22 22 0 0 1 22-22h56a22 22 0 0 1 22 22v34"/><path d="M70 220h280"/><circle cx="210" cy="220" r="16"/><path d="M110 300h40v-40h50M310 300h-40v-40h-50" opacity=".55"/>`,
  'self-employed-and-trades': `<path d="M70 230 210 110l140 120"/><path d="M100 205v135h220V205"/><path d="M175 340v-80h70v80"/><path d="M300 70l40 40-110 110-40-40z" opacity=".6"/><circle cx="330" cy="80" r="26" opacity=".6"/>`,
  'buying-and-remodeling': `<path d="M60 240 200 120l140 120"/><path d="M90 215v125h220V215"/><path d="M160 340v-70h80v70"/><path d="M330 340V60h-120" opacity=".6"/><path d="M330 60l-40 40" opacity=".6"/><path d="M250 60v40" opacity=".6"/><rect x="236" y="100" width="28" height="22" opacity=".6"/>`,
  'family-and-estate': `<path d="M40 250 150 160l110 90"/><path d="M65 230v110h170V230"/><path d="M200 210 290 135l90 75" opacity=".6"/><path d="M220 195v145h140V195" opacity=".6"/><circle cx="125" cy="275" r="16"/><circle cx="175" cy="285" r="12"/><path d="M110 340v-30a15 15 0 0 1 30 0v30M165 340v-22a10 10 0 0 1 20 0v22"/>`,
  'planning': `<path d="M60 340h300"/><rect x="85" y="260" width="50" height="80"/><rect x="160" y="210" width="50" height="130"/><rect x="235" y="150" width="50" height="190"/><path d="M80 210 170 150l60 25 110-95" opacity=".6"/><path d="M300 80h40v40" opacity=".6"/>`,
  'home-equity': `<path d="M50 230 180 120l130 110"/><path d="M80 205v135h200V205"/><circle cx="300" cy="300" r="52" opacity=".6"/><path d="M280 320l40-40M282 290h.1M318 318h.1" opacity=".6" stroke-width="10"/><path d="M150 340v-70h60v70"/>`,
};

function page({ title, topic, topicSlug }) {
  const motif = MOTIFS[topicSlug] || MOTIFS['planning'];
  const size = title.length > 80 ? 54 : title.length > 60 ? 60 : 68;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:SG;src:url(${font('space-grotesk', 'space-grotesk-latin-600-normal.woff2')})}
@font-face{font-family:Plex;src:url(${font('ibm-plex-sans', 'ibm-plex-sans-latin-500-normal.woff2')})}
@font-face{font-family:Mono;src:url(${font('ibm-plex-mono', 'ibm-plex-mono-latin-500-normal.woff2')})}
*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;overflow:hidden;background:#1A1216;color:#fff;font-family:Plex}
.bg{position:absolute;inset:0;background:radial-gradient(900px 520px at 85% 20%,rgba(140,47,57,.55),transparent 70%),radial-gradient(600px 400px at 0% 100%,rgba(200,155,60,.12),transparent 70%)}
.motif{position:absolute;right:56px;top:105px;width:420px;height:420px;fill:none;stroke:#C89B3C;stroke-width:7;stroke-linecap:round;stroke-linejoin:round;opacity:.9}
.wrap{position:absolute;left:72px;top:64px;bottom:60px;width:640px;display:flex;flex-direction:column}
.eyebrow{font-family:Mono;font-size:22px;letter-spacing:.18em;text-transform:uppercase;color:#E8C46A;display:flex;align-items:center;gap:16px}
.eyebrow:before{content:"";width:40px;height:3px;background:#8C2F39;border-radius:2px}
h1{font-family:SG;font-weight:600;font-size:${size}px;line-height:1.08;letter-spacing:-.01em;margin-top:34px}
.by{margin-top:auto;display:flex;align-items:center;gap:18px;font-size:24px;color:rgba(255,255,255,.78)}
.by b{color:#fff;font-weight:500}
.mark{width:58px;height:58px}
.rule{position:absolute;left:0;right:0;bottom:0;height:10px;background:linear-gradient(90deg,#8C2F39,#C89B3C)}
</style></head><body><div class="bg"></div>
<svg class="motif" viewBox="0 0 420 420">${motif}</svg>
<div class="wrap"><div class="eyebrow">Insights · ${topic.replace(/&/g, '&amp;')}</div>
<h1>${title.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</h1>
<div class="by"><svg class="mark" viewBox="0 0 64 64" fill="none" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 34 32 14l24 20" stroke="#fff"/><path d="M14 46h36" stroke="#8C2F39"/></svg>
<span><b>Derek Shao</b> · Emory Financial · NMLS 242117</span></div></div>
<div class="rule"></div></body></html>`;
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const todo = items.filter(i => !fs.existsSync(path.join(outDir, i.slug + '.jpg')));
  if (!todo.length) { console.log('covers: up to date'); return; }
  const browser = await chromium.launch();
  const pg = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  for (const it of todo) {
    await pg.setContent(page(it), { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: path.join(outDir, it.slug + '.jpg'), type: 'jpeg', quality: 84 });
    console.log('covers: rendered', it.slug);
  }
  await browser.close();
})();
