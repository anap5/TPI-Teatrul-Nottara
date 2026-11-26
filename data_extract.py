import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from pathlib import Path
import time #adaug un ritm rezonabil
from datetime import datetime
import json


'''
Colectare automata = gasirea paginilor + extragerea informatiilor din ele

cerinta:
accesare site-ului institutiei si colectarea spectacolelor din repertoriu si programul reprezentatiilor
titlu, descriere, durata, recomandare de varsta, limba, distributia, echipa artistica, afisul, URL ul paginii ssursa 
Pentru fiecare reprezentație se vor colecta cel puțin spectacolul asociat, data și ora. Sala sau locația, ora de 
final, tipul reprezentației, starea acesteia și alte informații similare vor fi colectate atunci când sunt 
disponibile.

'''

home_url = 'https://nottara.ro/'
#multe site ur blocheaza traficul care provine din scripturi Python sau bot => trimit un "User-Agent" 
#care spune serverului ca e un browser real, ceea ce scade sansele ca cererea sa fie respinsa
headers = {"User-Agent": "Mozilla/5.0"} 

def get_soup(url):
    time.sleep(1)

    try:
        #fac o cerere tip GET catre url
        response = httpx.get(
            url=url, 
            headers=headers,  #masca de browser
            follow_redirects=True,  #daca site ul te muta automat pe o pagina veche, scriptul va urma redirectionarea
            timeout=15 #asteapta max 15 sec pt un raspuns
        )

        #verific codul de stare HTTP, daca serverul returneaza o eroase, linia forteaza declansarea unei exceptii
        response.raise_for_status()

        return BeautifulSoup(response.text, "html.parser")
    
    except httpx.HTTPError as e:
        print(f"Eroare la {url}: {e}")
        return None

#caut pagina care contine efectiv spectacolele (repertoriu):
spectacole_url = 'https://nottara.ro/spectacole/'

'''
soup = get_soup(spectacole_url)
print(soup.prettify()[:5000])
'''

#observ ca spectacolele au url ul stil: https://nottara.ro/spectacol/a-douasprezecea-noapte-sau-noaptea-magilor/
def get_shows():
    soup = get_soup(spectacole_url)

    if soup is None:
        return []
    
    shows = []

    for link in soup.find_all('a'): #pentru fiecare link gasit
        adresa = link.get('href') #extrag fix https://nottara.ro/spectacol/spectacolul x/

        if adresa and '/spectacol/' in adresa: #daca exista link ul si e link catre un spectacol
            shows.append(urljoin(spectacole_url, adresa))

    #elimin duplicatele (spectacolele apar o data si in imagini si in titlu)
    return list(dict.fromkeys(shows))


'''
shows = get_shows()

print(f'nr spectacole: {len(shows)}') 
    42

for s in shows: 
    print(s) 

se vor afisa adresele url ale spectacolelor
'''


#pentru fiecare url de spectacol scot un dictionar cu toate datele cerute
#scot titlu
def get_title(text):
    if text: 
        return text.get_text(' ', strip=True)

    return None 

#scot autorul: cu toate ca e fix sub titlu deobicei cu h2, ma folosesc de faptul ca are "de" in fata
def get_author(elements):
    author = None 

    for a in elements:
        text = a.get_text(' ', strip=True)

        if text.lower().startswith('de '):
            author = text[3:].strip() 

        elif text.lower().startswith('după '):
            author = text.strip()

        elif text.lower().startswith('adaptare'):
            author = text.strip()

    return author


#pentru durata, varsta recomandata
def get_specific_text(soup, text):
    element = soup.find(
        string = lambda s: s and text.lower() in s.lower()
    )

    if element:
        return element.strip()

    return None 

#toata descrierea este in acelas container: <div class="col-12 col-xl-6 gr-sin gr-lins pt-3">
def get_description(soup):
    description_sel = soup.select_one('div.gr-sin.gr-lins')
    description_parts = []

    if description_sel is None:
        return None 
    
    paragraphs = description_sel.select('p')

    for paragraph in paragraphs:
        text = paragraph.get_text(' ', strip=True)

        if text:
            description_parts.append(text)

    return '\n\n'.join(description_parts)


