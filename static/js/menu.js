export function initMenu() {
  const button = document.querySelector('[data-menu-toggle]');
  const panel = document.getElementById('site-menu');
  if (!button || !panel) return;
  panel.hidden = true; // visible without JS, collapsed once JS runs
  const setOpen = (open) => {
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    button.querySelector('[data-icon-open]').hidden = open;
    button.querySelector('[data-icon-close]').hidden = !open;
    panel.hidden = !open;
  };
  button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    setOpen(open);
    if (open) panel.querySelector('a')?.focus();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      setOpen(false);
      button.focus();
    }
  });
}
