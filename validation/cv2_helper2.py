#!/usr/bin/env python3
# -*- encoding: utf8 -*-
import os

from sinobot_ctpn.ctpn_helper import *
from validation.calamari_helper import calamari_apply_ocr


key_words_for_ztjg = [
    "主體結構",
    "主體結",
    "體結構",
    "主體",
    "體結",
    "結構",
    "構造"
]
key_words_for_sczao=["SC造","S.C造","S.C.造","SC.造","SC","S.C","S.C.","SC."]
key_words_for_dingzhu=['預鑄']
key_words_for_gangguzao=['鋼骨','鋼骨造','鋼骨構造']
key_words_for_RCzao=['RC造', 'R.C造','R.C.造', 'RC.造','RC', 'R.C','R.C.', 'RC.','生造','R(造','日c造','.C造']
key_words_for_gangjinhunning=['鋼筋混凝土','鋼筋混凝土造','鋼筋混凝土構造','混凝土造','鋼筋混']
key_words_for_gangjinhunnitu=['鋼筋混泥土造']
key_words_for_jiaqiangzhuanzao=['加強磚造','加強磚']
key_words_for_zhuanzao=['磚造']
key_words_for_srczao=['SRC造','S.R.C造','S.R.C.造','SRC.造','SRC','S.R.C','S.R.C.','SRC.']
key_words_for_ganggugangjin=['鋼骨鋼筋混凝土','鋼骨鋼筋混凝土造','鋼骨鋼筋混凝土構造','鋼骨RC造']
key_words_for_gangguhunningtu=['鋼骨混凝土造' ,'鋼骨混凝土結構造']
key_words_for_ganggu_rc_zao=['鋼骨RC造']
key_words_shizao=['石造']
key_words_muzao=['木造']
key_words_wazao=['瓦造']
key_words_tiejinzao=['鐵筋','鐵筋造']
key_words_tiejinjiaqiangzhuan=['鐵筋加強磚','鐵筋加強磚造']
def find_ztgz_value_in_lin_text(line_text):
    for sczao in key_words_for_sczao:
        if(sczao in line_text):
            return 'SC造'
            break
    for ding in key_words_for_dingzhu:
        if(ding in line_text):
            return '預鑄'    
            break
    for ganggugangjin in key_words_for_ganggugangjin:
        if(ganggugangjin in line_text):
            return '鋼骨鋼筋混凝土造'
            break
    for gangjinhunning in key_words_for_gangjinhunning:
        if(gangjinhunning in line_text):
            return '鋼筋混凝土造'     
            break        
    for gangguhunningtu in key_words_for_gangguhunningtu:
        if(gangguhunningtu in line_text):
            return '鋼骨混凝土造' 
            break          
    for gangguzao in key_words_for_gangguzao:
        if(gangguzao in line_text):
            return '鋼骨造'
            break
    for ganggurc_zao in  key_words_for_ganggu_rc_zao:
        if(ganggurc_zao in line_text):
            return '鋼骨RC造'   
            break   

    for rc in key_words_for_RCzao:
        if(rc in line_text and '鋼筋' not in line_text or ('R.' in line_text and 'C造' in line_text)):
            return 'RC造'
            break
    for gangjinhunni in key_words_for_gangjinhunnitu:
        if(gangjinhunni in line_text):
            return '鋼筋混泥土造'   
            break
 
    for jiaqiangzhuan in key_words_for_jiaqiangzhuanzao:
        if(jiaqiangzhuan in line_text):
            return '加強磚造'        
            break
    for zhuanzao in key_words_for_zhuanzao:
        if(zhuanzao in line_text):
            return '磚造'
            break
    for src in key_words_for_srczao:
        if(src in line_text):
            return 'SRC造'
            break                  
    for shizao in key_words_shizao:
        if(shizao in line_text):
            return '石造'        
            break
    for muzao in key_words_muzao:
        if(muzao in line_text):
            return '木造'
            break
    for wazao in key_words_wazao:
        if(wazao in line_text):
            return '瓦造'
            break
    for tiejin in key_words_tiejinzao:
        if(tiejin in line_text):
            return '鐵筋造'   
            break
    for tiejinjiaqiang in key_words_tiejinjiaqiangzhuan:
        if(tiejinjiaqiang in line_text):
            return '鐵筋加強磚造'
            break
    for zhuti in key_words_for_ztjg:
        if(zhuti in line_text and 'C' in line_text and '造' in line_text and '鋼筋' not in line_text):
            return 'RC造'        
            break        
    return '' 

