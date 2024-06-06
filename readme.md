# Character Lora Development App
Automating the building of LoRA datasets and the testing of LoRA models.

## Project Goal
To automate as much of the tedious process of building and testing a character lora as possible. To produce dataset worthy images that are as close in likeness to the reference inputs as possible. 

## MVP
A local CLI utility that interacts with a local A1111 instance.

- Takes an original full body reference nude and it's half, bust, and close up crops and outputs a large batch of generations across a variety of dimensions using the inputs as controlnet references.
- At least one output in any arbitrary prompt batch is within one or two minor corrections worth of tolerance to the reference image
- The outputs include a wide variety across pose, expression, and style


## Usage:
- Create a new project directory with the full, half, bust, and close up reference shots. Include what shot it is in the filename itself.
- Expected reference image aspect ratios:
    - Full & Half: 2x3
    - Bust: 4x5
    - Close: 1x1
- Expected reference minimum resolution: 640px (shortest side)
- Create a json file with 'positive' and 'negative' properties that contain the base character description tokens
- Add style prompt tokens to styles.py
- Add additional artist style tokens to artists.py
- Run `python3 main.py "path/to/project/folder"`



### Stretch Goals
- Clothing
- Programmatic augmentation tool to run on final edited selections to further increase dataset quality (black and white, hypersaturation, rotation, blurred)