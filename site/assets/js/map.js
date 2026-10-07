function loadCss(href) {
  return new Promise((resolve, reject) => {
    const link = Object.assign(document.createElement('link'), { rel: 'stylesheet', href });
    link.onload = resolve; link.onerror = reject;
    document.head.append(link);
  });
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = Object.assign(document.createElement('script'), { src, async: true });
    s.onload = resolve; s.onerror = reject;
    document.head.append(s);
  });
}

function popup(p) {
  const el = document.createElement('div');
  const name = document.createElement('strong');
  name.textContent = p.name;
  const addr = document.createElement('div');
  addr.textContent = p.address;
  const tel = Object.assign(document.createElement('a'), { href: `tel:${p.tel}`, textContent: p.phone });
  el.append(name, addr, tel);
  return el;
}

export function initMap() {
  const panel = document.querySelector('[data-map]');
  if (!panel || !('IntersectionObserver' in window)) return;
  const canvas = panel.querySelector('.map-canvas');
  const load = async () => {
    try {
      await loadCss('/assets/vendor/leaflet/leaflet.css');
      await loadScript('/assets/vendor/leaflet/leaflet.js');
      const L = window.L;
      const points = JSON.parse(panel.dataset.points);
      const map = L.map(canvas, { scrollWheelZoom: false });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      points.forEach((p) => L.marker([p.lat, p.lng], { title: p.name, alt: p.name }).addTo(map).bindPopup(popup(p)));
      map.fitBounds(points.map((p) => [p.lat, p.lng]), { padding: [36, 36] });
      panel.classList.add('is-loaded');
    } catch (error) {
      panel.classList.add('is-failed');
      canvas.hidden = true;
    }
  };
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { io.disconnect(); load(); }
  }, { rootMargin: '300px' });
  io.observe(panel);
}