def get_cast(soup):
    cast = []

    #<section class="container mt-6 gr-sprou gr-distrib"
    cast_sel = soup.select_one('section.gr-distrib') #gasesc un <sectiom> care are clasa gr-distrib

    if cast_sel is None:
        return cast 

    #caut <div class="carousel-cell">
    actors = cast_sel.select('.carousel-cell') #care se gliseaza
    
    for actor in actors:
        name = actor.select_one('.card-aname') #<h5 class="card-aname">nume</h5>
        charact = actor.select_one('.card-arole') #<p class="card-arole">rolul</p>

        if name:
            name = name.get_text(' ', strip=True)
            person = {'name': name} 

            if charact:
                charact = charact.get_text(' ', strip=True)
                person['character'] = charact

            cast.append(person)

    return cast

#la echipa artistica structura e mai simplă decât la distribuție, pentru că fiecare membru al echipei are exact două elemente clare
#gr-role si gr-pers
def get_team(soup):
    team = []
    team_sel = soup.select_one(".gr-team")

    if team_sel is None:
        return team

    members = team_sel.select(".row > .col")

    for member in members:
        role = member.select_one(".gr-role")
        name = member.select_one(".gr-pers")

        if name:
            name = name.get_text(" ", strip=True)
            person = {"name": name}

            if role:
                role = role.get_text(" ", strip=True)
                role = role.rstrip(":")
                person["role"] = role

            team.append(person)

    return team

def get_director(team):
    for person in team:
        role = person.get("role", "").strip().lower()

        if (role.startswith("regia") or role == "regie" or role.startswith("regie ")):
            return person["name"]

    return None


def get_poster(soup):
    img = soup.select_one('.carousel-cell img')

    if img is None:
        return None

    return img.get('src')

def get_poster_path(poster_url, filename):
    if poster_url is None:
        return None

    Path("posters").mkdir(exist_ok=True)

    time.sleep(1)

    try:
        response = httpx.get(poster_url, headers=headers, timeout=15)
        response.raise_for_status()

        path = f"posters/{filename}.jpg"

        with open(path, "wb") as file:
            file.write(response.content)

        return path

    except httpx.HTTPError:
        return None


def parse_show(url):
    soup = get_soup(url)

    if soup is None:
        return None
    
    title = get_title(soup.find('h1'))
    author = get_author(soup.find_all(["h2"]))
    description = get_description(soup)
    duration = get_specific_text(soup, 'Durata:')

    if duration:
        duration = duration.replace('Durata:', '').strip()

    age = get_specific_text(soup, 'Recomandat:')

    if age:
        age = age.replace('Recomandat:', '').strip()

    cast = get_cast(soup)
    team = get_team(soup)
    director = get_director(team)
    poster_url = get_poster(soup)

    filename = url.rstrip("/").split("/")[-1]
    poster_path = get_poster_path(poster_url, filename)

    show = {
        "title": title,
        "author": author,
        "director": director,
        "description": description,
        "duration_text": duration,
        "age_recommendation": age,
        "language": None, #teatrul nu afiseaza limba
        "cast": cast,
        "team": team,
        "poster_source_url": poster_url,
        "poster_path": poster_path,
        "source_url": url
    }
    
    return show 


#show = parse_show('https://nottara.ro/spectacol/badaranii/')
#print(show)

'''
show_soup = get_soup('https://nottara.ro/spectacol/a-douasprezecea-noapte-sau-noaptea-magilor/')
heading = show_soup.find(
    string=lambda s:
        s and s.strip() == "Distribuția"
)

team_heading = show_soup.find(
    lambda tag:
        tag.name in ["h2", "h3"]
        and tag.get_text(" ", strip=True) == "Echipa spectacolului"
)

team_section = team_heading.find_parent("section")
print(team_section.prettify())
'''
'''
shows_data = {} 

for show_url in shows: 
    show_dict = parse_show(show_url)

    if show_dict is None:
        continue

    shows_data[show_dict['source_url']] = show_dict 


#print(dict(list(shows_data.items())[:3]))
'''


'''
cerinta: 

Pentru fiecare reprezentație se vor colecta cel puțin spectacolul asociat, data și ora. Sala sau locația, ora de 
final, tipul reprezentației, starea acesteia și alte informații similare vor fi colectate atunci când sunt 
disponibile. 
'''

months = {
    "ian": 1, "feb": 2, "mar": 3, "apr": 4,
    "mai": 5, "iun": 6, "iul": 7, "aug": 8,
    "sep": 9, "oct": 10, "noi": 11, "dec": 12
}

