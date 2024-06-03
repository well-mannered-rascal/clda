from PIL import Image
import requests
import sys
import os
import json
import base64
from datetime import datetime
from io import BytesIO
from app_config import SD_API_URL, SD_API_PORT
from wildcards.styles import STYLES
from wildcards.expressions import EXPRESSIONS
from wildcards.backgrounds import BACKGROUNDS


# TODO: These should all be configurable
BASE_URL = f"http://{SD_API_URL}:{SD_API_PORT}"
TXT2IMG = f"{BASE_URL}/sdapi/v1/txt2img"

OUTPUT_DIR = "./output"
MODELS = ["yiffymix_v36.safetensors [fb27ebf750]"]

COMMON_NEG = "blurry, soft focus, poor quality, bad quality, bad art, bad anatomy, bizarre anatomy, creepy, grotesque, nightmare, unsettling"


"""
Roadmap:
    - finish configuring controlnet base payloads
    - handle txt2img response
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

class CharacterReference:
    def __init__(self, path: str):
        self._path = path
        
        try:
            self._image = Image.open(self._path)
        except Exception as e:
            print(e)

    def path(self) -> str:
        return self._path
    
    def image(self) -> Image.Image:
        return self._image


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
                    self.full_ref = CharacterReference(path)
                elif "half" in path:
                    self.half_ref = CharacterReference(path)
                elif "bust" in path:
                    self.bust_ref = CharacterReference(path)
                elif "close" in path:
                    self.close_ref = CharacterReference(path)
                elif "prompt" in path:
                    with open(path, 'r') as f:
                        prompt_obj = json.load(f)
                        self.base_positive = prompt_obj.get("positive")
                        self.base_negative = prompt_obj.get("negative")

        except Exception as e:
            print(e)
            return False
        
        return True
    
    def build_payload(self, expression: str, background: str, reference: CharacterReference) -> dict:
        """
        Given expression and background prompt snippets, construct the full payload
        necessary for a text2image API POST request. Adds the reference to the proper
        controlnet module payload objects.
        """
        # TODO: This should be configurable :P
        payload = {
            "batch_size": 2,
            "cfg_scale": 7,
            "height": 980,
            "width": 640,
            "n_iter": 1,
            "sampler_name": "Euler a",
            "steps": 25
        }

        dynamic_artists = '{2-5$$__artists__}'
        payload["prompt"] = f"{self.base_positive}, {expression}, {background}, {dynamic_artists}"
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
                        "guidance_end" : 0.8,   # make this configurable
                        "guidance_start" : 0,
                        "hr_option" : "Both",
                        "image" : ref_b64, #f"{reference.image().tostring()}", # base64.b64encode(reference.image().tobytes()).decode('utf-8'),
                        "model" : "None",
                        "module" : "reference_only",
                        "pixel_perfect" : False,
                        "processor_res" : 0.5,
                        "resize_mode" : "Crop and Resize",
                        "save_detected_map": False,
                        "threshold_a" : 0.5,
                        "threshold_b" : 0.5,
                        "weight" : 0.85     # make this configurable
                    },
                    {
                        "control_mode": "Balanced",
                        "enabled": True,
                        "guidance_end": 0.3,    # variable
                        "guidance_start": 0,
                        "hr_option": "Both",
                        "image": ref_b64,
                        "input_mode": "simple",
                        # "mask_image": null,
                        "model": "control_v11p_sd15_canny [d14c016b]",
                        "module": "canny",
                        "pixel_perfect": True,
                        # "processor_res": 512,
                        "resize_mode": "Crop and Resize",
                        "save_detected_map": False,
                        "threshold_a": 100,
                        "threshold_b": 200,
                        "use_preview_as_input": False,
                        "weight": 0.4
                    }
                    # Worry about pose later :P
                    # {
                    #     "control_mode": "ControlNet is more important",
                    #     "enabled": True,
                    #     "guidance_end": 0.6,    # variable
                    #     "guidance_start": 0,
                    #     "hr_option": "Both",
                    #     "image": {
                    #         # "image": "base64image placeholder",
                    #     },
                    #     "input_mode": "simple",
                    #     # "mask_image": null,
                    #     "model": "control_v11p_sd15_openpose [cab727d4]",
                    #     "module": "None",
                    #     "pixel_perfect": True,
                    #     # "processor_res": 512,
                    #     "resize_mode": "Just Resize",
                    #     "save_detected_map": False,
                    #     "threshold_a": 0.5,
                    #     "threshold_b": 0.5,
                    #     "weight": 0.85  # variable
                    # }
                ]
            }
        }

        return payload

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

        # build output directory for this run
        self.run_output_path = os.path.join(self.project_dir, f"{datetime.now()}")
        os.mkdir(self.run_output_path)


        # build prompts for each reference
        
        if self.full_ref.image() is not None:
            # create output directory for this reference if not exists
            full_ref_output_path = os.path.join(self.run_output_path, "FULL")
            os.mkdir(full_ref_output_path)

            # build and send prompt payloads, capture results
            for background in BACKGROUNDS:
                for expression in EXPRESSIONS:
                
                    # for pose in POSES

                    # build and send payload
                    payload = self.build_payload(expression, background, self.full_ref)
                    response = requests.post(url=TXT2IMG, json=payload).json()
                    

                    for img_bytes in response.get("images", []):
                        # decode response image bytes
                        result_img = Image.open(BytesIO(base64.b64decode(img_bytes)))
                        result_img.save(os.path.join(full_ref_output_path, f"{datetime.now()}"), "png")


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