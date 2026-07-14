#!/usr/bin/env bash
#===============================================================================
# Общие хелперы для deploy-local.sh во всех проектах (meteopavel, Briefing,
# Home_Router_Panel, Django_EDU_Multisite). Только source, не запускать напрямую.
#===============================================================================

# run_with_heartbeat "описание" команда арг1 арг2 ...
# Запускает команду в фоне и раз в 5с печатает "прошло Nс", пока не завершится —
# чтобы зависание было видно, а не выглядело как тишина. Таймаута нет: используется
# для команд, которые не хотим прерывать (например, деплой на сервер).
run_with_heartbeat() {
    local label="$1"; shift
    local start=$SECONDS
    "$@" &
    local pid=$!
    while kill -0 "$pid" 2>/dev/null; do
        sleep 5
        echo "   ⏳ ${label} — прошло $((SECONDS - start))с..."
    done
    wait "$pid"
    return $?
}

# timeout_run СЕКУНДЫ команда арг1 арг2 ...
# Как run_with_heartbeat, но с жёстким пределом: если команда не завершилась за
# указанное число секунд — убивает её и возвращает ненулевой код.
timeout_run() {
    local secs="$1"; shift
    local start=$SECONDS
    "$@" &
    local pid=$!
    while kill -0 "$pid" 2>/dev/null; do
        if (( SECONDS - start >= secs )); then
            kill -9 "$pid" 2>/dev/null
            wait "$pid" 2>/dev/null
            echo "   ⏱ превышен лимит ${secs}с — прерываем"
            return 124
        fi
        sleep 5
        echo "   ⏳ прошло $((SECONDS - start))с (лимит ${secs}с)..."
    done
    wait "$pid"
    return $?
}

# rsync_via_tunnel USER HOST SRC DEST [EXTRA_RSYNC_FLAGS...]
# Передача файлов: rsync поверх SSH (ключ ~/.ssh/timeweb_shared), с
# переиспользуемым ControlMaster-соединением.
rsync_via_tunnel() {
    local user="$1" host="$2" src="$3" dest="$4"
    shift 4
    local ctl="/tmp/ssh_ctl_${user}_${host}"
    ssh -i ~/.ssh/timeweb_shared -o StrictHostKeyChecking=no -o ConnectTimeout=15 \
        -o ControlMaster=yes -o ControlPath="$ctl" -o ControlPersist=60s \
        -nNf "${user}@${host}" || return 1
    rsync -avz --progress --timeout=60 "$@" \
        --rsh="ssh -i ~/.ssh/timeweb_shared -o StrictHostKeyChecking=no -o ControlMaster=no -o ControlPath=$ctl -o ServerAliveInterval=10 -o ServerAliveCountMax=3" \
        "$src" "${user}@${host}:${dest}"
    local status=$?
    ssh -o ControlPath="$ctl" -O exit "${user}@${host}" 2>/dev/null || true
    return $status
}
