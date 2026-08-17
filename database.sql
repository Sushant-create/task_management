CREATE DATABASE IF NOT EXISTS task_management_system;
USE task_management_system;

DROP TABLE IF EXISTS task;
DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS login;

CREATE TABLE login (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,   -- stores a hashed password, not plain text
    role ENUM('admin', 'manager') NOT NULL
);

CREATE TABLE employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    department VARCHAR(80) NOT NULL
);

CREATE TABLE task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    title VARCHAR(120) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_task_employee
        FOREIGN KEY (employee_id)
        REFERENCES employee(id)
        ON DELETE CASCADE
);

-- Demo accounts: admin/admin123 and manager/manager123
-- Passwords below are pbkdf2:sha256 hashes of those values (see README "Security Notes").
-- Generate your own with:
--   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"
INSERT INTO login (username, password, role) VALUES
('admin', 'pbkdf2:sha256:1000000$RSyQl2uM7Vc2wU6O$490537cb1d426e673af92cc11f59b44afabb2bd4fcc47c7a41c9093b59defced', 'admin'),
('manager', 'pbkdf2:sha256:1000000$qqYfnsBVB8XLomNz$fea0ed7da0c0c4a3c71e0f6a380267472a7750487eee926a4195f64a61873727', 'manager');

INSERT INTO employee (employee_name, email, department) VALUES
('Rahul Sharma', 'rahul@example.com', 'Operations'),
('Sneha Verma', 'sneha@example.com', 'Support'),
('Amit Patel', 'amit@example.com', 'Data Entry'),
('Priya Singh', 'priya@example.com', 'Documentation');
