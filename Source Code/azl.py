import urllib.request, urllib.parse, urllib.error, ssl, sqlite3, re, winsound
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

con = sqlite3.connect('lyrics.sqlite')
cur = con.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS Albums
(id INTEGER PRIMARY KEY, album TEXT UNIQUE, year INTEGER)
'''
)
cur.execute('''
CREATE TABLE IF NOT EXISTS Artists
(id INTEGER PRIMARY KEY, artist TEXT UNIQUE)''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Songs
(id INTEGER PRIMARY KEY, title TEXT, lyrics TEXT, url_id INTEGER, artist_id INTEGER, album_id INTEGER)''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Pages
(id INTEGER PRIMARY KEY, url TEXT UNIQUE, html TEXT, error INTEGER, old_rank REAL, new_rank REAL)''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Links
(from_id INTEGER, to_id INTEGER)''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Webs
(url TEXT UNIQUE)''')

cur.execute('''
SELECT id, url FROM Pages WHERE html IS NULL AND error IS NULL ORDER BY RANDOM() LIMIT 1''')
row = cur.fetchone()

if row is not None:
    print('Restarting existing crawl or remove spider_.sqlite to start a fresh crawl.')
else:
    starturl = 'https://www.azlyrics.com'
    web = starturl

    if len(web) > 1:
        cur.execute('INSERT OR IGNORE INTO Webs (url) VALUES (?)',(web,))
        cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES (?, NULL, 1.0)',(starturl,))
        con.commit()

webs = list()
cur.execute('SELECT url FROM Webs')
for row in cur:
    webs.append(row[0])
print(webs)

many = 0
while True:
    if many < 1:
        numofpages = input('How many pages:')
        if len(numofpages) < 1:
            break
        try:
            many = int(numofpages)
        except KeyboardInterrupt:
            print('Program is terminated . . .')
            break
        except:
            print('Please enter a numeric number')
            continue
    many = many - 1

    cur.execute('SELECT id, url FROM Pages WHERE html IS NULL AND error IS NULL ORDER BY Random() LIMIT 1')
    try:
        row = cur.fetchone()
        fromid = row[0]
        url = row[1]
    except KeyboardInterrupt:
        print('Program is terminated . . .')
        break
    except:
        print('No unretrieved HTML pages found')
        many = 0
        break

    print('URL ID:',fromid,'| URL:', url, '|', end=' ')

    cur.execute('DELETE FROM Links WHERE from_id = ?', (fromid,))
    try:
        document = urllib.request.urlopen(url, context=ctx)
        html = document.read()
        if document.getcode() != 200:
            print('Error on page: ', document.getcode())
            cur.execute('UPDATE Pages SET error = ? WHERE url = ?',(document.getcode(),url))
            con.commit()
        if document.info().get_content_type() != 'text/html':
            print('Ignore non text/html page')
            cur.execute('DELETE FROM Pages WHERE url = ?', (url,))
            cur.execute('UPDATE FROM Pages SET error = 0 WHERE url = ?', (url,))
            con.commit()

        print('('+str(len(html))+')', end=' ')
        soup = BeautifulSoup(html, 'html.parser')
    except KeyboardInterrupt:
        print('Program is terminated . . .')
        break
    except:
        print('Unable to retrieve or parse page')
        cur.execute('UPDATE Pages SET error = -1 WHERE url = ?', (url,))
        con.commit()
        continue

    cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES (?, NULL, 1.0)', (url,))
    cur.execute('UPDATE Pages SET html = ? WHERE url = ?', (memoryview(html),url))
    con.commit()

    tags = soup('a')
    count = 0
    for tag in tags:
        href = tag.get('href', None)

        if href is None:
            continue
        if len(href) < 1:
            continue
        if len(urllib.parse.urlparse(href).scheme) < 1:
            href = urllib.parse.urljoin(url, href)
        if href.endswith('.pdf') or href.endswith('.epub') or href.endswith('.doc'):
            continue
        if href.endswith('/'):
            href = href[:-1]
        ipos = href.find('#')
        if ipos > 1:
            href = href[:ipos]
        if href.endswith('.png') or href.endswith('.jpg') or href.endswith('.gif'):
            continue

        found = False
        for web in webs:
            if href.startswith(web):
                found = True
                break
            if href.startswith('https://'+web.split('//')[1]):
                found = True
                break
        if not found:
            continue

        cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES (?, NULL, 1.0)', (href,))
        count = count + 1
        con.commit()

        cur.execute('SELECT id FROM Pages WHERE url = ? LIMIT 1',(href,))
        try:
            row = cur.fetchone()
            toid = row[0]
        except KeyboardInterrupt:
            print('Program is terminated . . .')
            break
        except:
            print('Could not retrieve id')
            continue

        cur.execute('INSERT OR IGNORE INTO Links (from_id, to_id) VALUES (?, ?)', (fromid, toid))
        con.commit()

    print('URLs retrieved:',count, end=' ')

    if many == 0 :
        print('Done')
        winsound.Beep(440, 100)
        winsound.Beep(554, 100)
        winsound.Beep(659, 100)

    if '/lyrics/' not in url:
        print('| Pages left:',many)
        continue
    if '/lyrics/' in url:
        try:
            tagx = soup.find_all('b')
            artist_info = list()
            for tag in tagx:
                artist_info.append(tag.getText().strip())
            artist_name = artist_info[0]
            artist_name_only = artist_name[:artist_name.find('Lyrics')]
            song_title = artist_info[1].replace('"','')
            print('| Artist:',artist_name_only, '| Title:', song_title, end= ' ')
        except:
            print('Could not retrieve artist name and song title')
            continue

        try:
            taga = soup.find('div', class_='panel album-panel noprint').a
            album = None
            year = None
            for child in taga:
                try:
                    pos1 = child.rfind('(')
                    pos2 = child.rfind(')')
                    album = child[:pos1].replace('"','')
                    year = child[pos1+1:pos2]
                except:
                    album = child.replace('"','')
            print('| Album:', album, end= ' ')
        except:
            album = artist_name_only+'(Other Song)'
            year = '-'
            print('Could not retrieve album name')

        try:
            tagl = soup.find_all("div", {"class": "container main-page"})

            for tag in tagl:
                divtag = tag.find_all("div", {"class": ""})
                for tag in divtag:
                    lyrics = tag.text.rstrip()
            print('| Lyrics retrieved', end=' ')
        except:
            print('Could not retrieve lyrics')
            continue

        cur.execute('INSERT OR IGNORE INTO Albums (album, year) VALUES (?, ?)', (album, year))
        con.commit()
        cur.execute('SELECT id FROM Albums WHERE album = ? LIMIT 1', (album,))
        try:
            row = cur.fetchone()
            album_id = row[0]
        except:
            print('Could not retrieve id')
            continue

        cur.execute('INSERT OR IGNORE INTO Artists (artist) VALUES (?)',(artist_name_only,))
        con.commit()
        cur.execute('SELECT id FROM Artists WHERE artist = ? LIMIT 1',(artist_name_only,))
        try:
            row = cur.fetchone()
            artist_id = row[0]
        except:
            print('Could not retrieve id')
            continue

        cur.execute('''
        INSERT OR IGNORE INTO Songs (title, lyrics, url_id, artist_id, album_id) VALUES(?,?,?,?,?)''',
        (song_title, lyrics, fromid, artist_id, album_id))
        con.commit()

    winsound.PlaySound("SystemExit", winsound.SND_ALIAS)
    print('| Pages left:',many)

    if many == 0 :
        print('Done')
        winsound.Beep(440, 100)
        winsound.Beep(554, 100)
        winsound.Beep(659, 100)
    else:
        continue

cur.close()
