export const DAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const toMin = (hhmm) => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };

export function chicagoNow(date = new Date(), tz = 'America/Chicago') {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: tz, weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date);
  const get = (type) => parts.find((p) => p.type === type).value;
  return { day: DAYS.indexOf(get('weekday').slice(0, 3).toLowerCase()), minutes: (Number(get('hour')) % 24) * 60 + Number(get('minute')) };
}

export function formatTime(hhmm) {
  const [h, m] = hhmm.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  return m ? `${h12}:${String(m).padStart(2, '0')} ${suffix}` : `${h12} ${suffix}`;
}

export function statusFor(hours, now) {
  const today = hours[DAYS[now.day]];
  if (today) {
    if (now.minutes >= toMin(today[0]) && now.minutes < toMin(today[1])) {
      return { open: true, label: `Open, closes ${formatTime(today[1])}` };
    }
    if (now.minutes < toMin(today[0])) {
      return { open: false, label: `Closed, opens ${formatTime(today[0])}` };
    }
  }
  for (let i = 1; i <= 7; i += 1) {
    const d = (now.day + i) % 7;
    const h = hours[DAYS[d]];
    if (h) return { open: false, label: `Closed, opens ${i === 1 ? 'tomorrow' : DAY_NAMES[d]} ${formatTime(h[0])}` };
  }
  return { open: false, label: 'Closed' };
}

export function initStatus(root = document) {
  const pills = [...root.querySelectorAll('[data-hours]')];
  const rows = [...root.querySelectorAll('[data-day]')];
  if (!pills.length && !rows.length) return;
  const tick = () => {
    const now = chicagoNow();
    pills.forEach((el) => {
      const s = statusFor(JSON.parse(el.dataset.hours), now);
      el.textContent = s.label;
      el.classList.toggle('is-open', s.open);
      el.classList.toggle('is-closed', !s.open);
      el.hidden = false;
    });
    rows.forEach((r) => r.classList.toggle('is-today', r.dataset.day.split(' ').includes(DAYS[now.day])));
  };
  tick();
  setInterval(tick, 60_000);
}
