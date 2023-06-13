from unittest import result

from utils import *
import imutils
import numpy as np
import cv2
from math import ceil
from model import CNN_Model
from collections import defaultdict
import sys

import tkinter as tk
from PIL import Image, ImageTk

def get_x(s):
    return s[1][0]

da = read_da_from_file('da.json')

def get_y(s):
    return s[1][1]


def get_h(s):
    return s[1][3]


def get_x_ver1(s):
    s = cv2.boundingRect(s)
    return s[0] * s[1]

def crop_image(img):
    # convert image from BGR to GRAY to apply canny edge detection algorithm
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # remove noise by blur image
    blurred = cv2.GaussianBlur(gray_img, (5, 5), 0)

    # apply canny edge detection algorithm
    img_canny = cv2.Canny(blurred, 100, 200)

    # find contours
    cnts = generate_contours(img_canny)

    ans_blocks = []
    x_old, y_old, w_old, h_old = 0, 0, 0, 0
    # ensure that at least one contour was found
    if len(cnts) > 0:
        # sort the contours according to their size in descending order
        cnts = sorted(cnts, key=get_x_ver1)

        # loop over the sorted contours
        for i, c in enumerate(cnts):
            x_curr, y_curr, w_curr, h_curr = cv2.boundingRect(c)

            if w_curr * h_curr > 100000:
                # check overlap contours
                check_xy_min = x_curr * y_curr - x_old * y_old
                check_xy_max = (x_curr + w_curr) * (y_curr + h_curr) - (x_old + w_old) * (y_old + h_old)

                # if list answer box is empty
                if len(ans_blocks) == 0:
                    ans_blocks.append(
                        (gray_img[y_curr:y_curr + h_curr, x_curr:x_curr + w_curr], [x_curr, y_curr, w_curr, h_curr]))
                    # update coordinates (x, y) and (height, width) of added contours
                    x_old = x_curr
                    y_old = y_curr
                    w_old = w_curr
                    h_old = h_curr
                elif check_xy_min > 20000 and check_xy_max > 20000:
                    ans_blocks.append(
                        (gray_img[y_curr:y_curr + h_curr, x_curr:x_curr + w_curr], [x_curr, y_curr, w_curr, h_curr]))
                    # update coordinates (x, y) and (height, width) of added contours
                    x_old = x_curr
                    y_old = y_curr
                    w_old = w_curr
                    h_old = h_curr
        # sort ans_blocks according to x coordinate
        sorted_ans_blocks = sorted(ans_blocks, key=get_x)

    """Get answer dots contours"""
    ans_dots = []

    # thresh_gauss = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,13,2)
    # thresh_mean = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,13,2)
    thresh_simple = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    cnts = generate_contours(thresh_simple)

    if len(cnts) > 0:
        cnts = sorted(cnts, key=get_x_ver1)
        width, height, *_ = img.shape
        for i, c in enumerate(cnts):
            # compute the bounding box of the contour, then use the
            # bounding box to derive the aspect ratio
            # boundingRect fins a straight (non-rotated) rectangle that bounds the countour
            # (x,y) is the top-left coordinate of the rectangle and (w,h) are its width and height
            (x, y, w, h) = cv2.boundingRect(c)
            ar = w / float(h)
            # taking the area of our thresholds will help us eliminate the numbers
            # in front of the bubbles like '10' and '6'
            area = cv2.contourArea(c)
            # area is crucial to get the right contours. You will probably need to adjust these parameters
            # my photos were taken from about 1.5 feet above the piece of paper, with the paper taking up
            # most of the photo
            if y >= height*0.29 and w >= 8 and w <= 20 and h >= 8 and h <= 20 and ar >= 0.5 and ar <= 1.35 and area >= 150:
                ans_dots.append(c)

    return sorted_ans_blocks, ans_dots


