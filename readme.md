# Character Lora Development App
Automating the building of LoRA datasets and the testing of LoRA models.

## Project Goal
To automate the tedious process of building and testing a character lora. Through programmatic prompting via A1111 API, allow the creation of draft datasets and testing of LoRA models with just the input of a character's base description, and run entirely headless in the background over extended periods of time. Utilize A1111 to generate a large body of images such that a sufficient number of raws that are "close enough" can be selected and used for lora training of an original character. By automating the testing of a created lora, the lora's behavior and ideal conditions can be programmatically identified without long manual prompting sessions. Additionally, testing can potentially yield images that are suitable to be appended to the existing dataset, supporting an iterative approach to dataset creation. 

## MVP
A local CLI utility that interacts with a local A1111 instance.
#### Build mode:

Given a base positive and negative prompt (without any quality modifiers, embeddings, etc) that strictly describes the features of a character, output a large body of images spanning the dimensions described below. 

#### Test mode:
Given a list of character lora version names (that are loaded into A1111 already) and a character's base prompt (positive and negative), generate a large body of images spanning the dimensions described below for each 0.1 increment in lora strength for each lora version (epoch checkpoint).

## Dimensions of a Dataset
- Pose
- Angle
- Clothing
- Background
- Expression
- Image Dimension

## Automating each dimension
Shot angle, clothing, background, and expressions can all be automated with Dynamic Prompts' wildcards. Image dimension is simple integer tuple constants. Pose can be automated through Controlnet Openpose libraries.

## Building vs Testing
The wildcard and pose libraries should be completely distinct from each other. This is to ensure that the lora under test can properly handle novel prompts outside its dataset. 


### Notes
- Combinatorial generation could be set on dynamic prompts to ensure the full possible list of combinations are explored between angle, clothing, background, and expression. This will have the side effect of creating large batches that are more likely to contain enough images for an initial dataset.