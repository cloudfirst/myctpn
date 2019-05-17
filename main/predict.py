# coding=utf-8
import os
import shutil
import sys
import time
import glob
import xml.etree.ElementTree as ET

import scipy.misc
import cv2
import numpy as np
import tensorflow as tf

sys.path.append(os.getcwd())
from sinobot_ctpn.nets import model_train as model
from sinobot_ctpn.utils.rpn_msr.proposal_layer import proposal_layer
from sinobot_ctpn.utils.text_connector.detectors import TextDetector

tf.app.flags.DEFINE_string('test_data_path', '', 'directory path to data to be predicted')
tf.app.flags.DEFINE_string('output_path', '/tmp/ctpn_predict/', 'directory path to output result')
tf.app.flags.DEFINE_string('box_output_path', '/tmp/box_output/', 'directory to box')
tf.app.flags.DEFINE_string('gpu', '0, 1', 'GPU indexes')
tf.app.flags.DEFINE_string('checkpoint_path', '', 'directory path to store ctpn model')
FLAGS = tf.app.flags.FLAGS

def save_segment(img, coordinate_box, im_fn, i, base_path):
    x_min = coordinate_box[0][0][0][0]
    y_min = coordinate_box[0][0][0][1]
    
    x_max = coordinate_box[0][2][0][0]
    y_max = coordinate_box[0][2][0][1]

    save_img = img[y_min:y_max, x_min:x_max, :]
    #img_name = im_fn.split('/')[-1].split('.')[0]
    img_name = im_fn.split('/')[-1]
    file_name = img_name.split('.')[0]
    extension = '.' + img_name.split('.')[1]    

    img_name = file_name + '_{}'.format(i) + extension
    path = os.path.join(base_path, img_name)

    scipy.misc.imsave(path, save_img)
    

def get_images():
    files = []
    exts = ['jpg', 'png', 'jpeg', 'JPG']
    for parent, dirnames, filenames in os.walk(FLAGS.test_data_path):
        for filename in filenames:
            for ext in exts:
                if filename.endswith(ext):
                    files.append(os.path.join(parent, filename))
                    break
    print('Find {} images'.format(len(files)))
    return files


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

def usage():
    print("python predict.py -h for all available options")
    print("python predict.py --test_data_path <data path to be predicted>")
    print("                  --checkpoint_path <model path>")
    print("                  --output_path <path to predict result>")

def main(argv=None):
    if not os.path.exists(FLAGS.test_data_path):
        print("test_data_path is not valide.")
        usage()
        return
    
    if not os.path.exists(FLAGS.checkpoint_path):
        print("checkpoint_path is not valide")
        usage()
        return
    
    if not os.path.exists(FLAGS.box_output_path):
        os.makedirs(FLAGS.box_output_path)

    if os.path.exists(FLAGS.output_path):
        shutil.rmtree(FLAGS.output_path)
    os.makedirs(FLAGS.output_path)

    os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpu

    with tf.get_default_graph().as_default():
        input_image = tf.placeholder(tf.float32, shape=[None, None, None, 3], name='input_image')
        input_im_info = tf.placeholder(tf.float32, shape=[None, 3], name='input_im_info')

        global_step = tf.get_variable('global_step', [], initializer=tf.constant_initializer(0), trainable=False)

        bbox_pred, cls_pred, cls_prob = model.model(input_image)

        variable_averages = tf.train.ExponentialMovingAverage(0.997, global_step)
        saver = tf.train.Saver(variable_averages.variables_to_restore())

        with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:
            tf.get_variable_scope().reuse_variables()
            ckpt_state = tf.train.get_checkpoint_state(FLAGS.checkpoint_path)
            model_path = os.path.join(FLAGS.checkpoint_path, os.path.basename(ckpt_state.model_checkpoint_path))
            print('Restore from {}'.format(model_path))
            saver.restore(sess, model_path)

            im_fn_list = get_images()
            return_val = []
            results = []
            for im_fn in im_fn_list:
                print('===============')
                print(im_fn)
                start = time.time()
                try:
                    im = cv2.imread(im_fn)[:, :, ::-1]
                except:
                    print("Error reading image {}!".format(im_fn))
                    continue

                img, (rh, rw) = resize_image(im)

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

                cost_time = (time.time() - start)
                print("cost time: {:.2f}s".format(cost_time))

                for i, box in enumerate(boxes):
                    coordinate_box = [box[:8].astype(np.int32).reshape((-1, 1, 2))]
                    base_path = FLAGS.box_output_path
                    save_segment(img, coordinate_box, im_fn, i, base_path)
                    cv2.polylines(img, coordinate_box, True, color=(0, 255, 0), thickness=2)
                
                img = cv2.resize(img, None, None, fx=1.0 / rh, fy=1.0 / rw, interpolation=cv2.INTER_LINEAR)
                cv2.imwrite(os.path.join(FLAGS.output_path, os.path.basename(im_fn)), img[:, :, ::-1])

                with open(os.path.join(FLAGS.output_path, os.path.splitext(os.path.basename(im_fn))[0]) + ".txt",
                          "w") as f:
                    for i, box in enumerate(boxes):
                        line = ",".join(str(box[k]) for k in range(8))
                        line += "," + str(scores[i]) + "\r\n"
                        f.writelines(line)

if __name__ == '__main__':
    tf.app.run()
