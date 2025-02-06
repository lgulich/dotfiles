#!/usr/bin/env python3
import sys

import torch

path = sys.argv[1]
checkpoint = torch.load(path)

print(checkpoint.keys())
