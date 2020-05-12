import cv2
import numpy as np
import math
import copy
from collections import deque
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys

#flags for event of clicking gui buttons
background_capture = 0
reset_background = 0
exit_app = 0
path = ""
name =""

def draw():

    isBgCaptured = 0  # flag for whether the background captured

    # Arrays to store all colored points where finger points
    bpoints = [deque(maxlen=512)]
    gpoints = [deque(maxlen=512)]
    rpoints = [deque(maxlen=512)]
    ypoints = [deque(maxlen=512)]
    bindex = 0
    gindex = 0
    rindex = 0
    yindex = 0
    colorIndex = 0
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]
    black = (0, 0, 0)
    white = (255, 255, 255)
    
    # Function to remove background
    def removeBG(image):
        fgmask = bgModel.apply(image, learningRate=0)  #apply the model which subtracts the background
        kernel = np.ones((3, 3), np.uint8)
        fgmask = cv2.erode(fgmask, kernel, iterations=1)
        res = cv2.bitwise_and(image, image, mask=fgmask) #the output here will be any object added infront of the background
        return res

    # Function to draw contours of fingers and count them
    #The counting is done by calculating the number of defects in the contour + 1 which is the spacing between the fingers
    def calculateFingers(res, drawing):
       #  convexity defect
        hull = cv2.convexHull(res, returnPoints=False)
        if len(hull) > 3:
            defects = cv2.convexityDefects(res, hull)
            if type(defects) != type(None):  # avoid crashing.   (BUG not found)
                    
                count = 0
            
                for i in range(defects.shape[0]):  # calculate the angle
                    s, e, f, d = defects[i][0]
                    start = tuple(res[s][0])
                    end = tuple(res[e][0])
                    far = tuple(res[f][0])
                    a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                    b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                    c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
                    angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))  # cosine theorem
                    if angle <= math.pi / 2:  # angle less than 90 degree, treat as fingers
                        count += 1
                    cv2.circle(drawing, far, 8, [211, 84, 0], -1)
                return True, count
        return False, 0

    #starting camera 
    camera = cv2.VideoCapture(0)
    camera.set(10, 250)
    global path
    path = path+"/"+name+".avi"
    vid_cod = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(path, vid_cod, 17.0, (640, 480))
            
    while camera.isOpened():
            
            #opens video for user
            ret, orignal = camera.read()
            frame = orignal
            # smoothing filter
            frame = cv2.bilateralFilter(frame, 5, 50, 100)
            # flip the frame horizontally			
            orignal = cv2.flip(orignal,1)
            frame = cv2.flip(frame, 1)  
            
            #this is the blue frame in which the operations occur and the background is captured
            cv2.rectangle(frame, (int(0.5* frame.shape[1]), 0), (frame.shape[1], int(frame.shape[0])), (255, 0, 0), 2)

            if isBgCaptured == 0:
                cv2.namedWindow('background capture', cv2.WINDOW_NORMAL)
                cv2.resizeWindow('background capture',1080,720)
                cv2.imshow('background capture', frame)
                
            if isBgCaptured == 1:  # this part wont run until background captured

                # Applying operations on captured frame to get hand
                img = removeBG(frame)
                img = img[0:int(frame.shape[0]),int(0.5* frame.shape[1]):frame.shape[1]]  # clip the image
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  #convert to greyscale
                blur = cv2.GaussianBlur(gray, (41,41), 0)
                ret, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)  #apply thresholding, the output is a B&W frame of the hand
                
                #We detect the fingertip by detecting the highest white pixel in the image's y-axis
                if cv2.countNonZero(thresh) != 0:
                    nz = np.argwhere(thresh)
                    Y, X = nz[0]
                    y, x = np.argwhere(nz > 128)[0]   #returns the coordinates of the first white pixel (fingertip)
                    highest_point_image = cv2.circle(thresh, (X, Y), 5, white, -1)
                    
                    
                thresh1 = copy.deepcopy(thresh) #creates a new instance of the image for applying contours
            
                # Getting contours of hand
                _, contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                length = len(contours)
                maxArea = -1
                
                if length > 0:
                    for i in range(length):  # find the biggest contour (according to area)
                        temp = contours[i]
                        area = cv2.contourArea(temp)
                        if area > maxArea:
                            maxArea = area
                            ci = i

                    res = contours[ci]
                    hull = cv2.convexHull(res)
                    drawing = np.zeros(img.shape, np.uint8)
                    cv2.drawContours(drawing, [res], 0, (0, 255, 0), 2)
                    cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 3)

                    isFinishCal, cnt = calculateFingers(res, drawing)
                         

                # paint interface
                paintWindow = np.zeros((471, 636, 3)) + 255
                cv2.namedWindow('Paint', cv2.WINDOW_AUTOSIZE)
                #colors interface
                # x1 stands for start of drawing frame
                x1 = int(0.5* frame.shape[1])
                
                #The following are the boxes which indicate the colour and CLEAR
                frame = cv2.rectangle(frame, (x1, 50), (x1+40, 70), white, -1)
                frame = cv2.putText(frame, "Clear ", (x1 + 13, 69), cv2.FONT_HERSHEY_PLAIN, 0.9, black, 3, cv2.LINE_AA)

                frame = cv2.rectangle(frame, (x1 + 50, 50), (x1 + 100, 70), colors[0], -1)
                frame = cv2.rectangle(frame, (x1 + 110, 50), (x1 + 160, 70), colors[1], -1)
                frame = cv2.rectangle(frame, (x1 + 170, 50), (x1 + 220, 70), colors[2], -1)
                frame = cv2.rectangle(frame, (x1 + 230, 50), (x1 + 280, 70), colors[3], -1)
                # Aligning the point from the mask with thenactual video capture
                center = (X + int(0.5* frame.shape[1]), Y + 10)
                if cnt == 0:   # draw only if the pointer finger is raised

                 # if the user pointer in the interface area
                        if center[1] <= 70:
                                
                            #clear all area
                            if x1 <= center[0] <= x1 + 40: 
                            # Clear All what is drawen in blue frame

                                bpoints = [deque(maxlen=512)]
                                gpoints = [deque(maxlen=512)]
                                rpoints = [deque(maxlen=512)]
                                ypoints = [deque(maxlen=512)]

                                bindex = 0
                                gindex = 0
                                rindex = 0
                                yindex = 0
                            # colors area, maps the location of the points from the frame to the whole image
                            elif x1 + 50 <= center[0] <= x1 + 100:
                                colorIndex = 0  # Blue
                            elif x1 + 110 <= center[0] <= x1 + 160:
                                colorIndex = 1  # Green
                            elif x1 + 170 <= center[0] <= x1 + 220:
                                colorIndex = 2  # Red
                            elif x1 + 230 <= center[0] <= x1 + 280:
                                colorIndex = 3  # Yellow           
                        else:
                            if colorIndex == 0:
                                 bpoints[bindex].appendleft(center)
                            elif colorIndex == 1:
                                 gpoints[gindex].appendleft(center)
                            elif colorIndex == 2:
                                 rpoints[rindex].appendleft(center)
                            elif colorIndex == 3:
                                 ypoints[yindex].appendleft(center)
                                
                else:
                     bpoints.append(deque(maxlen=512))
                     bindex += 1
                     gpoints.append(deque(maxlen=512))
                     gindex += 1
                     rpoints.append(deque(maxlen=512))
                     rindex += 1
                     ypoints.append(deque(maxlen=512))
                     yindex += 1
                
                painter = cv2.circle(frame, (X + int(0.5* frame.shape[1]), Y + 10), 10, (255, 255, 255),2)  #the circle which indicates the fingertip
                points = [bpoints, gpoints, rpoints, ypoints]  #the coordinates of the fingertip in each colour
                
                #the drawing function
                for i in range(len(points)):
                    for j in range(len(points[i])):
                        for k in range(1, len(points[i][j])):
                            if points[i][j][k - 1] is None or points[i][j][k] is None:
                               continue
                            cv2.line(orignal, points[i][j][k - 1], points[i][j][k], colors[i], 5)
                            cv2.line(painter, points[i][j][k - 1], points[i][j][k], colors[i], 5)
                            cv2.line(paintWindow, points[i][j][k - 1], points[i][j][k], colors[i], 5)
                cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
                cv2.resizeWindow('frame',1080,720)
                cv2.imshow('frame', painter)
                cv2.imshow("Paint", paintWindow)
                out.write(orignal)

            #driver function

            #Keyboard Oprations
            k = cv2.waitKey(10)
            global background_capture
            global reset_background
            global exit_app
            if k == 27 or exit_app == 1:  # press ESC to exit
                camera.release()
                out.release()
                cv2.destroyAllWindows()
                exit_app = 0
                break
            elif k == ord('c') or background_capture == 1:  # press 'c' to capture the empty background
                bgModel = cv2.createBackgroundSubtractorMOG2(0, 50) #assign the model when key is pressed
                isBgCaptured = 1
                background_capture = 0
                cv2.destroyAllWindows()
            elif k == ord('r') or reset_background :  # press 'r' to reset the background
                bgModel = None
                isBgCaptured = 0
                cv2.destroyAllWindows()
                reset_background = 0

                
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # The GUI settings
        self.setWindowTitle("Lend Me a Hand")
        self.setGeometry(100,100,500,500)
        self.setFixedSize(500,500)
        qImage = QImage("lendme.jpg")
        sImage = qImage.scaled(500,500)
        back_ground=QPalette()
        back_ground.setBrush(10,QBrush(sImage))
        self.setPalette(back_ground)
        self.setWindowIcon(QIcon("lendme.jpg"))
        self.UiComponents()
        self.show()

    def capture(self):
        global background_capture
        background_capture = 1

    def reset(self):
        global reset_background
        reset_background = 1
    def quit(self):
        global exit_app
        exit_app = 1
    def browse(self):
        global path
        options = QFileDialog.Options()
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        global name
        name = self.videoName.text()
    def UiComponents(self):

        label = QLabel("Your Video's Name : ", self)
        label.setGeometry(30, 30, 150, 50)
        label.setFont(QFont('Helvetica', 10))

        self.videoName = QLineEdit(self)
        self.videoName.setGeometry(200, 40, 200, 30)
        self.videoName.setText("")

        button1 = QPushButton("Choose Video's Saving Location",self)
        button1.clicked.connect(self.browse)
        button1.setStyleSheet("background-color: white")
        button1.setGeometry(30, 100, 250, 40)
        button1.setFont(QFont('Helvetica', 10))

        button2 = QPushButton("Open Camera", self)
        button2.clicked.connect(draw)
        button2.setStyleSheet("background-color: white")
        button2.setGeometry(30, 160, 220, 60)
        button2.setFont(QFont('Helvetica', 10))

        button3 = QPushButton("Capture Empty Background \n and Start Recording", self)
        button3.clicked.connect(self.capture)
        button3.setStyleSheet("background-color: white")
        button3.setGeometry(30, 240, 220, 60)
        button3.setFont(QFont('Helvetica', 10))

        button4 = QPushButton("Save Video", self)
        button4.clicked.connect(self.quit)
        button4.setStyleSheet("background-color: white")
        button4.setGeometry(30, 320, 220, 60)
        button4.setFont(QFont('Helvetica', 10))

        button5 = QPushButton("Reset Background", self)
        button5.clicked.connect(self.reset)
        button5.setGeometry(30, 400, 220, 60)
        button5.setStyleSheet("background-color: white")
        button5.setFont(QFont('Helvetica', 10))





App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec_())





