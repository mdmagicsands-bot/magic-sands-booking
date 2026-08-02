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

  const SKIP_UPPER_TYPES = new Set([
    "checkbox",
    "radio",
    "file",
    "hidden",
    "submit",
    "button",
    "number",
    "password",
  ]);

  const shouldForceUpper = (el) => {
    if (!el || (el.tagName !== "INPUT" && el.tagName !== "TEXTAREA")) return false;
    return !SKIP_UPPER_TYPES.has(el.type || "");
  };

  const forceUpper = (el) => {
    if (!shouldForceUpper(el)) return;
    const upper = el.value.toLocaleUpperCase("en-US");
    if (el.value === upper) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    el.value = upper;
    if (typeof start === "number" && typeof end === "number") {
      try {
        el.setSelectionRange(start, end);
      } catch (_) {
        /* some input types reject selection */
      }
    }
  };

  const upperAllTextFields = () => {
    form.querySelectorAll("input, textarea").forEach(forceUpper);
  };

  form.addEventListener("input", (event) => forceUpper(event.target));
  form.addEventListener("blur", (event) => forceUpper(event.target), true);
  form.addEventListener("change", (event) => forceUpper(event.target));
  upperAllTextFields();

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
    if (prevBtn) prevBtn.hidden = index === 0;
    if (nextBtn) nextBtn.hidden = index === panels.length - 1;
    if (submitBtn) submitBtn.hidden = index !== panels.length - 1;
    form.dataset.lastStep = index === panels.length - 1 ? "true" : "false";
    if (progress) progress.textContent = `Step ${index + 1} of ${panels.length}`;
    form.scrollIntoView({ behavior: "smooth", block: "start" });
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

  nextBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    if (!validatePanel(panels[index])) return;
    show(index + 1);
  });
  prevBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    show(index - 1);
  });

  form.addEventListener("submit", (event) => {
    upperAllTextFields();
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
