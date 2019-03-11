#!/usr/bin/env python3
# -*- encoding: utf8 -*-

import os
import sys

sys.path.append(os.getcwd())
from validation.cv2_helper2 import *

def validate(val_path):
    for root, dirs, files in os.walk(val_path):
        for f in files:
            (shotname, extension) = os.path.splitext(f)

            if extension.lower() == ".png": 
                try:
                    table = cv2.imread(os.path.join(val_path, f), -1)
                    text_blocks = step_3_find_text_lines_v2(table, shotname)
                    areas, ztgz = step_4_read_keyword_and_value_v2(text_blocks)

                    ret = {}
                    ret['filename']  = shotname
                    if len(areas) == 2:
                        ret['heji1'] = areas[0]
                        ret['heji2'] = areas[1]
                    else:
                        ret['heji1'] = "0.0"
                        ret['heji2'] = "0.0"
                    # ret['ztgz']      = u"鋼筋混凝土造"
                    ret['ztgz']      = ztgz
                    ret['confident'] = 0.8
                    ret['Status']    = "OK"
                    ret['ErrDesc']   = ""

                    print(ret['filename'], " # ", ret['heji1'], " / ", ret['heji2'] ,"ztgz:",ztgz)

                except Exception as e:
                    print(str(e))
    
if __name__ == '__main__':
    val_path = "./data/dataset/validation"
    validate(val_path)

