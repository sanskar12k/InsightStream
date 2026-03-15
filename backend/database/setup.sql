CREATE DATABASE IF NOT EXISTS `insight_stream`;
USE `insight_stream`;
CREATE USER IF NOT EXISTS 'insight_stream_backend'@'%' IDENTIFIED BY 'backend20260220';

GRANT SELECT, INSERT, UPDATE, DELETE, INDEX, CREATE, CREATE TEMPORARY TABLES, 
EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER 
on `insight_stream`.* TO 'insight_stream_backend'@'%';

FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `searches` (
  `search_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `platforms` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'amazon',
  `product_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('PENDING','IN_PROGRESS','COMPLETED','FAILED') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING',
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deep_details` int NOT NULL DEFAULT '1',
  `max_products` int NOT NULL DEFAULT '80',
  `include_reviews` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `output_filename` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `insight_generated` tinyint(1) DEFAULT '0',
  `total_products_scraped` int DEFAULT '0',
  `auto_generate_insights` int DEFAULT '0',
  `data_quality_passed` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`search_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_category` (`category`),
  CONSTRAINT `searches_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create system user for orphaned searches
INSERT INTO users (name, email, password_hash, created_at)
VALUES (
    'DeletedUser',
    'deleted@system.internal',
    '$2b$12$SYSTEM_USER_NO_LOGIN_ALLOWED',
    NOW()
)
ON DUPLICATE KEY UPDATE name = name;

-- Stored procedure to safely delete users
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS delete_user_safely(IN target_user_id INT)
BEGIN
    DECLARE system_user INT;

    -- Get system user ID
    SELECT user_id INTO system_user
    FROM users
    WHERE email = 'deleted@system.internal'
    LIMIT 1;

    -- Reassign all searches from target user to system user
    UPDATE searches
    SET user_id = system_user
    WHERE user_id = target_user_id;

    -- Now delete the user
    DELETE FROM users WHERE user_id = target_user_id;

    SELECT CONCAT('User ', target_user_id, ' deleted and ', ROW_COUNT(), ' searches reassigned') AS result;
END //
DELIMITER ;