import os
import cv2
import time
from tqdm import tqdm

from calamari_ocr.ocr import MultiPredictor
from calamari_ocr.ocr.voting import voter_from_proto
from calamari_ocr.proto import VoterParams
from calamari_ocr.ocr.datasets import RawInputDataset, DataSetMode

class Sinobot_Predictor(MultiPredictor):
    def __init__(self, checkpoints=None, text_postproc=None, data_preproc=None, batch_size=1, processes=1):
        super().__init__(checkpoints=checkpoints, text_postproc=text_postproc, data_preproc=data_preproc, batch_size=batch_size, processes=processes)

    def sinobot_predict_dataset(self, img, progress_bar=True):
        start_time = time.time()
        datas = [img]

        # preprocessing step (if all share the same preprocessor)
        if self.same_preproc:
            data_params = self.predictors[0].data_preproc.apply(datas, processes=self.processes, progress_bar=progress_bar)
        else:
            raise Exception('Different preprocessors are currently not allowed during prediction')

        raw_dataset = [
            RawInputDataset(DataSetMode.PREDICT,
                            [img for img, _ in data_params],
                            [None] * len(data_params),
                            [p for _, p in data_params],
                            None if self.same_preproc else p.data_preproc,
                            None if self.same_preproc else p.text_postproc,
                            ) for p in self.predictors]

        # predict_raw returns list of prediction objects
        prediction = [predictor.predict_input_dataset(ds, progress_bar=False)
                      for ds, predictor in zip(raw_dataset, self.predictors)]
      
        return zip(*prediction) 

    def sinobot_batch_predict_dataset(self, datas, progress_bar=True):
        start_time = time.time()

        # preprocessing step (if all share the same preprocessor)
        if self.same_preproc:
            data_params = self.predictors[0].data_preproc.apply(datas, processes=self.processes, progress_bar=progress_bar)
        else:
            raise Exception('Different preprocessors are currently not allowed during prediction')

        def progress_bar_wrapper(l):
            if progress_bar:
                l = list(l)
                return tqdm(l, total=len(l), desc="Prediction")
            else:
                return l

        for data_idx in progress_bar_wrapper(range(0, len(datas), self.batch_size)):
            batch_data_params = data_params[data_idx:data_idx+self.batch_size]
            #samples = dataset.samples()[data_idx:data_idx+self.batch_size]
            raw_dataset = [
                RawInputDataset(DataSetMode.PREDICT,
                                [img for img, _ in batch_data_params],
                                [None] * len(batch_data_params),
                                [p for _, p in batch_data_params],
                                None if self.same_preproc else p.data_preproc,
                                None if self.same_preproc else p.text_postproc,
                                ) for p in self.predictors]

            # predict_raw returns list of prediction objects
            prediction = [predictor.predict_input_dataset(ds, progress_bar=False)
                          for ds, predictor in zip(raw_dataset, self.predictors)]

            for result in zip(*prediction):
                yield result 

        print("Prediction of {} models took {}s".format(len(self.predictors), time.time() - start_time))
