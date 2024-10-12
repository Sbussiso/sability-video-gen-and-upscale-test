import requests
import logging
from PIL import Image
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def resize_image(image_path, output_path, size):
    try:
        with Image.open(image_path) as img:
            img = img.resize(size, Image.LANCZOS)  # Use LANCZOS for high-quality downsampling
            img.save(output_path)
            logging.info(f"Image resized to {size} and saved as {output_path}")
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
        return False
    return True

def generate_video(image_path):
    logging.info(f"Starting video generation for image: {image_path}")
    try:
        with open(image_path, "rb") as image_file:
            response = requests.post(
                f"https://api.stability.ai/v2beta/image-to-video",
                headers={
                    "authorization": f"Bearer {os.getenv('STABLE_API_KEY')}"
                },
                files={
                    "image": image_file
                },
                data={
                    "seed": 0,
                    "cfg_scale": 1.8,
                    "motion_bucket_id": 127
                },
            )
    except Exception as e:
        logging.error(f"Error opening image file: {e}")
        return None

    if response.status_code == 200:
        logging.info("Video generation request successful.")
        return response.json().get('id')
    else:
        logging.error(f"Video generation request failed with status code: {response.status_code}")
        logging.error(f"Response content: {response.content}")
        return None

def fetch_video(generation_id):
    if not generation_id or len(generation_id) != 64:
        logging.error("Invalid generation ID received.")
        return

    logging.info(f"Fetching video with generation ID: {generation_id}")
    while True:
        response = requests.request(
            "GET",
            f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
            headers={
                'accept': "video/*",
                'authorization': f"Bearer {os.getenv('STABLE_API_KEY')}"
            },
        )

        if response.status_code == 202:
            logging.info("Generation in-progress, trying again in 10 seconds.")
            time.sleep(10)  # Wait for 10 seconds before retrying
        elif response.status_code == 200:
            logging.info("Generation complete!")
            with open("video.mp4", 'wb') as file:
                file.write(response.content)
            break
        else:
            logging.error(f"Failed to fetch video. Error: {response.json()}")
            break

if __name__ == "__main__":
    logging.info("Script started.")
    resized_image_path = "resized_image.png"
    if resize_image("generated_image.png", resized_image_path, (1024, 576)):
        generation_id = generate_video(resized_image_path)
        if generation_id:
            fetch_video(generation_id)
    logging.info("Script finished.")

