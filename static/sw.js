importScripts('https://cdn.onesignal.com/sdks/OneSignalSDKWorker.js');

// Listen for install event, set callback
self.addEventListener('install', function (event) {
    console.log('Super install', event)
});

self.addEventListener('activate', function (event) {
    console.log('Super activate', event)
});

self.addEventListener('fetch', function (event) {
    console.log('Super fetch', event)
    event.respondWith(
        caches.open('mysite-dynamic').then(function (cache) {
            return cache.match(event.request).then(function (response) {
                return response || fetch(event.request).then(function (response) {
                    console.log('response fetch', event)
                    cache.put(event.request, response.clone());
                    console.log('put fetch', event)
                    return response;
                });
            });
        })
    );
});
