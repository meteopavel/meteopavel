function toggleDevlog(btn) {
  var panel = document.getElementById('devlog-panel');
  var card = document.getElementById('mailganer-card');
  var isOpen = panel.classList.contains('devlog--open');
  panel.classList.toggle('devlog--open', !isOpen);
  btn.classList.toggle('devlog__toggle--open', !isOpen);
  btn.setAttribute('aria-expanded', String(!isOpen));
  if (card) card.classList.toggle('mailganer__card--open', !isOpen);
  if (!isOpen && !panel.dataset.initialized) {
    initDevlog(panel);
    panel.dataset.initialized = '1';
  }
}

function initDevlog(panel) {
  var months = panel.querySelectorAll('.devlog__month');
  var nav = panel.querySelector('.devlog__nav');

  var years = {};
  months.forEach(function (m) {
    var year = m.dataset.period.slice(0, 4);
    if (!years[year]) years[year] = [];
    years[year].push(m);
  });

  var sortedYears = Object.keys(years).sort().reverse();

  var yearsHtml = '<div class="devlog__years">';
  sortedYears.forEach(function (y) {
    yearsHtml += '<button class="devlog__year-btn" data-year="' + y + '">' + y + '</button>';
  });
  yearsHtml += '</div>';

  var monthsHtml = '';
  sortedYears.forEach(function (y) {
    monthsHtml += '<div class="devlog__months-row" data-year-row="' + y + '">';
    years[y].forEach(function (m) {
      var shortLabel = m.dataset.label.split(' ')[0];
      monthsHtml += '<button class="devlog__month-btn" data-period="' + m.dataset.period + '">' + shortLabel + '</button>';
    });
    monthsHtml += '</div>';
  });

  nav.innerHTML = yearsHtml + monthsHtml;

  nav.querySelectorAll('.devlog__year-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { selectYear(panel, nav, btn.dataset.year); });
  });
  nav.querySelectorAll('.devlog__month-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { selectMonth(panel, nav, btn.dataset.period); });
  });

  selectYear(panel, nav, sortedYears[0]);
}

function selectYear(panel, nav, year) {
  nav.querySelectorAll('.devlog__year-btn').forEach(function (b) {
    b.classList.toggle('devlog__year-btn--active', b.dataset.year === year);
  });
  nav.querySelectorAll('.devlog__months-row').forEach(function (r) {
    r.hidden = r.dataset.yearRow !== year;
  });
  var firstMonthBtn = nav.querySelector('.devlog__months-row:not([hidden]) .devlog__month-btn');
  if (firstMonthBtn) selectMonth(panel, nav, firstMonthBtn.dataset.period);
}

function selectMonth(panel, nav, period) {
  nav.querySelectorAll('.devlog__month-btn').forEach(function (b) {
    b.classList.toggle('devlog__month-btn--active', b.dataset.period === period);
  });
  panel.querySelectorAll('.devlog__month').forEach(function (m) {
    m.hidden = m.dataset.period !== period;
  });
}
