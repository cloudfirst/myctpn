import sys
import os

sys.path.append(os.getcwd())
from validation.calamari_helper import init_calamary
from validation.validate import validate

predictor = init_calamary()

val_path = "./data/dataset/validation"
validate(val_path, predictor)

