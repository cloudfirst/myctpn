import sys
import os

sys.path.append(os.getcwd())
from validation.validate import validate

val_path = "./data/dataset/validation"
validate(val_path)

