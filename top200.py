from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import unicodedata
import time

_remove_accents = lambda input_str: ''.join(
    (c for c in unicodedata.normalize('NFKD', input_str) if not unicodedata.combining(c)))
_clean_string = lambda s: set(re.sub(r'[^\w\s]', '', _remove_accents(s)).lower().split())
_jaccard = lambda set1, set2: float(len(set1 & set2)) / float(len(set1 | set2))

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def search(entity_type: str, query: str):
    return requests.get(
        'http://musicbrainz.org/ws/2/{entity}/'.format(entity=entity_type),
        params={
            'fmt': 'json',
            'query': query
        }
    ).json()


def get_release_url(artist: str, title: str):
    type_ = 'release'
    search_results = search(type_, '%s AND artist:%s' % (title, artist))

    artist = _clean_string(artist)
    title = _clean_string(title)

    # print("title = " + str(title) +' artist=' + str(artist))
    for item in search_results.get(type_ + 's', []):
        names = list()
        for artists in item['artist-credit']:
            if 'artist' in artists:
                names.append(_clean_string(artists['artist']['name']))
                for alias in artists['artist'].get('aliases', {}):
                    names.append(_clean_string(alias.get('name', '')))
                # print('  title=' + str(_clean_string(item['title'])) + ' names=' + ', '.join(itertools.chain(*names)))

        # if _jaccard(_clean_string(item['title']), title) > 0.5 and \
        #         (any(_jaccard(artist, name) > 0.3 for name in names) or len(names) == 0):
            return 'http://musicbrainz.org/ws/2/{type}/{id}?inc=artist-credits+media&fmt=json'.format(id=item['id'], type=type_)

    return None


def extractinfo(test):
    infoholder = list()
    if test != None:
        response = requests.get(test).json()
        track_count = 0
        x = 0
        disc_count = len(response['media'])
        while x < len(response['media']):
            track_count += response['media'][x]['track-count']
            x += 1
    else:
        track_count = float('NaN')
        disc_count = float('NaN')
    infoholder.insert(0, track_count)
    infoholder.insert(1, disc_count)
    return infoholder


def get_billboard_top_albums_dataframe(date: str='2001-06-02', count: int=5) -> pd.DataFrame:
    datetemp = "https://www.billboard.com/charts/billboard-200/"
    datetemp += date
    html = requests.get(datetemp, verify=False).text

    soup = BeautifulSoup(html, 'lxml')
    top5albums = pd.DataFrame(columns=["Album", "Artist", "Rank", "Track Count", "Disc Count"])
    counter = 1

    rank1 = 1
    album1 = soup.find('div', attrs={"class": "chart-number-one__title"}).text.strip('\n').lstrip().rstrip()
    artist1 = soup.find('div', attrs={"class": "chart-number-one__artist"}).text.strip('\n').lstrip().rstrip()
    get_URL1 = get_release_url(artist1, album1)
    holder = extractinfo(get_URL1)
    track_count1 = holder[0]
    disc_count1 = holder[1]
    top5albums = top5albums.append({'Album': album1, 'Artist': artist1, 'Rank': rank1, 'Track Count': track_count1, 'Disc Count': disc_count1},ignore_index=True)
    counter += 1

    for row in soup.find_all('div', attrs={"class": "chart-list-item"}):
        if counter <= count:
            rank = row.find('div', attrs={"class": "chart-list-item__rank"}).text.strip('\n').lstrip().rstrip()
            album = row.find('span', attrs={"class": "chart-list-item__title-text"}).text.strip('\n').lstrip().rstrip()
            artist = row.find('div', attrs={"class": "chart-list-item__artist"}).text.strip('\n').lstrip().rstrip()
            get_URL = get_release_url(artist, album)
            holder = extractinfo(get_URL)
            track_count = holder[0]
            disc_count = holder[1]
            top5albums = top5albums.append({'Album': album, 'Artist': artist, 'Rank': rank, 'Track Count': track_count, 'Disc Count': disc_count},ignore_index=True)
            counter += 1
            time.sleep(1)
        else:
            break

    pd.set_option('display.max_columns', None)
    return top5albums


# TEST CASES
# top_5_albums = get_billboard_top_albums_dataframe(count=10, date='2018-11-03')
# top_5_albums = get_billboard_top_albums_dataframe(count=29, date='2018-10-27')
# top_5_albums = get_billboard_top_albums_dataframe(count=200, date='2018-10-20')
# top_5_albums = get_billboard_top_albums_dataframe(count=150, date='2018-10-13')
# top_5_albums = get_billboard_top_albums_dataframe(count=55, date='2018-10-06')
# top_5_albums = get_billboard_top_albums_dataframe(count=200, date='2018-09-29')
top_5_albums = get_billboard_top_albums_dataframe(count=10, date='2018-11-10')
print(top_5_albums)
