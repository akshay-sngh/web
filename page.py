from flask import Flask
import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, abort
import xlrd
from werkzeug import secure_filename
from datetime import datetime
from datetime import time
import cv2
import numpy as np
from flask_wtf import FlaskForm
from wtforms import DateField
from datetime import date



class DateForm(FlaskForm):
    dt = DateField('Pick a Date', format="%m/%d/%Y")

app = Flask(__name__)
username = ''
myname = ''
# This is the path to the upload directory
app.config['PHOTO_UPLOAD_FOLDER'] = 'trainSet/'
# These are the extension that we are accepting to be uploaded
app.config['PHOTO_ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','tif'])

# For a given file, return whether it's an allowed type or not
def photo_allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['PHOTO_ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation



@app.route('/photos',methods=['POST','GET'])
def photo_upload():
    return render_template('photo_upload.html')


# Route that will process the file upload
@app.route('/photos/upload', methods=['POST'])
def photo_uploader():
    #haar cascade file
    faceDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_frontalface_alt.xml')
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    Ids = []
    Faces = []
    size = (50,50)
    recognizerEigen = cv2.createEigenFaceRecognizer()
    recognizerFisher = cv2.createFisherFaceRecognizer()
    recognizerLBPH = cv2.createLBPHFaceRecognizer()
    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and photo_allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup

            file.save(os.path.join(app.config['PHOTO_UPLOAD_FOLDER'], filename))
            # Save the filename into a list, we'll use it later
            imagePath = 'trainSet/'+filename
            img = cv2.imread(imagePath)

            Id = os.path.split(imagePath)[-1].split('.')
            Id = '.'.join(Id[0:2])
            Id = Id[1:]
            print Id

            #convert image into greyscale
            gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            #detect faces from the grayscale image
            #list those faces
            faces = faceDetect.detectMultiScale(gray,1.3, 5)

            #
            for (x,y,w,h) in faces:
                #cutting the image
                new = gray[y:y+h,x:x+h]

                w_rm = int(0.2 * w/2)
                gray = gray[y:y+h, x+ w_rm : x+w-w_rm]

                #normalizing the pixel density of the image
                new = cv2.equalizeHist(new)
                gray = cv2.equalizeHist(gray)

                #resizing the image
                if gray.shape < size:
                    gray = cv2.resize(gray,size,interpolation = cv2.INTER_AREA)
                else:
                    gray = cv2.resize(gray,size,interpolation = cv2.INTER_CUBIC)

                #writing the images on their designated forlder

            cv2.imwrite('dataSet/' + str(Id),gray)
            # faceNp = np.array(gray,'uint8')
            # imagePath = 'dataSet/'+filename
            # ID = (os.path.split(imagePath)[-1].split('.')[0])
            #
            # ID = ID[1:7]
            # ID = int(ID)
            # Faces.append(faceNp)
            # Ids.append(ID)
            filenames.append(filename)
    Ids = []
    Faces = []
    path = 'dataSet/'
    count = 0
    for file in os.listdir(path):
        if count == 0:
            count+=1
            continue
        img = cv2.imread(path+file)
        Id = file[0:6]
        print count, path+file,Id
        Ids.append(int(Id))
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faceNp = np.array(gray,'uint8')
        Faces.append(faceNp)


        count+=1


    Ids = np.array(Ids)
    print Ids

    recognizerEigen.train(Faces,Ids)
    recognizerEigen.save('recognizerData/EigenData.yml')

    recognizerFisher.train(Faces,Ids)
    recognizerFisher.save('recognizerData/FisherData.yml')

    recognizerLBPH.train(Faces,Ids)
    recognizerLBPH.save('recognizerData/LBPHData.yml')

    return render_template("upload.html",filenames=filenames)


# This is the path to the upload directory
app.config['EXCEL_UPLOAD_FOLDER'] = 'spreadsheet/'
# These are the extension that we are accepting to be uploaded
app.config['EXCEL_ALLOWED_EXTENSIONS'] = set(['xlsx', 'xls'])

def insertRows(filenames):
    try:
        book = xlrd.open_workbook("spreadsheet/%s"%(filenames[0]))
    except:
        book= xlrd.open_workbook("spreadsheet/%s"%(filename[0]))

    sheet = book.sheet_by_index(0)

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
            Time = int(Time * 24 * 3600) # convert to number of seconds
            Time = time(Time//3600, (Time%3600)//60, Time%60)
            IsJoined = row[6]
            Track = row[7]
            query = "INSERT OR Replace INTO Person (Id,Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track,Time) VALUES(%d,'%s','%s',%d,'%s','%s','%s','%s','%s')"%(i,Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track,Time)
            conn.execute(query)
    except Exception,e:
        print 'error'
        print str(e)

    conn.commit()
    conn.close()
    return render_template("excel.html",filenames=filenames)


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['EXCEL_ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/excel',methods=['POST','GET'])
def index():
    return render_template('xlupload.html')


# Route that will process the file upload
@app.route('/excel/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            file.save(os.path.join(app.config['EXCEL_UPLOAD_FOLDER'], filename))
            # Save the filename into a list, we'll use it later
            filenames.append(filename)
            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
    # Load an html page with a link to each uploaded file
    '''return render_template('xlupload.html',filenames=filenames)'''
    return insertRows(filenames)

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload

@app.route('/search_name',methods=['GET'])
def searchName():
    return render_template("name_form.html")

@app.route('/search_corpID',methods=['GET'])
def searchID():
    return render_template("corpID_form.html")

@app.route('/search_name_result',methods=['POST'])
def returnName():
    status = 0
    name = request.form['name']
    if name == '':
        status=0;
        return render_template("name_form.html",status=status)
    conn=sqlite3.Connection('EmployeeBase.db')
    cur = conn.execute("SELECT * FROM Person WHERE Name  LIKE '{}%' COLLATE NOCASE".format(name))
    Employees = [dict(Id=row[0],
                Name=row[1],
                CorpID=row[2],
                Contact=row[3],
                PDOJ = row[4],
                ADOJ = row[5],
                IsJoined =row[6],
                Track = row[7],
                Time = row[8]
                ) for row in cur.fetchall()]
    conn.close()

    print 'E',Employees
    if name=='':
        status=0
    elif Employees == []:
        status=2
    else:
        status=1
    return render_template("name_form.html",Employees=Employees,status=status)


# corpid search result
@app.route('/search_corpID_result',methods=['POST'])
def returnCorpID():
    status = 0
    name = request.form['name']
    if name == '':
        status=0;
        return render_template("name_form.html",status=status)
    conn=sqlite3.Connection('EmployeeBase.db')
    cur = conn.execute("SELECT * FROM Person WHERE CorpID  LIKE '{}' COLLATE NOCASE".format(name))
    Employees = [dict(Id=row[0],
                Name=row[1],
                CorpID=row[2],
                Contact=row[3],
                PDOJ = row[4],
                ADOJ = row[5],
                IsJoined =row[6],
                Track = row[7],
                Time = row[8]
                ) for row in cur.fetchall()]
    conn.close()

    print 'E',Employees
    if name=='' :
        status=0
    elif not Employees:
        status = 2
    else:
        status=1
    return render_template("corpID_form.html",Employees=Employees,status=status)
# end of corpid search result



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['PHOTOS_UPLOAD_FOLDER'],
                               filename)

def recordEntry(name,corpID,BU,entry,time):
    conn = sqlite3.Connection('FaceBase.db')
    query = "INSERT OR Replace INTO Employee (Name,CorpId,BU,Entry,Time)\n VALUES('%s','%s','%s','%s','%s')"%(name,corpID,BU,entry,time)
    rows = conn.execute(query)
    conn.commit()
    conn.close()
    return home()

@app.route('/new',methods=['GET','POST'])
def send():
    if request.method == 'POST':
        name = request.form['name']
        corpID = request.form['corpID']
        BU = request.form['BU']
        entry = request.form['entry']
        time = request.form['time']
        print 'name received::' , name
        print name, corpID, BU, entry, time
        return recordEntry(name,corpID,BU,entry,time)
    return render_template("form.html")

def authenticateUser(username,password):
    conn = sqlite3.Connection('AdminBase.db')
    query = (" SELECT password From User Where username='%s'" % (username))
    try:
        rows = conn.execute(query)
    except:
        return False

    for row in rows:
        try:
            actual = row[0]
        except:
            return False
    try:
        print actual
    except:
        return False
    if password == actual:
        return True
        conn.close()
    else:
        return False
        conn.close()

@app.route('/',methods=['GET','POST'])
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    # else:
    #     return "Hello Boss!"
    else:
        count = 1
        conn=sqlite3.Connection('EmployeeBase.db')
        cur = conn.execute('SELECT * from Person')
        Employees = [dict(Id=row[0],
                    Name=row[1],
                    CorpID=row[2],
                    Contact=row[3],
                    PDOJ = row[4],
                    ADOJ = row[5],
                    IsJoined =row[6],
                    Track = row[7],
                    Time = row[8]
                    ) for row in cur.fetchall()]
        conn.close()
        return render_template('homepage.html', Employees=Employees)


@app.route('/login', methods=['POST'])

def do_admin_login():
    global username
    global myname
    session['logged_in'] = False
    # if request.form['password'] == 'password' and request.form['username'] == 'admin':
    #     session['logged_in'] = True
    if authenticateUser(request.form['username'],request.form['password']) is True:
        username = request.form['username']
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()

@app.route('/remove',methods=['GET','POST'])
def remove():
    if request.method == 'POST':
        corpID = request.form['corpID']
        return removeEntry(name,corpID)


@app.route('/logout',methods=['POST','GET'])
def logout():
    session['logged_in'] = False
    username = ''
    myname = ''
    return home()

@app.route('/add_user',methods=['GET'])
def addUser():
    return render_template("add_user.html",username = username)

@app.route('/date_form',methods=['GET','POST'])
def dateForm():
    Employees = []
    status = 0
    dateString = ''
    form = DateForm()
    if request.method == 'POST':
        try:
            dateString = form.dt.data.strftime('%x')
            dateString = str(dateString)
            dateString = dateString.split('/')
            dateString[0],dateString[1]=dateString[1],dateString[0]
            dateString = '/'.join(dateString)
            print dateString
            print 'datString is {}'.format(str(dateString))
            conn=sqlite3.Connection('EmployeeBase.db')
            cur = conn.execute("SELECT * FROM Person WHERE ADOJ ==  '{}'".format(dateString))
            cnt = 0
            Employees = [dict(Id=cnt,
                        Name=row[1],
                        CorpID=row[2],
                        Contact=row[3],
                        PDOJ = row[4],
                        ADOJ = row[5],
                        IsJoined =row[6],
                        Track = row[7],
                        Time = row[8],
                        cnt=cnt+1
                        ) for row in cur.fetchall()]
            print Employees
            if not Employees:
                status = 2
            else:
                status = 1
            conn.close()
        except Exception,e:
            print e
            return render_template('date_form.html',form=form,Employees=Employees,status = status)

    return render_template('date_form.html', form=form,Employees=Employees,status=status)

@app.route('/add_user_result',methods=['POST'])
def validateEntry():
    error = ''
    name =  request.form['name']
    newname =request.form['newname']
    password =request.form['password']
    repassword= request.form['repassword']
    if name =='' or newname == '' or password == '' or repassword == '':
        error = 'all fields are compulsory'
        return render_template("add_user.html",error=error)
    if ' ' in newname:
        error = 'no spaces allowed in the username'
        print error
        return render_template("add_user.html",error = error)

    conn = sqlite3.Connection('AdminBase.db')
    query = "SELECT * FROM User WHERE username='{}'".format(newname)
    rows = conn.execute(query)
    for row in rows:
        error = 'username is already taken'

    if password == repassword:
        pass
    else:
        error = 'passwords do not match'
        return render_template("add_user.html",error = error)
    if error == '':
        query = "INSERT INTO User(username,password,name) VALUES('{}','{}','{}')".format(newname,password,name)
        conn.execute(query)
        conn.commit()
        conn.close()
        # return render_template("add_successful.html",name=name,newname=newname)
        return render_template("add_user_success.html",name=name,newname=newname)
    else:
        return render_template("add_user.html",error=error)

@app.route('/delete_user',methods=['GET'])
def showDeleteForm():
    return render_template("delete_user.html",username = username)

@app.route('/delete_user_result',methods=['POST'])
def validateExit():
    global username
    error = ''
    password = request.form['password']
    repassword = request.form['repassword']
    if password == '' or repassword == '':
        error = 'all fields are compulsory'
        return render_template("/delete_user.html",username = username,error=error)


    if password == repassword:
        conn = sqlite3.Connection("AdminBase.db")
        query = "SELECT * FROM User WHERE username = '{}' AND password = '{}'".format(username,password)
        rows = conn.execute(query)
        for row in rows:
            query = "DELETE FROM User WHERE username = '{}'".format(username)
            conn.execute(query)
            conn.commit()
            conn.close()
            return logout()
        error = 'incorrect password entered'
        return render_template("/delete_user.html",username = username,error=error)
    else:
        error = 'passwords do not match'
        return render_template("/delete_user.html",username =username,error = error)


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(host="0.0.0.0",debug=True)
