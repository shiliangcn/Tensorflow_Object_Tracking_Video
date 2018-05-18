# """
# Preparing model:
#  - Install bazel ( check tensorflow's github for more info )
#     Ubuntu 14.04:
#         - Requirements:
#             sudo add-apt-repository ppa:webupd8team/java
#             sudo apt-get update
#             sudo apt-get install oracle-java8-installer
#         - Download bazel, ( https://github.com/bazelbuild/bazel/releases )
#           tested on: https://github.com/bazelbuild/bazel/releases/download/0.2.0/bazel-0.2.0-jdk7-installer-linux-x86_64.sh
#         - chmod +x PATH_TO_INSTALL.SH
#         - ./PATH_TO_INSTALL.SH --user
#         - Place bazel onto path ( exact path to store shown in the output)
# - For retraining, prepare folder structure as
#     - root_folder_name
#         - class 1
#             - file1
#             - file2
#         - class 2
#             - file1
#             - file2
# - Clone tensorflow
# - Go to root of tensorflow
# - bazel build tensorflow/examples/image_retraining:retrain
# - bazel-bin/tensorflow/examples/image_retraining/retrain --image_dir /path/to/root_folder_name  --output_graph /path/output_graph.pb -- output_labels /path/output_labels.txt -- bottleneck_dir /path/bottleneck
# ** Training done. **
# For testing through bazel,
#     bazel build tensorflow/examples/label_image:label_image && \
#     bazel-bin/tensorflow/examples/label_image/label_image \
#     --graph=/path/output_graph.pb --labels=/path/output_labels.txt \
#     --output_layer=final_result \
#     --image=/path/to/test/image
# For testing through python, change and run this code.
# """

import numpy as np
import os
import tensorflow as tf
import sys
import vid_classes
import progressbar
import Utils_Image
import multiclass_rectangle
from PIL import Image



modelFullPath = 'output_model/retrained_graph.pb' ##### Put the 
checkpoint_dir= "output_model/model.ckpt-250000"
label_file='output_model/retrained_labels.txt'

def create_graph():
    """Creates a graph from saved GraphDef file and returns a saver."""
    # Creates graph from saved graph_def.pb.
    with tf.gfile.FastGFile(modelFullPath, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')

def run_inception_once(picture_path):

    if not tf.gfile.Exists(picture_path):
        tf.logging.fatal('File does not exist %s', picture_path)
        sys.exit()

    image_data = tf.gfile.FastGFile(picture_path, 'rb').read()

    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line in tf.gfile.GFile(label_file)]
    # Creates graph from saved GraphDef.
    create_graph()
    saver = tf.train.Saver()  # defaults to saving all variables - in this case w and b
    with tf.Session() as sess:
        sess.run(tf.initialize_all_variables())
        # load_checkpoint(sess, saver)

        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        predictions = sess.run(softmax_tensor,
                               {'DecodeJpeg/contents:0': image_data})
        predictions = np.squeeze(predictions)

        top_k = predictions.argsort()[-3:][::-1]  # Getting top 5 predictions

        #CHECK OUTPUT
        for node_id in top_k:
            human_string = label_lines[node_id]
            score = predictions[node_id]
            print('%s (score = %.5f)' % (human_string, score))

        # CHECK BEST LABEL
        print "Best Label: %s with conf: %.5f"%(label_lines[top_k[0]],predictions[top_k[0]])

        return label_lines[top_k[0]],predictions[top_k[0]]

# def run_inception(pictures_path_array):

#     labels=[]
#     confidences=[]
#     # Creates graph from saved GraphDef.
#     # Creates graph from saved GraphDef.
#     create_graph()
#     saver = tf.train.Saver()  # defaults to saving all variables - in this case w and b
    
#     with tf.Session() as sess:
#         sess.run(tf.initialize_all_variables())
#         # load_checkpoint(sess, saver)

#         softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

#         for picture_path in pictures_path_array:

#             if not tf.gfile.Exists(picture_path):
#                 tf.logging.fatal('File does not exist %s', picture_path)
#                 sys.exit()

