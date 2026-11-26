CREATE DATABASE IF NOT EXISTS theater_crawler
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE theater_crawler;

/* 
in cerinta sa cer exact 2 tabele principale: shows si performances
cast si team trebuie pastrate ca JSON
*/

CREATE TABLE IF NOT EXISTS shows (
    -- va contine cate un rand pentru fiecare spectacol
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NULL,
    director VARCHAR(255) NULL,

    description TEXT NULL, -- descrierea poate fi foarte lunga
    language VARCHAR(255) NULL,

    duration_text VARCHAR(255) NULL,
    age_recommendation VARCHAR(255) NULL,

    cast_json JSON NULL,
    team_json JSON NULL,

    poster_storage ENUM('file', 'base64') NULL, 
    -- ENUM: coloana poate avea doar una din valorile enumerate => accepta: file, base64, NULL
    poster_path VARCHAR(1024) NULL,
    poster_source_url VARCHAR(2048) NULL,

    source_url VARCHAR(2048) NOT NULL,

    -- pot salva cand a vazut crawler ul spectacolul ultima data deoarece un spectacol dispare ulterior de pe site
    last_seen_at TIMESTAMP NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_shows_source_url (source_url(500)),

    INDEX idx_shows_title (title),
    INDEX idx_shows_author (author),
    INDEX idx_shows_director (director)
)

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS performances (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- legatura cu tabelul shows
    show_id BIGINT UNSIGNED NOT NULL,

    start_at DATETIME NOT NULL,
    end_at DATETIME NULL,

    venue VARCHAR(255) NULL,
    address VARCHAR(500) NULL,

    performance_type VARCHAR(100) NULL,
    status VARCHAR(100) NULL,
    notes TEXT NULL,

    source_url VARCHAR(2048) NULL,

    last_seen_at TIMESTAMP NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    -- creez evetiv relatia: performances.show_id -> show_id
    CONSTRAINT fk_performances_show
        FOREIGN KEY (show_id)
        REFERENCES shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- aceeasi reprezentatie nu trebuie introdusa de doua ori
    -- deduplicrea reprezentatiilor folosind spectacolul, data/ora si locatia
    UNIQUE KEY uq_performance (
        show_id,
        start_at,
        venue
    ),

    INDEX idx_performances_show_id (show_id),
    INDEX idx_performances_start_at (start_at),
    INDEX idx_performances_venue (venue)
)


ENGINE = InnoDB -- motor de stocare
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;


