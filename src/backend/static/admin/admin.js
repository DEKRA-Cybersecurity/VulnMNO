// VulnMNO admin — tiny helpers.
// Currently a placeholder; HTMX is loaded from CDN in base.html and handles all interactivity.
document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("htmx:responseError", (ev) => {
    console.warn("HTMX error", ev.detail);
  });
});
