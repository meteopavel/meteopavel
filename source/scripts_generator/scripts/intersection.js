document.addEventListener('DOMContentLoaded', () => {
  if (window.innerWidth >= 460) {
    return;
  }

  const elements = document.querySelectorAll('.highlightable');

  const options = {
    root: null,
    rootMargin: '0px',
    threshold: 0.75,
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        elements.forEach(el => el.classList.remove('highlighted'));
        entry.target.classList.add('highlighted');
      } else {
        entry.target.classList.remove('highlighted');
      }
    });
  }, options);

  elements.forEach(element => {
    observer.observe(element);
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth >= 460) {
      elements.forEach(el => el.classList.remove('highlighted'));
    } else {
      elements.forEach(element => {
        observer.observe(element);
      });
    }
  });
});