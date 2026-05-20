(function () {
  const navToggle = document.querySelector("[data-nav-toggle]");
  const navMenu = document.querySelector("[data-nav-menu]");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      const expanded = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", String(!expanded));
      navMenu.classList.toggle("is-open");
    });
  }

  document.querySelectorAll("[data-confirm-delete]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm("آیا از حذف این مورد از سبد خرید مطمئن هستید؟")) {
        e.preventDefault();
      }
    });
  });

  document.querySelectorAll(".alert[data-auto-dismiss]").forEach(function (el) {
    setTimeout(function () {
      el.classList.add("is-hidden");
    }, 6000);
  });
})();
