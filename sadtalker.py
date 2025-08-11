from glob import glob
import shutil
import torch
from time import  strftime
import os, sys, time
from argparse import ArgumentParser

from src.utils.preprocess import CropAndExtract
from src.test_audio2coeff import Audio2Coeff  
from src.facerender.animate import AnimateFromCoeff
from src.generate_batch import get_data
from src.generate_facerender_batch import get_facerender_data
from src.utils.init_path import init_path

def main(args):
    #torch.backends.cudnn.enabled = False

    pic_path = args.source_image
    audio_path = args.driven_audio
    save_dir = os.path.join(args.result_dir, strftime("%Y_%m_%d_%H.%M.%S"))
    os.makedirs(save_dir, exist_ok=True)
    pose_style = args.pose_style
    device = args.device
    batch_size = args.batch_size
    input_yaw_list = args.input_yaw
    input_pitch_list = args.input_pitch
    input_roll_list = args.input_roll
    ref_eyeblink = args.ref_eyeblink
    ref_pose = args.ref_pose

    current_root_path = os.path.split(sys.argv[0])[0]

    sadtalker_paths = init_path(args.checkpoint_dir, os.path.join(current_root_path, 'src/config'), args.size, args.old_version, args.preprocess)

    #init model
    preprocess_model = CropAndExtract(sadtalker_paths, device)

    audio_to_coeff = Audio2Coeff(sadtalker_paths,  device)
    
    animate_from_coeff = AnimateFromCoeff(sadtalker_paths, device)

    #crop image and extract 3dmm from image
    first_frame_dir = os.path.join(save_dir, 'first_frame_dir')
    os.makedirs(first_frame_dir, exist_ok=True)
    print('3DMM Extraction for source image')
    first_coeff_path, crop_pic_path, crop_info =  preprocess_model.generate(pic_path, first_frame_dir, args.preprocess,\
                                                                             source_image_flag=True, pic_size=args.size)
    if first_coeff_path is None:
        print("Can't get the coeffs of the input")
        return

    if ref_eyeblink is not None:
        ref_eyeblink_videoname = os.path.splitext(os.path.split(ref_eyeblink)[-1])[0]
        ref_eyeblink_frame_dir = os.path.join(save_dir, ref_eyeblink_videoname)
        os.makedirs(ref_eyeblink_frame_dir, exist_ok=True)
        print('3DMM Extraction for the reference video providing eye blinking')
        ref_eyeblink_coeff_path, _, _ =  preprocess_model.generate(ref_eyeblink, ref_eyeblink_frame_dir, args.preprocess, source_image_flag=False)
    else:
        ref_eyeblink_coeff_path=None

    if ref_pose is not None:
        if ref_pose == ref_eyeblink: 
            ref_pose_coeff_path = ref_eyeblink_coeff_path
        else:
            ref_pose_videoname = os.path.splitext(os.path.split(ref_pose)[-1])[0]
            ref_pose_frame_dir = os.path.join(save_dir, ref_pose_videoname)
            os.makedirs(ref_pose_frame_dir, exist_ok=True)
            print('3DMM Extraction for the reference video providing pose')
            ref_pose_coeff_path, _, _ =  preprocess_model.generate(ref_pose, ref_pose_frame_dir, args.preprocess, source_image_flag=False)
    else:
        ref_pose_coeff_path=None

    #audio2ceoff
    batch = get_data(first_coeff_path, audio_path, device, ref_eyeblink_coeff_path, still=args.still)
    coeff_path = audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path)

    # 3dface render
    if args.face3dvis:
        from src.face3d.visualize import gen_composed_video
        gen_composed_video(args, device, first_coeff_path, coeff_path, audio_path, os.path.join(save_dir, '3dface.mp4'))
    
    #coeff2video
    data = get_facerender_data(coeff_path, crop_pic_path, first_coeff_path, audio_path, 
                                batch_size, input_yaw_list, input_pitch_list, input_roll_list,
                                expression_scale=args.expression_scale, still_mode=args.still, preprocess=args.preprocess, size=args.size)
    
    result = animate_from_coeff.generate(data, save_dir, pic_path, crop_info, \
                                enhancer=args.enhancer, background_enhancer=args.background_enhancer, preprocess=args.preprocess, img_size=args.size)
    
    shutil.move(result, save_dir+'.mp4')
    print('The generated video is named:', save_dir+'.mp4')

    if not args.verbose:
        shutil.rmtree(save_dir)

    

# 외부에서 사용할 수 있는 run_sadtalker 함수
def run_sadtalker(face_path, audio_path,
                 checkpoint_dir=r"C:\Artech5\0.Main\checkpoints",
                 result_dir=r"C:\Artech5\Image_Box\Image3",
                 pose_style=0, batch_size=7, size=512, expression_scale=1.0,
                 input_yaw=None, input_pitch=None, input_roll=None,
                 enhancer=None, background_enhancer=None,
                 cpu=False, face3dvis=False, still=False, preprocess='crop',
                 verbose=False, old_version=False):
    """
    face_path: 변환된 얼굴 이미지 경로 (ex: face2)
    audio_path: 음성 파일 경로 (ex: first_voice)
    return: 생성된 talking video mp4 경로 (성공 시), 실패 시 None
    """
    class Args:
        pass
    args = Args()
    args.driven_audio = audio_path
    args.source_image = face_path
    args.ref_eyeblink = None
    args.ref_pose = None
    args.checkpoint_dir = checkpoint_dir
    args.result_dir = result_dir
    args.pose_style = pose_style
    args.batch_size = batch_size
    args.size = size
    args.expression_scale = expression_scale
    args.input_yaw = input_yaw
    args.input_pitch = input_pitch
    args.input_roll = input_roll
    args.enhancer = enhancer
    args.background_enhancer = background_enhancer
    args.cpu = cpu
    args.face3dvis = face3dvis
    args.still = still
    args.preprocess = preprocess
    args.verbose = verbose
    args.old_version = old_version
    args.net_recon = 'resnet50'
    args.init_path = None
    args.use_last_fc = False
    args.bfm_folder = './checkpoints/BFM_Fitting/'
    args.bfm_model = 'BFM_model_front.mat'
    args.focal = 1015.
    args.center = 112.
    args.camera_d = 10.
    args.z_near = 5.
    args.z_far = 15.
    if torch.cuda.is_available() and not args.cpu:
        args.device = "cuda"
    else:
        args.device = "cpu"
    try:
        main(args)
        # 결과 mp4 파일 경로 추정
        from time import strftime
        save_dir = os.path.join(result_dir, strftime("%Y_%m_%d_%H.%M.%S"))
        video_path = save_dir + '.mp4'
        if os.path.exists(video_path):
            return video_path
        else:
            # 혹시라도 이름이 다를 경우, 가장 최근 mp4 반환
            mp4s = sorted(glob(os.path.join(result_dir, '*.mp4')), key=os.path.getmtime, reverse=True)
            return mp4s[0] if mp4s else None
    except Exception as e:
        print(f"[ERROR] SadTalker 실행 실패: {e}")
        return None

