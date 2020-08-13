import urllib3
from bs4 import BeautifulSoup
import hashlib
import sqlite3
import time
from sqlite3 import Error

# configure this to your needs
xml_out = "/home/micha/websites/exitnode.net/htdocs/ard_teletext.xml"
db = r"/home/micha/bla.db"

def create_conn(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

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

def get_tafeln(conn):
    sql = ''' SELECT description,title from tafeln order by unixtime desc limit 20 '''
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except Error as e:
        print(e)

def store_tafel(conn, tafel):
    link = "http://www.ard-text.de/mobil/"+str(tafel)
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

def gen_rss(rows):
    f = open(xml_out, "w")

    out = """<?xml version="1.0" encoding="UTF-8" ?>
            <rss version="2.0">

            <channel>
                <title>ARD Teletext RSS Feed (inofficial)</title>
                <link>https://www.exitnode.net</link>
                <description>bla</description>"""

    for r in rows:
        cont = r[0]
        title = r[1]

        if cont is not None:
            cont = cont.replace("\n","")
            out+= """
                <item>
                <title>""" + title + """</title>
                <description>
                """ + cont + """
                </description>
                </item>"""

    out += """ 
            </channel>
            </rss>
            """

    f.write(out)
    f.close()

def main():
    conn = create_conn(db)
    if conn is not None:
        create_tables(conn)
        for s in range(104, 129):
            store_tafel(conn,s)

        rows = get_tafeln(conn)
        gen_rss(rows)
    else:
        print("Error: No db conn")

if __name__ == "__main__":
    main()

