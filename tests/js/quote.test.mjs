import { test } from 'node:test';
import assert from 'node:assert/strict';
import { quoteUrl, QUOTE_URL } from '../../static/js/quote.js';

test('empty goes to the quote page without a ZIP', () => {
  assert.deepEqual(quoteUrl(''), { ok: true, url: QUOTE_URL });
  assert.deepEqual(quoteUrl('   '), { ok: true, url: QUOTE_URL });
});

test('valid ZIP, https, single parameter', () => {
  assert.deepEqual(quoteUrl('60630'), { ok: true, url: 'https://quote.insureonthespot.com/?zipcode=60630' });
  assert.deepEqual(quoteUrl(' 60630 '), { ok: true, url: 'https://quote.insureonthespot.com/?zipcode=60630' });
});

test('invalid ZIPs return an error message', () => {
  for (const bad of ['6063', '606301', 'abcde', '60630-1234', '6O630']) {
    const r = quoteUrl(bad);
    assert.equal(r.ok, false, bad);
    assert.equal(r.error, 'Enter a 5-digit ZIP code, like 60630.');
  }
});
