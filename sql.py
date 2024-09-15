from mysql.connector import connect # type: ignore
import json

config = json.load(open('data/config.json', 'r'))
db = connect(host='localhost', user=config['database']['db_name'], password=config['database']['db_password'], database=config['database']['db_username'])
cursor = db.cursor(buffered=True)

cursor.execute("""
CREATE TABLE IF NOT EXISTS `users` (
	`row` INT(11) AUTO_INCREMENT PRIMARY KEY,
	`from_id` BIGINT(20) NOT NULL,
	`step` VARCHAR(200) DEFAULT 'none',
    `balance` FLOAT DEFAULT 0,
    `wallet` TEXT DEFAULT NULL,
    `join_time` BIGINT DEFAULT 0,
    `lang` VARCHAR(5) DEFAULT 'none',
    `status` BOOLEAN DEFAULT 1,
    `count_accounts` BIGINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `accounts` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `from_id` BIGINT(20) NOT NULL,
    `country_code` TEXT NOT NULL,
    `number` TEXT NOT NULL,
    `status` BOOLEAN DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `open_country` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `country_name` TEXT NOT NULL,
    `country_code` TEXT NOT NULL,
    `country_flag` TEXT NOT NULL,
    `country_price` FLOAT DEFAULT 1,
    `country_capacity` BIGINT DEFAULT 10,
    `country_time` FLOAT DEFAULT 1,
	`status` BOOLEAN DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `close_country` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `country_name` TEXT NOT NULL,
    `country_code` TEXT NOT NULL,
    `country_flag` TEXT NOT NULL,
	`status` BOOLEAN DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `withdrawal_factors` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `from_id` BIGINT(20) NOT NULL,
    `price` FLOAT NOT NULL,
    `wallet` TEXT NOT NULL,
    `code` BIGINT DEFAULT 0,
	`status` BOOLEAN DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `temporary_data` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `from_id` BIGINT(20) NOT NULL,
    `api_id` BIGINT DEFAULT NULL,
    `api_hash` TEXT DEFAULT NULL,
    `number` TEXT NOT NULL,
    `phone_code_hash` TEXT DEFAULT NULL,
    `code` TEXT DEFAULT NULL,
    `password` TEXT DEFAULT NULL,
    `proxy` TEXT DEFAULT NULL,
    `other` TEXT DEFAULT NULL,
    `status` BOOLEAN DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `proxies` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `ip` TEXT NOT NULL,
    `port` TEXT NOT NULL,
    `username` TEXT DEFAULT NULL,
    `password` TEXT DEFAULT NULL,
    `count_use` BIGINT DEFAULT 0,
    `status` BOOLEAN DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `admins` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `from_id` BIGINT(20) NOT NULL,
    `username` TEXT NOT NULL,
    `password` TEXT NOT NULL,
    `status` BOOLEAN DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `channels` (
    `row` INT(11) AUTO_INCREMENT PRIMARY KEY,
    `channel` TEXT NOT NULL,
    `status` BOOLEAN DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS `settings` (
    `min_withdrawal` FLOAT DEFAULT 2,
    `max_withdrawal` FLOAT DEFAULT 500,
    `withdrawal_status` BOOLEAN DEFAULT 1,
    `new_user_status` BOOLEAN DEFAULT 1,
    `add_account_status` BOOLEAN DEFAULT 1,
    `count_proxy_use` BIGINT DEFAULT 2,
    `account_password` TEXT DEFAULT NULL,
    `session_channel` TEXT DEFAULT NULL,
    `bot_status` BOOLEAN DEFAULT 1,
    `spam_account_status` BOOLEAN DEFAULT 0,
    `payment_channel` TEXT DEFAULT NULL,
    `process_time` FLOAT DEFAULT 1,
    `anti_login_status` BOOLEAN DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
""")
db.commit()

print('[+] Success!')
