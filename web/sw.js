/**
 * SYS - Speak Your Story — Service Worker
 *
 * Cache-first for app shell, network-first for API calls.
 */

const CACHE_NAME = 'sys-v1';
const APP_SHELL = [
    './',
    './index.html',
    './css/style.css',
    './js/notes.js',
    './js/refiner.js',
    './js/speech.js',
    './js/app.js',
    './manifest.json',
    './icons/icon-192.png',
    './icons/icon-512.png',
];

// Install — cache app shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
    );
    self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch — cache-first for app, network-first for APIs
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API calls — network first
    if (url.hostname.includes('huggingface.co') || url.hostname.includes('googleapis.com')) {
        event.respondWith(
            fetch(event.request).catch(() => new Response('{}', { status: 503, headers: { 'Content-Type': 'application/json' } }))
        );
        return;
    }

    // App shell — cache first
    event.respondWith(
        caches.match(event.request).then(cached => cached || fetch(event.request))
    );
});
