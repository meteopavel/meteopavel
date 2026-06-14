var CAROUSEL_SIZE = 4;

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

  var html = '';
  sortedYears.forEach(function (y) {
    html += '<div class="devlog__year-row">';
    html += '<button class="devlog__year-btn" data-year="' + y + '">' + y + '</button>';
    html += '<div class="devlog__months-carousel">';
    html += '<button class="devlog__carousel-btn devlog__carousel-prev" data-year="' + y + '" aria-label="Назад" disabled>&#8249;</button>';
    html += '<div class="devlog__months-row" data-year-row="' + y + '" hidden>';
    years[y].forEach(function (m) {
      var fullLabel = m.dataset.label.split(' ')[0];
      var abbrLabel = fullLabel.slice(0, 3);
      var numLabel = parseInt(m.dataset.period.slice(5, 7), 10);
      html += '<button class="devlog__month-btn" data-period="' + m.dataset.period + '">';
      html += '<span class="devlog__month-long">' + fullLabel + '</span>';
      html += '<span class="devlog__month-abbr">' + abbrLabel + '</span>';
      html += '<span class="devlog__month-num">' + numLabel + '</span>';
      html += '</button>';
    });
    html += '</div>';
    html += '<button class="devlog__carousel-btn devlog__carousel-next" data-year="' + y + '" aria-label="Вперёд">&#8250;</button>';
    html += '</div>';
    html += '</div>';
  });

  nav.innerHTML = html;

  nav.querySelectorAll('.devlog__year-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { selectYear(panel, nav, btn.dataset.year); });
  });
  nav.querySelectorAll('.devlog__month-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { selectMonth(panel, nav, btn.dataset.period); });
  });
  nav.querySelectorAll('.devlog__carousel-prev').forEach(function (btn) {
    btn.addEventListener('click', function () { shiftCarousel(nav, btn.dataset.year, -CAROUSEL_SIZE); });
  });
  nav.querySelectorAll('.devlog__carousel-next').forEach(function (btn) {
    btn.addEventListener('click', function () { shiftCarousel(nav, btn.dataset.year, CAROUSEL_SIZE); });
  });

  selectYear(panel, nav, sortedYears[0]);
}

function updateCarousel(nav, year) {
  var row = nav.querySelector('.devlog__months-row[data-year-row="' + year + '"]');
  if (!row) return;
  var offset = parseInt(row.dataset.carouselOffset || '0', 10);
  var btns = row.querySelectorAll('.devlog__month-btn');
  var total = btns.length;

  btns.forEach(function (btn, i) {
    btn.classList.toggle('devlog__month-btn--hidden', i < offset || i >= offset + CAROUSEL_SIZE);
  });

  var prevBtn = nav.querySelector('.devlog__carousel-prev[data-year="' + year + '"]');
  var nextBtn = nav.querySelector('.devlog__carousel-next[data-year="' + year + '"]');
  if (prevBtn) prevBtn.disabled = offset <= 0;
  if (nextBtn) nextBtn.disabled = offset + CAROUSEL_SIZE >= total;
}

function shiftCarousel(nav, year, delta) {
  var row = nav.querySelector('.devlog__months-row[data-year-row="' + year + '"]');
  if (!row) return;
  var btns = row.querySelectorAll('.devlog__month-btn');
  var total = btns.length;
  var offset = parseInt(row.dataset.carouselOffset || '0', 10);
  offset = Math.max(0, Math.min(offset + delta, Math.max(0, total - CAROUSEL_SIZE)));
  row.dataset.carouselOffset = offset;
  updateCarousel(nav, year);
}

function selectYear(panel, nav, year) {
  nav.querySelectorAll('.devlog__year-btn').forEach(function (b) {
    b.classList.toggle('devlog__year-btn--active', b.dataset.year === year);
  });
  nav.querySelectorAll('.devlog__months-row').forEach(function (r) {
    var isActive = r.dataset.yearRow === year;
    r.hidden = !isActive;
    if (isActive) r.dataset.carouselOffset = '0';
  });
  nav.querySelectorAll('.devlog__carousel-btn').forEach(function (btn) {
    btn.style.display = btn.dataset.year === year ? '' : 'none';
  });
  updateCarousel(nav, year);
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
