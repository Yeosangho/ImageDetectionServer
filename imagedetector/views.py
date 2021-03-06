from django.shortcuts import render
from django.http import HttpResponse
import os
import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile
import boto3
import botocore
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
from imagedetector.utils import label_map_util

from imagedetector.utils import visualization_utils as vis_util
if tf.__version__ != '1.4.1':
  raise ImportError('Please upgrade your tensorflow installation to v1.4.0!')
# This is needed to display the images.
# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")

# What model to download.
MODELS = ['ssd_mobilenet_v1_coco_2017_11_17', 'ssd_inception_v2_coco_2017_11_17', 'faster_rcnn_resnet50_coco_2017_11_08', 'faster_rcnn_resnet101_coco_2017_11_08', 'faster_rcnn_inception_resnet_v2_atrous_lowproposals_coco_2017_11_08']


BUCKET_NAME = 'yeosangho' # replace with your bucket name
KEY = 'ssd_mobilenet_v1_coco_2017_11_17.tar.gz' # replace with your object key



# List of the strings that is used to add correct label for each box.
APP_DIR = os.path.abspath(os.path.dirname(__file__))
DATADIR = os.path.join(APP_DIR, 'data/')
PATH_TO_LABELS = os.path.join(DATADIR, 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATICDIR = os.path.join(BASE_DIR, 'static/')
detection_graph = tf.Graph()

def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)
# Create your views here.
def index(request):
    return render(request, 'home/index.html', {})
def ready_model(request):
    global detection_graph
    modelIdx = request.GET['model']

    MODEL_NAME = MODELS[int(modelIdx)]
    KEY = MODEL_NAME + '.tar.gz'  # replace with your object key
    FILEDIR = os.path.join(BASE_DIR, MODEL_NAME)
    MODEL_FILE = FILEDIR + '.tar.gz'

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    MODELDIR = os.path.join(BASE_DIR, MODEL_NAME)
    PATH_TO_CKPT = MODELDIR + '/frozen_inference_graph.pb'
    s3 = boto3.resource('s3')
    if (os.path.exists(MODEL_FILE)):
        print("file already exists")
    else:
        print("file download")
        try:
            s3.Bucket(BUCKET_NAME).download_file(KEY, MODEL_FILE)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
            else:
                raise

    if (os.path.exists(MODEL_NAME)):
        print("model folder already exists")
    else:
        print("model folder create")
        tar_file = tarfile.open(MODEL_FILE)
        for file in tar_file.getmembers():
            file_name = os.path.basename(file.name)
            if 'frozen_inference_graph.pb' in file_name:
                tar_file.extract(file, os.getcwd())


    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
        return HttpResponse(MODEL_NAME)

def show_image(request):
    imageIdx = request.GET['image']
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    # For the sake of simplicity we will use only 2 images:
    # image1.jpg
    # image2.jpg
    # If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
    PATH_TO_TEST_IMAGES_DIR = os.path.join(APP_DIR, 'test_images/')
    TEST_IMAGE_PATHS = [os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(1, 6)]

    # Size, in inches, of the output images.
    IMAGE_SIZE = (12, 8)

    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            # Definite input and output Tensors for detection_graph
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            # Each box represents a part of the image where a particular object was detected.
            detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
            detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')

            image = Image.open(TEST_IMAGE_PATHS[int(imageIdx)])
            # the array based representation of the image will be used later in order to prepare the
            # result image with boxes and labels on it.
            image_np = load_image_into_numpy_array(image)
            # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
            image_np_expanded = np.expand_dims(image_np, axis=0)
            # Actual detection.
            (boxes, scores, classes, num) = sess.run(
                [detection_boxes, detection_scores, detection_classes, num_detections],
                feed_dict={image_tensor: image_np_expanded})
            # Visualization of the results of a detection.
            vis_util.visualize_boxes_and_labels_on_image_array(
                    image_np,
                    np.squeeze(boxes),
                    np.squeeze(classes).astype(np.int32),
                    np.squeeze(scores),
                    category_index,
                    use_normalized_coordinates=True,
                    line_thickness=8)
            img = Image.fromarray(image_np)
            img.save('result.png')
    image_data = open('result.png', "rb").read()
    return HttpResponse(image_data, content_type='image/png')
