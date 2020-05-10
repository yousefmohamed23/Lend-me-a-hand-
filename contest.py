# Function to remove background

learningRate = 0

def removeBG(image):
    fgmask = bgModel.apply(image, learningRate=learningRate)
    kernel = np.ones((3, 3), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    res = cv2.bitwise_and(image, image, mask=fgmask)
    return res

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


