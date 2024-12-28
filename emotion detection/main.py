import cv2 #OpenCV, library for computer vision, image processing...
from deepface import DeepFace #Deeplearning facial recognition

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +"haarcascade_frontalface_default.xml") #pre-trained model from cv2

video = cv2.VideoCapture(0,cv2.CAP_DSHOW) #capture webcam, first arg is for which cam usage, second arg is for backend.

if not video.isOpened():
    raise IOError("Cannot open webcam")

while video.isOpened():
    _, frame = video.read() #captures 1 frame from video stream, returns a boolean and a numpy array.

    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) #convert one colorspace to another, convert colors to grayscale, used for making emotion detection algorithms faster
    face = face_cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5)  #detect objects in image,

    for x,y,w,h, in face:
        image = cv2.rectangle(frame,(x,y),(x+w,y+h),(89,2,236),6) #draw a rectangle
        try:
            analyze = DeepFace.analyze(frame,actions=["emotion"])
            cv2.putText(image,analyze[0]["dominant_emotion"],(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(224,77,176),2) #
            print(analyze[0]["dominant_emotion"])
            # analyze = DeepFace.analyze(frame,actions=["race"])
            # cv2.putText(image,analyze[0]["race"],(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(224,77,176),2)
        #     analyze = DeepFace.analyze(frame,actions=["age"])
        #     age=str(analyze[0]["age"])
        #     cv2.putText(image,age,(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(224,77,176),2)
            # analyze = DeepFace.analyze(frame,actions=["race"])
            # race = str(analyze[0]["race"])
            # cv2.putText(image,race,(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(224,77,176),2)
        except:
            print("no face")



    cv2.imshow("video",frame) #display video frame.
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

video.release() #release camera resources.
cv2.destroyAllWindows()