def search_heji_keyword_index(line_text):
    he_index = -1
    ji_index = -1
    heji_index = -1

    ret = [s for s in forbidden_keywords if s in line_text]
    if len(ret) > 0:
        return 0, -1

    if '合' in line_text:
        if "集合" in line_text or "造" in line_text:
            pass
        else:
            he_index = line_text.find('合')
    if '計' in line_text:
        ji_index = line_text.find('計')
    if "合計" in line_text:
        heji_index = line_text.find("合計")
        heji_index += 1
    
    if heji_index > -1:
        return 100, heji_index
    elif he_index > -1 and ji_index > -1:
        if he_index < ji_index:
            return 100, ji_index
        else:
            return 0, -1
    elif ji_index > -1:
        return 50, ji_index
    elif he_index > -1:
        return 30, he_index
    else:
        return 0, -1


def process_digits_recognized(digit_str):
    _tmp = digit_str
    try:
        while _tmp[0] == '.':               # remove the . at the beginning of string
            _tmp = _tmp[1:]    
        while _tmp[len(_tmp) - 1 ] == '.':  # remove the . at the end of string
            _tmp = _tmp[0:len(_tmp) - 1]

        _index = [pos for pos, char in enumerate(_tmp) if char == '.']

        if len(_index) == 0:
            f = float(_tmp)
            if f > 100:
                heji_number = str(f/100)
            else:
                heji_number = _tmp
        elif len(_index) > 1:
            first = _index.pop(0)
            left = _tmp[:first]
            right = _tmp[first+1:]
            right = right.replace('.', '')
            heji_number = left + '.' + right[:2]
        else:
            heji_number = _tmp
    except Exception as e:
        heji_number = "0.0"
    
    return heji_number


# Input: line_text, score, index
# Output: heji value or ""
def search_heji_keyword_value(line_text, score, index):
    text = line_text[index+1:]
    num_str = []
    for i in range(len(text)):
        if text[i] >= "0" and text[i] <= "9":
            num_str.append(text[i])
        elif text[i] == ".":
            num_str.append(text[i])
        elif text[i] == '‧':
            num_str.append(".")
        elif text[i] > u'\u4e00' and text[i] < u'\u9fff':
            if len(num_str) > 0:
                break
        elif text[i] >= 'a' and text[i] <= 'z':
            if len(num_str) > 0:
                break
        elif text[i] >= 'A' and text[i] <= 'Z':
            if len(num_str) > 0:
                break

    area = ''.join(num_str)
    if area == '.':
        area = ''
    
    if score >= 90 and area == "":
        area = "0.0"

    if len(area) > 0:
        area = process_digits_recognized(area)
    return area

import heapq
# siv_list = [(score, index, value), ... ...]
def method_1_to_find_heji_value(siv_list):
    # search two largest score
    if len(siv_list) <= 1:
        return siv_list

    result = heapq.nlargest(2, siv_list)
    # sort by index
    result = sorted(result, key=lambda kv:kv[1]) 
    return result

# Input : raw line texts, result of method_1
# Output: siv_list = [(score, index, value), ... ...]
forbidden_keywords = [
    "年","月", "申請","日期", "測量", "建物","坐落", "門牌", "主體", "主要", "用途", 
    "使用","執照", "層", "姓名","雨", "遮", "陽","台", "門","廊", "騎","建", "市", "鄉",
    "鎮", "股", "物","段", "地", "街", "路", "樓", "巷", "弄", "第", "集合", "字", "突",
    "門", "牌", "執", "計算",
]

