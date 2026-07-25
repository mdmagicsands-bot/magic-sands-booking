(() => {
  const form = document.getElementById("partner-register-form");
  if (!form) return;

  const panels = Array.from(form.querySelectorAll(".pr-panel"));
  const steps = Array.from(document.querySelectorAll("#pr-steps li"));
  const prevBtn = document.getElementById("pr-prev");
  const nextBtn = document.getElementById("pr-next");
  const submitBtn = document.getElementById("pr-submit");
  const progress = document.getElementById("pr-progress");
  let index = 0;

  const show = (i) => {
    index = Math.max(0, Math.min(i, panels.length - 1));
    panels.forEach((panel, n) => {
      const active = n === index;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
    steps.forEach((step, n) => {
      step.classList.toggle("is-active", n === index);
      step.classList.toggle("is-done", n < index);
    });
    prevBtn.hidden = index === 0;
    nextBtn.hidden = index === panels.length - 1;
    submitBtn.hidden = index !== panels.length - 1;
    progress.textContent = `Step ${index + 1} of ${panels.length}`;
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const validatePanel = (panel) => {
    const fields = Array.from(
      panel.querySelectorAll("input, select, textarea")
    ).filter((el) => !el.disabled);
    for (const el of fields) {
      if (el.type === "checkbox" && el.name === "business_types") continue;
      if (!el.checkValidity()) {
        el.reportValidity();
        return false;
      }
    }
    if (panel.dataset.step === "3") {
      const checked = panel.querySelectorAll('input[name="business_types"]:checked');
      if (!checked.length) {
        alert("Please select at least one of FIT / Groups / MICE.");
        return false;
      }
    }
    return true;
  };

  nextBtn?.addEventListener("click", () => {
    if (!validatePanel(panels[index])) return;
    show(index + 1);
  });
  prevBtn?.addEventListener("click", () => show(index - 1));

  form.addEventListener("submit", (event) => {
    if (!validatePanel(panels[index])) {
      event.preventDefault();
      return;
    }
    const terms = form.querySelector('input[name="accepted_terms"]');
    if (terms && !terms.checked) {
      event.preventDefault();
      terms.reportValidity();
    }
  });

  show(0);
})();