#             image_data = tf.gfile.FastGFile(picture_path, 'rb').read()
#             predictions = sess.run(softmax_tensor,
#                                    {'DecodeJpeg/contents:0': image_data})
#             predictions = np.squeeze(predictions)

#             top_k = predictions.argsort()[-5:][::-1]  # Getting top 5 predictions

#             #CHECK OUTPUT
#             # for node_id in top_k:
#             #     human_string = vid_classes.code_comp_to_class(node_id)
#             #     score = predictions[node_id]
#             #     print('%s (score = %.5f)' % (human_string, score))

#             #CHECK BEST LABEL
#             #print "Best Label: %s with conf: %.5f"%(vid_classes.code_comp_to_class(top_k[0]),predictions[top_k[0]])

#             labels.append(vid_classes.code_comp_to_class(top_k[0]), len(labels))
#             confidences.append(predictions[top_k[0]], len(confidences))

#         return labels, confidences


def label_video(video_info, frames):

    progress = progressbar.ProgressBar(widgets=[progressbar.Bar('=', '[', ']'), ' ',progressbar.Percentage(), ' ',progressbar.ETA()])
    if not os.path.exists(frames[0].split("/")[0]+"/cropped_rects/"):
        os.makedirs(frames[0].split("/")[0]+"/cropped_rects/")
        print("Created Folder: %s"%(frames[0].split("/")[0]+"/cropped_rects/"))
    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line in tf.gfile.GFile(label_file)]
    # Creates graph from saved GraphDef.
    create_graph()
    saver = tf.train.Saver()  # defaults to saving all variables - in this case w and b
    with tf.Session() as sess:
        sess.run(tf.initialize_all_variables())
        # load_checkpoint(sess, saver)
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        idx=0
        for frame_info in progress(video_info):
            print "Tracking Frame Nr: %d"%frame_info.frame
            print len(frame_info.rects)
            rect_id=0
            frame_info.filename = frames[idx]
            for rect in frame_info.rects:
                
                img= Image.open(frames[idx])
                width, height= utils_image.get_Image_Size(frames[idx])
                print rect.x1,rect.y1,rect.x2 ,rect.y2
                x1,y1,x2,y2=utils_image.get_orig_rect(width, height, 640, 480, rect.x1,rect.y1,rect.x2 ,rect.y2)
                print x1,y1,x2,y2
                if(x1==x2):
                    x2=x2-10
                if(y1==y2):
                    y2=y2-10    
                cor = (min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2))
                print cor
                cropped_img=img.crop(cor)
                cropped_img_name=frames[0].split("/")[0]+"/cropped_rects/cropped_frame_%d_rect_%d.JPEG"%(frame_info.frame, rect_id)
                cropped_img.save(cropped_img_name)
                print "Frame: %d Rect: %d conf: %.2f"%(frame_info.frame, rect_id, rect.true_confidence)
                if not tf.gfile.Exists(cropped_img_name):
                    tf.logging.fatal('File does not exist %s', cropped_img_name)
                    sys.exit()
                image_data = tf.gfile.FastGFile(cropped_img_name, 'rb').read()

                predictions = sess.run(softmax_tensor,{'DecodeJpeg/contents:0': image_data})
                predictions = np.squeeze(predictions)

                top_k = predictions.argsort()[-3:][::-1]  # Getting top 5 predictions

                #CHECK OUTPUT
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[node_id]
                    print('%s (score = %.5f)' % (human_string, score))

                # CHECK BEST LABEL
                print "Best Label: %s with conf: %.5f"%(vid_classes.code_to_class_string(label_lines[top_k[0]]),predictions[top_k[0]])
                rect.set_rect_coordinates(x1,x2,y1,y2)
                rect.set_label(predictions[top_k[0]], vid_classes.code_to_class_string(label_lines[top_k[0]]), top_k[0], label_lines[top_k[0]])
                rect_id=rect_id+1
            idx=idx+1
    return video_info


