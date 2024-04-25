import webuiapi
from app_config import SD_API_URL, SD_API_PORT

WEBUI_API = webuiapi.WebUIApi(host=SD_API_URL, port=SD_API_PORT)

# Current task:
"""
Implement a basic test mode. Given a config file with lora names and a character prompt,

"""



def test_mode(config: dict) -> None:
    pass

if __name__ == "__main__":
    # Get mode and config from CLI

    # launch selected mode with provided config or default if missing
    pass

"""
Notes:
- use a "run" folder to just run through all configs that are in a folder back to back

"""