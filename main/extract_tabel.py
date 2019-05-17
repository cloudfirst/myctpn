# -*- encoding: utf8 -*-

import os
from imutils import contours as ic
#from tqdm import tqdm

from sinobotocr.cv2_helper import *
from sinobotocr.cv2_helper2 import *
from sinobotocr.my_pdf2img import *

logger = get_my_logger()

def seperate_tabel_from_pdf(pdf, table_path):

    try:
        logger.error("Get image from pdf from %s" % pdf)
        dest_file = getImageFromPDF(pdf)
    
        # Step 1: 图像预处理
        logger.error("step_1_pre_processing_image ...")
        orig, canny = step_1_pre_processing_image(dest_file)
        
        # Step 2: 定位并提取表格部分
        logger.error("step_2_location_table ...")
        table       = step_2_location_table(orig, canny)
        save_processed_image(table, table_path) 
        
    except Exception as e:
        print(str(e))

def get_file_name(base_path):
    pdf_path = os.path.join(base_path, 'pdf')

    total_effective_data_num = 0
    img_gt_dict = dict()
    img_gt_list = []

    for root, dirs, files in os.walk(pdf_path): 
      for f in files:
          filepath, tempfilename = os.path.split(f);
          shotname, extension = os.path.splitext(tempfilename);
          
          if extension.lower() == '.pdf':
              #print('aaaaaaaaaaa')
              table_path = os.path.join(root.replace('pdf','tables', 1), shotname + '.png')
              file_path = os.path.join(root, tempfilename)
              #print(table_path)
              print(file_path)
              
              seperate_tabel_from_pdf(file_path, table_path)


def main():
    print("---------------------------------------")
    #seperate_tabel()

if __name__ == '__main__':
    main()
    base_path = '../training_data/'
    get_file_name(base_path) 