zzm_keywords = [
    "主要", "用途", "主體", "構造", "結構", "面積", "平方", "公尺",
    "要用", "體構",
]

def convert_digitstr_to_float(text):
    try:
        return float(text)
    except Exception as e:
        return 0.0

def method_2_to_find_heji_value(raw_line_texts, method_1_result):
    # step 1.1 : find all digit number in raw line texts
    all_digits = []
    for text in raw_line_texts:
        _line_digits = []
        _tmp_digit = []
        ret = [s for s in forbidden_keywords if s in text]
        if len(ret) > 0:
            all_digits.append([""])
            continue
        
        for i in range(len(text)):
            if text[i] >= "0" and text[i] <= "9":
                _tmp_digit.append(text[i])
            elif text[i] == ".":
                _tmp_digit.append(text[i])
            elif text[i] == '‧':
                _tmp_digit.append(".")
            elif text[i] > u'\u4e00' and text[i] < u'\u9fff':
                if len(_tmp_digit) > 0:
                    _tmp_digit_str = ''.join(_tmp_digit)
                    _line_digits.append(_tmp_digit_str)
                    _tmp_digit = []
            elif text[i] >= 'a' and text[i] <= 'z':
                if len(_tmp_digit) > 0:
                    _tmp_digit_str = ''.join(_tmp_digit)
                    _line_digits.append(_tmp_digit_str)
                    _tmp_digit = []
            elif text[i] >= 'A' and text[i] <= 'Z':
                if len(_tmp_digit) > 0:
                    _tmp_digit_str = ''.join(_tmp_digit)
                    _line_digits.append(_tmp_digit_str)
                    _tmp_digit = []

        if len(_tmp_digit) > 0:
            _tmp_digit_str = ''.join(_tmp_digit)
            _line_digits.append(_tmp_digit_str)
        if len(_line_digits) == 0:
            _line_digits = [""]
        all_digits.append(_line_digits)
    
    # step 1.2 construct digit array for table
    heji_number_candidate_array = []
    for line_digits in all_digits:
        if len(line_digits) == 0:
            heji_number_candidate_array.append("")
        elif len(line_digits) == 1:
            heji_number_candidate_array.append(line_digits[0])
        elif len(line_digits) == 2:
            heji_number_candidate_array.append(line_digits[1])
        else:
            heji_number_candidate_array.append(line_digits[1])
    
    # step 2: find index of forbiden keyword
    zzm_index_result = -1
    for (index, text) in enumerate(raw_line_texts):
        ret = [s for s in zzm_keywords if s in text]
        if len(ret) >= 2: # really find the the anchor just below heji_1
            zzm_index_result = index

    # step 3: search heji area number
    method_2_result = []
    if len(method_1_result) == 0: # method_1 does not provide any help
        if zzm_index_result > -1:
            # no help info from method_1, but get the zzm_index
            # [zzm_index - 3] contains heji_1
            # [ <=-3 ] contains heji_2
            _to_be_sorted_data = [convert_digitstr_to_float(x) for x in heji_number_candidate_array[zzm_index_result-2:zzm_index_result]]
            result = heapq.nlargest(2, _to_be_sorted_data)
            heji_1 = process_digits_recognized(str(result[0]))
            method_2_result.append((10, zzm_index_result-1, heji_1))

            _tmp_candidate = heji_number_candidate_array[zzm_index_result:]
            _tmp_candidate = _tmp_candidate[-3:]
            _tmp_candidate.reverse()
            bFlag = False
            for (index, _tmp) in enumerate(_tmp_candidate):
                if _tmp == "":
                    pass
                else:
                    _tmp = process_digits_recognized(_tmp)
                    heji_2 = (10, -1, _tmp)
                    method_2_result.append(heji_2)
                    bFlag = True
                    break
            if not bFlag:
                method_2_result.append((10, -1, "0.0"))
        else:
            # no help info from method_1, and not find zzm_index_result
            # so it can only find two largest digits for heji_1 and heji_2
            _to_be_sorted_data = [convert_digitstr_to_float(x) for x in heji_number_candidate_array[-9:]]
            result = heapq.nlargest(2, _to_be_sorted_data)
            heji_1 = process_digits_recognized(str(result[0]))
            heji_2 = process_digits_recognized(str(result[1]))
            method_2_result.append((11, -1, heji_1))
            method_2_result.append((11, -1, heji_2))

    if len(method_1_result) == 1: # method_1 already find one of heji keyword
        method_1_heji_index = method_1_result[0][1]
        if zzm_index_result > method_1_heji_index and abs(zzm_index_result - method_1_heji_index) <= 3:
            already_find_heji_no = 1
        else:
            already_find_heji_no = 2

        if zzm_index_result > -1:
             if already_find_heji_no == 1:
                 method_2_result.append(method_1_result[0])
                 # then need to find heji_2
                 _tmp_candidate = heji_number_candidate_array[zzm_index_result:]
                 _tmp_candidate = _tmp_candidate[-3:]
                 _tmp_candidate.reverse()
                 bFlag = False
                 for (index, _tmp) in enumerate(_tmp_candidate):
                     if _tmp == "":
                         pass
                     else:
                         _tmp = process_digits_recognized(_tmp)
                         heji_2 = (12, -1, _tmp)
                         method_2_result.append(heji_2)
                         bFlag = True
                         break
                 if not bFlag:
                     method_2_result.append((10, -1, "0.0"))
                 
             if already_find_heji_no == 2:
                 # need to find heji_1
                 heji_1 = heji_number_candidate_array[zzm_index_result-1]
                 heji_1 = process_digits_recognized(heji_1)
                 method_2_result.append((12, zzm_index_result-1, heji_1))
                 method_2_result.append(method_1_result[0])

        else:
            if already_find_heji_no == 1:
                heji_1_index = method_1_result[0][1]
                method_2_result.append(method_1_result[0])
                # then need to find heji_2
                heji_2 = (13, -1, max(heji_number_candidate_array[heji_1_index+1:]))
                method_2_result.append(heji_2)
            
            if already_find_heji_no == 2:
                # need to find heji_1
                _to_be_sorted_data = [convert_digitstr_to_float(x) for x in heji_number_candidate_array[-9:]]
                result = heapq.nlargest(2, _to_be_sorted_data)
                heji_1 = process_digits_recognized(str(result[0]))
                method_2_result.append((11, -1, heji_1))
                method_2_result.append(method_1_result[0])
            
            if method_2_result[0][2] == method_2_result[1][2]: # in case pdf have only one HEJI 
                score, index, value = method_2_result[1]
                method_2_result[1] = (score, index, "0.0")
            
    
    if float(method_2_result[1][2]) > float(method_2_result[0][2]):
        method_2_result.reverse()
    return method_2_result


