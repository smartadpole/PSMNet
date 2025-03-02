from onnxmodel import ONNXModel
from PIL import Image
import numpy as np
# from test_image import WriteDepthOnnx
from torchvision import transforms

net = ONNXModel("PSMNET.onnx")
# limg = np.array(Image.open("/home/ljx/Code/200sever/work/sunhao/Lac-GwcNet/images1/L/13_1664369833690648.L.jpg").convert('RGB')).astype("float32")
# limg=np.expand_dims(np.resize(limg,(3,400,640)),0)
# # limg=np.expand_dims(limg,0)
# rimg = np.array(Image.open("/home/ljx/Code/200sever/work/sunhao/Lac-GwcNet/images1/R/13_1664369833690648.R.jpg").convert('RGB')).astype("float32")
# rimg = np.expand_dims(np.resize(rimg,(3,400,640)),0)
# # rimg = np.expand_dims(rimg,0)

input_height = 400
input_width = 640
limg_ori = Image.open("image/left.png").convert('RGB')
limg_ori = limg_ori.resize((input_width, input_height), 3)
rimg_ori = Image.open("image/right.png").convert('RGB')
rimg_ori = rimg_ori.resize((input_width, input_height), 3)

# why crop
# w, h = limg_ori.size
# limg = limg_ori.crop((w - 320, h - 240, w, h))
# rimg = rimg_ori.crop((w - 320, h - 240, w, h))

limg_tensor = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])(limg_ori)
rimg_tensor = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])(rimg_ori)
limg_tensor = limg_tensor.unsqueeze(0).cuda()
rimg_tensor = rimg_tensor.unsqueeze(0).cuda()

limg = limg_tensor.cpu().numpy()
rimg = rimg_tensor.cpu().numpy()

output = net.forward(limg, rimg)
dis_array = output[0][0][0]
dis_array = (dis_array - dis_array.min()) / (dis_array.max() - dis_array.min()) * 255.0
dis_array = dis_array.astype("uint8")

import cv2

showImg = cv2.resize(dis_array, (dis_array.shape[-1], dis_array.shape[0]))
showImg = cv2.applyColorMap(cv2.convertScaleAbs(showImg, 1), cv2.COLORMAP_PARULA)
cv2.imwrite("onnx_result.jpg", showImg)
# limg = np.resize(np.squeeze(limg_ori),(400,640,3))
# WriteDepthOnnx(output,limg,"result/","L/34_1665285574842567.L.jpg",14.2)
