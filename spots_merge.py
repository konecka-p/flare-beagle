import math
from astropy.io import fits
import matplotlib.pyplot as plt
import glob
import cv2
import numpy as np
from scipy.interpolate import lagrange


def dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def create_circular_mask(shape, center, radius):
    h, w = shape
    y, x = np.ogrid[:h, :w]
    circular_mask = np.sqrt((x - center[0]) ** 2 + (y-center[1]) ** 2) <= radius

    return circular_mask


def coord_system_rotation(cnt, angle):
    c, s = math.cos(angle), math.sin(angle)

    # v = np.array((c, s, -s, c))
    v = np.array((c, -s, s, c))
    v = v.reshape((2, 2))

    new_cnt = cnt.copy()
    new_cnt = np.dot(new_cnt, v)

    return new_cnt.astype('int32')


def preprocessing(fits_file):
    norm_img = np.uint8(cv2.normalize(fits_file[1].data, None, 0, 255, cv2.NORM_MINMAX))

    # Radius of the Sun’s image in pixels
    r_sun = fits_file[1].header['r_sun']

    # location of disk center in x and y directions on image
    crpix = (fits_file[1].header['crpix1'], fits_file[1].header['crpix2'])

    mask = create_circular_mask(norm_img.shape, crpix, r_sun)

    masked_img = norm_img.copy()
    masked_img[~mask] = 0

    blur = cv2.medianBlur(masked_img, 7)

    # Cреднее значение плюс стандартное отклонение, умноженное на три / three sigma rule
    threshold = np.mean(blur) + 3 * np.std(blur)

    thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((4, 4)), iterations=1)

    return thresh


def get_sunspot(cnt):
    M = cv2.moments(cnt)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    sunspot = {'center': (cX, cY), 'cnt': cnt}

    return sunspot


def get_close_spots(sunspots):
    close_spots = {}

    for i in range(len(sunspots) - 1):
        for j in range(i + 1, len(sunspots)):
            center_1 = sunspots[i]['center']
            center_2 = sunspots[j]['center']

            if dist(center_1, center_2) < 500:
                if center_1[0] < center_2[0]:
                    s1 = i
                    s2 = j
                elif center_1[0] > center_2[0]:
                    s1 = j
                    s2 = i
                elif center_1[0] == center_2[0]:
                    if center_1[1] < center_2[1]:
                        s1 = i
                        s2 = j
                    else:
                        s1 = j
                        s2 = i

                a = math.atan2(sunspots[s2]['center'][1] - sunspots[s1]['center'][1],
                               sunspots[s2]['center'][0] - sunspots[s1]['center'][0])
                cnt_1 = sunspots[s1]['cnt']
                cnt_2 = sunspots[s2]['cnt']

                new_cntL = coord_system_rotation(cnt_1, a)
                new_cntR = coord_system_rotation(cnt_2, a)

                rightmost_l = new_cntL[new_cntL[:, :, 0].argmax()][0]
                leftmost_r = new_cntR[new_cntR[:, :, 0].argmin()][0]

                dist_x = leftmost_r[0] - rightmost_l[0]

                if abs(dist_x) < 15:
                    topmost_l = new_cntL[:, :, 1].argmax()
                    bottommost_l = new_cntL[:, :, 1].argmin()

                    topmost_r = new_cntR[:, :, 1].argmax()
                    bottommost_r = new_cntR[:, :, 1].argmin()

                    close_spots[(s1, s2)] = [topmost_l, bottommost_l, topmost_r, bottommost_r]

    return close_spots


def get_actual_id(id, sunspots_history):
    while id != sunspots_history[id]:
        id = sunspots_history[id]

    return id


def get_cnt_piece(cnt, start, end, direction):
    piece = []
    ids = []

    if direction == 'cw':
        if (start - end) < 0:
            for p in range(start, 0, -1):
                piece.append(cnt[p])
                ids.append(p)
            for p in range(0, end + 1):
                piece.append(cnt[p])
                ids.append(p)
        else:
            for p in range(start, len(cnt)):
                piece.append(cnt[p])
                ids.append(p)
            for p in range(0, end+1):
                piece.append(cnt[p])
                ids.append(p)

    return np.array(ids), np.array(piece)


def merge_close(sunspots, close_spots, img, sunspots_history):

    for cs in close_spots:
        actual_id = [get_actual_id(sunspots_history[cs[0]], sunspots_history),
                     get_actual_id(sunspots_history[cs[1]], sunspots_history)]

        spot_one = sunspots[actual_id[0]]
        spot_two = sunspots[actual_id[1]]

        topmost_l = close_spots[cs][0]
        bottommost_l = close_spots[cs][1]

        topmost_r = close_spots[cs][2]
        bottommost_r = close_spots[cs][3]

        piece1 = get_cnt_piece(spot_one['cnt'], topmost_l, bottommost_l, 'cw')[0]
        piece2 = get_cnt_piece(spot_two['cnt'], bottommost_r, topmost_r, 'cw')[0]
        piece2 = piece2[::-1]

        union_points = []

        for p1 in piece1:
            for p2 in piece2:
                d = dist(spot_one['cnt'][p1][0], spot_two['cnt'][p2][0])
                if d < 25:
                    union_points.append((p1, p2))

        if len(union_points) > 2:

            # neighbors_one = get_neighbors(spot_one['cnt'], topmost_l, 'ccw', 100)
            # neighbors_two = get_neighbors(spot_two['cnt'], topmost_r, 'cw', 100)

            # Изменение контура
            up1 = union_points[0]
            up2 = union_points[-1]

            new_cnt = get_cnt_piece(spot_one['cnt'], up2[0], up1[0], 'cw')[1]
            new_cnt = np.concatenate((new_cnt, get_cnt_piece(spot_two['cnt'], up1[1], up2[1], 'cw')[1]))

            cv2.drawContours(img, [new_cnt], -1, (150, 150, 150), 2)

            sunspots_history[actual_id[0]] = sunspots_history[actual_id[1]] = len(sunspots)
            sunspots_history = np.append(sunspots_history, len(sunspots_history))

            sunspots[len(sunspots_history)-1] = get_sunspot(new_cnt)

    return img



if __name__ == "__main__":
    plt.ion()
    # files = glob.glob("JSOC_20200215_259/*.image_lev1.fits")
    files = glob.glob("downloads/2013_5m/*.image_lev1.fits")
    # files = glob.glob("downloads/2013_12s/*.image_lev1.fits")
    # files = glob.glob("downloads/aia/*.image_lev1.fits")


    for i in range(1, len(files), 1):

        f = fits.open(files[i])
        f.verify("silentfix")

        thresh = preprocessing(f)

        cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = [cnt for cnt in cnts if cv2.contourArea(cnt) >= 500]

        sunspots = {}

        for i, cnt in enumerate(cnts):
            sunspots[i] = get_sunspot(cnt)

        sunspots_history = np.arange(0, len(sunspots))

        close_spots = get_close_spots(sunspots)
        merged = merge_close(sunspots, close_spots, thresh.copy(), sunspots_history)

        # al = cv2.bitwise_or(diff, prev_diff)

        plt.subplot(2, 1, 1)
        plt.imshow(thresh, origin='lower')

        plt.subplot(2, 1, 2)
        plt.imshow(merged, origin='lower')

        plt.show()

        plt.pause(10)