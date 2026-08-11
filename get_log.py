import json
import kaggle
import sys

kernel = 'sbmahafujbondhon/bubbleml-resolution-control-96x96-missing'
try:
    print(kaggle.api.kernel_status(kernel))
except Exception as e:
    print(e)
