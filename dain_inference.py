"""It's a helper for continues frames insertion.

Input: numbered frames listed as [%4d.png]
    e.g.: 1230.png 1231.png 1232.png ... etc
Output: numbered frames listed as [%4d%2d.png]
    e.g.: 123000.png 123001.png 123002.png 123003.png
         123100.png 123101.png ... etc
    p.s.: %2d is related with the slowmotion parameter you used [2x, 4x, 8x ... etc]

Attention: Redistribution under the MIT License.

# Use scipy ver 1.1.0, for now.
# Use imageio to optimize after reconstruct a whole close-loop test.
"""

import time
import os
from torch.autograd import Variable
import torch
import random
import numpy as np
import numpy
from DAIN import networks
from DAIN.my_args import parser
from scipy.misc import imread, imsave
from DAIN.AverageMeter import *
import shutil

torch.backends.cudnn.benchmark = True  # to speed up the

parser.add_argument(
    "--frame_split",
    "-sp",
    default=False,
    type=bool,
    help="split the frames when handling 1080p videos",
)

args = parser.parse_args()

def continue_frames_insertion_helper(
    input_dir: str, output_dir: str, model, time_step: float
):
    """For continue insert operation into curr input dir."""

    # curr_input_dir = os.path.join(INPUT_DATA, input_dir)
    print(f"************** current handling frame from {input_dir}. **************")
    print(f"************** current time_step is {time_step} **************")
    print(f"************** current output_dir is {output_dir} **************")

    # curr all_frame is out of order.
    all_frames = os.listdir(input_dir)
    # all_frames.sort(key=lambda x: int(x[:-4]))
    # Todo(C.Feng, Mar 30): More precise string processing.
    all_frames.sort()
    frames_num = len(all_frames)
    for num in range(frames_num - 1):
        begin_frame = os.path.join(input_dir, f"{all_frames[num]}")
        end_frame = os.path.join(input_dir, f"{all_frames[num+1]}")
        frames_insertion_helper(
            output_dir=output_dir,
            begin_frame=begin_frame,
            end_frame=end_frame,
            model=model,
            time_step=time_step,
        )

    # handle the last frame.
    shutil.copy(
        end_frame,
        os.path.join(output_dir, f"{os.path.split(end_frame)[-1].split('.')[0]}00.png"),
    )
    print(f"************** current image {end_frame} processed. **************")


def frames_insertion_helper(
    output_dir: str, begin_frame: str, end_frame: str, model, time_step: float
):
    """For insert operation between two frames."""

    # First, we copy the beginning frame into output dir.
    shutil.copy(
        begin_frame,
        os.path.join(
            output_dir, f"{os.path.split(begin_frame)[-1].split('.')[0]}00.png"
        ),
    )

    im_0 = imread(begin_frame)
    im_1 = imread(end_frame)
    # [720, 1280, 3]
    h, w, c = im_0.shape
    assert im_0.shape == im_1.shape

    im_0 = np.transpose(im_0, (2, 0, 1)).astype("float32") / 255.0
    im_1 = np.transpose(im_1, (2, 0, 1)).astype("float32") / 255.0

    if not args.frame_split:
        y_0 = model_inference_helper(im_0, im_1)
    else:
        frames_num = int(1.0 / time_step) - 1
        y_0 = []
        ym_0_0 = model_inference_helper(im_0[:, 0::2, 0::2], im_1[:, 0::2, 0::2])
        ym_0_1 = model_inference_helper(im_0[:, 0::2, 1::2], im_1[:, 0::2, 1::2])
        ym_1_0 = model_inference_helper(im_0[:, 1::2, 0::2], im_1[:, 1::2, 0::2])
        ym_1_1 = model_inference_helper(im_0[:, 1::2, 1::2], im_1[:, 1::2, 1::2])
        for i in range(frames_num):
            y_0.append(np.zeros(shape=(h, w, c)))
            y_0[-1][0::2, 0::2, :] = ym_0_0[i]
            y_0[-1][0::2, 1::2, :] = ym_0_1[i]
            y_0[-1][1::2, 0::2, :] = ym_1_0[i]
            y_0[-1][1::2, 1::2, :] = ym_1_1[i]

        del ym_0_0, ym_0_1, ym_1_0, ym_1_1

    # numFrames = int(1.0 / time_step) - 1
    # time_offsets = [kk * time_step for kk in range(1, 1 + numFrames, 1)]

    for i, item in enumerate(y_0):
        curr_output_tail = (
            f"{os.path.split(begin_frame)[-1].split('.')[0]}{i+1:02d}.png"
        )
        arguments_strOut = os.path.join(output_dir, curr_output_tail)
        imsave(arguments_strOut, np.round(item).astype(numpy.uint8))

    del y_0
    torch.cuda.empty_cache()

    print(f"************** current image {begin_frame} processed. **************")