def normalize_datetime(date, time):
    match = re.search(r"(\d{1,2})\s+([a-z]+)", date.lower())

    if match is None:
        return None

    day = int(match.group(1))
    month = months.get(match.group(2))

    if month is None:
        return None

    hour, minute = map(int, time.split(":"))

    year = datetime.now().year

    result = datetime(year, month, day, hour, minute)

    # Programul conține reprezentații viitoare.
    # Dacă luna/data a trecut deja, este anul următor.
    if result.date() < datetime.now().date():
        result = result.replace(year=year + 1)

    return result


def find_performances(show_url):
    soup = get_soup(show_url)

    if soup is None:
        return None

    buton_bilete = soup.select_one('div.gr-sbanbut a')
    #sau: buton_bilete = soup.find('a', class_='gr-ban-link')

    if buton_bilete is None:
        return None

    performances_url = buton_bilete.get("href")

    if not performances_url:
        return None

    performances_url = urljoin(show_url, performances_url)

    return performances_url


def parse_performance_item(item):
    sections = item.find_all("div", class_="q-item__section", recursive=False)
    #recusive = False => caut doar copiii

    date_section = None
    location_section = None

    for section in sections:
        classes = section.get("class", [])

        if "q-item__section--avatar" in classes:
            date_section = section

        elif "q-item__section--main" in classes:
            location_section = section

    # daca nu avem ambele, probabil este q-item-ul interior
    if date_section is None or location_section is None:
        return None

    #data si ora
    date_labels = date_section.select(".q-item__label")

    if len(date_labels) < 2:
        return None

    full_date = date_labels[0].get_text(" ", strip=True)
    time = date_labels[1].get_text(" ", strip=True)

    #"Vin, 30 oct." -> "Vin" + "30 oct."
    if "," in full_date:
        day, date = full_date.split(",", 1)

        day = day.strip()
        date = date.strip()

    else:
        day = None
        date = full_date

    #locatie si adresa
    location_labels = location_section.find_all("div", class_="q-item__label", recursive=False)

    venue = None
    address = None

    if len(location_labels) >= 1:
        venue = location_labels[0].get_text(" ", strip=True)

    if len(location_labels) >= 2:
        address = location_labels[1].get_text(" ", strip=True)

    status = 'Bilete disponibile' 
    status_elem = item.select_one('.q-badge[role="status"]')

    if status_elem:
        status = status_elem.get_text(" ", strip=True)

    start_at = normalize_datetime(date, time)

    if start_at is None:
        return None

    return {
        "day": day,
        "date": date,
        "time": time,
        "start_at": start_at,
        "venue": venue,
        "address": address,
        "status": status
    }


def get_performance_info(performance_url):
    if performance_url is None:
        return []
    
    soup = get_soup(performance_url)

    if soup is None:
        return []

    performance_data = []

    for item in soup.select(".q-item"):
        text = item.get_text(" ", strip=True)

        if re.search(r"\b\d{1,2}:\d{2}\b", text):
            performance_dict = parse_performance_item(item)

            if performance_dict is not None: 
                performance_dict['source_url'] = performance_url
                performance_data.append(performance_dict) 
                
    return performance_data 

    
def crawl():
    shows = get_shows()

    shows_data = {}

    for show_url in shows:
        show_dict = parse_show(show_url)

        if show_dict is None:
            continue

        shows_data[show_dict["source_url"]] = show_dict

    all_performances = []
    seen_performances = set()

    for show_url, show in shows_data.items():
        performance_url = find_performances(show_url)

        if performance_url is None:
            continue

        performances = get_performance_info(performance_url)

        for performance in performances:
            performance["show_source_url"] = show_url
            performance["show_title"] = show["title"]

            key = (
                show_url,
                performance["start_at"],
                performance["venue"]
            )

            if key not in seen_performances:
                seen_performances.add(key)
                all_performances.append(performance)

    return shows_data, all_performances


#rulare cod si descarcare date
if __name__ == "__main__":
    shows_data, all_performances = crawl()

    print("Spectacole:", len(shows_data))
    print("Reprezentatii:", len(all_performances))

    Path("data").mkdir(exist_ok=True)

    with open("data/shows.json", "w", encoding="utf-8") as file:
        json.dump(
            list(shows_data.values()),
            file,
            ensure_ascii=False,
            indent=4,
            default=str
        )

    with open("data/performances.json", "w", encoding="utf-8") as file:
        json.dump(
            all_performances,
            file,
            ensure_ascii=False,
            indent=4,
            default=str
        )