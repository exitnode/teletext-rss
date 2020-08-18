import urllib3
from bs4 import BeautifulSoup
import hashlib
import sqlite3
import time
from sqlite3 import Error

#########################
# Configuration options #
#########################

# configure these to your needs:

# Where the resulting RSS feed XML should be written to:
xml_out = "/home/micha/websites/exitnode.net/htdocs/ard_steletext.xml"

# Location of your database file:
db = r"/home/micha/teletext.db"

# Number of articles in the RSS XML file:
articles = "20"

# Source URL of teletext service:
url = "https://www.ard-text.de/mobil/"


################
# DB functions #
################

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
    sql = """CREATE TABLE IF NOT EXISTS tafeln (
                                    unixtime int NOT NULL,
                                    hash text PRIMARY KEY,
                                    tafel int,
                                    description text,
                                    title text,
                                    rubrik text
                                ); """

    try:
        c = conn.cursor()
        c.execute(sql)
        return conn
    except Error as e:
        print(e)

# inserts the text of a teletext tafel into the database
def insert_tafel(conn, content):
    sql = ''' INSERT INTO tafeln(unixtime,hash,tafel,description,title,rubrik)
                VALUES(?,?,?,?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, content)
        conn.commit()
        return c.lastrowid
    except Error as e:
        err = e

# returns the latest n tafeln 
def get_tafeln(conn):
    sql = "SELECT description,title,rubrik from tafeln order by unixtime desc limit " + articles

    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except Error as e:
        print(e)

# Cleanup db table
def cleanup_db(conn):
    sql = "DELETE FROM tafeln WHERE unixtime NOT IN (SELECT unixtime from tafeln order by unixtime desc limit " + articles + ")"
    print(sql)

    try:
        c = conn.cursor()
        c.execute(sql)
        conn.commit()
    except Error as e:
        print(e)


#################
# program logic #
#################

# downloads a teletext tafel and prepares it for database storage
def download_tafel(conn, tafel, rubrik):
    link = url+str(tafel)
    http = urllib3.PoolManager()
    r = http.request('GET', link)
    
    soup = BeautifulSoup(r.data, 'html.parser')
    desc = soup.find('div', class_='std')
    title = soup.find('h1')
    if desc is not None and title is not None:
        title = title.text.replace("<h1>","")
        title = title.replace("<b>","")
        title = title.replace("</h1>","")
        title = title.replace("</b>","")
        unixtime = time.time()
        desc = desc.text
        desc_hash = hashlib.md5(desc.encode('utf-8')).hexdigest()
        content = (unixtime,desc_hash,tafel,desc,title,rubrik)
        insert_tafel(conn,content)

# generates the RSS feed XML based on database content
def gen_rss(rows):
    f = open(xml_out, "w")

    out = """<?xml version="1.0" encoding="UTF-8" ?>
            <rss version="2.0">

            <channel>
                <title>ARD Teletext RSS Feed (inoffiziell)</title>
                <link>https://github.com/exitnode/teletext-rss</link>
                <description>RSS Feed des ARD Teletexts (Tafeln 104 bis 129)</description>"""

    for r in rows:
        desc = r[0]
        title = r[1]
        rubrik = r[2]

        if desc is not None:
            desc = desc.replace("\n"," ")
            desc = desc.strip()
            out+= """
                <item>
                <title>""" + rubrik + ": " + title + """</title>
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
            download_tafel(conn,s,"Nachrichten")
        for s in range(136, 144):
            download_tafel(conn,s,"Aus aller Welt")

        rows = get_tafeln(conn)
        gen_rss(rows)
        cleanup_db(conn)
    else:
        print("Error: No db conn")

if __name__ == "__main__":
    main()

