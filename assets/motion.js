(() => {
  const stage = document.getElementById("logo-stage");
  const replay = document.getElementById("replay");
  if (!stage || !replay) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  function play() {
    stage.setAttribute("data-reset", "");
    // Commit the static state so each stroke restarts on a second activation.
    stage.getBoundingClientRect();
    stage.removeAttribute("data-reset");
  }

  function syncPreference() {
    replay.hidden = reduced.matches;
  }

  replay.addEventListener("click", play);
  reduced.addEventListener("change", syncPreference);
  syncPreference();
})();
