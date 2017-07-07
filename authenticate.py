import sqlite3

def authenticateUser(username,password):
    conn = sqlite3.Connection('AdminBase.db')
    query = (" SELECT password From User Where username='%s'" % (username))
    rows = conn.execute(query)

    for row in rows:
        actual = row[0]
    print actual
    if password == actual:
        return True
        conn.close()
    else:
        return False
        conn.close()


print auth('Audi','Leap')
