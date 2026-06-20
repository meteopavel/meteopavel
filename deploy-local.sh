#!/bin/bash
set -euo pipefail

NON_INTERACTIVE=false
COMMIT_MESSAGE_ARG=''
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[$i]}" in
    --non-interactive) NON_INTERACTIVE=true ;;
    --message|-m) COMMIT_MESSAGE_ARG="${args[$((i+1))]}"; i=$((i+1)) ;;
  esac
done

REPO_REQUIRED_REMOTE='git@github.com:meteopavel/meteopavel.git'
REPO_REQUIRED_REMOTE_HTTPS='https://github.com/meteopavel/meteopavel.git'
BRANCH_NAME='main'

REPO_ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="${REPO_ROOT}/.env"
SOURCE_DIR="${REPO_ROOT}/source"
PYTHON_BIN="${SOURCE_DIR}/.venv/bin/python"
STATIC_SCRIPT='generate_static.py'

ARCHIVE_DIR='secure'
ARCHIVE_NAME='sensitive_bundle.7z'
ARCHIVE_PATH="${ARCHIVE_DIR}/${ARCHIVE_NAME}"

DEFAULT_COMMIT_MESSAGE='Update project'

# ================= ФУНКЦИИ =================

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "❌ Ошибка: команда '${command_name}' не найдена."
    exit 1
  fi
}

get_env() {
  local var_name="$1"
  local env_file="$2"

  if [[ ! -f "$env_file" ]]; then
    echo ""
    return
  fi

  grep -E "^${var_name}=" "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2-
}

require_env() {
  local var_name="$1"
  local var_value="$2"

  if [[ -z "$var_value" ]]; then
    echo "❌ Ошибка: переменная ${var_name} не найдена или пуста в ${ENV_FILE}"
    exit 1
  fi
}

confirm() {
  local prompt="${1:-Продолжить?}"
  local answer

  if [[ "$NON_INTERACTIVE" == true ]]; then
    return 0
  fi

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

update_project_passport() {
  echo '🪪 Обновляем паспорт проекта...'

  (
    cd "${REPO_ROOT}"
    "${PYTHON_BIN}" tools/build_project_passport.py --project-root .
    "${PYTHON_BIN}" tools/extract_api_map.py source --project-root . --exclude .venv __pycache__ node_modules
  )

  echo '✅ Паспорт проекта обновлён.'
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

# ================= ПРОВЕРКИ =================

echo '🔍 Проверяем, что мы внутри git-репозитория...'
git rev-parse --is-inside-work-tree >/dev/null 2>&1

echo '🔍 Проверяем обязательные команды...'
require_command git
require_command 7z
require_command rsync
require_command sshpass

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

echo '🔍 Загружаем переменные из .env...'
ARCHIVE_PASSWORD="$(get_env "ARCHIVE_PASSWORD" "$ENV_FILE")"
SECURE_RSYNC_USER="$(get_env "SECURE_RSYNC_USER" "$ENV_FILE")"
SECURE_RSYNC_HOST="$(get_env "SECURE_RSYNC_HOST" "$ENV_FILE")"
SECURE_RSYNC_PATH="$(get_env "SECURE_RSYNC_PATH" "$ENV_FILE")"
SECURE_RSYNC_PASSWORD="$(get_env "SECURE_RSYNC_PASSWORD" "$ENV_FILE")"
SHARED_SSH_USER="$(get_env "SHARED_SSH_USER" "$ENV_FILE")"
SHARED_SSH_HOST="$(get_env "SHARED_SSH_HOST" "$ENV_FILE")"
SHARED_SSH_PATH="$(get_env "SHARED_SSH_PATH" "$ENV_FILE")"
SHARED_SSH_PASSWORD="$(get_env "SHARED_SSH_PASSWORD" "$ENV_FILE")"

require_env "ARCHIVE_PASSWORD" "$ARCHIVE_PASSWORD"
require_env "SECURE_RSYNC_USER" "$SECURE_RSYNC_USER"
require_env "SECURE_RSYNC_HOST" "$SECURE_RSYNC_HOST"
require_env "SECURE_RSYNC_PATH" "$SECURE_RSYNC_PATH"
require_env "SECURE_RSYNC_PASSWORD" "$SECURE_RSYNC_PASSWORD"
require_env "SHARED_SSH_USER" "$SHARED_SSH_USER"
require_env "SHARED_SSH_HOST" "$SHARED_SSH_HOST"
require_env "SHARED_SSH_PATH" "$SHARED_SSH_PATH"
require_env "SHARED_SSH_PASSWORD" "$SHARED_SSH_PASSWORD"

mkdir -p "${ARCHIVE_DIR}"

# ================= АРХИВАЦИЯ =================

if [[ -f "${ARCHIVE_PATH}" ]]; then
  echo "🗑 Удаляем старый архив: ${ARCHIVE_PATH}"
  rm -f "${ARCHIVE_PATH}"
fi

echo '🔐 Создаём зашифрованный архив (docs/, CLAUDE.md, .claude/, .env)...'
(
  cd "${REPO_ROOT}"
  7z a -p"${ARCHIVE_PASSWORD}" -mhe=on "${ARCHIVE_PATH}" \
    "docs" \
    "CLAUDE.md" \
    ".claude" \
    ".env"
)
echo '✅ Архив успешно создан.'

echo '📤 Отправляем архив на backup-сервер...'
export SSHPASS="${SECURE_RSYNC_PASSWORD}"
rsync -avz --progress \
  --rsh="sshpass -e ssh" \
  "${ARCHIVE_PATH}" "${SECURE_RSYNC_USER}@${SECURE_RSYNC_HOST}:${SECURE_RSYNC_PATH}"
echo '✅ Архив успешно отправлен на сервер.'

# ================= PROJECT PASSPORT =================

update_project_passport

# ================= СБОРКА =================

if [[ "$NON_INTERACTIVE" == true ]]; then
  HTML_MODE='minify'
  USE_NO_SHIELDS='yes'
  echo
  echo 'ℹ️ Режим без ввода: сборка с параметрами по умолчанию (minify + --no-shields)'
else
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
fi

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

# ================= GIT =================

echo
echo '📋 Текущий git status:'
(
  cd "${REPO_ROOT}"
  git status --short
)
echo

if [[ -n "$COMMIT_MESSAGE_ARG" ]]; then
  COMMIT_MESSAGE="$COMMIT_MESSAGE_ARG"
elif [[ "$NON_INTERACTIVE" == true ]]; then
  COMMIT_MESSAGE="$DEFAULT_COMMIT_MESSAGE"
  echo "ℹ️ Режим без ввода: используется сообщение по умолчанию: ${COMMIT_MESSAGE}"
else
  read -r -p "✍️ Введите сообщение коммита [${DEFAULT_COMMIT_MESSAGE}]: " COMMIT_MESSAGE
  COMMIT_MESSAGE="${COMMIT_MESSAGE:-$DEFAULT_COMMIT_MESSAGE}"
fi

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
  echo '🎉 Готово: архив отправлен на backup-сервер.'
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

echo '📤 Синхронизируем static/ на shared хостинг...'
export SSHPASS="${SHARED_SSH_PASSWORD}"
rsync -avz --delete --progress \
  --rsh="sshpass -e ssh -o StrictHostKeyChecking=no" \
  "${REPO_ROOT}/static/" "${SHARED_SSH_USER}@${SHARED_SSH_HOST}:${SHARED_SSH_PATH}"
echo '✅ static/ успешно залит на shared хостинг.'

echo '🎉 Готово: архив на backup-сервере, код на GitHub, статика на хостинге.'
