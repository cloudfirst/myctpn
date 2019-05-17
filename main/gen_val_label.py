import os
import glob
import argparse
import pandas as pd
import xml.etree.ElementTree as ET
import sys
import cv2 as cv
import numpy as np
import scipy.misc
from PIL import Image, ImageDraw
from tqdm import tqdm

sys.path.append(os.getcwd())
from sinobot_ctpn.utils.prepare.utils import orderConvex, shrink_poly

def xml_to_csv(inputpath):
    inputxmlpath = os.path.join(inputpath, './*.xml')
    inputlabelpath = os.path.join(inputpath, "label")
    if not os.path.exists(inputlabelpath):
            os.makedirs(inputlabelpath)
    xml_list = []
    for xml_file in glob.glob(inputxmlpath):
        name = xml_file.split('/')[-1].split('.')[0]
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for member in root.findall('object'):
            value = (int(member[4][0].text), int(member[4][1].text),
                     int(member[4][2].text), int(member[4][1].text),
                     int(member[4][2].text), int(member[4][3].text),
                     int(member[4][0].text), int(member[4][3].text)
                     )
            xml_list.append(value)

        xml_df = pd.DataFrame(xml_list)
        gttxtpath = os.path.join(inputlabelpath, './gt_{}.txt')
        xml_df.to_csv(gttxtpath.format(name), index=None)
        xml_list = []

    return xml_df

def split_label(inputpath, OUTPUT):
    MAX_LEN = 1200
    MIN_LEN = 600

    im_fns = os.listdir(inputpath)
    im_fns.sort()

    if not os.path.exists(os.path.join(OUTPUT, "image")):
        os.makedirs(os.path.join(OUTPUT, "image"))
    if not os.path.exists(os.path.join(OUTPUT, "label")):
        os.makedirs(os.path.join(OUTPUT, "label"))

    for im_fn in tqdm(im_fns):
        try:
            _, fn = os.path.split(im_fn)
            bfn, ext = os.path.splitext(fn)
            if ext.lower() not in ['.jpg', '.png']:
                continue

            gt_path = os.path.join(inputpath, "label", 'gt_' + bfn + '.txt')
            img_path = os.path.join(inputpath, im_fn)

            img = cv.imread(img_path)
            img_size = img.shape
            im_size_min = np.min(img_size[0:2])
            im_size_max = np.max(img_size[0:2])

            im_scale = float(600) / float(im_size_min)
            if np.round(im_scale * im_size_max) > 1200:
                 im_scale = float(1200) / float(im_size_max)
            new_h = int(img_size[0] * im_scale)
            new_w = int(img_size[1] * im_scale)

            new_h = new_h if new_h // 16 == 0 else (new_h // 16 + 1) * 16
            new_w = new_w if new_w // 16 == 0 else (new_w // 16 + 1) * 16
                            
            re_im = cv.resize(img, (new_w, new_h), interpolation=cv.INTER_LINEAR)
            re_size = re_im.shape

            polys = []
            with open(gt_path, 'r') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if i > 0:
                    splitted_line = line.strip().lower().split(',')
                    x1, y1, x2, y2, x3, y3, x4, y4 = map(float, splitted_line[:8])
                    poly = np.array([x1, y1, x2, y2, x3, y3, x4, y4]).reshape([4, 2])
                    poly[:, 0] = poly[:, 0] / img_size[1] * re_size[1]
                    poly[:, 1] = poly[:, 1] / img_size[0] * re_size[0]
                    poly = orderConvex(poly)
                    polys.append(poly)

            res_polys = []
            for poly in polys:
                if np.linalg.norm(poly[0] - poly[1]) < 10 or np.linalg.norm(poly[3] - poly[0]) < 10:
                     continue

                res = shrink_poly(poly)
                res = res.reshape([-1, 4, 2])

                for r in res:
                    x_min = np.min(r[:, 0])
                    y_min = np.min(r[:, 1])
                    x_max = np.max(r[:, 0])
                    y_max = np.max(r[:, 1])
                    res_polys.append([x_min, y_min, x_max, y_max])

            cv.imwrite(os.path.join(OUTPUT, "image", fn), re_im)
            with open(os.path.join(OUTPUT, "label", bfn) + ".txt", "w") as f:
                for p in res_polys:
                    line = ",".join(str(p[i]) for i in range(4))
                    f.writelines(line + "\r\n")

        except:
            print("Error processing {}".format(im_fn))

def draw_rectangle(points, draw):
    point1 = (points[0], points[1])
    point2 = (points[2], points[1])
    point3 = (points[2], points[3])
    point4 = (points[0], points[3])
    draw.line([point1, point2], 'red', 3)
    draw.line([point1, point4], 'red', 3)
    draw.line([point3, point4], 'red', 3)
    draw.line([point3, point2], 'red', 3)

def read_file(path):
    text = []
    for line in open(path):
        c = line[:-1].split(',')
        c = [int(i) for i in c]
        text.append(c)

    return text

def validation_final_input(outputpath):
    base_path = os.path.join(outputpath, 'image')
    txt_path = os.path.join(outputpath, 'label/*.txt')
    val_path = os.path.join(outputpath, "val")
    if not os.path.exists(val_path):
        os.makedirs(val_path)

    for txt in glob.glob(txt_path):
        name = txt.split('/')[-1].split('.')[0] + '.png'
        text = read_file(txt)
        img_path = os.path.join(base_path, name)
        im = Image.open(img_path)
        draw = ImageDraw.Draw(im)
        for points in text:
            draw_rectangle(points, draw)

        val_files = os.path.join(val_path, '{}')
        new_name = txt.split('/')[-1].split('.')[0] + '_val' + '.png'
        im.save(val_files.format(new_name))

def usage():
    print("python gen_val_label.py  --dir    <path to prepated data(xml and png files)>")
    print("                         --output <path to save result>")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dir",     type=str, help="xml and png files directory")
    ap.add_argument("-o", "--output",  type=str, help="output directory")
    args = vars(ap.parse_args())
    if args["dir"] == None or not os.path.exists(args["dir"]):
        print("--dir value is not valide")
        usage()
        return
    
    if args["output"] == None:
        print("--output value is not valide")
        usage()
        return

    inputpath  = args["dir"]
    if inputpath == None:
       print("Please provide xml/png files' directory by using -d.")
       return
    if not os.path.exists(inputpath):
       print("%s is not exists." % inputpath)
       return

    current_path = os.getcwd()
    OUTPUT = args["output"]
    if not os.path.exists(OUTPUT):
        os.makedirs(OUTPUT)

    xml_to_csv(inputpath)
    split_label(inputpath, OUTPUT)    
    validation_final_input(OUTPUT)


if __name__ == '__main__':
    main()

