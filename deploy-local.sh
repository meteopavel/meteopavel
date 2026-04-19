#!/bin/bash
set -euo pipefail

REPO_REQUIRED_REMOTE='git@github.com:meteopavel/meteopavel.git'
REPO_REQUIRED_REMOTE_HTTPS='https://github.com/meteopavel/meteopavel.git'
BRANCH_NAME='main'

REPO_ROOT="$(git rev-parse --show-toplevel)"
SOURCE_DIR="${REPO_ROOT}/source"
PYTHON_BIN="${SOURCE_DIR}/.venv/bin/python"
STATIC_SCRIPT='generate_static.py'

DEFAULT_COMMIT_MESSAGE='Update project'

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "❌ Ошибка: команда '${command_name}' не найдена."
    exit 1
  fi
}

confirm() {
  local prompt="${1:-Продолжить?}"
  local answer

  read -r -p "${prompt} [y/N]: " answer
  case "${answer:-}" in
    y|Y|yes|YES|да|Да|ДА)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

build_static() {
  local html_mode="$1"
  local use_no_shields="$2"

  local cmd=("${PYTHON_BIN}" "${STATIC_SCRIPT}" --html-mode "$html_mode")

  if [[ "$use_no_shields" == "yes" ]]; then
    cmd+=(--no-shields)
  fi

  echo
  echo '🏗 Собираем статику...'
  echo "   Директория: ${SOURCE_DIR}"
  echo "   Команда: ${cmd[*]}"
  echo

  (
    cd "${SOURCE_DIR}"
    "${cmd[@]}"
  )

  echo '✅ Сборка завершена.'
}

echo '🔍 Проверяем, что мы внутри git-репозитория...'
git rev-parse --is-inside-work-tree >/dev/null 2>&1

echo '🔍 Проверяем обязательные команды...'
require_command git

echo '🔍 Проверяем remote origin...'
REMOTE_URL="$(git remote get-url origin)"
echo "   origin = ${REMOTE_URL}"

if [[ "${REMOTE_URL}" != "${REPO_REQUIRED_REMOTE}" && "${REMOTE_URL}" != "${REPO_REQUIRED_REMOTE_HTTPS}" ]]; then
  echo '❌ Ошибка: origin указывает не на ожидаемый репозиторий.'
  echo "Ожидалось: ${REPO_REQUIRED_REMOTE}"
  echo "      или: ${REPO_REQUIRED_REMOTE_HTTPS}"
  exit 1
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "❌ Ошибка: Python из venv не найден: ${PYTHON_BIN}"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/${STATIC_SCRIPT}" ]]; then
  echo "❌ Ошибка: файл не найден: ${SOURCE_DIR}/${STATIC_SCRIPT}"
  exit 1
fi

echo
echo '⚙️ Режимы сборки:'
echo '   1) По умолчанию: minify + --no-shields'
echo '   2) minify + со shields'
echo '   3) pretty + --no-shields'
echo '   4) Свой вариант'
echo

read -r -p 'Выбери режим сборки [1]: ' BUILD_MODE
BUILD_MODE="${BUILD_MODE:-1}"

HTML_MODE='minify'
USE_NO_SHIELDS='yes'

case "$BUILD_MODE" in
  1)
    HTML_MODE='minify'
    USE_NO_SHIELDS='yes'
    ;;
  2)
    HTML_MODE='minify'
    USE_NO_SHIELDS='no'
    ;;
  3)
    HTML_MODE='pretty'
    USE_NO_SHIELDS='yes'
    ;;
  4)
    read -r -p 'HTML mode [minify]: ' CUSTOM_HTML_MODE
    CUSTOM_HTML_MODE="${CUSTOM_HTML_MODE:-minify}"

    read -r -p 'Добавить --no-shields? [Y/n]: ' CUSTOM_NO_SHIELDS
    case "${CUSTOM_NO_SHIELDS:-Y}" in
      n|N|no|NO)
        USE_NO_SHIELDS='no'
        ;;
      *)
        USE_NO_SHIELDS='yes'
        ;;
    esac

    HTML_MODE="${CUSTOM_HTML_MODE}"
    ;;
  *)
    echo '❌ Ошибка: некорректный режим.'
    exit 1
    ;;
esac

echo
echo '🧾 Выбраны параметры сборки:'
echo "   html mode    = ${HTML_MODE}"
echo "   --no-shields = ${USE_NO_SHIELDS}"
echo "   branch       = ${BRANCH_NAME}"

if ! confirm 'Продолжить сборку?'; then
  echo '⏹ Операция отменена.'
  exit 0
fi

build_static "${HTML_MODE}" "${USE_NO_SHIELDS}"

echo
echo '📋 Текущий git status:'
(
  cd "${REPO_ROOT}"
  git status --short
)
echo

read -r -p "✍️ Введите сообщение коммита [${DEFAULT_COMMIT_MESSAGE}]: " COMMIT_MESSAGE
COMMIT_MESSAGE="${COMMIT_MESSAGE:-$DEFAULT_COMMIT_MESSAGE}"

echo "📝 Сообщение коммита: ${COMMIT_MESSAGE}"

if ! confirm 'Добавить изменения, закоммитить и отправить?'; then
  echo '⏹ Операция отменена.'
  exit 0
fi

echo '➕ Добавляем изменения в git...'
(
  cd "${REPO_ROOT}"
  git add .
)

if (
  cd "${REPO_ROOT}"
  git diff --cached --quiet
); then
  echo 'ℹ️ Нет изменений для коммита.'
  exit 0
fi

echo '📝 Создаём коммит...'
(
  cd "${REPO_ROOT}"
  git commit -m "${COMMIT_MESSAGE}"
)

echo "🚀 Выполняем push в origin/${BRANCH_NAME}..."
(
  cd "${REPO_ROOT}"
  git push origin "${BRANCH_NAME}"
)

echo '🎉 Готово.'