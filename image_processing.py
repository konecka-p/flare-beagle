import math
from astropy.io import fits
import matplotlib.pyplot as plt
import glob
import cv2
import numpy as np
from scipy import interpolate
from astropy.wcs import WCS


def dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def create_circular_mask(shape, center, radius):
    h, w = shape
    y, x = np.ogrid[:h, :w]
    circular_mask = np.sqrt((x - center[0])**2 + (y-center[1])**2) <= radius

    return circular_mask


def preprocessing(fits_file):
    norm_img = np.uint8(cv2.normalize(fits_file[1].data, None, 0, 255, cv2.NORM_MINMAX))

    # radius of the Sun’s image in pixels
    r_sun = fits_file[1].header['r_sun'] - 50

    # location of disk center in x and y directions on image
    crpix = (fits_file[1].header['crpix1'], fits_file[1].header['crpix2'])

    mask = create_circular_mask(norm_img.shape, crpix, r_sun)
    masked_img = norm_img.copy()
    masked_img[~mask] = 0

    blur = cv2.GaussianBlur(masked_img, (5, 5), 0)

    # three sigma rule
    threshold = np.mean(blur) + 3 * np.std(blur)

    thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)[1]

    return thresh


def get_sunspot(cnt):

    m = cv2.moments(cnt)
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])

    sunspot = {'center': (cx, cy), 'cnt': cnt}
    return sunspot


def coord_system_rotate(cnt, angle):
    c, s = math.cos(angle), math.sin(angle)

    # v = np.array((c, s, -s, c))
    v = np.array((c, -s, s, c))
    v = v.reshape((2, 2))

    new_cnt = cnt.copy()
    new_cnt = np.dot(new_cnt, v)

    return new_cnt.astype('int32')


def get_close_spots(sunspots):
    close_spots = {}

    for i in range(len(sunspots) - 1):
        for j in range(i + 1, len(sunspots)):
            center_1 = sunspots[i]['center']
            center_2 = sunspots[j]['center']

            if dist(center_1, center_2) < 500:#1500
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

                new_cntL = coord_system_rotate(cnt_1, a)
                new_cntR = coord_system_rotate(cnt_2, a)

                rightmost_l = new_cntL[new_cntL[:, :, 0].argmax()][0]
                leftmost_r = new_cntR[new_cntR[:, :, 0].argmin()][0]

                dist_x = leftmost_r[0] - rightmost_l[0]

                if abs(dist_x) < 15: #150
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

def get_neighbors(cnt, point_id, direction, num):
    if direction == 'ccw':
        if point_id - num > 0:
            return cnt[point_id:point_id - num:-3]
        else:
            return np.concatenate((cnt[point_id:0:-3], cnt[0:point_id-num]))

    elif direction == 'cw':
        if (point_id + num) > len(cnt):
            return(np.concatenate((cnt[point_id:len(cnt):3], cnt[:len(cnt)-num:3])))
        else:
            return(cnt[point_id:point_id+num:3])


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


def spline(line, s):
    x_points = []
    y_points = []

    for x in line[:, :, 0]:
        x_points.append(*x)

    for y in line[:, :, 1]:
        y_points.append(*y)
    x = np.array(x_points)
    y = np.array(y_points)

    dist = np.sqrt((x[:-1] - x[1:]) ** 2 + (y[:-1] - y[1:]) ** 2)
    dist_along = np.concatenate(([0], dist.cumsum()))

    spline, u = interpolate.splprep([x, y], u=dist_along, s=0)
    d = np.arange(u[s-1], u[s+1], 0.1)
    # d = np.arange(u[s], u[s+2], 0.1)
    interp_x, interp_y = interpolate.splev(d, spline)

    interp_x = np.rint(interp_x)
    interp_y = np.rint(interp_y)

    return np.array(interp_x), np.array(interp_y)


