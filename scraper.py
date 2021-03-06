import json, requests, re, datetime, sqlite3, time
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup as Soup
from bs4 import SoupStrainer

DB_FILE = 'data.sqlite'

rex = re.compile(r'\s+')
numb = re.compile(r'[^0-9]')
rdate = re.compile(r'[^a-z0-9]')
const = re.compile(r'[^a-z0-9\-]')

summerYears = {"1896":"Athens, Greece","1900":"Paris, France","1902":"Athens, Greece (unofficial)","1904":"St. Louis, United States","1906":"Athens, Greece (not an official Games)","1908":"London, United Kingdom","1912":"Stockholm, Sweden","1916":"Berlin, Germany (cancelled due to WWI)","1920":"Antwerp, Belgium","1924":"Paris, France","1928":"Amsterdam, Netherlands","1932":"Los Angeles, United States","1936":"Berlin, Germany","1940":"Tokyo, Japan (cancelled due to WWII)","1944":"London, United Kingdom (cancelled due to WWII)","1948":"London, United Kingdom","1952":"Helsinki, Finland","1956":"Melbourne, Australia","1956":"Stockholm, Sweden","1960":"Rome, Italy","1964":"Tokyo, Japan","1968":"Mexico City, Mexico","1972":"München, Germany","1976":"Montreal, Canada","1980":"Moscow, Soviet Union","1984":"Los Angeles, United States","1988":"Seoul, South Korea","1992":"Barcelona, Spain","1996":"Atlanta, United States","2000":"Sydney, Australia","2004":"Athens, Greece","2008":"Beijing, China","2012":"London, United Kingdom"}
winterYears = {"1924":"Chamonix, France","1928":"St. Moritz, Switzerland","1932":"Lake Placid, United States","1936":"Garmisch-Partenkirchen, Germany","1940":"St. Moritz, Switzerland (cancelled due to WWII)","1944":"Cortina d'Ampezzo, Italy (cancelled due to WWII)","1948":"St. Moritz, Switzerland","1952":"Oslo, Norway","1956":"Cortina d'Ampezzo, Italy","1960":"Squaw Valley, United States","1964":"Innsbruck, Austria","1968":"Grenoble, France","1972":"Sapporo, Japan","1976":"Innsbruck, Austria","1980":"Lake Placid, United States","1984":"Sarajevo, Yugoslavia (until 1988)","1988":"Calgary, Canada","1992":"Albertville, France","1994":"Lillehammer, Norway","1998":"Nagano, Japan","2002":"Salt Lake City, United States","2006":"Torino, Italy","2010":"Vancouver, Canada","2014":"Sochi, Russia"}

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('drop table IF EXISTS data')
c.execute('create table data (year,season,venue,sport,event,athelete,medal,country,result)')

session = requests.Session()
linksStrainer = SoupStrainer('a',href=True)
rowStrainer = SoupStrainer('tr')

def clean(s):
    return rex.sub(' ',s).strip()

######

site = session.get('http://www.databasesports.com/olympics/sport/sportlist.htm')
sitedata = Soup(site.text,'lxml',parse_only=linksStrainer)

for sportlink in sitedata.find_all():
    if 'sporteventlist' not in sportlink['href']:
        continue
    
    sport = clean(sportlink.text)
    print('Processing',sport)
    sportlink = 'http://www.databasesports.com'+sportlink['href']
    sportsdata = Soup(session.get(sportlink).text,'lxml',parse_only=linksStrainer)
    
    for eventlink in sportsdata.find_all():
        if 'sportevent' not in eventlink['href']:
            continue

        event = clean(eventlink.text)
        eventData = Soup(session.get('http://www.databasesports.com'+eventlink['href']).text,'lxml',parse_only=rowStrainer)
        for row in eventData.find_all():
            if 'class="cl' not in str(row):
                continue
            rowt = str(row.text).split('\n')[1:]
            year = int(rowt[0].strip())
            athelete = rowt[2]
            medal = rowt[3]
            country = rowt[4]
            result = rowt[5]
            season = "SUMMER"
            venue = ""
            if str(year) in summerYears:
                venue = summerYears[str(year)]
            else:
                season = "WINTER"
                venue = winterYears[str(year)]
        
            data = [year,season,venue,sport,event,athelete,medal,country,result]
            # year,season,venue,sport,event,athelete,medal,country,result
            c.execute('insert into data values (?,?,?,?,?,?,?,?,?)',data)
            
conn.commit()
c.close()
