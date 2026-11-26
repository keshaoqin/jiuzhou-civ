// 图鉴（Almanac）：每个数字的含义与数据来源。
import { resolveTables } from "../terrain.js";
import { esc } from "../format.js";
import { parseHex, luminance } from "../color.js";
import { icon, glyph } from "../ui/icon.js";

const COVER_ICON = { forest_deciduous: "l-forest", forest_evergreen: "l-forest", forest_mixed: "l-forest", cropland: "l-farmland", pasture: "l-farmland", urban: "l-developed" };
const inkOn = (hex) => {
  try { return /^#[0-9a-f]{6}$/i.test(hex || "") && luminance(parseHex(hex)) > 0.4 ? "#1c1710" : "#f8f0d8"; } catch { return "#f8f0d8"; }
};

export function initPedia(data) {
  const modal = document.getElementById("pedia");
  const card = modal.querySelector(".modal-card");
  const nav = document.getElementById("pedia-nav");
  const body = document.getElementById("pedia-body");
  const srcName = (id) => data.sources?.find((s) => s.id === id)?.title || id || "";
  let restoreFocus = null;
  const h2 = (ic, fb, text) => `<h2>${icon(ic, fb, { size: 24 })}<span>${esc(text)}</span></h2>`;

  const pages = {
    "About this map": () => `
      ${h2("pedia", "📖", "关于本图")}
      <p>这是用真实公开数据绘制的中国，像一张回合制战略地图。地形、城市、产出、资源与奇观都来自公开统计与地理数据；无法逐市获得的数据用模型估算，并在相应图层注明。</p>
      <h4>怎么做的</h4>
      <p>32 个省级行政区（含台湾）采用 Albers 等面积投影（标准纬线 25°N / 47°N，中央经线 105°E），切成 ${data.world.grid.cols}×${data.world.grid.rows} 个尖顶六边形，每格约 1,624 平方公里。每个格子按采样点归入省与地级市；高程来自 AWS Terrarium 地形瓦片（约 2 km 分辨率）。</p>
      <p><b>城市</b>是地级行政单元（直辖市为一个整体）。人口与 GDP 采用 2023–2024 年公开统计；城市内部的分布、就业结构与部分民生指标由省级结构和城市类型模型推算，图鉴与城市面板会标注。</p>
      <h4>操作</h4>
      <p>拖动或方向键 / WASD 平移 · 滚轮、+/− 或双击缩放 · 点击城市或省份打开详情 · / 或 ⌘K 搜索 · L 切换镜头 · R 显示资源 · ? 查看快捷键 · Esc 关闭。</p>
      <p>地址栏始终保存当前视图（镜头、选中项、位置），可用「分享」复制链接或下载图片。</p>`,
    Yields: () => `
      ${h2("y-production", "⚙️", "产出")}
      <p>《文明》的产出对应到真实指标。粮食、生产、科技、文化是<b>就业人口</b>（按常住地统计），金币是<b>GDP</b>（按生产地统计）。</p>
      <table>${data.nation.yields.map((y) => `<tr><td class="ic" style="color:${esc(y.color)}">${glyph(y, 26)}</td><td><b style="color:${esc(y.color)}">${esc(y.label)}${y.key === "gold" ? "（GDP）" : ""}</b><br>${esc(y.description)}</td></tr>`).join("")}</table>
      <h4>民生与住房</h4>
      <p>失业率为城镇调查失业率附近值；租金收入比 = 月租金 × 12 ÷ 居民可支配收入，是粗略的负担信号。</p>`,
    States: () => `
      ${h2("terrain", "🗺️", "省份")}
      <p>点击没有城市banner的陆地格子会打开所属省份。省份数字来自同一套省级统计（${esc(data.nation.vintage)}${data.nation.gdp_vintage ? `；GDP 来自 ${esc(data.nation.gdp_vintage)}` : ""}），不是城市加总，因此包含乡村地区。</p>
      <p><b>排名</b>覆盖 32 个省级行政区（含台湾，不含港澳），1 为最大。</p>`,
    Terrain: () => {
      const t = data.w?.tables || resolveTables(data.world.tables);
      const hasCover = Array.isArray(data.world.cover);
      const row = (x) => `<tr><td class="nm">${x.color ? `<span class="swatch" style="background:${esc(x.color)}"></span>` : ""}${COVER_ICON[x.key] ? icon(COVER_ICON[x.key], "", { size: 15 }) + " " : ""}<b>${esc(x.name)}</b></td><td>${esc(x.rule || "")}</td></tr>`;
      return `
      ${h2("terrain", "🗺️", "地形")}
      <p>每个格子取 7 个采样点的平均高程；起伏等级由格内高程标准差与平均高程判定。山体阴影按西北方向光照计算。</p>
      <h4>${icon("l-forest", "🌲", { size: 16 })} 土地覆盖</h4>
      ${hasCover
        ? `<p>底色是格子的主导土地覆盖类型，小图标显示混合比例：树木 = 森林，田块 = 耕地，芦苇 = 湿地，灌丛与草叶 = 荒漠/草地。</p>
           <table>${t.cover.filter((x) => x.id > 0).map(row).join("")}</table>`
        : `<p class="muted">本数据版本没有土地覆盖层，陆地按高程着色。</p>`}
      <h4>起伏</h4>
      <table>${t.relief.map(row).join("")}</table>
      <h4>${icon("r-hydro", "💧", { size: 16 })} 水域</h4>
      <table>${t.water.filter((x) => x.id > 0).map(row).join("")}</table>
      <p class="muted">邻国陆地以浅雾显示，仅作地理上下文。</p>`;
    },
    Lenses: () => `
      ${h2("layers", "▤", "镜头")}
      <p>镜头用一项指标给每个格子上色（${esc(data.lenses.vintage)}）。图例显示格值分布；悬停或拖动可只显示某个区间。</p>
      ${(data.lenses.groups || []).map((g) => {
        const ls = data.lenses.lenses.filter((l) => l.group === g.id);
        if (!ls.length) return "";
        return `${g.name ? `<h3 class="grp">${esc(g.name)}</h3>` : ""}${ls.map((l) => `
          <div class="lens-entry"><div class="le-ic">${glyph(l, 26)}</div><div>
          <h4>${esc(l.name)}</h4><p>${esc(l.description)}<br>
          <i class="le-ramp" style="background:linear-gradient(90deg, ${(l.ramp || []).map(esc).join(",")})"></i>
          <span class="muted">${esc(l.scale)} · ${l.domain[0].toLocaleString()}–${l.domain[1].toLocaleString()} ${esc(l.unit)}${l.note ? ` · ${esc(l.note)}` : ""}${l.source ? ` · ${esc(srcName(l.source))}` : ""}</span></p></div></div>`).join("")}`;
      }).join("")}`,
    Resources: () => {
      const r = data.resources;
      if (!r?.types?.length) return `${h2("resources", "⛏️", "资源")}<p class="muted">本数据版本没有资源图层。</p>`;
      const count = new Map();
      for (const it of r.items || []) count.set(it.type, (count.get(it.type) || 0) + 1);
      const cats = [...new Set(r.types.map((t) => t.category || "other"))];
      const catName = { energy: "能源", mineral: "矿产", agri: "油气" };
      return `
      ${h2("resources", "⛏️", "资源")}
      <p>资源图标标出规模以上电厂、矿区与油气田；每种类型的门槛写在说明里。缩小时每格显示优先级最高的资源，放大后可看到更多。按 <b>R</b> 开关。</p>
      ${cats.map((c) => `<h4>${esc(catName[c] || c)}</h4><table class="res-table">
        <tr><th></th><th>类型</th><th>计入标准</th><th>数量</th></tr>
        ${r.types.filter((t) => (t.category || "other") === c).map((t) => `<tr>
          <td class="ic"><span class="res-ic" style="background:${esc(t.color || "#24384f")};color:${inkOn(t.color)}">${glyph(t, 20)}</span></td>
          <td class="nm"><b>${esc(t.name)}</b>${t.unit ? `<br><span class="muted">单位：${esc(t.unit)}</span>` : ""}</td>
          <td>${esc(t.description || "")}<br><span class="muted">来源：${esc(srcName(t.source))}</span></td>
          <td class="num">${count.get(t.id) || 0}</td></tr>`).join("")}</table>`).join("")}`;
    },
    Sources: () => `
      ${h2("pedia", "📖", "数据来源")}
      ${data.sources.map((s) => `
        <h4>${esc(s.title)}</h4>
        <p>${esc(s.description)}<br>
        <span class="muted">${esc(s.publisher)} · ${esc(s.license)}${s.vintage ? " · " + esc(s.vintage) : ""}${s.homepage ? ` · <a href="${esc(s.homepage)}" target="_blank" rel="noopener">主页</a>` : ""}</span></p>
        <table>${(s.files || []).map((f) => `<tr><td><code>${esc(f.url)}</code></td><td class="muted" style="white-space:nowrap">${esc((f.retrieved || "").slice(0, 10))}<br>${((f.bytes || 0) / 1e6).toFixed(1)} MB</td></tr>`).join("")}</table>`).join("")}`,
  };

  const show = (name) => {
    if (!pages[name]) name = "About this map";
    body.innerHTML = pages[name]();
    body.scrollTop = 0;
    nav.querySelectorAll("button").forEach((b) => {
      const on = b.dataset.page === name;
      b.classList.toggle("active", on);
      b.setAttribute("aria-current", on ? "page" : "false");
    });
  };
  const labels = { "About this map": "关于本图", "Yields": "产出", "States": "省份", "Terrain": "地形", "Lenses": "镜头", "Resources": "资源", "Sources": "数据来源" };
  nav.innerHTML = `<div class="hd">图鉴</div>` + Object.keys(pages).map((p) => `<button data-page="${esc(p)}">${esc(labels[p] || p)}</button>`).join("");
  nav.onclick = (e) => {
    const b = e.target.closest("button[data-page]");
    if (b) show(b.dataset.page);
  };
  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    if (restoreFocus && document.contains(restoreFocus)) restoreFocus.focus();
    restoreFocus = null;
  };
  modal.onclick = (e) => {
    if (e.target === modal || e.target.closest("[data-close]")) close();
  };
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...card.querySelectorAll("button, a[href], [tabindex]:not([tabindex='-1'])")].filter((x) => x.offsetParent);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  return {
    open(name = "About this map") {
      restoreFocus = document.activeElement;
      show(name);
      modal.hidden = false;
      requestAnimationFrame(() => card.querySelector("button")?.focus());
    },
    close,
  };
}
