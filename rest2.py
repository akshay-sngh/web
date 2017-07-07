#!/usr/bin/env python
from flask import Flask, render_template, Response
import numpy as np
import cv2
import sqlite3
from datetime import datetime



app = Flask(__name__)
vc = cv2.VideoCapture(0)
ret = vc.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,600);
ret = vc.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,2000);
faceDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_frontalface_alt.xml') #face classifier
# myList = ['Unknown','Akshay','Abhishek','Audi','Viji','Sri']
new_font = cv2.cv.InitFont(cv2.FONT_HERSHEY_PLAIN,4,1,4,2,50)


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


recEigen.load('recognizerData/EigenData.yml')
recFisher.load('recognizerData/FisherData.yml')
recLBPH.load('recognizerData/LBPHData.yml')
#font style for the prediction text
font = cv2.cv.InitFont(cv2.FONT_HERSHEY_PLAIN,1.7,1,0,1,30)



@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('video.html')


def gen():
    """Video streaming generator function."""
    while True:
        rval, img = vc.read()
        #converting image into grayscale
    	gray_scale = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    	# img = cv2.flip(img,1)
    	#detect faces from the greyscale image
    	faces = faceDetect.detectMultiScale(gray_scale,1.3,5)
    	#use the coordinates of the ROI to draw a rectangle around it
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
    		cv2.cv.PutText(cv2.cv.fromarray(img),'Business Unit::'+str(info[3]),(3,440),font,(0,255,0),)
    		print str(datetime.now()).split()[1]
    		print '____________________________________________'
    		print
        cv2.imwrite('t.jpg', img)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('t.jpg', 'rb').read() + b'\r\n')



@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
