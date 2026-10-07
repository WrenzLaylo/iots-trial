// Instant search and topic filtering for the blog landing page.
// Server-rendered pages stay the default view; this module takes over only when someone searches or picks a topic.
import { buildIndex, searchPosts, paginate, pageNumbers, suggest, vocabulary, highlight, meaningfulTokens } from './search.js';

const INDEX_URL = '/assets/data/posts-index.json';
const SITE_SEARCH = 'https://www.insureonthespot.com/?s=';
const PHONE = { label: '773-202-5060', tel: '+17732025060' };
const PER_PAGE = 12;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const dateFmt = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });

export function initBlog() {
  const form = document.querySelector('[data-blog-search]');
  if (!form) return;
  const input = form.querySelector('#blog-q');
  const clearBtn = form.querySelector('[data-clear]');
  const results = document.getElementById('search-results');
  const defaultView = document.getElementById('default-view');
  const status = document.getElementById('search-status');
  const chips = [...document.querySelectorAll('.chip[data-topic]')];

  const state = { q: '', topic: '', page: 1 };
  let data = null; // { items, vocab, popular }
  let loading = null;
  let failed = false;
  let typingTimer = 0;

  const el = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (v === false || v == null) return;
      if (k === 'class') n.className = v; else if (k === 'html') n.innerHTML = v; else if (k === 'text') n.textContent = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v === true ? '' : v);
    });
    kids.flat().forEach((c) => c != null && n.append(c));
    return n;
  };
  const svgUse = (cls, id) => {
    const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    s.setAttribute('class', cls);
    s.setAttribute('aria-hidden', 'true');
    const u = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    u.setAttribute('href', `#t-${id}`);
    s.append(u);
    return s;
  };
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

  function load() {
    if (data || failed) return Promise.resolve(data);
    if (!loading) {
      const ms = window.IOTS_INDEX_TIMEOUT_MS || 8000; // a hanging request falls back like a failed one
      const timeout = new Promise((_, reject) => { window.setTimeout(() => reject(new Error('index timeout')), ms); });
      loading = Promise.race([fetch(INDEX_URL).then((r) => { if (!r.ok) throw new Error(`index ${r.status}`); return r.json(); }), timeout])
        .then((raw) => {
          const prefixed = { ...raw, posts: raw.posts.map((p) => [p[0], raw.base + p[1], ...p.slice(2)]) };
          const items = buildIndex(prefixed);
          const counts = new Map();
          items.forEach((it) => it.topics.forEach((t) => counts.set(t, (counts.get(t) || 0) + 1)));
          const popular = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6).map(([t]) => t);
          data = { items, vocab: vocabulary(items), popular, count: raw.count };
          return data;
        })
        .catch(() => { failed = true; return null; });
    }
    return loading;
  }

  // ---------- URL state ----------
  function readUrl() {
    const p = new URLSearchParams(window.location.search);
    state.q = p.get('q') || '';
    state.topic = p.get('topic') || '';
    state.page = Math.max(1, parseInt(p.get('page') || '1', 10) || 1);
  }
  function writeUrl(push) {
    const p = new URLSearchParams();
    if (state.q.trim()) p.set('q', state.q.trim());
    if (state.topic) p.set('topic', state.topic);
    if (state.page > 1) p.set('page', String(state.page));
    const url = `${window.location.pathname}${p.toString() ? `?${p}` : ''}`;
    if (url === `${window.location.pathname}${window.location.search}`) return;
    window.history[push ? 'pushState' : 'replaceState']({ blog: true }, '', url);
  }

  // ---------- rendering ----------
  function syncControls() {
    if (input.value !== state.q) input.value = state.q;
    const has = state.q.length > 0;
    clearBtn.hidden = !has;
    form.classList.toggle('has-value', has);
    chips.forEach((c) => {
      const on = (c.dataset.topic || '') === state.topic;
      c.classList.toggle('is-on', on);
      if (on) c.setAttribute('aria-current', 'true'); else c.removeAttribute('aria-current');
    });
  }

  function card(it) {
    const meta = el('p', { class: 'meta' }, it.topic ? el('span', { class: 'topic', text: it.topic }) : null, el('span', { text: `${it.mins} min read` }));
    const title = el('h3', { class: 'post-title', lang: it.lang || false }, el('a', { href: it.link, html: highlight(it.title, state.q) }));
    return el('li', {}, el('article', { class: 'card post' },
      el('div', { class: `cover tone-${it.tone}`, 'aria-hidden': 'true' }, svgUse('cover-icon', it.icon), svgUse('cover-mark', it.icon)),
      el('div', { class: 'post-body' }, meta, title,
        el('p', { class: 'excerpt', lang: it.lang || false, text: it.excerpt }),
        el('p', { class: 'date' }, el('time', { datetime: it.date, text: dateFmt.format(new Date(`${it.date}T00:00:00Z`)) })))));
  }

  function headline(total) {
    const q = state.q.trim();
    const what = plural(total, 'guide');
    if (q && state.topic) return `${what} for “${q}” in ${state.topic}`;
    if (q) return `${what} for “${q}”`;
    return `${what} in ${state.topic}`;
  }

  function pager(pg) {
    if (pg.pages <= 1) return null;
    const go = (n) => () => { state.page = n; writeUrl(true); render({ focus: true }); };
    const items = [el('li', {}, el('button', { type: 'button', class: 'pg-step', disabled: pg.page === 1, 'aria-label': 'Previous page', onclick: go(pg.page - 1), text: 'Previous' }))];
    pageNumbers(pg.page, pg.pages).forEach((n) => {
      items.push(el('li', {}, n === '…'
        ? el('span', { class: 'gap', 'aria-hidden': 'true', text: '…' })
        : el('button', { type: 'button', 'data-page': n, 'aria-label': `Page ${n}`, 'aria-current': n === pg.page ? 'page' : false, onclick: go(n), text: String(n) })));
    });
    items.push(el('li', {}, el('button', { type: 'button', class: 'pg-step', disabled: pg.page === pg.pages, 'aria-label': 'Next page', onclick: go(pg.page + 1), text: 'Next' })));
    return el('nav', { 'aria-label': 'Search result pages' }, el('ul', { class: 'pagination' }, items));
  }

  function emptyState() {
    const q = state.q.trim();
    const box = el('div', { class: 'empty' });
    const icon = el('div', { class: 'empty-icon', 'aria-hidden': 'true' });
    icon.innerHTML = document.querySelector('[data-blog-search] > .icon')?.outerHTML || '';
    const body = el('div');
    const heading = q ? `No guides match “${q}”${state.topic ? ` in ${state.topic}` : ''} yet` : `No guides in ${state.topic} yet`;
    body.append(el('h2', { id: 'results-h', tabindex: '-1', text: heading }));
    body.append(el('p', { text: 'Here are a few ways to find what you need.' }));
    const actions = el('div');
    if (q && state.topic) {
      const elsewhere = searchPosts(data.items, { q }).length;
      if (elsewhere) actions.append(el('button', { type: 'button', class: 'suggestion', text: `Show ${plural(elsewhere, 'guide')} in all topics`, onclick: () => { state.topic = ''; state.page = 1; writeUrl(true); render({ focus: true }); } }));
    }
    const fix = q ? suggest(q, data.vocab) : null;
    if (fix && searchPosts(data.items, { q: fix }).length) {
      actions.append(el('button', { type: 'button', class: 'suggestion', text: `Did you mean “${fix}”?`, onclick: () => { state.q = fix; state.topic = ''; state.page = 1; writeUrl(true); render(); input.focus(); } }));
    }
    if (actions.childNodes.length) body.append(actions);
    body.append(el('ul', { class: 'tips' },
      el('li', { text: 'Check the spelling, or use fewer words.' }),
      el('li', { text: 'Try a general term like “SR-22”, “claim” or “coverage”.' })));
    body.append(el('p', { text: 'Or browse a popular topic:' }));
    body.append(el('ul', { class: 'pop' }, data.popular.map((t) => el('li', {}, el('button', { type: 'button', text: t, onclick: () => { state.topic = t; state.q = ''; state.page = 1; writeUrl(true); render({ focus: true }); } })))));
    body.append(el('div', { class: 'ways' },
      q ? el('a', { href: SITE_SEARCH + encodeURIComponent(q), text: 'Search the whole website' }) : null,
      el('a', { href: `tel:${PHONE.tel}`, text: `Prefer to ask? Call ${PHONE.label}` })));
    box.append(icon, body);
    return box;
  }

  function skeleton() {
    const list = el('ul', { class: 'grid', 'aria-hidden': 'true' });
    for (let i = 0; i < 6; i += 1) {
      list.append(el('li', {}, el('div', { class: 'card post skeleton' }, el('div', { class: 'cover' }),
        el('div', { class: 'post-body' }, el('div', { class: 'bar w40' }), el('div', { class: 'bar w90' }), el('div', { class: 'bar w60' })))));
    }
    return list;
  }

  function showDefault() {
    results.hidden = true;
    results.replaceChildren();
    defaultView.hidden = false;
    status.textContent = '';
  }

  async function render({ focus = false } = {}) {
    syncControls();
    const filtering = meaningfulTokens(state.q).length > 0 || state.topic;
    if (!filtering) { showDefault(); return; }
    defaultView.hidden = true;
    results.hidden = false;
    if (!data && !failed) {
      results.replaceChildren(el('div', { class: 'results-head' }, el('h2', { id: 'results-h', tabindex: '-1', text: 'Searching guides…' })), skeleton());
      await load();
      return render({ focus }); // re-read state: the visitor may have cleared or changed it meanwhile
    }
    if (failed) {
      const q = state.q.trim();
      results.replaceChildren(el('p', { class: 'notice' }, 'Live search isn’t available right now. ',
        q ? el('a', { href: SITE_SEARCH + encodeURIComponent(q), text: 'Search the whole website' })
          : el('a', { href: SITE_SEARCH.replace('?s=', 'customer-service/blog/'), text: 'Browse the full blog' })));
      status.textContent = 'Live search unavailable. Press Enter to search the whole website.';
      chips.forEach((c) => c.classList.remove('is-on'));
      return;
    }
    const list = searchPosts(data.items, { q: state.q, topic: state.topic });
    if (!list.length) {
      results.replaceChildren(emptyState());
      status.textContent = state.q.trim() ? `No guides match ${state.q.trim()}.` : 'No guides found.';
    } else {
      const pg = paginate(list, state.page, PER_PAGE);
      if (pg.page !== state.page) { state.page = pg.page; writeUrl(false); } // ?page=999 -> last page, URL corrected
      const head = el('div', { class: 'results-head' },
        el('div', {}, el('h2', { id: 'results-h', tabindex: '-1', text: headline(pg.total) }),
          el('p', { class: 'results-range', text: `Showing ${pg.from} to ${pg.to} of ${pg.total}` })),
        el('button', { type: 'button', class: 'results-clear', text: 'Show all guides', onclick: () => { state.q = ''; state.topic = ''; state.page = 1; writeUrl(true); render(); input.focus(); } }));
      results.replaceChildren(head, el('ul', { class: 'grid' }, pg.items.map(card)), pager(pg));
      status.textContent = `${headline(pg.total)}. Showing ${pg.from} to ${pg.to}.`;
    }
    if (focus) {
      results.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
      document.getElementById('results-h')?.focus({ preventScroll: true });
    }
  }

  // ---------- events ----------
  input.addEventListener('focus', () => { load(); }, { once: true });
  input.addEventListener('input', () => {
    state.q = input.value;
    state.page = 1;
    syncControls();
    window.clearTimeout(typingTimer);
    typingTimer = window.setTimeout(() => { writeUrl(false); render(); }, 90);
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && input.value) { e.preventDefault(); state.q = ''; state.page = 1; writeUrl(false); render(); }
  });
  form.addEventListener('submit', (e) => {
    if (failed) return; // let the browser go to their WordPress search
    e.preventDefault();
    window.clearTimeout(typingTimer);
    state.q = input.value;
    state.page = 1;
    writeUrl(false);
    render({ focus: true });
  });
  clearBtn.addEventListener('click', () => { state.q = ''; state.page = 1; writeUrl(false); render(); input.focus(); });
  chips.forEach((c) => c.addEventListener('click', (e) => {
    if (failed || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return; // plain link: new tab, or index failed
    e.preventDefault();
    state.topic = c.dataset.topic || '';
    state.page = 1;
    writeUrl(true);
    render({ focus: !!state.topic });
  }));
  document.addEventListener('keydown', (e) => {
    const t = e.target;
    const typing = t instanceof HTMLElement && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if (e.key === '/' && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); input.focus(); }
  });
  document.querySelectorAll('a[href="#blog-q"]').forEach((a) => a.addEventListener('click', (e) => { e.preventDefault(); input.focus(); input.scrollIntoView({ block: 'center' }); }));
  window.addEventListener('popstate', () => { readUrl(); render(); });

  readUrl();
  if (!state.q && input.value.trim()) { state.q = input.value; writeUrl(false); } // typed before this module loaded
  if (document.activeElement === input) load();
  if (state.q || state.topic) render();
  else syncControls();
  form.dataset.ready = 'true';
}