def merge_close(sunspots, close_spots, img, sunspots_history):
    new_cnts = []
    img_points = img.copy()
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
                if d < 25: #100
                    union_points.append((p1, p2))

        if len(union_points) > 2:

            # Union point indices 
            up1 = union_points[0]
            up2 = union_points[-1]

            # Getting points to draw a spline 
            # -------------------------------------------------------------------------------------

            line_one_1 = get_neighbors(spot_one['cnt'], up1[0], 'ccw', 15)[::-1]
            line_one_2 = get_neighbors(spot_two['cnt'], up1[1], 'cw', 15)
            line_two_1 = get_neighbors(spot_one['cnt'], up2[0], 'cw', 15)[::-1]
            line_two_2 = get_neighbors(spot_two['cnt'], up2[1], 'ccw', 15)

            line_one = np.concatenate((line_one_1, line_one_2))
            line_two = np.concatenate((line_two_1, line_two_2))


            for l in line_two:
                cv2.circle(img_points, (l[0][0], l[0][1]), 1, (150, 150, 150), 2)
            for l in line_one:
                cv2.circle(img_points, (l[0][0], l[0][1]), 1, (150, 150, 150), 2)
            # Spline
            if len(line_one) > 3:
                xnew, ynew = spline(line_one, len(line_one_1))
                l = np.unique(np.array(np.c_[xnew, ynew]), axis=0)
                for i in l:
                    img[int(i[1]), int(i[0])] = 255
                    pass

            if len(line_two) > 3:
                xnew, ynew = spline(line_two, len(line_two_1))
                l = np.unique(np.array(np.c_[xnew, ynew]), axis=0)
                for i in l:
                    img[int(i[1]), int(i[0])] = 255
                    pass

            # -------------------------------------------------------------------------------------

            # Change contour 
            cnt_part_1 = get_cnt_piece(spot_one['cnt'], up2[0], up1[0], 'cw')[1]
            cnt_part_2 = get_cnt_piece(spot_two['cnt'], up1[1], up2[1], 'cw')[1]
            # print(spot_one['cnt'][up1[0]], spot_two['cnt'][up1[1]], line_one[0], line_one[-1])
            # print(np.where(spot_one['cnt'][-1] == line_one))
            new_cnt = np.concatenate((cnt_part_1[1:-1], line_one, cnt_part_2[1:-1], line_two))

            # print(cnt_part_1[-1], line_one[0])
            # new_cnt = get_cnt_piece(spot_one['cnt'], up2[0], up1[0], 'cw')[1]
            # new_cnt = np.concatenate((new_cnt, get_cnt_piece(spot_two['cnt'], up1[1], up2[1], 'cw')[1]))

            # cv2.drawContours(img, [new_cnt], -1, (255, 255, 255), -1)
            # cv2.drawContours(img, [new_cnt], -1, (255, 255, 255), 1)

            new_cnts.append(new_cnt)
            sunspots_history[actual_id[0]] = sunspots_history[actual_id[1]] = len(sunspots)
            sunspots_history = np.append(sunspots_history, len(sunspots_history))

            sunspots[len(sunspots_history)-1] = get_sunspot(new_cnt)

    return img, img_points


import sunpy.visualization.colormaps as cm
sdoaia171 = plt.get_cmap('sdoaia171')


def detect_flare(fits_img_one, fits_img_two):
    spots = []
    # difference between processed images 
    diff = cv2.absdiff(preprocessing(fits_img_two), preprocessing(fits_img_one))

    # morphological operations to remove unnecessary trash 
    diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, np.ones((3, 3)), iterations=2)
    diff = cv2.morphologyEx(diff, cv2.MORPH_CLOSE, np.ones((3, 3)), iterations=1)

    # search for contours with a large area 
    cnts, _ = cv2.findContours(diff.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [cnt for cnt in cnts if cv2.contourArea(cnt) >= 500]

    # if we find something big 
    if len(cnts) > 0:
        x = y = []
        for cnt in cnts:
            m = cv2.moments(cnt)
            cx = int(m["m10"] / m["m00"])
            cy = int(m["m01"] / m["m00"])
            x.append(cx)
            y.append(cy)
        spots.append((int(np.mean(x)), int(np.mean(y))))
    diff.fill(0)
    cv2.drawContours(diff, cnts, -1, (255, 255, 255), -1)
    return spots, diff


def accum(files, spots):
    # al = cv2.bitwise_or(al, diff)
    # print(np.var(img_next)) -- sometimes garbage comes in, you can clean it like this 
    sum_contour = np.zeros((4096, 4096), dtype='uint8')
    print("---", len(files))
    for i in range(0, len(files)):
        f = fits.open(files[i])
        f.verify("silentfix")

        image_prep = preprocessing(f)
        thresh = cv2.morphologyEx(image_prep, cv2.MORPH_CLOSE,
                                   cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,
                                   cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)

        cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # cnts = [cnt for cnt in cnts if cv2.contourArea(cnt) > 150]

        # thresh.fill(0)
        # cv2.drawContours(thresh, cnts, -1, (255, 255, 255), -1)

        sunspots = {}
        sum_contour = cv2.bitwise_or(thresh, sum_contour)
        for i, cnt in enumerate(cnts):
            s = get_sunspot(cnt)
            # print(dist(s['center'], spots[0]) )
            if dist(s['center'], spots[0]) < 500:
                pass
                # sunspots.append(s)
                # cv2.drawContours(sum_contour, [cnt], -1, (255, 255, 255), -1)
    return sum_contour

def hmi_calс(img_hmi, cnt, header_aia, header_hmi):
    aia_wcs = WCS(header_aia)
    hmi_wcs = WCS(header_hmi)


    # a = np.zeros_like((4096, 4096), dtype='uint8')
    a = np.zeros_like(img_hmi)
    for i, p in enumerate(cnt):
        aia_pix2world = aia_wcs.wcs_pix2world(((p[0][0], p[0][1]),), 1)
        new_pix = hmi_wcs.wcs_world2pix(aia_pix2world, 0)

        cv2.circle(img_hmi, (int(new_pix[0][0]), int(new_pix[0][1])), 1, (3000, 3000, 3000), 20)
        # cnt[i] = np.rint(new_pix)

    return img_hmi


if __name__ == "__main__":
    # files_12s = glob.glob("downloads/2013_12s/*.image_lev1.fits")
    # files_12s = glob.glob("downloads/full_flare_12s/*.image_lev1.fits")
    # files_5m = glob.glob("downloads/2013_5m/*.image_lev1.fits")
    # files_hmi = glob.glob("downloads/hmi/*.magnetogram.fits")
