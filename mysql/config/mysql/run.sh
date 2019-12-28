#!/bin/bash
touch /var/log/mysql_backup.log
tail -F /var/log/mysql_backup.log &

if [ -n "${INIT_BACKUP}" ]; then
  echo "=> Create a backup on the startup"
  /backup.sh
elif [ -n "${INIT_RESTORE_LATEST}" ]; then
  echo "=> Restore latest backup"
  until nc -z "$MYSQL_HOST" "$MYSQL_PORT"
  do
      echo "waiting database container..."
      sleep 1
  done
find /backup -maxdepth 1 -name '*.sql.gz' | tail -1 | xargs /restore.sh
fi

echo -e "${CRON_TIME} /backup.sh >> /var/log/mysql_backup.log 2>&1 \n" > /crontab.conf
crontab /crontab.conf
echo "=> Running cron task manager"
exec crond -f