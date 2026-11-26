export function compact(n) {
  if (n == null || Number.isNaN(n)) return "–";
  const a = Math.abs(n);
  if (a >= 1e12) return (n / 1e12).toFixed(a >= 1e13 ? 1 : 2) + "万亿";
  if (a >= 1e8) return (n / 1e8).toFixed(a >= 1e10 ? 0 : 1).replace(/\.0$/, "") + "亿";
  if (a >= 1e4) return (n / 1e4).toFixed(a >= 1e6 ? 0 : 1).replace(/\.0$/, "") + "万";
  return String(Math.round(n));
}

export const money = (n) => (n == null ? "–" : "¥" + compact(n));
export const dollars = (n) => (n == null ? "–" : "¥" + Math.round(n).toLocaleString("zh-CN"));
export const int = (n) => (n == null ? "–" : Math.round(n).toLocaleString("zh-CN"));
export const pct = (x, d = 1) => (x == null ? "–" : (x * 100).toFixed(d) + "%");

export function yieldValue(y, v) {
  return (y.unit === "usd" || y.unit === "cny") ? money(v) : compact(v);
}

export function popShort(n) {
  if (n >= 1e8) return (n / 1e8).toFixed(n >= 1e9 ? 0 : 1).replace(/\.0$/, "") + "亿";
  if (n >= 1e4) return Math.round(n / 1e4) + "万";
  return String(Math.round(n));
}

export const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
