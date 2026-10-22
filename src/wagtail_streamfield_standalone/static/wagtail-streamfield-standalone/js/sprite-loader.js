(function () {
    function load(c) {
        var u = c.getAttribute("data-sprite-url");
        if (!u) return;
        var ls = "localStorage" in window && window.localStorage != null;
        function inject(s) { c.innerHTML = s; }
        if (ls && localStorage.getItem("wagtail:spriteRevision") === u) {
            inject(localStorage.getItem("wagtail:spriteData") || "");
        }
        fetch(u).then(function (r) { return r.text(); }).then(function (s) {
            inject(s);
            if (ls) try {
                localStorage.setItem("wagtail:spriteData", s);
                localStorage.setItem("wagtail:spriteRevision", u);
            } catch (e) {}
        }).catch(function (e) { console.error("Error loading icon sprite:", e); });
    }

    function init() {
        document.querySelectorAll("[data-sprite][data-sprite-url]").forEach(load);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
