import cv2
from PyQt4 import QtGui, QtCore
import sqlite3
from datetime import datetime
import subprocess
import time
import threading
from multiprocessing import Process
import string
import speech_recognition as sr
from os import system

#cascase classifiers for face, palm and smile detection
faceDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_frontalface_alt.xml')
palmDetect = cv2.CascadeClassifier('cascadeFiles/palm.xml')
smileDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_smile.xml')

finalId =0

def useSpeech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print 'How can i help you buddy?'
        audio = r.listen(source)

    print r.recognize_google(audio)
    if "yes" in r.recognize_google(audio) or "yeah" in r.recognize_google(audio):
        return True
    else:
        return False


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

def recordDate(id):

    '''This function stores the current time in the database for the persond with ID = id'''

    # if person is unknown then don't record any Entry
    if id is 0:
        return

    corpID = 'a'+str(id)
    #get today's date using datetime module from python
    dateString = str(datetime.now().date())
    timeString = str(datetime.now().time())
    timeString = timeString[:8]

    conn = sqlite3.connect('EmployeeBase.db')
    #dateString is in yyyy mm dd

    #remove the 20 from 2017
    dateString = dateString[2:]
    #put each date field in a list
    dateString = dateString.split('-')
    #reverse that list to make it to dd mm yy
    dateString = dateString[::-1]
    #put it back to dd/mm/yy format just like an excel date format
    dateString = '/'.join(dateString)
    print ('dateString is ',dateString)


    #Update the date entry in the database
    query = (" UPDATE Person SET ADOJ='%s' WHERE CorpID='%s' " % (dateString,corpID))
    rows = conn.execute(query)
    query = (" UPDATE Person SET IsJoined='Yes' WHERE CorpID='%s' " % (corpID))
    print (query)
    rows = conn.execute(query)

    query = (" UPDATE Person SET Time='%s' WHERE CorpID='%s' " % (timeString,corpID))
    rows = conn.execute(query)

    conn.commit()

    conn.close()

    # print rows


#invoke recognizer objects
recEigen = cv2.createEigenFaceRecognizer()
recFisher = cv2.createFisherFaceRecognizer()
recLBPH = cv2.createLBPHFaceRecognizer()


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

#loading the data that used for training purposes
recEigen.load('recognizerData/EigenData.yml')
recFisher.load('recognizerData/FisherData.yml')
recLBPH.load('recognizerData/LBPHData.yml')
#font style for the prediction text
font = cv2.cv.InitFont(cv2.FONT_HERSHEY_PLAIN,1.7,1,0,1,30)

