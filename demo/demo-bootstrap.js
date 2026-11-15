// Install the demo adapter before the application starts. No API requests leave the browser.
const demoReady=import('./demo-api.mjs').then(({createBrowserStore,createDemoFetch})=>createDemoFetch(createBrowserStore(localStorage),location.origin));
window.fetch=(...args)=>demoReady.then(fetchDemo=>fetchDemo(...args));