def recurrent_label_video(video_info, frames):

    progress = progressbar.ProgressBar(widgets=[progressbar.Bar('=', '[', ']'), ' ',progressbar.Percentage(), ' ',progressbar.ETA()])
    decomposed_path =frames[0].split("/")
    folder = decomposed_path[len(decomposed_path)-2]
    if not os.path.exists(folder+"/cropped_rects/"):
    	os.makedirs(folder+"/cropped_rects/")
        print("Created Folder: %s"%(folder+"/cropped_rects/"))

    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line in tf.gfile.GFile(label_file)]
    # Creates graph from saved GraphDef.
    create_graph()
    saver = tf.train.Saver()  # defaults to saving all variables - in this case w and b
    with tf.Session() as sess:
        sess.run(tf.initialize_all_variables())
        # load_checkpoint(sess, saver)
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        idx=0
        video_labels=[]
        for frame_info in progress(video_info):
            print "Tracking Frame Nr: %d"%frame_info.frame
            print len(frame_info.rects)
            rect_id=0
            frame_labels=[]
            frame_info.filename = frames[idx]
            for rect in frame_info.rects:
                
                img= Image.open(frames[idx])
                width, height= utils_image.get_Image_Size(frames[idx])
                print rect.x1,rect.y1,rect.x2 ,rect.y2
                x1,y1,x2,y2=utils_image.get_orig_rect(width, height, 640, 480, rect.x1,rect.y1,rect.x2 ,rect.y2)
                print x1,y1,x2,y2
                cor = (min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2))
                print cor
                cropped_img=img.crop(cor)
                cropped_img_name=folder+"/cropped_rects/cropped_frame_%d_rect_%d.JPEG"%(frame_info.frame, rect_id)
                cropped_img.save(cropped_img_name)
                print "Frame: %d Rect: %d conf: %.2f"%(frame_info.frame, rect_id, rect.true_confidence)
                if not tf.gfile.Exists(cropped_img_name):
                    tf.logging.fatal('File does not exist %s', cropped_img_name)
                    sys.exit()
                image_data = tf.gfile.FastGFile(cropped_img_name, 'rb').read()

                predictions = sess.run(softmax_tensor,{'DecodeJpeg/contents:0': image_data})
                predictions = np.squeeze(predictions)

                top_k = predictions.argsort()[-3:][::-1]  # Getting top 5 predictions

                #CHECK OUTPUT
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[node_id]
                    print('%s (score = %.5f)' % (human_string, score))

                if(len(video_labels)>0):
                    if(video_labels[idx-1][rect_id][0]==top_k[0]):
                        # CHECK BEST LABEL
                        print "Best Label: %s with conf: %.5f"%(vid_classes.code_to_class_string(label_lines[top_k[0]]),predictions[top_k[0]])
                        rect.set_rect_coordinates(x1,x2,y1,y2)
                        rect.set_label(predictions[top_k[0]], vid_classes.code_to_class_string(label_lines[top_k[0]]), top_k[0], label_lines[top_k[0]])
                        frame_labels.append((top_k[0], predictions[top_k[0]]))
                    else:
                        label = video_labels[idx-1][rect_id][0] 
                        print "Best Label setted recurrently: %s "%(vid_classes.code_to_class_string(label_lines[label]))
                        rect.set_rect_coordinates(x1,x2,y1,y2)
                        rect.set_label(video_labels[idx-1][rect_id][1], vid_classes.code_to_class_string(label_lines[label]), label, label_lines[label])
                        frame_labels.append((label, video_labels[idx-1][rect_id][1]))
                else:
                    # CHECK BEST LABEL
                    print "Best Label: %s with conf: %.5f"%(vid_classes.code_to_class_string(label_lines[top_k[0]]),predictions[top_k[0]])
                    rect.set_rect_coordinates(x1,x2,y1,y2)
                    rect.set_label(predictions[top_k[0]], vid_classes.code_to_class_string(label_lines[top_k[0]]), top_k[0], label_lines[top_k[0]])
                    frame_labels.append((top_k[0], predictions[top_k[0]]))
                    
                rect_id=rect_id+1
            video_labels.append(frame_labels)
            idx=idx+1
    return video_info
