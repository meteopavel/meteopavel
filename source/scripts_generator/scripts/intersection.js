document.addEventListener('DOMContentLoaded', function () {
  if (window.innerWidth >= 460) return;

  var elements = Array.from(document.querySelectorAll('.highlightable'));

  function updateHighlight() {
    var bestEl = null;
    var bestRatio = 0;
    var viewH = window.innerHeight;
    elements.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      var visible = Math.max(0, Math.min(rect.bottom, viewH) - Math.max(rect.top, 0));
      var ratio = rect.height > 0 ? visible / rect.height : 0;
      if (ratio > bestRatio) {
        bestRatio = ratio;
        bestEl = el;
      }
    });
    elements.forEach(function (el) { el.classList.remove('highlighted'); });
    if (bestEl && bestRatio >= 0.5) bestEl.classList.add('highlighted');
  }

  window.addEventListener('scroll', updateHighlight, { passive: true });
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 460) {
      elements.forEach(function (el) { el.classList.remove('highlighted'); });
    } else {
      updateHighlight();
    }
  });

  updateHighlight();
});
