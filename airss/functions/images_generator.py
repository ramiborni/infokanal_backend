import base64
import io
import math
import os
import tempfile
import textwrap

import PIL
from PIL import Image, ImageDraw, ImageFont
import requests as requests

import sys





class ImagesGenerator:


    @staticmethod
    def generate_base64_image(text: str, width=600, height=200, font_size=16, padding_top=10):
        # Create a new image with the specified width and height
        image = Image.new("RGB", (width, height), color="black")
        draw = ImageDraw.Draw(image)

        # Load a font for drawing the text

        font_path = ""

        if sys.platform.startswith('darwin'):  # macOS
            font_path = "~/Library/Fonts/DejaVuSans.ttf"
        elif sys.platform.startswith('linux'):  # Linux
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


        font = ImageFont.truetype(font_path, font_size)

        # Calculate the available height for drawing text (considering the padding)
        available_height = height - padding_top

        # Wrap the text to fit within the image width
        wrapped_text = textwrap.wrap(text, width=width)

        # Calculate the maximum number of lines that can fit within the available height
        max_lines = available_height // (font_size + 4)

        if len(wrapped_text) > max_lines:
            wrapped_text = wrapped_text[:max_lines]
            wrapped_text[-1] = wrapped_text[-1][: len(wrapped_text[-1]) - 3] + "..."

        # Draw the wrapped text on the image
        y = padding_top
        for line in wrapped_text:
            draw.text((10, y), line, fill="white", font=font)
            y += font_size + 4

        # Convert the image to base64
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return base64_image

    def resize_image(self, image_url):
        target_size_kb = 100
        try:
            # Download the image from the URL
            response = requests.get(image_url)
            img = Image.open(io.BytesIO(response.content))

            # If the image has an alpha channel, convert it to RGB
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')

            # Calculate the current file size in KB
            current_size_kb = len(response.content) // 1024

            # Check if resizing is required
            if current_size_kb <= target_size_kb:
                # No resizing required, directly convert to base64
                base64_image = self.convert_image_to_base64(img)
                return base64_image

            # Calculate the desired width and height based on the target size
            width, height = img.size
            aspect_ratio = width / height
            desired_width = int(math.sqrt(target_size_kb * 1024 * aspect_ratio))
            desired_height = int(desired_width / aspect_ratio)

            # Resize the image using the desired width and height
            resized_img = img.resize((desired_width, desired_height), PIL.Image.LANCZOS)

            # Save the resized image to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_filename = temp_file.name
                resized_img.save(temp_filename, format="JPEG", quality=90, optimize=True)

            # Convert the resized image to base64
            with open(temp_filename, "rb") as file:
                base64_image = base64.b64encode(file.read()).decode("utf-8")

            # Delete the temporary file
            os.remove(temp_filename)

            return base64_image
        except Exception as e:
            print("Error resizing image:", e)
            return None

    def convert_image_to_base64(self, image):
        buffered = io.BytesIO()
        image.save(buffered, format='JPEG')
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return image_base64

    def is_base64_image(self, data):
        try:
            decoded_data = base64.b64decode(data)
            image = Image.open(io.BytesIO(decoded_data))
            image.verify()
            return True
        except:
            return False


