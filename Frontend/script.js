/* ================= THEME TOGGLE ================= */
const toggle = document.getElementById("themeToggle");
toggle?.addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("theme", theme);
});

/* LOAD THEME */
document.documentElement.dataset.theme =
  localStorage.getItem("theme") || "light";

/* ================= SIDEBAR COLLAPSE ================= */
const sidebar = document.querySelector(".sidebar");
document.getElementById("collapseBtn")?.addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
});

/* ================= ACCENT COLORS PER TOOL ================= */
document.querySelectorAll(".tool-item").forEach(item => {
  item.addEventListener("mouseenter", () => {
    document.documentElement.style.setProperty(
      "--accent",
      item.dataset.accent
    );
  });
});

/* ================= SCROLL AUTO HIGHLIGHT ================= */
const sections = document.querySelectorAll("section");
const toolItems = document.querySelectorAll(".tool-item");

window.addEventListener("scroll", () => {
  let current = "";
  
  sections.forEach((sec) => {
    const sectionTop = sec.offsetTop;
    const sectionHeight = sec.clientHeight;
    // Checks if the scroll position is within the section bounds
    if (window.scrollY >= (sectionTop - 150)) {
      current = sec.getAttribute("id");
    }
  });

  toolItems.forEach((a) => {
    a.classList.remove("active");
    if (a.dataset.section === current) {
      a.classList.add("active");
      
      // OPTIONAL: Auto-scroll the sidebar to keep the active item visible
      if (!window.matchMedia("(max-width: 768px)").matches) {
          a.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  });
}, { passive: true });


/* ================= FILE PREVIEW ================= */
document.querySelectorAll("input[type=file]").forEach(input => {
  input.addEventListener("change", e => {
    const img = document.getElementById(input.dataset.preview);
    if (img && e.target.files[0]) {
      img.src = URL.createObjectURL(e.target.files[0]);
      img.style.display = "block";
    }
  });
});
/*=====================Textbox=====================*/

  const copyBtn = document.getElementById("copyBtn");
  const textarea = document.getElementById("promptText");

  copyBtn.addEventListener("click", async () => {
    const text = textarea.value.trim();
    if (!text) return;

    try {
      // Modern clipboard API
      await navigator.clipboard.writeText(text);

      // Optional feedback
      const originalText = copyBtn.innerText;
      copyBtn.innerText = "✅ Copied!";
      setTimeout(() => {
        copyBtn.innerText = originalText;
      }, 1200);
    } catch (err) {
      // Fallback for old browsers
      textarea.select();
      textarea.setSelectionRange(0, 99999);
      document.execCommand("copy");

      const originalText = copyBtn.innerText;
      copyBtn.innerText = "✅ Copied!";
      setTimeout(() => {
        copyBtn.innerText = originalText;
      }, 1200);
    }
  });