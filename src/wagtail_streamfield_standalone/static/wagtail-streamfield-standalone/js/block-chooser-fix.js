(function () {
    // Change block-chooser Tippy popups from placement:"bottom" (centred) to
    // "bottom-start" (left-aligned) so they stay inside the form container.
    function patchBtn(el) {
        if (el._tippy && !el._wssfixed) {
            el._tippy.setProps({ placement: "bottom-start" });
            el._wssfixed = true;
        }
    }

    // Correct the Draftail floating toolbar when Popper has clipped it left of
    // the text selection centre.  The old x≤10 threshold broke inside a centred
    // Bootstrap container whose left edge sits well above x=10.
    var correcting = false;
    function correctToolbar(root) {
        if (correcting) return;
        if (!root.querySelector(".Draftail-Tooltip")) return;
        var sel = window.getSelection();
        if (!sel || !sel.rangeCount) return;
        var sr = sel.getRangeAt(0).getBoundingClientRect();
        if (!sr.width) return;
        var rr = root.getBoundingClientRect();
        // Popper centres the toolbar over the selection; a positive drift means
        // Popper clipped it to the left — shift it right to re-centre.
        var drift = (sr.left + sr.width / 2) - (rr.left + rr.width / 2);
        if (drift < 1) return;
        var m = root.style.transform.match(/translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/);
        if (!m) return;
        correcting = true;
        root.style.transform = "translate(" + (parseFloat(m[1]) + drift) + "px," + m[2] + "px)";
        correcting = false;
    }

    function watchTippyRoot(root) {
        if (root._wssRootFixed) return;
        root._wssRootFixed = true;
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
        if (tRoots.length > 0) {
            // A Tippy popup has opened — Tippy is now initialised on all visible
            // add-buttons.  Re-scan the whole document so the first button (which
            // may have been present before Tippy ran) gets patched.
            document.querySelectorAll(".c-sf-add-button").forEach(patchBtn);
            tRoots.forEach(watchTippyRoot);
        }
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
