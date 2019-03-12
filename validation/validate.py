#!/usr/bin/env python3
# -*- encoding: utf8 -*-

import os
import sys

sys.path.append(os.getcwd())
from validation.cv2_helper2 import *

def read_gt(gt_file):
    gt = []
    for line in open(gt_file):
        line = line.split('\n')[0]
        gt.append(line)
    return gt

def validate(val_path, predictor):
    suc_rate = 0.
    suc_num = 0
    total_num = 0
    failed_num = 0

    for root, dirs, files in os.walk(val_path):
        for f in files:
            (shotname, extension) = os.path.splitext(f)

            if extension.lower() == ".png": 
                total_num += 1
                try:
                    table = cv2.imread(os.path.join(val_path, f), -1)
                    text_blocks = step_3_find_text_lines_v2(table, shotname)
                    areas, ztgz = step_4_read_keyword_and_value_v2(text_blocks, predictor)

                    ret = {}
                    ret['filename']  = shotname
                    if len(areas) == 2:
                        ret['heji1'] = areas[0]
                        ret['heji2'] = areas[1]
                    else:
                        ret['heji1'] = "0.0"
                        ret['heji2'] = "0.0"

                    gt_file = os.path.join(val_path, shotname + '.gt.txt')
                    gt = read_gt(gt_file)
                    print(gt)

                    if gt[0] == ret['heji1'] and gt[1] == ret['heji2']:
                        suc_num += 1
                    else:
                        failed_num += 1

                    print(ret['filename'], " # ", ret['heji1'], " / ", ret['heji2'])

                except Exception as e:
                    print(str(e))

    
    suc_rate = float(suc_num)/total_num
    print('suc_rate:', suc_rate)
    suc_rate = "%.2f%%" % (suc_rate * 100)
    print('suc_rate:', suc_rate)
    return suc_rate
    
if __name__ == '__main__':
    val_path = "./data/dataset/validation"
    validate(val_path)

