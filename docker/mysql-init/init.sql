-- Grant all privileges to badgr user for both production and test databases
GRANT ALL PRIVILEGES ON badgr.* TO 'badgr'@'%';
GRANT ALL PRIVILEGES ON test_badgr.* TO 'badgr'@'%';

-- Also grant privileges for any database starting with 'test_'
GRANT ALL PRIVILEGES ON `test_\_%`.* TO 'badgr'@'%';

FLUSH PRIVILEGES;