import numpy as np 
import cv2 as cv
import glob 
import os 

chessboardSize = (10, 7)
frameSize = (640, 480)

# terminate criteria 
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# object points in the camera 
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)
objp[:,:2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1, 2)


checker_size = 22
objp = objp * checker_size

# array to store obj points and img points 

objpoints = []
imgpointsL = []
imgpointsR = []

imageLeft = glob.glob('/home/ale/ros2_ws/src/ueye_cam_ros2/ueye_cam/scripts/calibration/stereoLeft/*.png')
imageRight = glob.glob('/home/ale/ros2_ws/src/ueye_cam_ros2/ueye_cam/scripts/calibration/stereoRight/*.png')

imageLeft.sort(key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
imageRight.sort(key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))

for imgLeft, imgRight in zip(imageLeft, imageRight):

    imgL = cv.imread(imgLeft)
    imgR = cv.imread(imgRight)

    grayL = cv.cvtColor(imgL, cv.COLOR_BGR2GRAY)
    grayR = cv.cvtColor(imgR, cv.COLOR_BGR2GRAY)

    # Find corners
    retL, cornersL = cv.findChessboardCorners(grayL, chessboardSize, None)
    retR, cornersR = cv.findChessboardCorners(grayR, chessboardSize, None)

    # add object points 
    if retL and retR == True: 

        objpoints.append(objp)

        cornersL = cv.cornerSubPix(grayL, cornersL, (11, 11), (-1, -1), criteria)
        imgpointsL.append(cornersL)

        cornersR = cv.cornerSubPix(grayR, cornersR, (11, 11), (-1, -1), criteria)
        imgpointsR.append(cornersR)

        cv.drawChessboardCorners(imgL, chessboardSize, cornersL, retL)
        cv.imshow("Chessboard Left", imgL)

        cv.drawChessboardCorners(imgR, chessboardSize, cornersR, retR)
        cv.imshow("Chessboard Right", imgR)

        cv.waitKey(1000)

cv.destroyAllWindows()

# Calibration 

retL, cameraMatrixL, distL, rvecsL, tvecsL = cv.calibrateCamera(objpoints, imgpointsL, frameSize, None, None)
heightL, widthL, channelsL = imgL.shape
newCameraMatrixL, roi_L = cv.getOptimalNewCameraMatrix(cameraMatrixL, distL, (widthL, heightL), 1, (widthL, heightL))

retR, cameraMatrixR, distR, rvecsR, tvecsR = cv.calibrateCamera(objpoints, imgpointsR, frameSize, None, None)
heightR, widthR, channelsR = imgR.shape
newCameraMatrixR, roi_R = cv.getOptimalNewCameraMatrix(cameraMatrixR, distR, (widthR, heightR), 1, (widthR, heightR))

# Stereo 

flags = 0 
flags |= cv.CALIB_FIX_INTRINSIC

criteria_stero = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

retStereo, newCameraMatrixL, distL, newCameraMatrixR, distR, rot, trans, essentialMatrix, foundamentalMatrix = cv.stereoCalibrate(objpoints, imgpointsL, imgpointsR, newCameraMatrixL, distL, newCameraMatrixR, distR, frameSize)

# Rectification 
rectifyScale = 1
rectL, rectR, projMatrixL, projMatrixR, Q, roi_L, roi_R = cv.stereoRectify(newCameraMatrixL, distL, newCameraMatrixR, distR, grayL.shape[::-1], rot, trans, rectifyScale, (0,0))

stereoMapL = cv.initUndistortRectifyMap(newCameraMatrixL, distL, rectL, projMatrixL, grayL.shape[::-1], cv.CV_16SC2)
stereoMapR = cv.initUndistortRectifyMap(newCameraMatrixR, distR, rectR, projMatrixR, grayR.shape[::-1], cv.CV_16SC2)

print("Saving paramters...")

cv_file = cv.FileStorage('StereoMap.xml', cv.FILE_STORAGE_WRITE)

cv_file.write('stereoMapL_x', stereoMapL[0])
cv_file.write('stereoMapL_y', stereoMapL[1])
cv_file.write('stereoMapR_x', stereoMapR[0])
cv_file.write('stereoMapR_y', stereoMapR[1])

