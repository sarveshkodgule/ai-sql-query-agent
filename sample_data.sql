-- Run in MySQL Workbench as an administrator.
CREATE DATABASE IF NOT EXISTS sql_mini_project;
USE sql_mini_project;
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY, name VARCHAR(100) NOT NULL,
    email VARCHAR(150), age INT, city VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY, user_id INT, product VARCHAR(100),
    amount DECIMAL(10, 2), FOREIGN KEY (user_id) REFERENCES users(id)
);
INSERT IGNORE INTO users VALUES
    (1, 'Asha', 'asha@example.com', 24, 'Pune'),
    (2, 'Rahul', 'rahul@example.com', 35, 'Mumbai'),
    (3, 'Neha', 'neha@example.com', 42, 'Pune'),
    (4, 'Amit', 'amit@example.com', 29, 'Delhi'),
    (5, 'Priya', 'priya@example.com', 33, 'Mumbai');
INSERT IGNORE INTO orders VALUES
    (1, 1, 'Keyboard', 1500), (2, 2, 'Monitor', 12000),
    (3, 2, 'Mouse', 700), (4, 3, 'Laptop', 55000),
    (5, 5, 'Headphones', 2500);
-- Run separately after choosing a password, then put this user in .env:
-- CREATE USER 'sql_reader'@'localhost' IDENTIFIED BY 'choose_a_password';
-- GRANT SELECT ON sql_mini_project.* TO 'sql_reader'@'localhost';
