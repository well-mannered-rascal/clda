import requests
import sys
import os
import json
import base64
import random
import shutil

from PIL import Image
from datetime import datetime
from io import BytesIO
from app_config import SD_API_URL, SD_API_PORT
from wildcards.styles import STYLES
from wildcards.artists import ARTISTS
from wildcards.expressions import EXPRESSIONS
from wildcards.backgrounds import BACKGROUNDS


# TODO: These should all be configurable
BASE_URL = f"http://{SD_API_URL}:{SD_API_PORT}"
TXT2IMG = f"{BASE_URL}/sdapi/v1/txt2img"

OUTPUT_DIR = "./output"
MODELS = ["yiffymix_v36.safetensors [fb27ebf750]"]

COMMON_NEG = "colored sclera, blurry, soft focus, poor quality, bad quality, bad art, bad anatomy, bizarre anatomy, creepy, grotesque, nightmare, unsettling, text, artist name, signature"


"""
Roadmap:
    - finish configuring controlnet base payloads
"""



# def test_mode() -> None:
#     # Refresh available loras
#     requests.post(f"http://{SD_API_URL}:{SD_API_PORT}/sdapi/v1/refresh-loras")

#     for model in MODELS:
#         WEBUI_API.util_set_model(model, False)
#         # For each lora version, test a variety of prompts and resolutions
#         for lora in LORA_NAMES:
#             weight = 1
#             base_positive = f"{TRIGGER}, <lora:{lora}:{weight}>"

#             result = WEBUI_API.txt2img(
#                 prompt=base_positive,
#                 negative_prompt=BASE_NEGATIVE,
#                 sampler_name="Euler a",
#                 steps=25,
#                 width=640,
#                 height=960
#             )
            
#             for image in result.images:
#                 image.show()

def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')


def decode_and_save_base64(base64_str, save_path):
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))


class ReferenceImage:
    def __init__(self, path: str):
        self._path = path
        self._name = os.path.basename(path)
        
        try:
            self._image = Image.open(self._path)
        except Exception as e:
            print(e)

    def path(self) -> str:
        return self._path
    
    def image(self) -> Image.Image:
        return self._image

    def name(self) -> str:
        return self._name

