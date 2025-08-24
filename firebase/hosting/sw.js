// A minimal service worker to make the app installable.

self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  // This event is fired when the service worker is first installed.
  // You could pre-cache assets here if needed.
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  // This event is fired when the service worker becomes active.
  // It's a good place to clean up old caches.
});

self.addEventListener('fetch', (event) => {
  // This event is fired for every network request.
  // For an offline-first PWA, you would handle requests here.
  // For this MVP, we will let the browser handle all network requests by not calling event.respondWith().
  // console.log('Service Worker: Fetching', event.request.url);
});
