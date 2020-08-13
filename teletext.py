import urllib3
from bs4 import BeautifulSoup
import hashlib
import sqlite3
import time
from sqlite3 import Error

# configure this to your needs
xml_out = "/home/micha/websites/exitnode.net/htdocs/ard_teletext.xml"
db = r"/home/micha/teletext.db"
articles = "20"
url = "https://www.ard-text.de/mobil/"

# creates a connection to the SQLite database
def create_conn(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

# creates necessary tables inside the SQLite database
def create_tables(conn):
    sql_create_tafeln_table = """CREATE TABLE IF NOT EXISTS tafeln (
                                    unixtime int NOT NULL,
                                    hash text PRIMARY KEY,
                                    tafel int,
                                    description text,
                                    title text
                                ); """

    try:
        c = conn.cursor()
        c.execute(sql_create_tafeln_table)
        return conn
    except Error as e:
        print(e)

# inserts the text of a teletext tafel into the database
def insert_tafel(conn, tafel):
    
    sql = ''' INSERT INTO tafeln(unixtime,hash,tafel,description,title)
                VALUES(?,?,?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, tafel)
        conn.commit()
        return c.lastrowid
    except Error as e:
        err = e

# returns the latest n tafeln 
def get_tafeln(conn):
    sql = "SELECT description,title from tafeln order by unixtime desc limit " + articles
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except Error as e:
        print(e)

# downloads a teletext tafel and prepares it for database storage
def download_tafel(conn, tafel):
    link = url+str(tafel)
    http = urllib3.PoolManager()
    r = http.request('GET', link)
    
    soup = BeautifulSoup(r.data, 'html.parser')
    desc = soup.find('div', class_='std')
    title = soup.find('h1')
    if desc is not None:
        if title is not None:
            title = title.text.replace("<h1>","")
            title = title.replace("<b>","")
            title = title.replace("</h1>","")
            title = title.replace("</b>","")
        else:
            title = "N/A"
        unixtime = time.time()
        desc = desc.text
        desc_hash = hashlib.md5(desc.encode('utf-8')).hexdigest()
        content = (unixtime,desc_hash,tafel,desc,title)
        insert_tafel(conn,content)

# generates the RSS feed XML based on database content
def gen_rss(rows):
    f = open(xml_out, "w")

    out = """<?xml version="1.0" encoding="UTF-8" ?>
            <rss version="2.0">

            <channel>
                <title>ARD Teletext RSS Feed (inoffiziell)</title>
                <link>https://exitnode.net/ard_teletext.xml</link>
                <description>RSS Feed des ARD Teletexts (Tafeln 104 bis 129)</description>"""

    for r in rows:
        desc = r[0]
        title = r[1]

        if desc is not None:
            desc = desc.replace("\n"," ")
            desc = desc.strip()
            out+= """
                <item>
                <title>""" + title + """</title>
                <description>""" + desc + """</description>
                </item>"""

    out += """ 
            </channel>
            </rss>
            """

    f.write(out)
    f.close()

# the main funtion
def main():
    conn = create_conn(db)
    if conn is not None:
        create_tables(conn)
        for s in range(104, 129):
            download_tafel(conn,s)

        rows = get_tafeln(conn)
        gen_rss(rows)
    else:
        print("Error: No db conn")

if __name__ == "__main__":
    main()

