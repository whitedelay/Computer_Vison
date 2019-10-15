import cv2
import numpy as np
import math
import time


#### For Assignment 1 ####

def image_padding(img, V, H):
    if V == 0 and H == 0:
        return img

    # 1D-horizontal
    if V == 0 and H != 0:
        edge_left = np.zeros((img.shape[0], H))
        edge_right = np.zeros((img.shape[0], H))
        for y in range(img.shape[0]):
            edge_left[y].fill(img[y][0])
            edge_right[y].fill(img[y][-1])
        return np.concatenate((np.concatenate((edge_left, img), axis=1), edge_right), axis=1)

    # 1D-vertical
    elif V != 0 and H == 0:
        edge_up = img[0, :].copy()
        edge_down = img[-1, :].copy()
        for i in range(V - 1):
            edge_up = np.vstack((edge_up, img[0, :].copy()))
            edge_down = np.vstack((edge_down, img[-1, :].copy()))
        return np.vstack((np.vstack((edge_up, img)), edge_down))
    # 2D padding
    else:
        h_padded = image_padding(img, 0, H)
        v_h_padded = image_padding(h_padded, V, 0)
        return v_h_padded


def cross_correlation_1d(img, kernel):
    output = np.zeros(img.shape)
    pad_size = int(kernel.shape[0] / 2)

    # horizontal
    if kernel.ndim == 1:
        img = image_padding(img, 0, pad_size)
        for y in range(output.shape[0]):
            for x in range(output.shape[1]):
                for dx in range(kernel.shape[0]):
                    output[y, x] += kernel[dx] * img[y, x + dx]
                output[y, x] /= 255.0
    # vertical
    else:
        img = image_padding(img, pad_size, 0)
        for y in range(output.shape[0]):
            for x in range(output.shape[1]):
                for dy in range(kernel.shape[0]):
                    output[y, x] += kernel[dy][0] * img[y + dy, x]
                output[y, x] /= 255.0

    return output


def cross_correlation_2d(img, kernel):
    output = np.zeros(img.shape)
    v_pad_size = int(kernel.shape[0] / 2)
    h_pad_size = int(kernel.shape[1] / 2)
    img = image_padding(img, v_pad_size, h_pad_size)

    kernel_idx = [(i, j) for i in range(kernel.shape[0]) for j in range(kernel.shape[1])]
    for y in range(output.shape[0]):
        for x in range(output.shape[1]):
            for (dy, dx) in kernel_idx:
                output[y, x] += kernel[dy, dx] * img[y + dy, x + dx]
            output[y, x] /= 255.0
    return output


def gaussian_function(x, sigma):
    return (1 / pow(2 * math.pi, 1 / 2)) * pow(math.e, -(x * x) / (2 * sigma * sigma))


def get_gaussian_filter_1d(size, sigma):
    # mean = 0
    length = int(size / 2)
    output = np.array([gaussian_function(x, sigma) for x in range(-length, length + 1)])
    # 가우시안의 합은 1
    output = output * (1 / sum(output))

    return output


def get_gaussian_filter_2d(size, sigma):
    # Gaussian은 separable
    row_1d = get_gaussian_filter_1d(size, sigma)
    col_1d = row_1d.reshape(size, 1)

    # nx1 * 1xn = nxn 가우시안 필터
    res = np.outer(col_1d, row_1d)
    # print("* 합은 항상 1 :",sum(sum(res)))
    # print(res)

    return res


#### For Assignment 2 ####

def sobel_filtering(image, axis):
    blurring = np.array([1, 2, 1])
    derivative_1D = np.array([-1, 0, 1])
    if (axis == 0):
        return cross_correlation_1d(255 * cross_correlation_1d(image, blurring.reshape(3, 1)), derivative_1D)
    else:
        return cross_correlation_1d(255 * cross_correlation_1d(image, derivative_1D.reshape(3, 1)), blurring)


def compute_image_gradient(imagepath):
    # time recording
    start = time.time()

    image = cv2.imread(imagepath, cv2.IMREAD_GRAYSCALE)

    # 2-1 Apply the Gaussian filtering to the input image
    image = cross_correlation_2d(image, get_gaussian_filter_2d(7, 1.5))

    # mag, dir 값 포함하는 3차원 np array 생성 - [2][y][x]
    output = np.zeros([2] + list(image.shape))

    # calculating gradient
    xdir_grad = sobel_filtering(255 * image, axis=0)
    ydir_grad = sobel_filtering(255 * image, axis=1)

    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            df_dx = xdir_grad[y, x]
            df_dy = ydir_grad[y, x]
            # direction 계산

            # 1사분면을 양수로.
            dir = math.atan2(-df_dy, df_dx) * (180 / math.pi)
            dir = 180+dir if dir<0 else dir

            # magnitude 계
            mag = math.pow((df_dx * df_dx) + (df_dy * df_dy), 1 / 2)
            # print("mag",mag)

            output[0][y, x] = mag
            output[1][y, x] = dir

    print("computing image gradient Time: ", time.time() - start)

    return output[0], output[1]


def non_maximum_suppression_dir(mag, dir):

    M, N = mag.shape
    # direction to array index pair
    dy = [[0, 0], [-1, 1], [-1, 1], [-1, 1]]
    dx = [[1, -1], [1, -1], [0, 0], [-1, 1]]
    output = mag.copy()

    for i in range(1, M - 1):
        for j in range(1, N - 1):
            # quantize
            q = int((22.5+dir[i, j]) / 45)%4  # 0 ~ 3 values
            # suppression
            if (mag[i, j] <= mag[i+dy[q][0],j+dx[q][0]]) or (mag[i, j] <= mag[i+dy[q][1],j+dx[q][1]]):
                output[i, j] = 0


    cv2.imshow("image suppressed", output)
    cv2.waitKey()

    return