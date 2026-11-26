import json #pentru citire shows.json si performances.json
import mysql.connector #connectorul python -> SQL
from datetime import datetime

'''
-> data_extract.py : crawlerul
-> database.py : python <-> SQL 
-> schema.sql : crearea bazei de data

'''

#deschidere conexiunea intre Python si MySQL Server
#functia intoarce un obiect de conexiune: connection = get_connection()
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="PAROLA_MYSQL",
        database="theater_crawler",
        charset="utf8mb4"
    )


#introduc un singur spectacol in tabelul shows
def save_show(cursor, show):
    #transform in JSON
    #ensure_ascii = False pentru a nu transforma in coduri Unicode si a pastra textul
    cast_json = json.dumps(show["cast"], ensure_ascii=False)
    team_json = json.dumps(show["team"], ensure_ascii=False)


    query = """
        INSERT INTO shows (
            title, author, director, description, language,
            duration_text, age_recommendation, cast_json, team_json,
            poster_storage, poster_path, poster_source_url, source_url, last_seen_at
        )

        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, NOW()
        )

        ON DUPLICATE KEY UPDATE

            title = VALUES(title),
            author = VALUES(author),
            director = VALUES(director),
            description = VALUES(description),
            language = VALUES(language),

            duration_text = VALUES(duration_text),
            age_recommendation = VALUES(age_recommendation),

            cast_json = VALUES(cast_json),
            team_json = VALUES(team_json),

            poster_storage = VALUES(poster_storage),
            poster_path = VALUES(poster_path),
            poster_source_url = VALUES(poster_source_url),

            last_seen_at = NOW()
    """

    values = (
        show["title"],
        show["author"],
        show["director"],
        show["description"],
        show["language"],
        show["duration_text"],
        show["age_recommendation"],
        cast_json,
        team_json,
        "file" if show["poster_path"] else None,
        show["poster_path"],
        show["poster_source_url"],
        show["source_url"]
    )

    #combina query-ul si valorile si trimite comanda catre MySQL
    cursor.execute(query, values)


#pentru performance am nevoie de show_id
def get_show_id(cursor, source_url):
    query = """
        SELECT id
        FROM shows
        WHERE source_url = %s
    """

    cursor.execute(query, (source_url,)) 
                        #tuple cu un singur element
    result = cursor.fetchone() #ia primul rand din rezultatul SELECT ului

    if result:
        return result[0]

    return None


#salvez o reprezentatie
def save_performance(cursor, performance):
    show_id = get_show_id(cursor, performance["show_source_url"])

    if show_id is None:
        return

    start_at = datetime.strptime(performance["start_at"], "%Y-%m-%d %H:%M:%S")

    query = """
        INSERT INTO performances (
            show_id, start_at, venue, address, status, source_url, last_seen_at
        )

        VALUES (
            %s, %s, %s, %s, %s, %s, NOW()
        )

        ON DUPLICATE KEY UPDATE

            status = VALUES(status),
            address = VALUES(address),
            source_url = VALUES(source_url),

            last_seen_at = NOW()
    """

    values = (
        show_id,
        start_at,
        performance["venue"],
        performance["address"],
        performance["status"],
        performance["source_url"]
    )

    cursor.execute(query, values)


#import cele 2 JSON uri
def load_data():
    with open(
        "data/shows.json", "r", encoding="utf-8"
    ) as file:
        shows = json.load(file)

    with open(
        "data/performances.json", "r", encoding="utf-8"
    ) as file:
        performances = json.load(file)

    #connection reprezinta conexiunea cu serverul (canal deschis catre MySQL)
    #cursor este obiectul cu care trimit efectiv comenzile SQL (instrumentul prin care execut comenzile SQL prin acel canal)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        for show in shows:
            save_show(cursor, show)

        connection.commit()

        for performance in performances:
            save_performance(cursor, performance)

        connection.commit()

        print(f"{len(shows)} spectacole salvate.")
        print(f"{len(performances)} reprezentatii salvate.")

    except Exception as e:
        connection.rollback()
        print("Eroare:", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    load_data()
