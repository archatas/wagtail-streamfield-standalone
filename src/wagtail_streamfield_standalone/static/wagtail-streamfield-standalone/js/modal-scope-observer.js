// Wrap Wagtail overlays appended to <body> in a .wagtail-streamfield-standalone div so
// that CSS @scope rules apply to them. The guard prevents duplicate observers when
// multiple widgets are on the same page.
if (!window.__wssModalObserver) {
    function wssWrap(n) {
        if (n.nodeType !== 1) return;
        if (!(n.classList.contains("modal") ||
              n.classList.contains("modal-backdrop") ||
              n.classList.contains("w-dialog") ||
              n.tagName === "DIALOG")) return;
        var w = document.createElement("div");
        w.className = "wagtail-streamfield-standalone";
        n.parentNode.insertBefore(w, n);
        w.appendChild(n);
        // Remove the wrapper once Wagtail teleports the overlay back out.
        new MutationObserver(function (ms, obs) {
            if (!w.children.length) { w.remove(); obs.disconnect(); }
        }).observe(w, { childList: true });
    }
    window.__wssModalObserver = new MutationObserver(function (ms) {
        ms.forEach(function (m) { m.addedNodes.forEach(wssWrap); });
    });
    (function init() {
        if (document.body) {
            window.__wssModalObserver.observe(document.body, { childList: true });
        } else {
            document.addEventListener("DOMContentLoaded", function () {
                window.__wssModalObserver.observe(document.body, { childList: true });
            });
        }
    })();
}
