# Default config values. 
# Make copies to specify custom configs and pass to CLI command without
# needing to change this file. (Not Implemented)

SD_API_URL = "127.0.0.1"
SD_API_PORT = 7860

# Map samplers to use and their desired step count
SAMPLERS = {
    "DPM++ 2M Karras": 25,
    "Euler a": 25
}

# width, height
IMAGE_DIMENSIONS = [
    (512, 512),
    (512, 768),
    (768, 512),
    (512, 640),
    (640, 512)
]

# put the names of your models here as they appear in A1111
SD_MODELS = [
    "arthemyComics_v60.safetensors [b9ca0fa8a9]" # delete me
]