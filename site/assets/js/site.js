import { initStatus } from './hours.js';
import { initQuoteForms } from './quote.js';
import { initMenu } from './menu.js';

initMenu();
initStatus();
initQuoteForms();
if (document.querySelector('[data-map]')) {
  import('./map.js').then((m) => m.initMap()).catch(() => {});
}
if (document.querySelector('[data-blog-search]')) {
  import('./blog.js').then((m) => m.initBlog()).catch(() => {});
}
