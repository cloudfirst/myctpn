import os
import shutil
import sys
import time

import cv2
import tensorflow as tf
from sinobot_ctpn.nets import model_train as model
import numpy as np
from sinobotocr.my_log import *
from sinobot_ctpn.utils.rpn_msr.proposal_layer import proposal_layer
from sinobot_ctpn.utils.text_connector.detectors import TextDetector

logger = get_my_logger()

CTPN_MODEL_PATH = "/usr/share/ctpn/model/"

tf.reset_default_graph()
dg = tf.get_default_graph().as_default()
input_image = tf.placeholder(tf.float32, shape=[None, None, None, 3], name='input_image')
input_im_info = tf.placeholder(tf.float32, shape=[None, 3], name='input_im_info')
global_step = tf.get_variable('global_step', [], initializer=tf.constant_initializer(0), trainable=False)
bbox_pred, cls_pred, cls_prob = model.model(input_image)
variable_averages = tf.train.ExponentialMovingAverage(0.997, global_step)
saver = tf.train.Saver(variable_averages.variables_to_restore())
sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
ckpt_state = tf.train.get_checkpoint_state(CTPN_MODEL_PATH)
model_path = os.path.join(CTPN_MODEL_PATH, os.path.basename(ckpt_state.model_checkpoint_path))
print('Restore from {}'.format(model_path))
logger.error('-------------------Restore from {}'.format(model_path))
saver.restore(sess, model_path)
logger.error("-------------------saver.restore() complete")

def resize_image(img):
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

    re_im = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    return re_im, (new_h / img_size[0], new_w / img_size[1])

def get_ctpn_boxes(table_img):
    start = time.time()

    img, (rh, rw) = resize_image(table_img)
    h, w, c = img.shape
    im_info = np.array([h, w, c]).reshape([1, 3])
    bbox_pred_val, cls_prob_val = sess.run([bbox_pred, cls_prob],
                                        feed_dict={input_image: [img],
                                                input_im_info: im_info})

    textsegs, _ = proposal_layer(cls_prob_val, bbox_pred_val, im_info)
    scores = textsegs[:, 0]
    textsegs = textsegs[:, 1:5]

    textdetector = TextDetector(DETECT_MODE='H')
    boxes = textdetector.detect(textsegs, scores[:, np.newaxis], img.shape[:2])
    boxes = np.array(boxes, dtype=np.int)
    showed_img = img.copy()
    for i, box in enumerate(boxes):
        coordinate_box = [box[:8].astype(np.int32).reshape((-1, 1, 2))]
        cv2.polylines(showed_img, coordinate_box, True, color=(0, 255, 0), thickness=2)
    showed_img = cv2.resize(showed_img, None, None, fx=1.0 / rh, fy=1.0 / rw, interpolation=cv2.INTER_LINEAR)        
    
    cost_time = (time.time() - start)
    print("cost time: {:.2f}s".format(cost_time))
    
    return boxes,img,showed_img

