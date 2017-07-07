import os
import cv2
import numpy as np
# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

# Initialize the Flask application
app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'trainSet/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','tif'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    return render_template('index.html')


# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
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
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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
            faceNp = np.array(gray,'uint8')
            imagePath = 'dataSet/'+filename
            ID = (os.path.split(imagePath)[-1].split('.')[0])

            ID = ID[1:7]
            ID = int(ID)
            Faces.append(faceNp)
            Ids.append(ID)
            filenames.append(filename)
    Ids = np.array(Ids)
    print Ids
    recognizerEigen.train(Faces,Ids)
    recognizerEigen.save('recognizerData/EigenData.yml')

    recognizerFisher.train(Faces,Ids)
    recognizerFisher.save('recognizerData/FisherData.yml')

    recognizerLBPH.train(Faces,Ids)
    recognizerLBPH.save('recognizerData/LBPHData.yml')

            # '''filenames.append(filename)'''

            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
    # Load an html page with a link to each uploaded file
    return render_template('upload.html', filenames=filenames)

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        debug=True
    )
