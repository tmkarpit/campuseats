CREATE DATABASE IF NOT EXISTS campuseats_graphql;
USE campuseats_graphql;

CREATE TABLE IF NOT EXISTS dishes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  price DECIMAL(10,2) NOT NULL,
  available BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT valid_dish_price CHECK (price >= 0)
);

INSERT IGNORE INTO dishes (name, price, available) VALUES
  ('Masala Dosa', 80.00, TRUE),
  ('Veg Burger', 65.00, TRUE),
  ('Cold Coffee', 55.00, TRUE),
  ('Paneer Wrap', 95.00, FALSE);
