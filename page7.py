from flask import Flask
import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, abort, Response
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
app.config['PHOTO_ALLOWED_EXTENSIONS'] = set([ 'png', 'jpg', 'jpeg','tif','tiff'])

# For a given file, return whether it's an allowed type or not
def photo_allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['PHOTO_ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation

askflag = 0
info = []

def validateName(filename,errors):
    if filename[0] != 'a':
        errors.append("'{}' is not a valid file name".format(filename))
        return False,errors
    cid = filename[1:7]
    try:
        print 'string cid is ',cid
        cid = int(cid)
        print "corp ID is ",cid
        return True,errors
    except:
        errors.append("'{}' is not a valid file name".format(filename))
        return False, errors





def resizeImage(image,size=(50,50)):
	'''this function resizes the image to 50x50 for Eigen and Fisher Reconginizers'''
	if image.shape < size:
		image = cv2.resize(image,size,interpolation=cv2.INTER_AREA)
	else:
		image = cv2.resize(image,size,interpolation = cv2.INTER_CUBIC)
	return image

def cutImage(image,x,y,w,h):
	'''crop the image so that only the face retains'''
	w_rm = int(0.2*w/2)
	image = image[y:y+h, x+w_rm : x+ w- w_rm]
	return image

def normalizePixels(image):
	'''normalizes the pixel density to adjust contrast the image'''
	image = cv2.equalizeHist(image)
	return image


def getInfo(id):
	corpID = 'a'+str(id)
	print corpID
	'''This function retrieves the profile from the database'''
	#get connection to database
	conn = sqlite3.connect('EmployeeBase.db')

	#running the sql query
	query = "SELECT * FROM Person WHERE CorpID='%s'"%(str(corpID))
	print query
	rows = conn.execute(query)
	info = None
	for row in rows:
		info = row
	conn.close()
	if info == None:
		info=['','Unknown','','','']
		return info
	print info
	return info


@app.route('/photos',methods=['POST','GET'])
def photo_upload():
    return render_template('photo_upload.html')


# Route that will process the file upload
@app.route('/photos/upload', methods=['POST'])
def photo_uploader():
    #haar cascade file
    faceDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_frontalface_alt.xml')
    smileDetect = cv2.CascadeClassifier('CascadeClassifier/haarcascade_smile.xml')
    palmDetect = cv2.CascadeClassifier('CascadeClassifier/palm.xml')
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    Ids = []
    errors = []
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
            filename1 = filename.split(".")[0]
            print 'filename1 is ', filename1
            retval,errors = validateName(filename1,errors)
            if retval == False:
                continue
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

            faceFound = False
            for (x,y,w,h) in faces:
                faceFound = True
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
            if faceFound == False:
                errors.append('No face found in {}'.format(filename))
                os.remove(imagePath)
                print "removed ",imagePath
                continue
            else:
                cv2.imwrite('dataSet/' + str(Id),gray)

            filenames.append(filename)
    if not filenames:
        errors.append('No file provided for training')
        return render_template("upload.html",filenames=filenames,errors=errors)
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
        try:
            Ids.append(int(Id))
        except Exception,e:
            errors.append(str(e))
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faceNp = np.array(gray,'uint8')
        Faces.append(faceNp)


        count+=1


    Ids = np.array(Ids)
    print Ids
    try:
        recognizerEigen.train(Faces,Ids)
        recognizerEigen.save('recognizerData/EigenData.yml')

        recognizerFisher.train(Faces,Ids)
        recognizerFisher.save('recognizerData/FisherData.yml')

        recognizerLBPH.update(Faces,Ids)
        recognizerLBPH.save('recognizerData/LBPHData.yml')
    except Exception,e:
        pass

    return render_template("upload.html",filenames=filenames,errors=errors)


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
            query = "INSERT OR Replace INTO Person (Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track,Time) VALUES('%s','%s',%d,'%s','%s','%s','%s','%s')"%(Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track,Time)
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
    cur = conn.execute("SELECT * FROM Person WHERE Name  LIKE '{}%' COLLATE NOCASE ORDER BY Name".format(name))
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
    cur = conn.execute("SELECT * FROM Person WHERE CorpID  LIKE '{}%' COLLATE NOCASE ORDER BY CorpID".format(name))
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
def welcome():
    global myname
    global username
    if not session.get('logged_in'):
        return render_template('login.html')
    # else:
    #     return "Hello Boss!"
    else:
        return render_template("head.html",myname=myname,username=username)

@app.route('/records',methods=['GET','POST'])
def home():
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
    return welcome()

@app.route('/remove',methods=['GET','POST'])
def remove():
    if request.method == 'POST':
        corpID = request.form['corpID']
        return removeEntry(name,corpID)


@app.route('/logout',methods=['POST','GET'])
def logout():
    global myname
    global username
    session['logged_in'] = False
    username = ''
    myname = ''
    return welcome()

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

@app.route("/camera",methods=['GET'])
def showCamera():
    global askflag
    global info
    """Video streaming home page."""
    return render_template('video.html')
def gen():
    global askflag
    global info
    askflag = 0
    info = []
    """Video streaming generator function."""
    vc = cv2.VideoCapture(0)
    ret = vc.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,600);
    ret = vc.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,2000);
    faceDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_frontalface_alt.xml') #face classifier
    smileDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_smile.xml')
    # myList = ['Unknown','Akshay','Abhishek','Audi','Viji','Sri']
    new_font = cv2.cv.InitFont(cv2.FONT_HERSHEY_PLAIN,4,1,4,2,50)

    flag = 0
    #invoke recognizer objects
    recEigen = cv2.createEigenFaceRecognizer()
    recFisher = cv2.createFisherFaceRecognizer()
    recLBPH = cv2.createLBPHFaceRecognizer()


    recEigen.load('recognizerData/EigenData.yml')
    recFisher.load('recognizerData/FisherData.yml')
    recLBPH.load('recognizerData/LBPHData.yml')

    #font style for the prediction text
    font = cv2.cv.InitFont(cv2.FONT_HERSHEY_PLAIN,1.7,1,0,1,30)
    '''code for the camera to process frames'''

    while True:
        rval, img = vc.read()
        #converting image into grayscale
    	gray_scale = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    	# img = cv2.flip(img,1)
    	#detect faces from the greyscale image
    	faces = faceDetect.detectMultiScale(gray_scale,1.3,5)
    	#use the coordinates of the ROI to draw a rectangle around it
        smiles = smileDetect.detectMultiScale(gray_scale,1.7,27)

    	for(x,y,w,h) in faces:
    		#draw a rectangle around the face
    		cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

    		#converting into grayscale
    		gray = cutImage(gray_scale,x,y,w,h)



    		#normalizing pixels
    		gray = normalizePixels(gray)


    		#resizing the image
    		gray = resizeImage(gray)


    		myId = 0
    		id1,conf1 = recLBPH.predict(gray)
    		print 'LBPH says',id1, 'recognised with a confidence of ' , conf1
    		#cv2.cv.PutText(cv2.cv.fromarray(img),'LPBH::'+myList[id1],(x,y+h+25),font,(0,255,0),)


    		id2,conf2 = recFisher.predict(gray)
    		print 'Fisher says',id2, 'recognised with a confidence of ' , conf2
    		#cv2.cv.PutText(cv2.cv.fromarray(img),'Fisher::'+myList[id2],(x,y+h+45),font,(0,255,0),)
    		#if any two IDs match then identify the person
    		if id1 == id2:
    			myId = id2



    		id3,conf3 = recEigen.predict(gray)
    		print 'Eigen says',id3, 'recognised with a confidence of ' , conf3
    		#cv2.cv.PutText(cv2.cv.fromarray(img),'Eigen::'+myList[id3],(x,y+h+65),font,(0,255,0),)
    		if id1 == id3:
    			myId = id3
    		elif id2 == id3:
    			myId = id3

    		#print the name of the person with atleast 2 out of 3 votes
    		info = getInfo(myId)
    		# cv2.cv.PutText(cv2.cv.fromarray(img),'Name::'+str(info[1]),(x,y+h+25),font,(0,255,0),)
    		# cv2.cv.PutText(cv2.cv.fromarray(img),'CorpID::'+str(info[2]),(x,y+h+50),font,(0,255,0),)
    		# cv2.cv.PutText(cv2.cv.fromarray(img),'Business Unit::'+str(info[3]),(x,y+h+75),font,(0,255,0),)

    		cv2.cv.PutText(cv2.cv.fromarray(img),'Name::'+str(info[1]),(3,400),font,(0,255,0),)
    		cv2.cv.PutText(cv2.cv.fromarray(img),'CorpID::'+str(info[2]),(3,420),font,(0,255,0),)
    		try:
                        cv2.cv.PutText(cv2.cv.fromarray(img),'Track::'+str(info[7]),(3,440),font,(0,255,0),)
                except:
                        cv2.cv.PutText(cv2.cv.fromarray(img),'Track:: N/A',(3,440),font,(0,255,0),)
    		print str(datetime.now()).split()[1]
    		print '____________________________________________'
    		print
                # for (x1,y1,w1,h1) in smiles:
                #     #cv2.rectangle(img,(x1,y1),(x1+w1,y1+h1),(0,0,255),2)
                #     askflag = 1
                #     print "++++++++++++++ askflag is 1"
                #     print "++++++++++ info is ",info



        if flag is 1:
            break

        cv2.imwrite('t.jpg', img)
        try:
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('t.jpg', 'rb').read() + b'\r\n')
        except:
            pass





