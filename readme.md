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
- Create a new project directory with the full, half, bust, and face reference shots. Include what shot it is in the filename itself.
- Create a json file with 'positive' and 'negative' properties that contain the base character description tokens
- Run `python3 main.py "path/to/project/folder"`



### Stretch Goals
- Clothing
- Backgrounds
- Programmatic augmentation tool to run on final edited selections to further increase dataset quality (black and white, hypersaturation, rotation, blurred)