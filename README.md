<!-- README.md -->
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Резюме Найденова Павла Андреевича</title>
  <style>
    /* Встроенные стили */
    body {
      font-family: 'Open Sans', sans-serif;
      line-height: 1.6;
      margin: 0;
      padding: 0;
      background-color: #f9f9f9;
      color: #333;
    }
    header {
      text-align: center;
      padding: 20px;
      background-color: #007bff;
      color: white;
    }
    main {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    section {
      margin-bottom: 40px;
    }
    h2 {
      color: #007bff;
      border-bottom: 2px solid #007bff;
      padding-bottom: 10px;
    }
    .shields-container {
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      justify-content: center;
    }
    .shields-container img {
      height: 30px;
    }
  </style>
</head>
<body>
  <header>
    <h1>Найденов Павел Андреевич</h1>
    <p>Python разработчик</p>
  </header>

  <main>
    <!-- Раздел "Обо мне" -->
    <section id="about-me">
      <h2>Обо мне</h2>
      <p>Я выбрал бэкенд-разработку на Python, потому что она является основой для создания современных веб-приложений. Мне нравится работать с "невидимой" частью приложений, обеспечивая их функциональность и стабильность.</p>
    </section>
    <!-- Раздел "Технологии" -->
    <section id="shields">
      <h2>Технологии</h2>
      <div class="shields-container">
        <a href="https://www.python.org/downloads/release/python-31010/">
          <img src="https://img.shields.io/badge/Python-blue?style=flat&logo=python&labelColor=FDEBD0&logoColor=blue" alt="Python">
        </a>
        <a href="https://docs.djangoproject.com/en/5.0/releases/5.0/">
          <img src="https://img.shields.io/badge/Django-green?style=flat&logo=django&labelColor=FDEBD0&logoColor=blue" alt="Django">
        </a>
        <a href="https://flask.palletsprojects.com/en/2.2.x/changes/">
          <img src="https://img.shields.io/badge/Flask-blue?style=flat&logo=flask&labelColor=FDEBD0&logoColor=blue" alt="Flask">
        </a>
        <!-- Добавьте остальные шилды -->
      </div>
    </section>
    <!-- Раздел "Опыт работы" -->
    <section id="experience">
      <h2>Опыт работы</h2>
      <ul>
        <li><strong>Legacy сервис рассылки email</strong> (Апрель 2023 — настоящее время)</li>
        <li><strong>Telegram-бот для поиска коммерческой недвижимости</strong></li>
        <li><strong>API для отзывов на произведения</strong></li>
      </ul>
    </section>
  </main>

  <footer>
    <p>© 2023 Найденов Павел Андреевич</p>
  </footer>
</body>
</html>