export const QUOTE_URL = 'https://quote.insureonthespot.com/';
const ERROR = 'Enter a 5-digit ZIP code, like 60630.';

export function quoteUrl(raw) {
  const zip = String(raw ?? '').trim();
  if (zip === '') return { ok: true, url: QUOTE_URL };
  if (/^\d{5}$/.test(zip)) return { ok: true, url: `${QUOTE_URL}?zipcode=${zip}` };
  return { ok: false, error: ERROR };
}

export function initQuoteForms(root = document) {
  root.querySelectorAll('form[data-quote]').forEach((form) => {
    const input = form.querySelector('input[name="zipcode"]');
    const error = form.querySelector('.field-error');
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const result = quoteUrl(input.value);
      if (!result.ok) {
        error.textContent = result.error;
        error.hidden = false;
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        return;
      }
      error.hidden = true;
      input.removeAttribute('aria-invalid');
      window.location.assign(result.url);
    });
  });
}
