import sqlite3

con = sqlite3.connect("hh.sqlite3")
cur = con.cursor()

cur.execute('delete from save_data')
cur.execute('delete from sd_id_skills')
cur.execute('delete from vacancy')
cur.execute('delete from skills')
cur.execute('delete from region')
cur.execute('delete from employment')
cur.execute('delete from currency')
cur.execute('update dif_variable set num_search = 0')
con.commit()