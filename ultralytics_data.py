import cv2
import numpy as np
import cv2
import qrCode as qr
import cube
from tqdm import tqdm
import os
import random

def parseRawToTraining(path, color_name, color_class, starting_index):
    #steps
    #for image in raw folder
        #read image
        #find qr code
        #if found:
            #remove qr code from image
            #save corresponding masked image
            #save data to text file
        #else:
            #continue

    img_index = 0
    missing_multiple = 0   
    training = 0
    validation = 0
    
    for filename in tqdm(os.listdir(path), desc="progress on "+color_name+" class"):
        # for filename in os.listdir(path):
        #input rgb image
        f = os.path.join(path, filename)
        img = cv2.imread(f)
        
        #search for qr code
        xyz_cords, qr_pixel_coords, _, tvec, rmat =  qr.qrCodeDetect(img)
        
        #if found
        if len(xyz_cords) > 0:
        
        #mask qrcode to white
            qr_mask = np.zeros((img.shape[0], img.shape[1]))
            
            qr.showBox(qr_mask, qr_pixel_coords)
            #mask interior of qr code polygon to white
            rows_with_line = np.any(qr_mask == 255, axis=1)

            leftmost_255 = np.argmax(qr_mask==255, axis = 1)
            rightmost_255 = qr_mask.shape[1] - np.argmax(np.flip(qr_mask == 255, axis = 1), axis = 1) - 1

            for ind, row in enumerate(rows_with_line):
                if row:
                    for j in range(leftmost_255[ind], rightmost_255[ind]):
                        img[ind][j] = [225,225,225]
                    
            #get cube location in the pciture space
            _, cube_top_pixels, _, cube_tvec, cube_rmat = cube.cubeLocator(rmat, tvec)
            
            bottom_pixels = cube.cubeBottom(cube_rmat, cube_tvec)
            
            #error check for valid projection
            #top left and right of qr code
            top_l_qr = qr_pixel_coords[0]
            top_r_qr = qr_pixel_coords[1]
            
            #right shift
            qr.showBox(img, cube_top_pixels)
            qr.showBox(img, bottom_pixels)
            
            #top left of bottom face of the cube
            top_l_bottom_cube = bottom_pixels[0]
            
            #distance
            dist = np.sqrt((top_l_bottom_cube[0] - top_r_qr[0])**2 + (top_l_bottom_cube[1] - top_r_qr[1])**2)
            
            #distance limit
            dist_qr_top = np.sqrt((top_r_qr[0]-top_l_qr[0])**2 + (top_r_qr[1]-top_l_qr[1])**2)
            limit = ((qr.D/qr.QR_DIMENSION)*dist_qr_top) + 20
            
            #check if distance is greater than limit
            if dist > limit:
                continue
            #continue if true

            #determine which cube points on the bottom are hidden
            #create binary mask of top face
            top_mask = np.zeros((img.shape[0], img.shape[1]))
            qr.showBox(top_mask, cube_top_pixels)
            rows_with_line = np.any(top_mask == 255, axis=1)

            leftmost_255 = np.argmax(top_mask==255, axis = 1)
            rightmost_255 = top_mask.shape[1] - np.argmax(np.flip(top_mask == 255, axis = 1), axis = 1) - 1

            for ind, row in enumerate(rows_with_line):
                if row:
                    for j in range(leftmost_255[ind], rightmost_255[ind]):
                        top_mask[ind][j] = 255
            
            #look for points on bottom face that are projected onto top plane
            count = 0
            visible = []
            out_of_bounds = False
            for pair in bottom_pixels:
                #error check out of bounds
                if pair[0] >= img.shape[0] or pair[1] >= img.shape[1]:
                    out_of_bounds = True
                    break
                
                if top_mask[pair[0]][pair[1]] == 255:
                    visible.append("0")
                    count += 1
                else:
                    visible.append("1")
             
            #handle error check for out of bounds
            if out_of_bounds:
                continue
            
            if count > 1:
                missing_multiple += 1        
            #get center point and width and height of 2d bounding box
            centroidX, centroidY, width, height = cube.cubeOutline(cube_top_pixels, bottom_pixels)
            
            #save all training data
            final_img_ind = img_index + starting_index
            ind_str = str(final_img_ind)
            pad_length = 6 - len(ind_str)
            file_str = '0'*pad_length + ind_str
            
            #save to training or testing
            r = random.random()
            save_path = "/home/jared/datasets"
            if r < .85:
                x = "/training/"
                training += 1
            else:
                x = "/val/"
                validation += 1
            
            # cv2.imwrite(save_path+"/images"+x+file_str+".png", img)
            
            # #save data about class and position
            # with open(save_path+"/labels"+x+file_str+".txt", "w") as file:
            #     file.write(str(color_class)+ " ")
                
            #     #all data is normalixed to be between 0 and 1
            #     #centroids and w/h
            #     file.write(str(centroidX/img.shape[0])+ " ")
            #     file.write(str(centroidY/img.shape[1])+ " ")
            #     file.write(str(width/img.shape[0])+ " ")
            #     file.write(str(height/img.shape[1])+ " ")
                
            #     #write top pixels
            #     for pair in cube_top_pixels:
            #         file.write(str(pair[0]/img.shape[0]) + " ")
            #         file.write(str(pair[1]/img.shape[1]) + " ")
                    
            #         #all top points are visible so we write true after each pair
            #         file.write("1 ")
                    
            #     #write bottom pixels
            #     for ind, pair in enumerate(bottom_pixels):
            #         file.write(str(pair[0]/img.shape[0]) + " ")
            #         file.write(str(pair[1]/img.shape[1]) + " ")
                    
            #         #writes the visibility of that pair
            #         file.write(visible[ind] + " ")
                    
            img_index+=1
    
    print("completed "+str(img_index)+" images for "+color_name+" class")
    print(str(missing_multiple) + " images had more than one occluded point")
    print(str(training) + " training images, " + str(validation) + " validation images")
    return img_index + starting_index        
if __name__ == "__main__":
    colors = ["red", "blue", "green"]
    numbers = [0, 1, 2]
    
    img_index = 0
    for ind, color in enumerate(colors):
        # path = "/home/jared/SeniorDesign/images/raw_images/"+color+"/rgb"
        path = "images/raw_images/"+color+"/rgb"

        img_index = parseRawToTraining(path, color, numbers[ind], img_index)