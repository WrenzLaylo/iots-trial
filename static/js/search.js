// Pure search helpers for the blog's instant search (no DOM). Unit-tested in tests/js/search.test.mjs.
const DIACRITICS = /[\u0300-\u036f]/g;

export function normalize(s) {
  return String(s ?? '').normalize('NFD').replace(DIACRITICS, '').toLowerCase()
    .replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, ' ').trim();
}

export function tokens(q) {
  const n = normalize(q);
  return n ? n.split(' ') : [];
}

export function buildIndex(raw) {
  return raw.posts.map(([title, link, date, ti, mins, excerpt, lang]) => {
    const topic = ti >= 0 && raw.topics[ti] ? raw.topics[ti] : null;
    return {
      title, link, date, mins, excerpt, lang: lang || '',
      topic: topic ? topic.name : '', topicSlug: topic ? topic.slug : '',
      icon: topic ? topic.icon : 'newspaper', tone: topic ? topic.tone : 'pale',
      titleNorm: normalize(title),
      hay: normalize(`${title} ${topic ? topic.name : ''} ${excerpt}`),
    };
  });
}

export function searchPosts(items, { q = '', topic = '' } = {}) {
  const toks = tokens(q);
  const hits = [];
  for (const it of items) {
    if (topic && it.topic !== topic) continue;
    if (!toks.every((t) => it.hay.includes(t))) continue;
    hits.push({ it, score: toks.filter((t) => it.titleNorm.includes(t)).length });
  }
  hits.sort((a, b) => b.score - a.score || (a.it.date < b.it.date ? 1 : a.it.date > b.it.date ? -1 : 0));
  return hits.map((h) => h.it);
}

export function paginate(list, page, per = 12) {
  const total = list.length;
  const pages = Math.max(1, Math.ceil(total / per));
  const p = Math.min(Math.max(Number(page) || 1, 1), pages);
  const start = (p - 1) * per;
  const items = list.slice(start, start + per);
  return { items, page: p, pages, from: total ? start + 1 : 0, to: start + items.length, total };
}

export function pageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const keep = new Set([1, total, current - 1, current, current + 1]);
  if (current <= 3) [2, 3, 4].forEach((n) => n <= current + 2 && keep.add(n));
  if (current >= total - 2) [total - 1, total - 2].forEach((n) => keep.add(n));
  const nums = [...keep].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b);
  const out = [];
  nums.forEach((n, i) => {
    const prev = nums[i - 1];
    if (prev && n - prev === 2) out.push(prev + 1);
    else if (prev && n - prev > 2) out.push('…');
    out.push(n);
  });
  return out;
}

export function vocabulary(items) {
  const counts = new Map();
  for (const it of items) {
    for (const w of `${it.titleNorm} ${normalize(it.topic)}`.split(' ')) {
      if (w.length >= 3) counts.set(w, (counts.get(w) || 0) + 1);
    }
  }
  return counts;
}

function distance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i += 1) {
    const cur = [i];
    let rowMin = i;
    for (let j = 1; j <= b.length; j += 1) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      rowMin = Math.min(rowMin, cur[j]);
    }
    if (rowMin > max) return max + 1;
    prev = cur;
  }
  return prev[b.length];
}

export function suggest(q, vocab) {
  let changed = false;
  const fixed = tokens(q).map((t) => {
    if (t.length < 4 || vocab.has(t)) return t;
    const max = t.length <= 5 ? 1 : 2;
    let best = null;
    let bestD = max + 1;
    let bestCount = 0;
    for (const [w, count] of vocab) {
      const d = distance(t, w, max);
      if (d < bestD || (d === bestD && d <= max && count > bestCount)) { best = w; bestD = d; bestCount = count; }
    }
    if (best && bestD <= max) { changed = true; return best; }
    return t;
  });
  return changed ? fixed.join(' ') : null;
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);

export function highlight(title, q) {
  const toks = tokens(q);
  if (!toks.length) return escapeHtml(title);
  let norm = '';
  const map = [];
  [...title].forEach((ch, i) => {
    const n = ch.normalize('NFD').replace(DIACRITICS, '').toLowerCase();
    if (/^[a-z0-9]+$/.test(n)) { for (const c of n) { norm += c; map.push(i); } } else if (/\s/.test(ch)) { norm += ' '; map.push(i); }
  });
  const chars = [...title];
  const ranges = [];
  for (const t of toks) {
    let at = norm.indexOf(t);
    while (at !== -1) {
      ranges.push([map[at], map[at + t.length - 1] + 1]);
      at = norm.indexOf(t, at + t.length);
    }
  }
  if (!ranges.length) return escapeHtml(title);
  ranges.sort((a, b) => a[0] - b[0]);
  const merged = [ranges[0]];
  for (const r of ranges.slice(1)) {
    const last = merged[merged.length - 1];
    if (r[0] <= last[1]) last[1] = Math.max(last[1], r[1]); else merged.push(r);
  }
  let out = '';
  let pos = 0;
  for (const [s, e] of merged) {
    out += escapeHtml(chars.slice(pos, s).join('')) + '<mark>' + escapeHtml(chars.slice(s, e).join('')) + '</mark>';
    pos = e;
  }
  return out + escapeHtml(chars.slice(pos).join(''));
}