@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/delete_entry')
def removeRow():
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
    return render_template("delete_entry.html",Employees=Employees)

@app.route("/delete_entry/<corpID>")
def removeRowCorpID(corpID):
    myID = str(corpID)
    myID = myID[1:-1]
    print type(myID)
    print 'my id is ',myID
    conn = sqlite3.Connection("EmployeeBase.db")
    query = "DELETE FROM Person WHERE CorpID='{}'".format(myID)
    try:
        conn.execute(query)
    except Exception,e:
        print e
    conn.commit()
    return removeRow()

@app.route('/add_entry',methods=['GET','POST'])
def putFormRow():
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
    return render_template("add_entry.html",Employees=Employees)

@app.route("/add_new_entry",methods=["POST","GET"])
def putNewRow():
    Name = request.form["name"]
    print Name
    CorpID = request.form["corpID"]
    print CorpID
    Contact = request.form["contact"]
    Contact = int(Contact)
    print Contact
    PDOJ = request.form["PDOJ"]
    print PDOJ
    ADOJ = request.form["ADOJ"]
    print ADOJ
    IsJoined = request.form["IsJoined"]
    print "Is joined is" , IsJoined
    Track = request.form["Track"]
    print "Track is ",Track
    Time = request.form["Time"]
    print "Time is ",Time

    conn = sqlite3.Connection("EmployeeBase.db")
    query = "INSERT OR Replace INTO Person (Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track,Time) VALUES('%s','%s',%d,'%s','%s','%s','%s','%s')"%(Name,CorpID,Contact,PDOJ,ADOJ,IsJoined,Track,Time)

    try:
        conn.execute(query)
    except Exception,e:
        print "There is an error::",e
    conn.commit()
    conn.close()
    return putFormRow()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(host="0.0.0.0",debug = True,threaded=True)
