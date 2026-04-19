#!/bin/bash
set -euo pipefail

REPO_REQUIRED_REMOTE='git@github.com:meteopavel/meteopavel.git'
REPO_REQUIRED_REMOTE_HTTPS='https://github.com/meteopavel/meteopavel.git'
DEFAULT_BRANCH_NAME='main'
REPO_ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="${REPO_ROOT}/.env"

SOURCE_DIR="${REPO_ROOT}/source"
PYTHON_BIN="${SOURCE_DIR}/.venv/bin/python"
STATIC_SCRIPT="generate_static.py"

DEFAULT_COMMIT_MESSAGE='Update project'
DEFAULT_HTML_MODE='minify'
DEFAULT_SHIELDS_MODE='no'

get_env() {
  local var_name="$1"
  local env_file="$2"

  if [[ ! -f "$env_file" ]]; then
    echo ""
    return
  fi

  grep -E "^${var_name}=" "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2-
}

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
  local shields_mode="$2"

  local cmd=("${PYTHON_BIN}" "${STATIC_SCRIPT}" --html-mode "$html_mode")

  if [[ "$shields_mode" == "no" ]]; then
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

echo '🔍 Загружаем настройки из .env, если он есть...'

ENV_HTML_MODE="$(get_env "DEPLOY_HTML_MODE" "$ENV_FILE")"
ENV_SHIELDS_MODE="$(get_env "DEPLOY_NO_SHIELDS" "$ENV_FILE")"
ENV_BRANCH_NAME="$(get_env "DEPLOY_BRANCH" "$ENV_FILE")"

HTML_MODE="${ENV_HTML_MODE:-$DEFAULT_HTML_MODE}"
SHIELDS_MODE="$DEFAULT_SHIELDS_MODE"
BRANCH_NAME="${ENV_BRANCH_NAME:-$DEFAULT_BRANCH_NAME}"

if [[ -n "${ENV_SHIELDS_MODE}" ]]; then
  case "${ENV_SHIELDS_MODE}" in
    1|true|TRUE|yes|YES|y|Y)
      SHIELDS_MODE='no'
      ;;
    0|false|FALSE|no|NO|n|N)
      SHIELDS_MODE='yes'
      ;;
  esac
fi

echo
echo '⚙️ Режимы сборки:'
echo '   1) Продакшн по умолчанию: --html-mode minify --no-shields'
echo '   2) Сборка с shields:      --html-mode minify'
echo '   3) Читаемый HTML:         --html-mode pretty --no-shields'
echo '   4) Свой вариант'
echo

read -r -p 'Выбери режим сборки [1]: ' BUILD_MODE
BUILD_MODE="${BUILD_MODE:-1}"

case "$BUILD_MODE" in
  1)
    HTML_MODE='minify'
    SHIELDS_MODE='no'
    ;;
  2)
    HTML_MODE='minify'
    SHIELDS_MODE='yes'
    ;;
  3)
    HTML_MODE='pretty'
    SHIELDS_MODE='no'
    ;;
  4)
    read -r -p "HTML mode [${HTML_MODE}]: " CUSTOM_HTML_MODE
    CUSTOM_HTML_MODE="${CUSTOM_HTML_MODE:-$HTML_MODE}"

    read -r -p "Отключить shields? (yes/no) [${SHIELDS_MODE}]: " CUSTOM_SHIELDS_MODE
    CUSTOM_SHIELDS_MODE="${CUSTOM_SHIELDS_MODE:-$SHIELDS_MODE}"

    HTML_MODE="$CUSTOM_HTML_MODE"
    SHIELDS_MODE="$CUSTOM_SHIELDS_MODE"
    ;;
  *)
    echo '❌ Ошибка: некорректный режим.'
    exit 1
    ;;
esac

echo
echo '🧾 Выбраны параметры сборки:'
echo "   html mode  = ${HTML_MODE}"
echo "   no shields = ${SHIELDS_MODE}"
echo "   branch     = ${BRANCH_NAME}"

if ! confirm 'Продолжить сборку?'; then
  echo '⏹ Операция отменена.'
  exit 0
fi

build_static "${HTML_MODE}" "${SHIELDS_MODE}"

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