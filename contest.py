# Function to remove background

learningRate = 0

def removeBG(image):
    fgmask = bgModel.apply(image, learningRate=learningRate)
    kernel = np.ones((3, 3), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    res = cv2.bitwise_and(image, image, mask=fgmask)
    return res

#starting camera 
camera = cv2.VideoCapture(0)
camera.set(10, 250)
cv2.namedWindow('trackbar')
cv2.createTrackbar('trh1', 'trackbar', threshold, 100, printThreshold)
	
    while camera.isOpened():
	
        #opens video for user
        ret, frame = camera.read()
		#apply thershold 
        threshold = cv2.getTrackbarPos('trh1', 'trackbar')
		# smoothing filter
        frame = cv2.bilateralFilter(frame, 5, 50, 100)
		# flip the frame horizontally			
        frame = cv2.flip(frame, 1)  
        
	cv2.rectangle(frame, (int(capturingBGregionX * frame.shape[1]), 0), (frame.shape[1], int(capturingBGregionY * frame.shape[0])), (255, 0, 0), 2)
        
	cv2.imshow('background capture', frame)
	if isBgCaptured == 1:  # this part wont run until background captured

            # Applying operations on captured frame to get hand
            img = removeBG(frame)
            img = img[0:int(capturingBGregionY * frame.shape[0]),int(capturingBGregionX * frame.shape[1]):frame.shape[1]]  # clip the ROI
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (blurValue, blurValue), 0)
            ret, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
            if cv2.countNonZero(thresh) != 0:
		nz = np.argwhere(thresh)
		Y, X = nz[0]
		y, x = np.argwhere(nz > 128)[0]
		highest_point_image = cv2.circle(thresh, (X, Y), 5, white, -1)
		cv2.imshow('ori', highest_point_image)
	thresh1 = copy.deepcopy(thresh)
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
            if triggerSwitch is True:
                if isFinishCal is True and cnt <= 2:
                    print(cnt) #number of fingers that is present in frame
        cv2.imshow('output', drawing)
	 # paint interface
    	paintWindow = np.zeros((471, 636, 3)) + 255
    	cv2.namedWindow('Paint', cv2.WINDOW_AUTOSIZE)
	#colors interface
    	x1 = int(capturingBGregionX * frame.shape[1])
	frame = cv2.rectangle(frame, (x1, 50), (x1+40, 70), white, -1)
	frame = cv2.putText(frame, "Clear ", (x1 + 13, 69), cv2.FONT_HERSHEY_PLAIN, 0.9, black, 3, cv2.LINE_AA)

	frame = cv2.rectangle(frame, (x1 + 50, 50), (x1 + 100, 70), colors[0], -1)
	frame = cv2.rectangle(frame, (x1 + 110, 50), (x1 + 160, 70), colors[1], -1)
	frame = cv2.rectangle(frame, (x1 + 170, 50), (x1 + 220, 70), colors[2], -1)
	frame = cv2.rectangle(frame, (x1 + 230, 50), (x1 + 280, 70), colors[3], -1)
	# Aligning the point from the mask with thenactual video capture
	center = (X + int(capturingBGregionX * frame.shape[1]), Y + 10)


	

	#driver function

	#Keyboard Oprations
	k = cv2.waitKey(10)
	if k == 27:  # press ESC to exit
	    camera.release()
	    cv2.destroyAllWindows()
	    break
	elif k == ord('c'):  # press 'c' to capture the empty background
	    bgModel = cv2.createBackgroundSubtractorMOG2(0, backgroundSubThreshold) #assign the model when key is pressed
	    isBgCaptured = 1
	elif k == ord('r'):  # press 'r' to reset the background
	    bgModel = None
	    isBgCaptured = 0

