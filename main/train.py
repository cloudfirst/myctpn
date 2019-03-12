import datetime
import os
import sys
import time

import tensorflow as tf

sys.path.append(os.getcwd())
from validation.calamari_helper import init_calamary
from validation.validate import validate
from tensorflow.contrib import slim
from sinobot_ctpn.nets import model_train as model
from sinobot_ctpn.utils.dataset import data_provider as data_provider

tf.app.flags.DEFINE_float('learning_rate', 1e-5, '')
#tf.app.flags.DEFINE_integer('max_steps', 50000, '')
tf.app.flags.DEFINE_integer('max_steps', 10000, '')
tf.app.flags.DEFINE_integer('decay_steps', 30000, '')
#tf.app.flags.DEFINE_integer('decay_rate', 0.1, '')
tf.app.flags.DEFINE_float('decay_rate', 0.1, '')
tf.app.flags.DEFINE_float('moving_average_decay', 0.997, '')
tf.app.flags.DEFINE_integer('num_readers', 4, '')
tf.app.flags.DEFINE_string('gpu', '0,1', '')
tf.app.flags.DEFINE_string('checkpoint_path', 'checkpoints_mlt/', '')
tf.app.flags.DEFINE_string('logs_path', 'logs_mlt/', '')
tf.app.flags.DEFINE_string('pretrained_model_path', 'data/vgg_16.ckpt', '')
tf.app.flags.DEFINE_boolean('restore', True, '')
#tf.app.flags.DEFINE_boolean('restore', False, '')
#tf.app.flags.DEFINE_integer('save_checkpoint_steps', 2000, '')
tf.app.flags.DEFINE_integer('save_checkpoint_steps', 100, '')
FLAGS = tf.app.flags.FLAGS


#################### validation by raymond #################
tf.app.flags.DEFINE_string('best_checkpoint_path', 'best_checkpoint/', '')
tf.app.flags.DEFINE_integer('early_stopping_nbest', 5, '')
tf.app.flags.DEFINE_integer('early_stopping_frequency', 20, '')
tf.app.flags.DEFINE_boolean('early_stopping_enabled', True, '')
tf.app.flags.DEFINE_float('early_stopping_suc_lower_bound', 0.3, '')
tf.app.flags.DEFINE_integer('early_stopping_step_lower_bound', 20, '')
tf.app.flags.DEFINE_string('val_path', "./data/dataset/validation", '')


def del_file(path):
    ls = os.listdir(path)
    for i in ls:
        c_path = os.path.join(path, i)
        if os.path.isdir(c_path):
            del_file(c_path)
        else:
            os.remove(c_path)

#################### validation finished #################