def process_ans_blocks(ans_blocks):
    """
        this function process 2 block answer box and return a list answer has len of 200 bubble choices
        :param ans_blocks: a list which include 2 element, each element has the format of [image, [x, y, w, h]]
    """
    list_answers = []
    for ans_block in ans_blocks:
        ans_block_img = np.array(ans_block[0])

        offset1 = ceil(ans_block_img.shape[0] / 6)
        for i in range(6):
            box_img = np.array(ans_block_img[i * offset1:(i + 1) * offset1, :])
            height_box = box_img.shape[0]

            box_img = box_img[14:height_box - 14, :]
            offset2 = ceil(box_img.shape[0] / 5)
            for j in range(5):
                list_answers.append(box_img[j * offset2:(j + 1) * offset2, :])

    return list_answers


def process_list_ans(list_answers):
    list_choices = []
    offset = 44
    start = 32
    for answer_img in list_answers:
        for i in range(4):
            bubble_choice = answer_img[:, start + i * offset:start + (i + 1) * offset]
            bubble_choice = cv2.threshold(bubble_choice, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

            bubble_choice = cv2.resize(bubble_choice, (28, 28), cv2.INTER_AREA)
            bubble_choice = bubble_choice.reshape((28, 28, 1))
            list_choices.append(bubble_choice)

    if len(list_choices) != 480:
        raise ValueError("Length of list_choices must be 480")
    return list_choices


def map_answer(idx):
    if idx % 4 == 0:
        answer_circle = '0'
    elif idx % 4 == 1:
        answer_circle = '1'
    elif idx % 4 == 2:
        answer_circle = '2'
    elif idx % 4 == 3:
        answer_circle = '3'
    else:
        answer_circle = ' '
    return answer_circle


def get_answers(list_answers):
    results = defaultdict(list)
    model = CNN_Model('weight.h5').build_model(rt=True)
    list_answers = np.array(list_answers)
    scores = model.predict_on_batch(list_answers / 255.0)
    for idx, score in enumerate(scores):
        question = idx // 4

        # score [unchoiced_cf, choiced_cf]
        if score[1] > 0.9:  # choiced confidence score > 0.9
            chosed_answer = map_answer(idx)
            results[question + 1].append(chosed_answer)
    return results


def scores(results, x=0):
    for k, v in results.items():
        for i, j in da.items():
            if k == int(i) and v == j:
                x += 1
    return x

window_width = 1080
window_height = 720

if __name__ == '__main__':
    path = sys.argv[1]
    img = cv2.imread(path)
    list_ans_boxes, list_ans_dots = crop_image(img)
    list_ans = process_ans_blocks(list_ans_boxes)
    list_ans = process_list_ans(list_ans)
    answers = get_answers(list_ans)
    score = scores(answers)
    diem = score * 0.25
    # print(da)
    # print(answers)
    print(diem)

    # Create a GUI window
    window = tk.Tk()
    window.title("Image Processing")
    window.geometry("1200x720")
    window.resizable(False, False)

    # Load the input image
    input_image = Image.open(path)
    
    cv2.drawContours(img, list_ans_dots, -1, (255,0,0), 3)

    # Convert the images to Tkinter format
    output_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB for PIL
    output_image = Image.fromarray(img)

    # Resize the images to fit the window
    input_image = input_image.resize((540, window_height), Image.ANTIALIAS)
    output_image = output_image.resize((540, window_height), Image.ANTIALIAS)

    # Convert the images to Tkinter format
    input_image_tk = ImageTk.PhotoImage(input_image)
    output_image_tk = ImageTk.PhotoImage(output_image)

    # Create image panels
    input_panel = tk.Label(window, image=input_image_tk)
    output_panel = tk.Label(window, image=output_image_tk)

    # Create a label to display the "diem" variable
    diem_label = tk.Label(window, text="Điểm: {:.2f}".format(diem), font=("Arial", 20, "bold"))
    diem_label.pack(side="bottom", pady=10)


    # Add the image panels to the GUI window
    input_panel.pack(side="left", padx=10, pady=10)
    output_panel.pack(side="right", padx=10, pady=10)

    # Start the GUI event loop
    window.mainloop()
