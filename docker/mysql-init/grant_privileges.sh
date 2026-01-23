#!/bin/bash

# Wait for MySQL to be ready
until docker-compose exec db mysqladmin ping --silent; do
    echo "Waiting for MySQL to be ready..."
    sleep 2
done

# Get the root password from environment or use default
echo "Enter the MySQL root password (BADGR_DB_PASSWORD):"
read -s root_password

echo "Granting privileges to badgr user..."

# Create and run SQL script
docker-compose exec db bash -c "
    echo 'CREATE DATABASE IF NOT EXISTS test_badgr;' > /tmp/grant_privs.sql
    echo 'GRANT ALL PRIVILEGES ON badgr.* TO "badgr"@"%" WITH GRANT OPTION;' >> /tmp/grant_privs.sql
    echo 'GRANT ALL PRIVILEGES ON test_badgr.* TO "badgr"@"%" WITH GRANT OPTION;' >> /tmp/grant_privs.sql
    echo 'GRANT ALL PRIVILEGES ON \`test_\\%\`.* TO "badgr"@"%" WITH GRANT OPTION;' >> /tmp/grant_privs.sql
    echo 'FLUSH PRIVILEGES;' >> /tmp/grant_privs.sql
    mysql -u root -p${root_password} < /tmp/grant_privs.sql
    rm /tmp/grant_privs.sql
"

echo "Privileges granted successfully!"