class DatasetBuilder:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def load_project(self) -> bool:
        """
        Load any reference images and a base character description found in the project directory into memory.

        Returns
        ----------
        True if successful, false otherwise
        """

        try:
            # load all file names
            file_paths = [f.lower() for f in os.listdir(self.project_dir) 
                     if os.path.isfile(os.path.join(self.project_dir, f))]
            
            # identify the specific reference types and prompt by file name
            for path in file_paths:
                path = os.path.join(self.project_dir, path)
                if "full" in path:
                    self.full_ref = ReferenceImage(path)
                elif "half" in path:
                    self.half_ref = ReferenceImage(path)
                elif "bust" in path:
                    self.bust_ref = ReferenceImage(path)
                elif "close" in path:
                    self.close_ref = ReferenceImage(path)
                elif "prompt" in path:
                    with open(path, 'r') as f:
                        prompt_obj = json.load(f)
                        self.base_positive = prompt_obj.get("positive")
                        self.base_negative = prompt_obj.get("negative")

        except Exception as e:
            print(e)
            return False
        
        return True
    
    def build_payload(
            self, expression: str, 
            background: str,
            reference: ReferenceImage,
            pose: ReferenceImage|None,
            style: str) -> dict:
        """
        Given expression and background prompt snippets, construct the full payload
        necessary for a text2image API POST request. Adds the reference to the proper
        controlnet module payload objects.
        """
        # config value TODO
        # the short side
        desired_prompt_res = 512
        
        # Get ref image dimensions and aspect ratio.
        ref_height = reference.image().height
        ref_width = reference.image().width
        
        if ref_height > ref_width:
            prompt_width = desired_prompt_res
            prompt_height = (ref_height * desired_prompt_res) / ref_width
        else:
            prompt_height = desired_prompt_res
            prompt_width = (ref_width * desired_prompt_res) / ref_height
        

        # TODO: This should be configurable :P
        payload = {
            "batch_size": 1,
            "cfg_scale": 7,
            "height": prompt_height,
            "width": prompt_width,
            "n_iter": 1,
            "sampler_name": "Euler a",
            "steps": 25,

        }

        # If the style is RANDOM, pull a random set of artist names from the wildcard,
        # otherwise pass style directly into the prompt
        if style == "RANDOM":
            style = ""
            num_artists = random.randint(2, 6)
            for _ in range(0, num_artists):
                style += f"{ARTISTS[random.randint(0, len(ARTISTS) - 1)]}, "

        if pose:
            pose_tags = pose.name().split(".")[0]
        else:
            pose_tags = ""

        payload["prompt"] = f"{self.base_positive}, {expression}, ({pose_tags}), {background}, {style}, (best quality, masterpiece)"
        payload["negative_prompt"] = f"{self.base_negative}, {COMMON_NEG}"

        # convert reference image to bytes
        ref_file = BytesIO()
        reference.image().save(ref_file, "png")
        ref_bytes = ref_file.getvalue()
        ref_b64 = base64.b64encode(ref_bytes).decode('utf-8')

        

        # Controlnet 
        payload["alwayson_scripts"] = {
            "ControlNet": {
                "args": [
                    # Reference
                    {
                        "control_mode" : "Balanced",
                        "enabled" : True,
                        "guidance_end" : 0.75,   # make this configurable
                        "guidance_start" : 0,
                        "hr_option" : "Both",
                        "image" : ref_b64,
                        "model" : "None",
                        "module" : "reference_only",
                        "pixel_perfect" : False,
                        "processor_res" : 0.5,
                        "resize_mode" : "Crop and Resize",
                        "save_detected_map": False,
                        "threshold_a" : 0.5,
                        "threshold_b" : 0.5,
                        "weight" : 0.75     # make this configurable
                    },
                    {
                        "control_mode": "My prompt is more important",
                        "enabled": True,
                        "guidance_end": 0.25,    # variable
                        "guidance_start": 0,
                        "hr_option": "Both",
                        "image": ref_b64,
                        "input_mode": "simple",
                        # "mask_image": null,
                        "model": "control_v11p_sd15_lineart [43d4be0d]",
                        "module": "lineart_standard (from white bg & black line)",
                        "pixel_perfect": True,
                        # "processor_res": 512,
                        "resize_mode": "Crop and Resize",
                        "save_detected_map": False,
                        "threshold_a": 100,
                        "threshold_b": 200,
                        "use_preview_as_input": False,
                        "weight": 0.25
                    },
                    
                ]
            }
        }

        if pose:
            # convert pose reference image to bytes
            pose_file = BytesIO()
            pose.image().save(pose_file, "png")
            pose_bytes = pose_file.getvalue()
            pose_b64 = base64.b64encode(pose_bytes).decode('utf-8')

            payload["alwayson_scripts"]["ControlNet"]["args"].append(
                {
                    "control_mode": "ControlNet is more important",
                    "enabled": True,
                    "guidance_end": 0.6,    # variable
                    "guidance_start": 0,
                    "hr_option": "Both",
                    "image": pose_b64,
                    "input_mode": "simple",
                    "model": "control_v11p_sd15_openpose [cab727d4]",
                    "module": "None",
                    "pixel_perfect": True,
                    # "processor_res": 512,
                    "resize_mode": "Just Resize",
                    "save_detected_map": False,
                    "threshold_a": 0.5,
                    "threshold_b": 0.5,
                    "weight": 1  # variable
                }
            )

        return payload

    def reference_workflow(
            self, reference_img: ReferenceImage, output_path: str, poses: str = ""):
        """
        Parameters
        ---------
        - reference_img: the image to use as reference
        - output_path: path to save this workflow run's images
        - poses: shot length keyword for which poses to use (if any) for this run. ("FULL", "HALF", "BUST", "CLOSE")
        """

        if poses:
            # load pose collection for the desired shot length
            # Prepend a 'None' so that the pose isn't applied for one iteration
            pose_imgs = [None]

            # load all file names
            file_paths = [f"./poses/{poses}/{f.lower()}" for f in os.listdir(f"./poses/{poses}") 
                     if os.path.isfile(os.path.join(f"./poses/{poses}", f))]

            for pose_path in file_paths:
                pose_imgs.append(ReferenceImage(pose_path))

        # build and send prompt payloads, capture results
        for style in STYLES:
            for pose in pose_imgs:
                for background in BACKGROUNDS:
                    for expression in EXPRESSIONS:
                        # build and send payload
                        payload = self.build_payload(expression, background, reference_img, pose, style)
                        response = requests.post(url=TXT2IMG, json=payload).json()
                        
                        # save results
                        for img_bytes in response.get("images", []):
                            path = os.path.join(output_path, f"{datetime.now()}.png")
                            decode_and_save_base64(img_bytes, path)

    def run(self):
        """
        Run the full dataset builder routine. Load the reference images from the
        project directory. For each reference, run the specific set of standard prompts
        for that image type (full, half, bust, face).
        """
        # load reference images
        if not self.load_project():
            print("Failed to load reference images.")
            return

        # Create run folder if not exists
        run_output_dir = os.path.join(self.project_dir, "dataset_builder_runs")
        os.makedirs(run_output_dir, exist_ok=True)

        # build output directory for this run
        self.run_output_path = os.path.join(run_output_dir, f"{datetime.now()}")
        os.mkdir(self.run_output_path)

        # copy prompt.json from project_dir into output dir
        shutil.copyfile(
            os.path.join(self.project_dir, "prompt.json"),
            os.path.join(self.run_output_path, "prompt.json"))

        # build and execute prompts for each reference
        
        if self.full_ref.image() is not None:
            # create output directory for this reference if not exists
            output_path = os.path.join(self.run_output_path, "FULL")
            os.mkdir(output_path)

            self.reference_workflow(self.full_ref, output_path, poses="FULL")

        if self.half_ref.image() is not None:
            # create output directory for this reference if not exists
            output_path = os.path.join(self.run_output_path, "HALF")
            os.mkdir(output_path)

            self.reference_workflow(self.half_ref, output_path, poses="HALF")
        
        if self.bust_ref.image() is not None:
            # create output directory for this reference if not exists
            output_path = os.path.join(self.run_output_path, "BUST")
            os.mkdir(output_path)

            self.reference_workflow(self.bust_ref, output_path, poses="BUST")
        
        if self.close_ref.image() is not None:
            # create output directory for this reference if not exists
            output_path = os.path.join(self.run_output_path, "CLOSE")
            os.mkdir(output_path)

            self.reference_workflow(self.close_ref, output_path, poses="CLOSE")




if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <working_dir_path>")
    path = sys.argv[1]

    dataset_builder = DatasetBuilder(path)
    dataset_builder.run()




"""
Notes:
- use a "run" folder to just run through all configs that are in a folder back to back

"""