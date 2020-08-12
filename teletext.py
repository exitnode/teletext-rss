import urllib3
from bs4 import BeautifulSoup
import hashlib
import sqlite3
import time
from sqlite3 import Error

def create_conn(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_SQL):
    try:
        c = conn.cursor()
        c.execute(create_table_SQL)
        return conn
    except Error as e:
        print(e)

def insert_site(conn, site):
    
    sql = ''' INSERT INTO sites(unixtime,hash,tafel,description,title)
                VALUES(?,?,?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, site)
        conn.commit()
        return c.lastrowid
    except Error as e:
        err = e

def get_sites(conn):
    sql = ''' SELECT description,title from sites order by unixtime desc limit 3 '''
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except Error as e:
        print(e)

def store_site(conn, tafel):
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
        insert_site(conn,content)

def gen_rss(rows):
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
            </rss>"""

    print(out)

def main():
    db = r"/home/micha/bla.db"
    sql_create_sites_table = """CREATE TABLE IF NOT EXISTS sites (
                                    unixtime int NOT NULL,
                                    hash text PRIMARY KEY,
                                    tafel int,
                                    description text,
                                    title text
                                ); """

    conn = create_conn(db)
    if conn is not None:
        create_table(conn, sql_create_sites_table)
        for s in range(104, 116):
            store_site(conn,s)

        rows = get_sites(conn)
        gen_rss(rows)
    else:
        print("Error: No db conn")

if __name__ == "__main__":
    main()

