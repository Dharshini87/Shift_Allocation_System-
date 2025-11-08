// Toggle password show/hide for all eye buttons
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".eye-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      if (!targetId) return;
      const input = document.getElementById(targetId);
      if (!input) return;
      if (input.type === "password") {
        input.type = "text";
        btn.textContent = "🙈";
      } else {
        input.type = "password";
        btn.textContent = "👁";
      }
    });
  });

  // auto-hide flashes after 4s
  setTimeout(() => {
    document.querySelectorAll(".flash").forEach(el => {
      el.style.transition = "opacity 0.5s";
      el.style.opacity = 0;
      setTimeout(() => el.remove(), 600);
    });
  }, 4000);
});