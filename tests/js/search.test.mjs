import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalize, tokens, buildIndex, searchPosts, paginate, pageNumbers, suggest, vocabulary, highlight } from '../../static/js/search.js';

const RAW = {
  topics: [{ name: 'SR-22', slug: 'sr-22' }, { name: 'Coverages', slug: 'coverages' }, { name: 'Legal', slug: 'legal' }],
  posts: [
    // [title, link, date, topicIndex, minutes, excerpt, lang]
    ['How Long Do You Need SR-22 Insurance in Illinois?', 'https://x/1', '2026-06-18', 0, 16, 'Illinois SR-22 requirements typically last three years.', ''],
    ['What Is Auto Liability Insurance?', 'https://x/2', '2026-06-20', 1, 10, 'Liability covers damage you cause. Mentions sr22 filings too.', ''],
    ['Qué Pasa Si Te Detienen Sin Seguro en Illinois', 'https://x/3', '2026-06-10', 2, 9, 'Si te detienen sin seguro…', 'es'],
    ['Comprehensive vs Collision Coverage', 'https://x/4', '2026-06-01', 1, 12, 'What each covers.', ''],
  ],
};
const items = buildIndex(RAW);

test('normalize strips accents, case and punctuation', () => {
  assert.equal(normalize('Qué Pasa'), 'que pasa');
  assert.equal(normalize('SR-22'), 'sr22');
  assert.equal(normalize("  Chicago's   Guide "), 'chicagos guide');
});

test('tokens drops empty input and splits words', () => {
  assert.deepEqual(tokens('   '), []);
  assert.deepEqual(tokens('sr 22  Illinois'), ['sr', '22', 'illinois']);
});

test('sr22 matches SR-22 and que matches Qué', () => {
  assert.ok(searchPosts(items, { q: 'sr22' }).some((p) => p.title.startsWith('How Long')));
  assert.equal(searchPosts(items, { q: 'que pasa' })[0].title.startsWith('Qué'), true);
});

test('every word must match', () => {
  assert.equal(searchPosts(items, { q: 'liability collision' }).length, 0);
  assert.equal(searchPosts(items, { q: 'liability insurance' }).length, 1);
});

test('topic filter, alone and with a query', () => {
  assert.deepEqual(searchPosts(items, { topic: 'Coverages' }).map((p) => p.link), ['https://x/2', 'https://x/4']);
  assert.equal(searchPosts(items, { q: 'illinois', topic: 'Coverages' }).length, 0);
});

test('title matches rank before excerpt-only matches, then newest', () => {
  const r = searchPosts(items, { q: 'sr22' });
  assert.equal(r[0].link, 'https://x/1'); // title match beats the newer excerpt-only match
  assert.equal(r[1].link, 'https://x/2');
});

test('paginate clamps and reports the range', () => {
  const list = Array.from({ length: 30 }, (_, i) => i);
  assert.deepEqual(paginate(list, 2, 12), { items: list.slice(12, 24), page: 2, pages: 3, from: 13, to: 24, total: 30 });
  assert.equal(paginate(list, 99, 12).page, 3);
  assert.equal(paginate(list, 0, 12).page, 1);
  assert.deepEqual(paginate([], 1, 12), { items: [], page: 1, pages: 1, from: 0, to: 0, total: 0 });
});

test('pageNumbers collapses long ranges', () => {
  assert.deepEqual(pageNumbers(1, 1), [1]);
  assert.deepEqual(pageNumbers(3, 7), [1, 2, 3, 4, 5, 6, 7]);
  assert.deepEqual(pageNumbers(1, 8), [1, 2, 3, '…', 8]);
  assert.deepEqual(pageNumbers(5, 8), [1, '…', 4, 5, 6, 7, 8]); // a gap of one page shows the number, not …
  assert.deepEqual(pageNumbers(4, 8), [1, 2, 3, 4, 5, '…', 8]);
  assert.deepEqual(pageNumbers(8, 8), [1, '…', 6, 7, 8]);
  assert.deepEqual(pageNumbers(25, 50), [1, '…', 24, 25, 26, '…', 50]);
});

test('suggest fixes a typo from real title words', () => {
  const vocab = vocabulary(items);
  assert.equal(suggest('insurence', vocab), 'insurance');
  assert.equal(suggest('illinios liabilty', vocab), 'illinois liability');
  assert.equal(suggest('insurance', vocab), null);
  assert.equal(suggest('zzqxv', vocab), null);
});

test('highlight wraps matches, keeps accents and escapes HTML', () => {
  assert.equal(highlight('Qué Pasa Si', 'que'), '<mark>Qué</mark> Pasa Si');
  assert.equal(highlight('Need SR-22 Insurance', 'sr22'), 'Need <mark>SR-22</mark> Insurance');
  assert.equal(highlight('<b>Fish & Chips</b>', 'fish'), '&lt;b&gt;<mark>Fish</mark> &amp; Chips&lt;/b&gt;');
  assert.equal(highlight('Plain title', ''), 'Plain title');
});
