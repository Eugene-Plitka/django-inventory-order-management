/* Mobile navigation and existing HTMX global search control.
 * No changes to server-side endpoints or desktop layout.
 */
(function () {
    "use strict";
    const cutoff = window.matchMedia("(max-width: 760px)");
    const sidebar = document.querySelector(".sidebar");
    const topbar = document.querySelector(".topbar");
    const search = topbar?.querySelector(".topbar-search");
    if (!sidebar || !topbar) return;

    const menuButton = document.createElement("button");
    menuButton.type = "button";
    menuButton.className = "mobile-menu-toggle";
    menuButton.setAttribute("aria-label", "Open navigation menu");
    menuButton.setAttribute("aria-controls", "inventory-mobile-sidebar");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
    sidebar.id = "inventory-mobile-sidebar";
    topbar.prepend(menuButton);

    const backdrop = document.createElement("button");
    backdrop.type = "button";
    backdrop.className = "mobile-sidebar-backdrop";
    backdrop.setAttribute("aria-label", "Close navigation menu");
    document.body.append(backdrop);

    const searchButton = document.createElement("button");
    searchButton.type = "button";
    searchButton.className = "mobile-search-toggle";
    searchButton.setAttribute("aria-label", "Open global search");
    searchButton.setAttribute("aria-expanded", "false");
    searchButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/></svg>';
    if (search) topbar.insertBefore(searchButton, search);

    function closeMenu() {
        document.body.classList.remove("mobile-nav-open");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.setAttribute("aria-label", "Open navigation menu");
    }
    function closeSearch() {
        document.body.classList.remove("mobile-search-open");
        searchButton.setAttribute("aria-expanded", "false");
    }
    menuButton.addEventListener("click", () => {
        const willOpen = !document.body.classList.contains("mobile-nav-open");
        closeSearch();
        document.body.classList.toggle("mobile-nav-open", willOpen);
        menuButton.setAttribute("aria-expanded", String(willOpen));
        menuButton.setAttribute("aria-label", willOpen ? "Close navigation menu" : "Open navigation menu");
    });
    backdrop.addEventListener("click", closeMenu);
    searchButton.addEventListener("click", () => {
        const willOpen = !document.body.classList.contains("mobile-search-open");
        closeMenu();
        document.body.classList.toggle("mobile-search-open", willOpen);
        searchButton.setAttribute("aria-expanded", String(willOpen));
        if (willOpen) search?.querySelector("input")?.focus();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
            closeSearch();
            search?.querySelector("input")?.blur();
        }
    });
    sidebar.querySelectorAll("a").forEach((a) => a.addEventListener("click", closeMenu));
    cutoff.addEventListener("change", (event) => {
        if (!event.matches) {
            closeMenu();
            closeSearch();
        }
    });
})();