def get_text_blocks_by_opencv_v2(img, boxes):
    new_text_blocks = {}
    buckets = []

    # create bucket based on box y value
    for i,box in enumerate(boxes):
        bMatched = False
        coordinate_box = [box[:8].astype(np.int32).reshape((-1, 1, 2))]
        y_1 = coordinate_box[0][0][0][1]
        y_2 = coordinate_box[0][2][0][1]
        for index in range(0,len(buckets)):
            (top, bottom) = buckets[index]
            _seta = set(range(top, bottom))
            _setb = set(range(y_1, y_2))
            ret = _seta & _setb
            r1 = len(ret) / len(_seta)
            r2 = len(ret) / len(_setb)
            if _seta <= _setb or _seta >= _setb:
                buckets[index] = (min(top, y_1), max(bottom, y_2))
                bMatched = True
                break
            elif r1 > 0.5 or r2 > 0.5:
                buckets[index] = (min(top, y_1), max(bottom, y_2))
                bMatched = True
                break
        if not bMatched:
            buckets.append((y_1, y_2))
           
    # sort bucket by y value
    buckets = sorted(buckets, key = lambda x: x[0])    

    table_lines = []
    for index, _ in enumerate(buckets):
        table_lines.append([])
    for i_box,box in enumerate(boxes):
        coordinate_box = [box[:8].astype(np.int32).reshape((-1, 1, 2))]
        x_min = coordinate_box[0][0][0][0]
        y_min = coordinate_box[0][0][0][1]
        x_max = coordinate_box[0][2][0][0]
        y_max = coordinate_box[0][2][0][1]
        for index in range(0, len(buckets)):
            (top, bottom) = buckets[index]
            _seta = set(range(top, bottom))
            _setb = set(range(y_min, y_max))
            ret = _seta & _setb
            if _seta >= _setb:
                (x, y, w, h) = (x_min, y_min, abs(x_max-x_min), abs(y_max-y_min))
                table_lines[index].append((x, y, w, h))
    
        # sort again
    for index in range(0, len(table_lines)):
        table_lines[index] = sorted(table_lines[index], key = lambda x: x[0])
    
    new_text_blocks["image"] = img
    new_text_blocks['text_boxes'] = table_lines

    return new_text_blocks

