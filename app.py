from flask import Flask, render_template, abort, send_from_directory, request
from pathlib import Path #pentru a construi calea catre folderul posters.
import json #pentru cast_json si team_json

from database import get_connection #importul din propriul fisier database.py

'''
Flask = clasa principala cu care creez aplicatia web 
render_template = functia prin care Flask ia un fisier HTML din folderul templates/ si ii trimite date din Python
abort = pentru a opri procesarea si a returna o eroare HTTP
send_from_directory = pentru a trimite fisiere locale browserului
request = cererea HTTP pe care browserul tocmai a trimis o catre FLask
    exemplu: utilizatorul cauts Amadeus => browserul ajunge la /shows?q=Amadeus
            flask poate accesa q-Amadeus prin request.args
'''

app = Flask(__name__) #creez efectiv aplicatia

project_folder = Path(__file__).resolve().parent
# __file__ = calea fisierului Python care ruleaza
#.resolve() = calea absolut completa
#.parent = ia folderul care contine fisierul

posters_folder = project_folder / "posters"
#operatorul "/" construieste o cale 


def execute_query(query, params=(), one=False):
    #executa o interogare SQL si intoarce rezultatul
    #param query va contine SQL-ul
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params)

        if one:
            return cursor.fetchone()

        return cursor.fetchall()

    #inidferent de ce se intampla, execut aceasta bucata
    #nu vreau sa am conexiuni MySQL care au ramas deschise dupa fiecare acces al unui utilizator
    finally:
        cursor.close()
        connection.close()


def parse_json_field(value):
    if value is None:
        return []

    if isinstance(value, str): #verific daca valoarea este string
        try:
            return json.loads(value) #json text -> obiect python [{}]
        
        except json.JSONDecodeError: #dc am JSON invalid
            return []

    return value


#decorator: daca browserul cere acest URL, executa functia de dedesubt
#pagina principala este si pagina repertoriului
@app.route("/")
@app.route("/shows")
def shows():
    search = request.args.get("q", "").strip() #citesc cautarea

    if search:
        pattern = f"%{search}%" 
        #adauga % in fata cuvantului deoarece in SQL % = orice nr de caractere
        #caut orice text care contine "search" oriunde

        query = """
            SELECT
                id,
                title,
                author,
                director,
                duration_text,
                age_recommendation,
                poster_path
            FROM shows
            WHERE title LIKE %s
               OR author LIKE %s
               OR director LIKE %s
            ORDER BY title
        """

        shows_data = execute_query(query, (pattern, pattern, pattern))

    #daca nu exista cautare: aduc toate spectacolele
    else:
        query = """
            SELECT
                id,
                title,
                author,
                director,
                duration_text,
                age_recommendation,
                poster_path
            FROM shows
            ORDER BY title
        """

        shows_data = execute_query(query)

    return render_template("shows.html", shows=shows_data, search=search)

'''
execute_query(...) : 
1. deschide conexiunea
2. creează cursor
3. execută SELECT
4. citește rezultatele
5. închide cursor
6. închide conexiunea
'''

#ruta unui spectacol
@app.route("/show/<int:show_id>")
@app.route("/shows/<int:show_id>")
def show_detail(show_id):
    query = """
        SELECT *
        FROM shows
        WHERE id = %s
    """

    show = execute_query(query, (show_id,), one=True)

    if show is None:
        abort(404) #404 = Not Found

    show["cast"] = parse_json_field(show["cast_json"])
    show["team"] = parse_json_field(show["team_json"])

    performances_query = """
        SELECT
            id,
            start_at,
            venue,
            address,
            status,
            source_url
        FROM performances
        WHERE show_id = %s
        ORDER BY start_at
    """

    performances = execute_query(performances_query, (show_id,))

    '''
    deschide show_detail.html si pune la dispozitia lui
    variabilele show si performances
    '''
    return render_template("show_detail.html", show=show, performances=performances)


@app.route("/schedule")
def schedule():
    query = """
        SELECT
            p.id,
            p.start_at,
            p.venue,
            p.address,
            p.status,
            p.source_url,

            s.id AS show_id,
            s.title,
            s.author

        FROM performances p

        JOIN shows s
            ON p.show_id = s.id

        ORDER BY p.start_at
    """

    performances = execute_query(query)

    return render_template("schedule.html", performances=performances)


@app.route("/posters/<path:filename>")
def poster_file(filename):
    return send_from_directory(posters_folder, filename)


'''
app.run(...) : porneste serverul web Flask
debug = True: daca modific codul, Flask detecteaza modificare si reporneste automat serverul
                daca apare o eroare, primesc o pagina detaliata cu traceback ul 
'''

if __name__ == "__main__":
    app.run(debug=True)