cv_file.release()

# Save to TXT file
with open('stereo_calibration_params.txt', 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("STEREO CAMERA CALIBRATION PARAMETERS\n")
    f.write("=" * 80 + "\n\n")
    
    # Left Camera Parameters
    f.write("LEFT CAMERA PARAMETERS:\n")
    f.write("-" * 80 + "\n")
    f.write(f"Reprojection Error: {retL:.6f}\n\n")
    f.write("Camera Matrix:\n")
    f.write(f"{cameraMatrixL}\n\n")
    f.write("Distortion Coefficients:\n")
    f.write(f"{distL.ravel()}\n\n")
    f.write("Optimal Camera Matrix:\n")
    f.write(f"{newCameraMatrixL}\n\n")
    
    # Right Camera Parameters
    f.write("RIGHT CAMERA PARAMETERS:\n")
    f.write("-" * 80 + "\n")
    f.write(f"Reprojection Error: {retR:.6f}\n\n")
    f.write("Camera Matrix:\n")
    f.write(f"{cameraMatrixR}\n\n")
    f.write("Distortion Coefficients:\n")
    f.write(f"{distR.ravel()}\n\n")
    f.write("Optimal Camera Matrix:\n")
    f.write(f"{newCameraMatrixR}\n\n")
    
    # Stereo Calibration Parameters
    f.write("STEREO CALIBRATION PARAMETERS:\n")
    f.write("-" * 80 + "\n")
    f.write(f"Stereo Reprojection Error: {retStereo:.6f}\n\n")
    
    # Rotation Matrix
    f.write("Rotation Matrix (R):\n")
    f.write(f"{rot}\n\n")
    
    # Translation Vector (baseline)
    f.write("Translation Vector (T):\n")
    f.write(f"{trans.ravel()}\n\n")
    
    # Calculate baseline (Euclidean distance)
    baseline = np.linalg.norm(trans)
    f.write(f"Baseline (distance between cameras): {baseline:.6f} mm\n\n")
    
    # Essential Matrix
    f.write("Essential Matrix:\n")
    f.write(f"{essentialMatrix}\n\n")
    
    # Fundamental Matrix
    f.write("Fundamental Matrix:\n")
    f.write(f"{foundamentalMatrix}\n\n")
    
    # Rectification Parameters
    f.write("RECTIFICATION PARAMETERS:\n")
    f.write("-" * 80 + "\n")
    f.write("Left Rectification Matrix:\n")
    f.write(f"{rectL}\n\n")
    f.write("Right Rectification Matrix:\n")
    f.write(f"{rectR}\n\n")
    f.write("Left Projection Matrix:\n")
    f.write(f"{projMatrixL}\n\n")
    f.write("Right Projection Matrix:\n")
    f.write(f"{projMatrixR}\n\n")
    f.write("Disparity-to-Depth Mapping Matrix (Q):\n")
    f.write(f"{Q}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write(f"Number of calibration images used: {len(objpoints)}\n")
    f.write(f"Chessboard size: {chessboardSize}\n")
    f.write(f"Square size: {checker_size} mm\n")
    f.write("=" * 80 + "\n")

print("Parameters saved to 'stereo_calibration_params.txt'")

# Verify rectification with last image pair
imgL_rectified = cv.remap(imgL, stereoMapL[0], stereoMapL[1], cv.INTER_LANCZOS4)
imgR_rectified = cv.remap(imgR, stereoMapR[0], stereoMapR[1], cv.INTER_LANCZOS4)

# Draw horizontal lines to check epipolar alignment
for i in range(0, imgL_rectified.shape[0], 50):
    cv.line(imgL_rectified, (0, i), (imgL_rectified.shape[1], i), (0, 255, 0), 1)
    cv.line(imgR_rectified, (0, i), (imgR_rectified.shape[1], i), (0, 255, 0), 1)

combined = np.hstack((imgL_rectified, imgR_rectified))
cv.imshow("Rectified Stereo Pair - Lines should align", combined)
cv.waitKey(0)
cv.destroyAllWindows()