def step_3_find_text_lines_v2(table, filename):
    boxes, img, showed_img = get_ctpn_boxes(table) 
    cv2.imwrite("/tmp/ctpn/ctpn_{!s}.png".format(filename), showed_img[:, :, ::-1])
    new_text_blocks = get_text_blocks_by_opencv_v2(img, boxes) 
    return new_text_blocks

def step_4_read_keyword_and_value_v2(text_blocks):
    heji_number = []
    ztgz = ""

    table_img = text_blocks['image']
    table_lines = text_blocks['text_boxes']

    raw_table_line_texts = []

    # first, recognize each line to text and 
    # save at raw_table_line_texts
    to_be_ocred_table = []
    for (index, line) in enumerate(table_lines):
        to_be_ocred_line = []
        ## ocr each line of the table
        for (myid, block) in enumerate(line):
            (x,y,w,h) = block
            new_block_img = table_img[y:y+h, x:x+w]
            to_be_ocred_line.append(new_block_img)
        to_be_ocred_table.append(to_be_ocred_line)
    
    raw_table_line_texts = calamari_apply_ocr(to_be_ocred_table)

    print("================recogonition text===============")
    # second, scan each line's text to find value of ztgz
    for (index, line_text) in enumerate(raw_table_line_texts):
        _tmp_value = find_ztgz_value_in_lin_text(line_text)
        if len(_tmp_value) > 0:
            ztgz = _tmp_value
            break

    # third, scan each line's text and save {score, index, value} to siv_list
    siv_list = []
    for (index, line_text) in enumerate(raw_table_line_texts):
        score, __index  = search_heji_keyword_index(line_text)
        if score > 0 and score < 100 and __index > -1:
            if index == len(raw_table_line_texts)-1: # HE or JI in last line should be 100
                score = 90
        if score > 0 and __index > -1:
            area = search_heji_keyword_value(line_text, score, __index)
            if area == "":
                pass
            else:
                siv_list.append((score, index, area))
    
    # fourth, find the heji and heji2 based on the result of third step
    heji_siv_array = method_1_to_find_heji_value(siv_list)

    # check if fourth step is failed, try another method to find heji1 and heji2 value
    if len(heji_siv_array) != 2:
        heji_siv_array = method_2_to_find_heji_value(raw_table_line_texts, heji_siv_array)

    heji_number = [ x[2] for x in heji_siv_array ]

    return heji_number, ztgz
        

        
        


