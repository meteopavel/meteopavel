document.addEventListener('DOMContentLoaded', () => {
  // Проверяем ширину экрана
  if (window.innerWidth >= 460) {
    return; // Если ширина экрана больше или равна 460px, ничего не делаем
  }

  // Находим все элементы, которые нужно подсвечивать
  const elements = document.querySelectorAll('.highlightable');

  // Настройки для Intersection Observer
  const options = {
    root: null, // Относительно viewport
    rootMargin: '0px', // Без отступов
    threshold: 0.5, // Элемент считается видимым, если 50% его площади в зоне видимости
  };

  // Callback-функция, которая вызывается при пересечении элемента с viewport
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Убираем подсветку у всех элементов
        elements.forEach(el => el.classList.remove('highlighted'));

        // Добавляем подсветку только текущему элементу
        entry.target.classList.add('highlighted');
      } else {
        // Убираем подсветку, если элемент выходит из зоны видимости
        entry.target.classList.remove('highlighted');
      }
    });
  }, options);

  // Начинаем наблюдать за каждым элементом
  elements.forEach(element => {
    observer.observe(element);
  });

  // Обновление при изменении размера окна
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 460) {
      // Если ширина экрана стала больше или равна 460px, убираем все подсветки
      elements.forEach(el => el.classList.remove('highlighted'));
    } else {
      // Если ширина экрана снова меньше 460px, перезапускаем Intersection Observer
      elements.forEach(element => {
        observer.observe(element);
      });
    }
  });
});