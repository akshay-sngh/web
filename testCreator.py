import cv2
import numpy as np
import os
def dataSetCreator(path):
	faceDetect = cv2.CascadeClassifier('cascadeFiles/haarcascade_frontalface_alt.xml')
	# path = 'trainSet'
	imagePaths = [os.path.join(path,f) for f in os.listdir(path)]
	faces = []
	Ids = []
	#tuple used for resizing the image
	size = (50,50)

	print imagePaths
	for imagePath in imagePaths:
		img = cv2.imread(imagePath)
		retval,buff = cv2.imencode('.jpg',img,CV_IMWRITE_JPEG_QUALITY)
		Id = os.path.split(imagePath)[-1].split('.')
		Id = '.'.join(Id[0:2])
		Id = Id[1:]
		print Id
		Ids.append(str(Id))

		#convert image into greyscale
		gray  = cv2.cvtColor(buff, cv2.COLOR_BGR2GRAY)

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
			#cv2.imwrite('newSet/User.' + str(Id) + '.jpg',new)

			#drawing a green rectangle around the face

			cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
			cv2.imshow("cropping",img)
			cv2.waitKey(250)

dataSetCreator('trainSet')