@torch.no_grad()
def model_inference_helper(x_0: np.array, x_1: np.array):
    """
    Input: x_0, x_1
    Output: y_0
    """
    x_0 = torch.from_numpy(x_0).type(args.dtype)
    x_1 = torch.from_numpy(x_1).type(args.dtype)
    y_0 = torch.FloatTensor()

    intWidth = x_0.size(2)
    intHeight = x_0.size(1)
    channel = x_0.size(0)
    assert channel == 3, "input frame's channel is not equal to 3."

    if intWidth != ((intWidth >> 7) << 7):
        intWidth_pad = ((intWidth >> 7) + 1) << 7  # more than necessary
        intPaddingLeft = int((intWidth_pad - intWidth) / 2)
        intPaddingRight = intWidth_pad - intWidth - intPaddingLeft
    else:
        intWidth_pad = intWidth
        intPaddingLeft = 32
        intPaddingRight = 32

    if intHeight != ((intHeight >> 7) << 7):
        intHeight_pad = ((intHeight >> 7) + 1) << 7  # more than necessary
        intPaddingTop = int((intHeight_pad - intHeight) / 2)
        intPaddingBottom = intHeight_pad - intHeight - intPaddingTop
    else:
        intHeight_pad = intHeight
        intPaddingTop = 32
        intPaddingBottom = 32

    # torch.set_grad_enabled(False)
    x_0 = Variable(torch.unsqueeze(x_0, 0))
    x_1 = Variable(torch.unsqueeze(x_1, 0))
    x_0 = torch.nn.ReplicationPad2d(
        [intPaddingLeft, intPaddingRight, intPaddingTop, intPaddingBottom]
    )(x_0)
    x_1 = torch.nn.ReplicationPad2d(
        [intPaddingLeft, intPaddingRight, intPaddingTop, intPaddingBottom]
    )(x_1)

    # if use_cuda:
    x_0 = x_0.cuda()
    x_1 = x_1.cuda()

    # y_s, offset, filter = model(torch.stack((X0, X1), dim=0))
    y_s, _, _ = model(torch.stack((x_0, x_1), dim=0))
    y_0 = y_s[args.save_which]

    torch.cuda.empty_cache()

    if not isinstance(y_0, list):
        y_0 = y_0.data.cpu().numpy()
    else:
        y_0 = [item.data.cpu().numpy() for item in y_0]
    y_0 = [
        np.transpose(
            255.0
            * item.clip(0, 1.0)[
                0,
                :,
                intPaddingTop : intPaddingTop + intHeight,
                intPaddingLeft : intPaddingLeft + intWidth,
            ],
            (1, 2, 0),
        )
        for item in y_0
    ]
    # print(f"model helper info:\ty_ shape: {y_0[0].shape}")

    return y_0


if __name__ == "__main__":
    LOC = os.getcwd()
    if LOC.split("/")[-1] != "MVIMP":
        raise ValueError("Please change directory to the root of MVIMP.")
    DAIN_PREFIX = os.path.join(LOC, "DAIN")
    os.chdir(DAIN_PREFIX)

    print(f"Current PyTorch version is {torch.__version__}")

    input_data_dir = os.path.join(LOC, "Data/Input")
    output_data_dir = os.path.join(LOC, "Data/Output")

    if len(os.listdir(input_data_dir)) < 2:
        raise FileNotFoundError("You need more than 2 frames to generate insertion.")

    # use cuda as default
    assert args.use_cuda, "CUDA only."

    # model select
    model = networks.__dict__[args.netName](
        channel=args.channels,
        filter_size=args.filter_size,
        timestep=args.time_step,
        training=False,
    )

    model = model.cuda()

    args.SAVED_MODEL = "./model_weights/best.pth"
    if os.path.exists(args.SAVED_MODEL):
        print("The testing model weight is: " + args.SAVED_MODEL)
        pretrained_dict = torch.load(args.SAVED_MODEL)

        model_dict = model.state_dict()
        # 1. filter out unnecessary keys
        pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}
        # 2. overwrite entries in the existing state dict
        model_dict.update(pretrained_dict)
        # 3. load the new state dict
        model.load_state_dict(model_dict)
        # 4. release the pretrained dict for saving memory
        pretrained_dict = []
    else:
        print("*****************************************************************")
        print("**** We don't load any trained weights **************************")
        print("*****************************************************************")

    model = model.eval()  # deploy mode

    with torch.no_grad():
        continue_frames_insertion_helper(
            input_dir=input_data_dir,
            output_dir=output_data_dir,
            model=model,
            time_step=args.time_step,
        )