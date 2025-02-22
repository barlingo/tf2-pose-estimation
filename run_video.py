import argparse
import logging
import time

import glob
import os
import cv2
import numpy as np

from tf_pose.estimator import TfPoseEstimator
from tf_pose.networks import get_graph_path, model_wh

logger = logging.getLogger('TfPoseEstimator-Video')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

fps_time = 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='tf-pose-estimation Video')
    parser.add_argument('--video', type=str, default='')
    parser.add_argument('--folder', type=str, default='dataset')

    parser.add_argument('--resolution', type=str, default='432x368', help='network input resolution. default=432x368')
    parser.add_argument('--model', type=str, default='mobilenet_thin', help='cmu / mobilenet_thin / mobilenet_v2_large / mobilenet_v2_small')
    parser.add_argument('--show-process', type=bool, default=False,
                        help='for debug purpose, if enabled, speed for inference is dropped.')
    parser.add_argument('--show_video', type=bool, default=False,
                        help='Display video as is processed.')
    parser.add_argument('--output_json', type=str, default='/tmp/', help='writing output json dir')
    parser.add_argument('--showBG', type=bool, default=True, help='False to show skeleton only.')
    args = parser.parse_args()

    logger.debug('initialization %s : %s' % (args.model, get_graph_path(args.model)))
    w, h = model_wh(args.resolution)
    e = TfPoseEstimator(get_graph_path(args.model), target_size=(w, h))

    if args.video:
        videos_paths = [args.video]
    else:
        if args.folder == 'dataset':
            path = f'{args.folder}/*/*.mp4'
        else:
            path = f'{args.folder}/*.mp4'
        videos_paths = glob.glob(path)
    for video in videos_paths:
        cap = cv2.VideoCapture(video)
        if args.output_json == '/tmp/':
            json_dir = video.replace('dataset', 'keypoint', 1)
            json_dir = json_dir.replace('.mp4', '', 1)
            if not os.path.exists(json_dir):
                os.makedirs('./' + json_dir)

        if cap.isOpened() is False:
            print("Error opening video stream or file")
        frame = 0
        while cap.isOpened():
                while True:
                    ret_val, image = cap.read()

                    logger.debug('image process+')
                    humans = e.inference(image, resize_to_default=(w > 0 and h> 0), upsample_size=4.0)

                    logger.debug('postprocess+')
                    if not args.showBG:
                        image = np.zeros(image.shape)
                    image = TfPoseEstimator.draw_humans(image, humans, imgcopy=False, frame=frame, output_json_dir=json_dir)
                    frame += 1

                    cv2.putText(image,
                                "FPS: %f" % (1.0 / (time.time() - fps_time)),
                                (10, 10),  cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                (0, 255, 0), 2)
                    if args.show_video:
                        cv2.imshow('tf-pose-estimation result', image)
                    fps_time = time.time()
                    if cv2.waitKey(1) == 27:
                        break
                    logger.debug('finished+')
