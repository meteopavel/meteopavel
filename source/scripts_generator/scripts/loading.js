function setupImgSkeleton(img) {
  if (img.complete && img.naturalWidth > 0) {
    img.classList.add('img-loaded');
  } else {
    img.addEventListener('load', function () { img.classList.add('img-loaded'); });
    img.addEventListener('error', function () { img.classList.add('img-loaded'); });
  }
}

function setupSvgSkeleton(svg) {
  var useEl = svg.querySelector('use');
  if (!useEl) { svg.classList.add('svg-loaded'); return; }
  var href = useEl.getAttribute('href') || useEl.getAttribute('xlink:href') || '';
  var filePath = href.split('#')[0];
  if (!filePath) { svg.classList.add('svg-loaded'); return; }
  fetch(filePath)
    .then(function () { svg.classList.add('svg-loaded'); })
    .catch(function () { svg.classList.add('svg-loaded'); });
}

document.querySelectorAll('.main-info__photo, .video-preview__image').forEach(setupImgSkeleton);

document.querySelectorAll('.project__shields img').forEach(function (img, i) {
  img.style.animationDelay = '-' + ((i * 0.25) % 1.5) + 's';
  setupImgSkeleton(img);
});

document.querySelectorAll('svg.contact-icon').forEach(function (svg, i) {
  svg.style.animationDelay = '-' + ((i * 0.2) % 1.5) + 's';
  setupSvgSkeleton(svg);
});

document.querySelectorAll('svg.preview-icon').forEach(function (svg, i) {
  svg.style.animationDelay = '-' + ((i * 0.3) % 1.5) + 's';
  setupSvgSkeleton(svg);
});
