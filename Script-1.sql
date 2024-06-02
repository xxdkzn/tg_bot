CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL
);

CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    target_word VARCHAR(100) NOT NULL,
    translate_word VARCHAR(100) NOT NULL
);

CREATE TABLE user_words (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    word_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
);

INSERT INTO words (target_word, translate_word) VALUES
    ('Peace', 'Мир'),
    ('Green', 'Зеленый'),
    ('Licence', 'Лицензия'),
    ('Door', 'Дверь'),
    ('Car', 'Машина'),
    ('Apple', 'Яблоко'),
    ('House', 'Дом'),
    ('Book', 'Книга'),
    ('Sky', 'Небо'),
    ('Sun', 'Солнце');

INSERT INTO users (chat_id, username) VALUES
    (123456789, 'user1'),
    (987654321, 'user2'),
    (456789123, 'user3');

-- Добавление слов для пользователя 1
INSERT INTO user_words (user_id, word_id) VALUES
    (1, 1),
    (1, 2),
    (1, 3);

-- Добавление слов для пользователя 2
INSERT INTO user_words (user_id, word_id) VALUES
    (2, 4),
    (2, 5),
    (2, 6);

-- Добавление слов для пользователя 3
INSERT INTO user_words (user_id, word_id) VALUES
    (3, 7),
    (3, 8),
    (3, 9);