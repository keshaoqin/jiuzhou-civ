// Keyboard & mouse cheat-sheet.
import { icon } from "../ui/icon.js";

const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "");
const MOD = isMac ? "⌘" : "Ctrl";

const ROWS = [
  ["移动", [
    [["拖动", "←↑→↓", "WASD"], "平移地图"],
    [["滚轮", "+", "–"], "放大 / 缩小"],
    [["双击"], "以该点放大"],
    [["双指"], "捏合缩放、拖动平移（触屏）"],
    [["缩略图"], "点击或拖动跳转"],
  ]],
  ["探索", [
    [["点击城市"], "打开城市视图"],
    [["点击陆地"], "打开所属省份"],
    [["/", `${MOD} K`], "搜索城市与省份"],
    [["L", "Shift L"], "下一个 / 上一个镜头"],
    [["图例"], "悬停或拖动色带，只显示该区间"],
    [["R"], "显示 / 隐藏资源"],
  ]],
  ["面板", [
    [["?"], "本帮助"],
    [["Esc"], "依次关闭帮助、搜索、图鉴与面板"],
  ]],
];

export function initHelp() {
  const modal = document.getElementById("help");
  if (!modal) return { open() {}, close() {}, get isOpen() { return false; } };
  const card = modal.querySelector(".help-card");
  let restore = null;
  card.innerHTML = `
    <button class="icon-btn help-close" data-close aria-label="关闭帮助">${icon("close", "✕", { size: 13 })}</button>
    <h2 id="help-title">${icon("help", "?", { size: 22 })}<span>操作指南</span></h2>
    <div class="help-cols">${ROWS.map(([title, rows]) => `
      <section><h3>${title}</h3>${rows.map(([keys, what]) => `
        <div class="help-row"><span class="keys">${keys.map((k) => `<kbd>${k}</kbd>`).join("")}</span><span>${what}</span></div>`).join("")}
      </section>`).join("")}</div>
    <p class="help-foot">每个数字都能追溯到公开数据：打开<b>图鉴</b>查看来源。地址栏链接会重新打开当前视图。
      代码以 MIT 许可开源；数据来源与口径见图鉴。</p>`;

  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    if (restore && document.contains(restore)) restore.focus();
    restore = null;
  };
  modal.addEventListener("click", (e) => {
    if (e.target === modal || e.target.closest("[data-close]")) close();
  });
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    e.preventDefault(); // the only focusable control is the close button
    card.querySelector("[data-close]").focus();
  });

  return {
    open() {
      if (!modal.hidden) return;
      restore = document.activeElement;
      modal.hidden = false;
      card.querySelector("[data-close]").focus();
    },
    close,
    toggle() { modal.hidden ? this.open() : close(); },
    get isOpen() { return !modal.hidden; },
  };
}
