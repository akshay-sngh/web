import xlrd
import sqlite3
from datetime import datetime
def insertRows(sheet,book):
    conn = sqlite3.Connection('EmployeeBase.db')
    try:
        for i in range(1,sheet.nrows):
            row = sheet.row_values(i)
            Name = row[0]
            CorpID = row[1]
            Contact = int(row[2])
            PDOJ = int(row[3])
            PDOJ = datetime(*xlrd.xldate_as_tuple(PDOJ, book.datemode))
            PDOJ = PDOJ.date().strftime("%d/%m/%y")

            ADOJ = row[4]
            ADOJ = datetime(*xlrd.xldate_as_tuple(ADOJ, book.datemode))
            ADOJ = ADOJ.date().strftime("%d/%m/%y")
            Time = row[5]
            IsJoined = row[6]
            Track = row[7]
            query = "INSERT INTO Person (Id,Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track) VALUES(%d,'%s','%s',%d,'%s','%s','%s','%s')"%(i,Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track)
            conn.execute(query)
    except Exception,e:
        print 'error'
        print str(e)

    conn.commit()
    conn.close()
    return

try:
    workbook = xlrd.open_workbook("employee.xls")
except:
    workbook = xlrd.open_workbook("employee.xlsx")

sheet = workbook.sheet_by_index(0)

insertRows(sheet,workbook)
