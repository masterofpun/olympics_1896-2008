import json, requests, re, datetime, sqlite3, time
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup as Soup

DB_FILE = 'data.sqlite'

rex = re.compile(r'\s+')
numb = re.compile(r'[^0-9]')
rdate = re.compile(r'[^a-z0-9]')
const = re.compile(r'[^a-z0-9\-]')

summerYears = {"1896":"Athens, Greece","1900":"Paris, France","1902":"Athens, Greece (unofficial)","1904":"St. Louis, United States","1906":"Athens, Greece (not an official Games)","1908":"London, United Kingdom","1912":"Stockholm, Sweden","1916":"Berlin, Germany (cancelled due to WWI)","1920":"Antwerp, Belgium","1924":"Paris, France","1928":"Amsterdam, Netherlands","1932":"Los Angeles, United States","1936":"Berlin, Germany","1940":"Tokyo, Japan (cancelled due to WWII)","1944":"London, United Kingdom (cancelled due to WWII)","1948":"London, United Kingdom","1952":"Helsinki, Finland","1956":"Melbourne, Australia","1956":"Stockholm, Sweden","1960":"Rome, Italy","1964":"Tokyo, Japan","1968":"Mexico City, Mexico","1972":"München, Germany","1976":"Montreal, Canada","1980":"Moscow, Soviet Union","1984":"Los Angeles, United States","1988":"Seoul, South Korea","1992":"Barcelona, Spain","1996":"Atlanta, United States","2000":"Sydney, Australia","2004":"Athens, Greece","2008":"Beijing, China","2012":"London, United Kingdom"}
winterYears = {"1924","Chamonix, France","1928","St. Moritz, Switzerland","1932","Lake Placid, United States","1936","Garmisch-Partenkirchen, Germany","1940","St. Moritz, Switzerland (cancelled due to WWII)","1944","Cortina d'Ampezzo, Italy (cancelled due to WWII)","1948","St. Moritz, Switzerland","1952","Oslo, Norway","1956","Cortina d'Ampezzo, Italy","1960","Squaw Valley, United States","1964","Innsbruck, Austria","1968","Grenoble, France","1972","Sapporo, Japan","1976","Innsbruck, Austria","1980","Lake Placid, United States","1984","Sarajevo, Yugoslavia (until 1988)","1988","Calgary, Canada","1992","Albertville, France","1994","Lillehammer, Norway","1998","Nagano, Japan","2002","Salt Lake City, United States","2006","Torino, Italy","2010","Vancouver, Canada","2014","Sochi, Russia"}

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('drop table IF EXISTS data')
c.execute('create table data (year,season,venue,sport,event,athelete,medal,country,result)')

def words2date(bdate):
    bdate = clean(rdate.sub(' ',bdate.lower()))
    if len(bdate)<2:
        return None
    bdate = bdate.replace('febuary','february')
    month = ['january','february','march','april','may','june','july','august','september','october','november','december']
    bdate = bdate.split(' ')
    date = datetime.date(int(bdate[2]),int(month.index(bdate[1])+1),int(numb.sub('',bdate[0])))
    return date.isoformat()

def text2int(textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
            return 0

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0
    return result + current

def num(s):
    s = numb.sub(' ',s)
    s = clean(s)
    if s is None:
        return 0
    return int(s)

def clean(s):
    return rex.sub(' ',s).strip()

######

site = requests.get('http://www.databasesports.com/olympics/sport/sportlist.htm')
sitedata = Soup(site.text,'lxml')

for sportlink in sitedata.find_all('a',href=True):
    if 'sporteventlist' not in sportlink['href']:
        continue
    
    sport = clean(sportlink.text)
    print('Processing',sport)
    sportlink = 'http://www.databasesports.com'+sportlink['href']
    sportsdata = Soup(requests.get(sportlink).text,'lxml')
    
    for eventlink in sportsdata.find_all('a',href=True):
        if 'sportevent' not in eventlink['href']:
            continue

        event = clean(eventlink.text)
        eventData = Soup(requests.get('http://www.databasesports.com'+eventlink['href']).text,'lxml')
        for row in eventData.find_all('tr'):
            if 'class="cl' not in str(row):
                continue
            rowt = str(row.text).split('\n')[1:] #Don't clean()
            year = int(clean(rowt[0]))
            athelete = rowt[2].strip()
            medal = clean(rowt[3])
            country = clean(rowt[4])
            result = clean(rowt[5])
            season = "SUMMER"
            venue = ""
            if str(year) in summerYears:
                venue = summerYears[str(year)]
            else:
                season = "WINTER"
                venue = winterYears[str(year)]
        
            data = [year,season,venue,sport,event,athelete,medal,country,result]
            print(data)
            # year,season,venue,sport,event,athelete,medal,country,result
            c.execute('insert into data values (?,?,?,?,?,?,?,?,?)',data)
conn.commit()
c.close()
