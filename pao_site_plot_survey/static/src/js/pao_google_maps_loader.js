/** @odoo-module **/

let mapsApiLoaderPromise = null;

export function loadGoogleMapsApi(apiKey) {
    if (!mapsApiLoaderPromise) {
        mapsApiLoaderPromise = new Promise((resolve, reject) => {
            const callbackName = "__pao_gmaps_cb_" + Date.now();
            window[callbackName] = resolve;
            const script = document.createElement("script");
            script.src =
                "https://maps.googleapis.com/maps/api/js?key=" +
                encodeURIComponent(apiKey) +
                "&libraries=geometry&callback=" +
                callbackName;
            script.async = true;
            script.onerror = () => reject(new Error("Failed to load Google Maps JS API"));
            document.head.appendChild(script);
        });
    }
    return mapsApiLoaderPromise;
}
