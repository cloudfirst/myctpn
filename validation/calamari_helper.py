from validation.calamari_utils import *

def get_model():
    path = '/usr/share/calamari/model/'
    checkpoint = []

    for root, dirs, files in os.walk(path): 
      for f in files:
          filepath, tempfilename = os.path.split(f);
          shotname, extension = os.path.splitext(tempfilename);
          if extension == '.json':
              checkpoint.append(os.path.join(root, shotname))

    # print(checkpoint)
    return checkpoint

def get_real_img_list(img_list):

    real_img_list = []
    line_num_list = [0]
    
    for i, imgs in enumerate(img_list):
        line_num_list.append(len(imgs) + line_num_list[i])
        for img in imgs:
            real_img_list.append(img)

    return real_img_list, line_num_list

def connect_text(text_list):
    total_text = ''
    for text in text_list:
         total_text += text
    return total_text    

def get_real_text_list(text_list, line_num_list):

    real_text_list = []
    new_text = ''

    for i, index in enumerate(line_num_list):
        if i != len(line_num_list) - 1:
            input_text = text_list[line_num_list[i]: line_num_list[i+1]]
            real_text_list.append(connect_text(input_text))
        
    return real_text_list

def init_calamary():
    # get model
    checkpoint = get_model()

    # predict for all models
    predictor = Sinobot_Predictor(checkpoints=checkpoint, batch_size=1, processes=1)

    return predictor

def calamari_apply_ocr(img_list, predictor):

    # pre-treat of input img_list
    real_img_list, line_num_list = get_real_img_list(img_list)
    
    # get model
    #checkpoint = get_model()

    # create voter
    voter_params = VoterParams()
    voter_params.type = VoterParams.Type.Value('CONFIDENCE_VOTER_DEFAULT_CTC')
    voter = voter_from_proto(voter_params)

    # predict for all models
    #predictor = Sinobot_Predictor(checkpoints=checkpoint, batch_size=1, processes=1)
    do_prediction = predictor.sinobot_batch_predict_dataset(real_img_list, progress_bar=True)

    avg_sentence_confidence = 0
    n_predictions = 0

    # output the voted results to the appropriate files
    rec = []
    for result in do_prediction:
        n_predictions += 1
        for i, p in enumerate(result):
            p.prediction.id = "fold_{}".format(i)

        # vote the results (if only one model is given, this will just return the sentences)
        prediction = voter.vote_prediction_result(result)
        prediction.id = "voted"
        sentence = prediction.sentence
        rec.append(sentence)
        avg_sentence_confidence += prediction.avg_char_probability

    # post-treat of output rec
    rec = get_real_text_list(rec, line_num_list)
    # print(rec)

    return rec

def main():
    img_file = '/tmp/gen_data/107FB526934PIC21840C980A898494AB3845E801237_22_528.tif'
    img = cv2.imread(img_file, -1)

if __name__ == "__main__":
    main()
