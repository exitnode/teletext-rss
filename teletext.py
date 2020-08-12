import urllib3
from bs4 import BeautifulSoup
import textwrap
import hashlib
import sqlite3
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

    sql = ''' INSERT INTO sites(hash,site,content)
                VALUES(?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, site)
        conn.commit()
        return c.lastrowid
    except Error as e:
        print(e)

def get_site(conn, site):
    #sql = ''' SELECT content from sites WHERE site = ? '''
    sql = ''' SELECT content from sites '''
    try:
        c = conn.cursor()
        #c.execute(sql, (site,))
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except Error as e:
        print(e)

def store_site(conn, site):
    link = "http://www.ard-text.de/mobil/"+str(site)
    http = urllib3.PoolManager()
    r = http.request('GET', link)
    
    soup = BeautifulSoup(r.data, 'html.parser')
    bla = soup.find('div', class_='std').text
    bla_hash = hashlib.md5(bla.encode('utf-8')).hexdigest()
    content = (bla_hash,site,bla)
    insert_site(conn,content)

def gen_rss():
    out = """ 
            <?xml version=1.0 encoding=UTF-8 ?>
            <rss version=2.0>

            <channel>
                <title>W3Schools Home Page</title>
                <link>https://www.w3schools.com</link>
                <description>Free web building tutorials</description>"""

     #bla = """ <item>
     #           <title>RSS Tutorial</title>
     #           <link>https://www.w3schools.com/xml/xml_rss.asp</link>
     #           <description>New RSS tutorial on W3Schools</description>
     #       </item>"""

    out += """ </channel>
            </rss>"""
    print(out)

def main():
    db = r"/home/micha/bla.db"
    sql_create_sites_table = """CREATE TABLE IF NOT EXISTS sites (
                                    hash text PRIMARY KEY,
                                    site int,
                                    content text
                                ); """

    #conn = create_conn(db)
    conn = None
    if conn is not None:
        create_table(conn, sql_create_sites_table)
        for s in range(104, 116):
            store_site(conn,s)

        rows = get_site(conn,"104")
        for row in rows:
            #r = row[0].replace("^ ", "")
            #print(row[0])

            print(textwrap.fill(r, 40))
    else:
        print("Error: No db conn")

    gen_rss()

if __name__ == "__main__":
    main()

