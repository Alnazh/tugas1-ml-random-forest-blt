(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function setupMenu() {
    const button = $(".menu-toggle");
    const nav = $("#main-nav");
    if (!button || !nav) return;
    button.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      button.setAttribute("aria-expanded", String(open));
    });
  }

  // Tab generik: dipakai untuk langkah simulasi dan untuk pilihan pohon.
  function setupTabs(group) {
    const tabs = $$('[role="tab"]', $(':scope > [role="tablist"]', group));
    const panels = $$(':scope > [role="tabpanel"]', group);
    const useHash = group.hasAttribute("data-hash");
    let current = 0;

    function show(index) {
      current = index;
      tabs.forEach((tab, i) => {
        const active = i === index;
        tab.setAttribute("aria-selected", String(active));
        tab.tabIndex = active ? 0 : -1;
        panels[i].hidden = !active;
      });
      if (useHash) history.replaceState(null, "", `#${panels[index].id}`);
    }

    tabs.forEach((tab, i) => tab.addEventListener("click", () => show(i)));
    tabs.forEach((tab, i) =>
      tab.addEventListener("keydown", (event) => {
        const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
        if (!step) return;
        const next = (i + step + tabs.length) % tabs.length;
        show(next);
        tabs[next].focus();
      })
    );

    group.addEventListener("click", (event) => {
      const go = event.target.closest("[data-tab-go]");
      if (!go || go.closest("[data-tabs]") !== group) return;
      const target = current + (go.dataset.tabGo === "next" ? 1 : -1);
      if (target < 0 || target >= panels.length) return;
      show(target);
      group.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    const fromHash = useHash ? panels.findIndex((panel) => `#${panel.id}` === location.hash) : -1;
    show(Math.max(fromHash, 0));
  }

  function setupSeedButton() {
    const form = $("#sim-form");
    $("[data-dice]", form || document)?.addEventListener("click", () => {
      form.elements.seed.value = Math.floor(Math.random() * 99999) + 1;
    });
  }

  function setupExample() {
    const button = $("[data-example]");
    if (!button) return;
    button.addEventListener("click", () => {
      const form = button.closest("form");
      form.elements.title.value = button.dataset.title;
      form.elements.csv.value = button.dataset.csv;
    });
  }

  function setupPresets() {
    $$("[data-preset]").forEach((button) =>
      button.addEventListener("click", () => {
        const form = button.closest("form");
        const values = JSON.parse(button.dataset.preset);
        Object.entries(values).forEach(([name, value]) => {
          form.elements[name].value = value;
        });
        form.requestSubmit();
      })
    );
  }

  setupMenu();
  $$("[data-tabs]").forEach(setupTabs);
  setupSeedButton();
  setupExample();
  setupPresets();
})();
