(function () {
  const storageKey = "populationBookTocCollapsed";

  function setupTocToggle() {
    const layout = document.querySelector(".layout");
    const toc = document.querySelector(".toc");
    const toggle = document.querySelector("[data-toc-toggle]");
    if (!layout || !toc || !toggle) return;

    const setCollapsed = (collapsed) => {
      layout.classList.toggle("toc-collapsed", collapsed);
      toggle.setAttribute("aria-expanded", String(!collapsed));
      toggle.setAttribute("title", collapsed ? "목차 펼치기" : "목차 접기");
      toggle.textContent = collapsed ? "목차" : "접기";
      try {
        window.localStorage.setItem(storageKey, collapsed ? "1" : "0");
      } catch (error) {
        // Local files or strict browser settings can block storage; the button still works.
      }
    };

    let initial = false;
    try {
      initial = window.localStorage.getItem(storageKey) === "1";
    } catch (error) {
      initial = false;
    }
    setCollapsed(initial);

    toggle.addEventListener("click", () => {
      setCollapsed(!layout.classList.contains("toc-collapsed"));
    });
  }

  document.addEventListener("DOMContentLoaded", setupTocToggle);
})();
