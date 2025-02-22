-- Create schemas for microservices
CREATE SCHEMA IF NOT EXISTS user_service;
CREATE SCHEMA IF NOT EXISTS activity_service;
CREATE SCHEMA IF NOT EXISTS mood_service;
CREATE SCHEMA IF NOT EXISTS notification_service;

-- Users Table kept in users schema
CREATE TABLE IF NOT EXISTS user_service.users(
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    age INT CHECK (age BETWEEN 20 AND 60),
    gender VARCHAR(20) CHECK (gender IN ('Male', 'Female', 'Prefer not to say')),
    weight FLOAT CHECK (weight BETWEEN 50 AND 100),
    email VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) not NULL
);
-- Table for Activity Service
CREATE TABLE IF NOT EXISTS activity_service.activity_data  (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    steps INT,
    calories_burned FLOAT,
    distance_km FLOAT,
    active_minutes INT,
    workout_type VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES user_service.users(user_id)
);

-- Table for ML Mood Service
CREATE TABLE IF NOT EXISTS mood_service.mood_data (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    heart_rate_avg INT,
    sleep_hours FLOAT,
    mood VARCHAR(50),
    weather_conditions VARCHAR(50),
    location VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES user_service.users(user_id)
);

-- Table for Notification Service
CREATE TABLE IF NOT EXISTS notification_service.notifications(
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    notification_text TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_service.users(user_id)
);


