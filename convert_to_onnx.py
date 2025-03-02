from __future__ import print_function
import argparse
import os
import random
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torch.nn.functional as F
import numpy as np
import time
import math
from models import *
import cv2
from PIL import Image

# 2012 data /media/jiaren/ImageNet/data_scene_flow_2012/testing/

parser = argparse.ArgumentParser(description='PSMNet')
parser.add_argument('--KITTI', default='2015',
                    help='KITTI version')
parser.add_argument('--datapath', default='/media/jiaren/ImageNet/data_scene_flow_2015/testing/',
                    help='select model')
parser.add_argument('--loadmodel', default='./trained/pretrained_model_KITTI2015.tar',
                    help='loading model')
parser.add_argument('--leftimg', default='./image/left.png',
                    help='load model')
parser.add_argument('--rightimg', default='./image/right.png',
                    help='load model')
parser.add_argument('--model', default='stackhourglass',
                    help='select model')
parser.add_argument('--maxdisp', type=int, default=192,
                    help='maxium disparity')
parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='enables CUDA training')
parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')
args = parser.parse_args()
args.cuda = not args.no_cuda and torch.cuda.is_available()

torch.manual_seed(args.seed)
if args.cuda:
    torch.cuda.manual_seed(args.seed)

if args.model == 'stackhourglass':
    model = stackhourglass(args.maxdisp)
elif args.model == 'basic':
    model = basic(args.maxdisp)
else:
    print('no model')

model = nn.DataParallel(model, device_ids=[0])
model.cuda()

if args.loadmodel is not None:
    print('load PSMNet')
    state_dict = torch.load(args.loadmodel)
    model.load_state_dict(state_dict['state_dict'])

print('Number of model parameters: {}'.format(sum([p.data.nelement() for p in model.parameters()])))


def test(imgL, imgR):
    model.eval()

    if args.cuda:
        imgL = imgL.cuda()
        imgR = imgR.cuda()

    with torch.no_grad():
        disp = model(imgL, imgR)

    disp = torch.squeeze(disp)
    pred_disp = disp.data.cpu().numpy()

    onnx_input_L = torch.rand(1, 3, 400, 640)
    onnx_input_R = torch.rand(1, 3, 400, 640)
    onnx_input_L = onnx_input_L.to("cuda:0")
    onnx_input_R = onnx_input_R.to("cuda:0")
    torch.onnx.export(model.module,
                      (onnx_input_L, onnx_input_R),
                      "PSMNET.onnx",
                      # where to save the model (can be a file or file-like object)
                      export_params=True,  # store the trained parameter weights inside the model file
                      verbose=False, opset_version=11,  # the ONNX version to export the model to
                      do_constant_folding=True,  # whether to execute constant folding for optimization
                      input_names=['left', 'right'],  # the model's input names
                      output_names=['output'])

    return pred_disp


def main():
    normal_mean_var = {'mean': [0.485, 0.456, 0.406],
                       'std': [0.229, 0.224, 0.225]}
    infer_transform = transforms.Compose([transforms.ToTensor(),
                                          transforms.Normalize(**normal_mean_var)])

    imgL_o = Image.open(args.leftimg).convert('RGB')
    imgR_o = Image.open(args.rightimg).convert('RGB')

    imgL = infer_transform(imgL_o)
    imgR = infer_transform(imgR_o)

    # pad to width and hight to 16 times
    if imgL.shape[1] % 16 != 0:
        times = imgL.shape[1] // 16
        top_pad = (times + 1) * 16 - imgL.shape[1]
    else:
        top_pad = 0

    if imgL.shape[2] % 16 != 0:
        times = imgL.shape[2] // 16
        right_pad = (times + 1) * 16 - imgL.shape[2]
    else:
        right_pad = 0

    imgL = F.pad(imgL, (0, right_pad, top_pad, 0)).unsqueeze(0)
    imgR = F.pad(imgR, (0, right_pad, top_pad, 0)).unsqueeze(0)

    start_time = time.time()
    pred_disp = test(imgL, imgR)


if __name__ == '__main__':
    main()
