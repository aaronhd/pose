#!/usr/bin/env python
import numpy as np
import cv2, time, sys, freenect

# NOTE: This is no longer going to be used
# Modified from: https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_calib3d/py_calibration/py_calibration.html
# Data checked with http://vision.in.tum.de/data/datasets/rgbd-dataset/file_formats

dims = (9, 6) 					# 9x6 chessboard
boards = 5						# number of boards to be collected
npoints = dims[0] * dims[1]		# Number of points on chessboard
successes = 0					# Number of successful collections

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objectpoints = np.zeros((9*6,3), np.float32)
objectpoints[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

print("Preparing to calculate camera intrinsics...")
time.sleep(1)

print("Press the spacebar to collect an image")

# Make a general-purpose frame
cv2.namedWindow('Calibration')

while True and successes != boards:
	k = cv2.waitKey()
	capture = None

	if k%256 == 32:
		# Capture an image
		(image, _) = freenect.sync_get_video()
		# Create a grayscale image
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		# Attempt to find the chessboard corners
		ret, corners = cv2.findChessboardCorners(gray, dims)

		# If found, add object points, image points (after refining them)
		if ret:
			print("Found frame {0}".format(successes+1))
			objpoints.append(objectpoints)

			cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
			imgpoints.append(corners[0])

	        # Draw and display the corners
			cv2.drawChessboardCorners(image, dims, corners, True)
			cv2.imwrite("output/calibration-images/calibration"+str(dims[0])+"x"+str(dims[1])+ "-"+str(successes+1)+".jpg", image)
			cv2.imshow('Calibration', image)
			successes += 1
		else:
			cv2.imshow('Calibration', image)
	elif k%256 == 27:
		cv2.destroyAllWindows()
		sys.exit()	

cv2.destroyAllWindows()
print("All frames found. Starting calibration....")

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(np.array(objectpoints), imgpoints, gray.shape[::-1],None,None)

img = cv2.imread("output/calibration-images/calibration"+str(dims[0])+"x"+str(dims[1])+"-1.jpg")
h,  w = img.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

np.savetxt("output/intrinsics" + str(dims[0])+"x"+str(dims[1]) + ".txt", newcameramtx)
np.savetxt("output/distortion" + str(dims[0])+"x"+str(dims[1]) + ".txt", dist)

print("Calibration complete. Intrinisics and distortion saved to output directory")
# print("Starting mapping and displaying undistorted view...")

# cv2.namedWindow('Undistorted')

# # undistort
# mapx,mapy = cv2.initUndistortRectifyMap(mtx,dist,None,newcameramtx,(w,h),5)
# while(2):
# 	capture = cv2.VideoCapture(1)
# 	_, image = capture.read()
# 	image = cv2.remap(image,mapx,mapy,cv2.INTER_LINEAR)
# 	cv2.imshow("Undistorted", image)

# 	c = cv2.waitKey()
# 	if (c%256 == 112):		# Enter 'p' key to pause for some time
# 		cv.WaitKey(2000)
# 	elif c%256 == 27:		# Enter esc key to exit
# 		break

print("Exiting")
sys.exit()
