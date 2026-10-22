(function () {
    // Change block-chooser Tippy popups from placement:"bottom" (centred) to
    // "bottom-start" (left-aligned) so they don't overflow the viewport's left edge.
    function patchBtn(el) {
        if (el._tippy && !el._wssfixed) {
            el._tippy.setProps({ placement: "bottom-start" });
            el._wssfixed = true;
        }
    }

    // Correct the Draftail floating toolbar when Popper clips it to x≤10px while
    // the text selection is further right.
    var correcting = false;
    function correctToolbar(root) {
        if (correcting) return;
        if (!root.querySelector(".Draftail-Tooltip")) return;
        var sel = window.getSelection();
        if (!sel || !sel.rangeCount) return;
        var sr = sel.getRangeAt(0).getBoundingClientRect();
        if (!sr.width) return;
        var rr = root.getBoundingClientRect();
        if (rr.x > 10) return;
        var shiftX = sr.x - rr.x;
        if (shiftX < 1) return;
        var m = root.style.transform.match(/translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/);
        if (!m) return;
        correcting = true;
        root.style.transform = "translate(" + (parseFloat(m[1]) + shiftX) + "px," + m[2] + "px)";
        correcting = false;
    }

    function watchTippyRoot(root) {
        correctToolbar(root);
        new MutationObserver(function () { correctToolbar(root); })
            .observe(root, { attributes: true, attributeFilter: ["style"] });
    }

    function fix(root) {
        if (!root || root.nodeType !== 1) return;
        var qs = root.querySelectorAll ? root.querySelectorAll.bind(root) : function () { return []; };
        Array.from(qs(".c-sf-add-button")).forEach(patchBtn);
        if (root.matches && root.matches(".c-sf-add-button")) patchBtn(root);
        var tRoots = (root.matches && root.matches("[data-tippy-root]"))
            ? [root]
            : Array.from(qs("[data-tippy-root]"));
        tRoots.forEach(watchTippyRoot);
    }

    function init() {
        new MutationObserver(function (ms) {
            ms.forEach(function (m) {
                m.addedNodes.forEach(function (n) { setTimeout(function () { fix(n); }, 0); });
            });
        }).observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