def main(argv=None):
    os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpu
    tf.reset_default_graph()
    now = datetime.datetime.now()
    StyleTime = now.strftime("%Y-%m-%d-%H-%M-%S")
    os.makedirs(FLAGS.logs_path + StyleTime)
    if not os.path.exists(FLAGS.checkpoint_path):
        os.makedirs(FLAGS.checkpoint_path)

    input_image = tf.placeholder(tf.float32, shape=[None, None, None, 3], name='input_image')
    input_bbox = tf.placeholder(tf.float32, shape=[None, 5], name='input_bbox')
    input_im_info = tf.placeholder(tf.float32, shape=[None, 3], name='input_im_info')

    global_step = tf.get_variable('global_step', [], initializer=tf.constant_initializer(0), trainable=False)
    learning_rate = tf.Variable(FLAGS.learning_rate, trainable=False)
    tf.summary.scalar('learning_rate', learning_rate)
    opt = tf.train.AdamOptimizer(learning_rate)

    #gpu_id = int(FLAGS.gpu)
    bbox_pred, cls_pred, cls_prob = model.model(input_image)
    total_loss, model_loss, rpn_cross_entropy, rpn_loss_box = model.loss(bbox_pred, cls_pred, input_bbox,
                                                                         input_im_info)
    batch_norm_updates_op = tf.group(*tf.get_collection(tf.GraphKeys.UPDATE_OPS))
    grads = opt.compute_gradients(total_loss)

    '''
    gpu_ids = FLAGS.gpu.split(',')
    gpu_ids = [int(i) for i in gpu_ids]
    for gpu_id in gpu_ids:
        with tf.device('/gpu:%d' % gpu_id):
            with tf.name_scope('model_%d' % gpu_id) as scope:
                bbox_pred, cls_pred, cls_prob = model.model(input_image)
                total_loss, model_loss, rpn_cross_entropy, rpn_loss_box = model.loss(bbox_pred, cls_pred, input_bbox,
                                                                                     input_im_info)
                batch_norm_updates_op = tf.group(*tf.get_collection(tf.GraphKeys.UPDATE_OPS, scope))
                grads = opt.compute_gradients(total_loss)
    '''
    
    #################### validation by raymond #################

    #################### validation finished #################

    apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

    summary_op = tf.summary.merge_all()
    variable_averages = tf.train.ExponentialMovingAverage(
        FLAGS.moving_average_decay, global_step)
    variables_averages_op = variable_averages.apply(tf.trainable_variables())
    with tf.control_dependencies([variables_averages_op, apply_gradient_op, batch_norm_updates_op]):
        train_op = tf.no_op(name='train_op')

    saver = tf.train.Saver(tf.global_variables(), max_to_keep=100)
    summary_writer = tf.summary.FileWriter(FLAGS.logs_path + StyleTime, tf.get_default_graph())

    init = tf.global_variables_initializer()

    if FLAGS.pretrained_model_path is not None:
        variable_restore_op = slim.assign_from_checkpoint_fn(FLAGS.pretrained_model_path,
                                                             slim.get_trainable_variables(),
                                                             ignore_missing_vars=True)

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 0.95
    config.allow_soft_placement = True
    with tf.Session(config=config) as sess:
        if FLAGS.restore:
            ckpt = tf.train.latest_checkpoint(FLAGS.checkpoint_path)
            restore_step = int(ckpt.split('.')[0].split('_')[-1])
            print("continue training from previous checkpoint {}".format(restore_step))
            saver.restore(sess, ckpt)
        else:
            sess.run(init)
            restore_step = 0
            if FLAGS.pretrained_model_path is not None:
                variable_restore_op(sess)

        data_generator = data_provider.get_batch(num_workers=FLAGS.num_readers)
        start = time.time()

        #################### validation by raymond #################
        early_stopping_best_at_iter = 0
        early_stopping_best_accuracy = 0.0
        early_stopping_best_cur_nbest = 0
        predictor = init_calamary()
        #################### validation finished #################

        for step in range(restore_step, FLAGS.max_steps):
            data = next(data_generator)
            ml, tl, _, summary_str = sess.run([model_loss, total_loss, train_op, summary_op],
                                              feed_dict={input_image: data[0],
                                                         input_bbox: data[1],
                                                         input_im_info: data[2]})

            summary_writer.add_summary(summary_str, global_step=step)

            if step != 0 and step % FLAGS.decay_steps == 0:
                sess.run(tf.assign(learning_rate, learning_rate.eval() * FLAGS.decay_rate))

            if step % 10 == 0:
                avg_time_per_step = (time.time() - start) / 10
                start = time.time()
                print('Step {:06d}, model loss {:.4f}, total loss {:.4f}, {:.2f} seconds/step, LR: {:.6f}'.format(
                    step, ml, tl, avg_time_per_step, learning_rate.eval()))

            if (step + 1) % FLAGS.save_checkpoint_steps == 0:
                filename = ('ctpn_{:d}'.format(step + 1) + '.ckpt')
                filename = os.path.join(FLAGS.checkpoint_path, filename)
                saver.save(sess, filename)
                print('Write model to: {:s}'.format(filename))

            #################### validation by raymond #################
            if FLAGS.early_stopping_enabled and (iter + 1) % FLAGS.early_stopping_frequency == 0 and step >= FLAGS.early_stopping_step_lower_bound:
                print("Checking early stopping model")

                accuracy = validate(FLAGS.val_path, predictor)
                print('accuracy: {!s} at step: {!s}'.format(accuracy, step))

                if accuracy > FLAGS.early_stopping_suc_lower_bound:

                    if accuracy > early_stopping_best_accuracy: 
                        early_stopping_best_accuracy = accuracy
                        early_stopping_best_cur_nbest = 1
                        early_stopping_best_at_iter = step + 1

                        # overwrite as best model
                        '''
                        last_checkpoint = make_checkpoint(
                            checkpoint_params.early_stopping_best_model_output_dir,
                            prefix="",
                            version=checkpoint_params.early_stopping_best_model_prefix,
                        )
                        '''

                        del_file(FLAGS.best_checkpoint_path)
                        filename = ('ctpn_{:d}'.format(step + 1) + '.ckpt')
                        filename = os.path.join(FLAGS.best_checkpoint_path, filename)
                        saver.save(sess, filename)

                        print('Write model to: {:s}'.format(filename))
                        print("Found better model with accuracy of {:%}".format(early_stopping_best_accuracy))
                    else:
                        early_stopping_best_cur_nbest += 1
                        print("No better model found. Currently accuracy of {:%} at iter {} (remaining nbest = {})".
                              format(early_stopping_best_accuracy, early_stopping_best_at_iter,
                                     FLAGS.early_stopping_nbest - early_stopping_best_cur_nbest))

                    if accuracy > 0 and early_stopping_best_cur_nbest >= FLAGS.early_stopping_nbest:
                        print("Early stopping now.")
                        break

                        if accuracy >= 1:
                            print("Reached perfect score on validation set. Early stopping now.")
                            break
            #################### validation finished #################

if __name__ == '__main__':
    tf.app.run()