class Capture():
    def __init__(self):
        self.capturing = False
        self.c = cv2.VideoCapture(0)
        ret = self.c.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,600);
        ret = self.c.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,2000);


    def startCapture(self):
        cv2.namedWindow("Capture")
        cv2.moveWindow("Capture",340,30)
        print ("pressed start")
        self.capturing = True
        cap = self.c
        while(self.capturing):
            ret, img = cap.read()
            #converting image into grayscale
            gray_scale = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            # img = cv2.flip(img,1)
            #detect faces from the greyscale image
            faces = faceDetect.detectMultiScale(gray_scale,1.3,5)
            #use the coordinates of the ROI to draw a rectangle around it
            #for detecting the presence of a palm

            global finalId
            finalId = 0
            for(x,y,w,h) in faces:
                smile = smileDetect.detectMultiScale(gray_scale,1.9,27)
                palm = palmDetect.detectMultiScale(gray_scale,1.5,5)
                finalId = 0
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
                print ('LBPH says',id1, 'recognised with a confidence of ' , conf1)
                #cv2.cv.PutText(cv2.cv.fromarray(img),'LPBH::'+myList[id1],(x,y+h+25),font,(0,255,0),)


                id2,conf2 = recFisher.predict(gray)
                print ('Fisher says',id2, 'recognised with a confidence of ' , conf2)
                #cv2.cv.PutText(cv2.cv.fromarray(img),'Fisher::'+myList[id2],(x,y+h+45),font,(0,255,0),)
                #if any two IDs match then identify the person
                if id1 == id2:
                    myId = id2




                id3,conf3 = recEigen.predict(gray)
                print ('Eigen says',id3, 'recognised with a confidence of ' , conf3)
                #cv2.cv.PutText(cv2.cv.fromarray(img),'Eigen::'+myList[id3],(x,y+h+65),font,(0,255,0),)
                if id1 == id3:
                    myId = id3
                elif id2 is id3:
                    myId = id3


                #print the name of the person with atleast 2 out of 3 votes
                info = getInfo(myId)
                # cv2.cv.PutText(cv2.cv.fromarray(img),'Name::'+str(info[1]),(x,y+h+25),font,(0,255,0),)
                # cv2.cv.PutText(cv2.cv.fromarray(img),'CorpID::'+str(info[2]),(x,y+h+50),font,(0,255,0),)
                # cv2.cv.PutText(cv2.cv.fromarray(img),'Business Unit::'+str(info[3]),(x,y+h+75),font,(0,255,0),)

                #printing the name on the left bottom corner of the screen
                cv2.cv.PutText(cv2.cv.fromarray(img),'Name::'+str(info[1]),(3,400),font,(0,255,0),)
                cv2.cv.PutText(cv2.cv.fromarray(img),'CorpID::'+str(info[2]),(3,420),font,(0,255,0),)
                cv2.cv.PutText(cv2.cv.fromarray(img),'Business Unit::'+str(info[3]),(3,440),font,(0,255,0),)

                finalId = myId


                print ('____________________________________________')
                print
                for (x1,y1,w1,h1) in smile:
                    cv2.rectangle(img,(x1,y1),(x1+w1,y1+h1),(0,0,255),2)
                    self.setTime()
                for (x2,y2,w2,h2) in palm:
                    cv2.rectangle(img,(x2,y2),(x2+w2,y2+h2),(255,0,0),2)
                    self.capturing=False
                    self.quitCapture()



            # cv2.namedWindow("Capture")
            # cv2.moveWindow("Caputure",300,30)
            cv2.imshow("Capture", img)
            cv2.waitKey(5)
        cv2.destroyAllWindows()


    def setTime(self):
        global finalId
        msgBox = QtGui.QMessageBox()
        self.capturing = False
        infos = getInfo(finalId)
        name = str(infos[1])
        firstname = name.split(' ')[0]
        #if id recognised is unknown
        if finalId is 0 or firstname == 'Unknown':
            msgBox.setIcon(QtGui.QMessageBox.Information)
            msgBox.setText("OOPS!")
            msgBox.setInformativeText("Sorry we weren't able to recognise you")

            ret = msgBox.exec_()
            self.capturing = True
            return




        print ('ID received is !', finalId)

        '''using message box
        # msgBox.setInformativeText("Are you %s?"%(firstname))
        # msgBox.setIcon(QtGui.QMessageBox.Information)
        # msgBox.setWindowTitle("Smile!")
        # msgBox.setText("WELCOME TO FIDELITY!")

        # msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
        # msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
        #
        # ret = msgBox.exec_()

        # print 'return value is ',ret
        # if ret == QtGui.QMessageBox.Yes:
        #     print 'YOU JUST CLICKED YESSSSSSSS'
        # else:
        #     print 'Sorry for the error!\n'
        #     finalId = 0
        #     return

        '''

        self.capturing = False
        cap = self.c

        r = sr.Recognizer()
        with sr.Microphone() as source:
            print 'Are you %s?'%(firstname)
            ret,img = cap.read()
            new_font = cv2.cv.InitFont(cv2.FONT_HERSHEY_PLAIN,4,1,4,2,50)
            cv2.cv.PutText(cv2.cv.fromarray(img),'Are you '+firstname+'?',(150,30),new_font,(255,255,255),)
            cv2.namedWindow("WELCOME TO FIDELITY!")
            cv2.moveWindow("WELCOME TO FIDELITY!",340,30)
            cv2.imshow("WELCOME TO FIDELITY!",img)
            cv2.waitKey(5)
            audio = r.listen(source)
            cv2.destroyWindow("WELCOME TO FIDELITY!")

        try:
            print 'you said', r.recognize_google(audio)
            if 'yes' in r.recognize_google(audio) or 'yeah' in r.recognize_google(audio):
                pass

            elif 'close' in r.recognize_google(audio):
                cv2.destroyAllWindowsWindows()
                self.capturing = False
                self.endCapture()
                return

            elif 'quit' in r.recognize_google(audio):
                cv2.destroyAllWindows()
                cap.release()
                self.quitCapture()
                return
            else:
                print 'sorry!'
                self.capturing = True
                return

        except:
            print 'nothing...'
            self.capturing = True
            return


        '''using QT documentation'''
        # msgBox.setText("The document has been modified.");
        # msgBox.setInformativeText("Do you want to save your changes?");
        # msgBox.setStandardButtons(QMessageBox::Save | QMessageBox::Discard | QMessageBox::Cancel);
        # msgBox.setDefaultButton(QMessageBox::Save);
        # int ret = msgBox.exec();


        '''Using tutorials point'''
    #     msg = QMessageBox()
    #    msg.setIcon(QMessageBox.Information)
       #
    #    msg.setText("This is a message box")
    #    msg.setInformativeText("This is additional information")
    #    msg.setWindowTitle("MessageBox demo")
    #    msg.setDetailedText("The details are as follows:")
    #    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)


        recordDate(finalId)

        ret,img = cap.read()
        #retrieve values from the database
        infos = getInfo(finalId)
        name = str(infos[1])
        corpID = str(infos[2])
        corpID = corpID.upper()
        corpID= ' '.join(corpID)
        firstname = name.split(' ')[0]
        print 'WELCOME' ,firstname

        cv2.cv.PutText(cv2.cv.fromarray(img),'WELCOME TO FIDELITY '+firstname,(5,30),new_font,(0,255,0),)
        # cv2.cv.PutText(cv2.cv.fromarray(img),firstname+'!!!',(185,60),new_font,(0,255,0),)

        cv2.namedWindow("WELCOME!")
        cv2.moveWindow("WELCOME!",340,30)
        cv2.imshow("WELCOME!",img)
        # self.endCapture()
        # time.sleep(0.5)
        cv2.waitKey(1)
        #subprocess is a package for running bash scripts
        subprocess.call(["say","-v","Samantha","WELCOME to FIDELITY INVESTMENTS!!!"])
        subprocess.call(["say","-v","Samantha","your ENTRY, has been SUCCESSFULLY recorded!!!"])
        subprocess.call(["say","-v","Samantha","Your corp ID is %s"%(corpID)])


        cv2.destroyWindow("WELCOME!")
        self.capturing = True



    def endCapture(self):
        print ("pressed End")
        global finalId
        finalId = 0
        self.capturing = False


    def quitCapture(self):
        self.capturing = False
        print ("pressed Quit")
        cap = self.c
        cv2.destroyAllWindows()
        cap.release()
        QtCore.QCoreApplication.quit()



class Window(QtGui.QWidget):
    def __init__(self):

        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Control Panel')

        self.capture = Capture()
        self.start_button = QtGui.QPushButton('Open',self)
        self.start_button.clicked.connect(self.capture.startCapture)

        self.end_button = QtGui.QPushButton('Close',self)
        self.end_button.clicked.connect(self.capture.endCapture)

        self.record_button = QtGui.QPushButton('Record Time',self)
        self.record_button.clicked.connect(self.capture.setTime)

        self.quit_button = QtGui.QPushButton('Quit',self)
        self.quit_button.clicked.connect(self.capture.quitCapture)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.end_button)
        vbox.addWidget(self.record_button)
        vbox.addWidget(self.quit_button)

        self.setLayout(vbox)
        self.setGeometry(100,100,250,200)
        self.move(530,550)
        self.show()


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
