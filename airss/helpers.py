import math
import os
import tempfile
import textwrap
import time
from datetime import datetime

import PIL
import openai
import pytz
import requests as requests
from feedgen.feed import FeedGenerator
import re
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# import msgspec

openai.api_key = "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"


def generate_rss_content(feed):
    fg = FeedGenerator()
    fg.load_extension("media", rss=True)
    fg.id('https://www.infokanal.com/feed/rss/ai.xml')
    fg.title('infokanal RSS feed')
    fg.link(href='https://www.infokanal.com/feed/rss/ai.xml')
    fg.description('infokanal RSS feed')
    fg.lastBuildDate(datetime.now(tz=pytz.timezone('Europe/Oslo')))

    for entry in feed:
        fe = fg.add_entry()
        if entry.source_feed_id:
            fe.id(entry.source_feed_id)
        if entry.title:
            fe.title(entry.title)
        if entry.article_url:
            fe.link(href=entry.article_url, rel='alternate')
        if entry.preamble:
            fe.summary(entry.preamble)
        if entry.pub_date:
            fe.pubDate(entry.pub_date)
        if entry.image_url:
            fe.enclosure(entry.image_url, 0, 'image/jpeg')
            fe.media.thumbnail({'url': entry.image_url, 'width': '200'},
                               group=None)
            fe.media.content({'url': entry.image_url, 'width': '400'},
                             group=None)

    rss_str = fg.rss_str(pretty=True)
    return rss_str


def join_feed_entries(feeds, serializer_data):
    joined_entries = []
    for index, feed in enumerate(feeds):
        feed_source_id = serializer_data[index]['id']
        for entry in feed.entries:
            joined_entries.append({
                "data": entry,
                "feed_source_id": feed_source_id,
                "feed_source_name": serializer_data[index]["feed_source_name"],
                "feed_id": serializer_data[index]["feed_source_name"] + "-" + entry["id"]
            })
    return joined_entries


def parse_published_date(date_string):
    date_formats = ['%a, %d %b %Y %H:%M:%S GMT', '%a, %d %b %Y %H:%M:%S %z']
    norway_timezone = pytz.timezone('Europe/Oslo')

    for date_format in date_formats:
        try:
            datetime_obj = datetime.strptime(date_string, date_format)
            datetime_obj = datetime_obj.replace(tzinfo=pytz.timezone('GMT')).astimezone(norway_timezone)
            return datetime_obj
        except ValueError:
            continue
    return None


def rephrase_news_with_openai(article):
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                              messages=[
                                                  {"role": "system",
                                                   "content": "You are a journalist that make a news story in "
                                                              "norwegian language only and results should be only in"
                                                              "three lines and add this attributes (title=...\n preamble=...\n "
                                                              "text=...)."},
                                                  {"role": "user",
                                                   "content": f"create a news story in norwegian based on this article object:\n{article['data']}\n"}])
    time.sleep(30)
    result = completion.choices[0].message.content.strip().replace('"', '')
    pattern = r'title=(.*?)\n{1,2}preamble=(.*?)\n{1,2}text=(.*)'
    match = re.search(pattern, result)

    if match:
        story = {
            'title': match.group(1),
            'preamble': match.group(2),
            'text': match.group(3),
        }

        image_url = ""
        links = article['data'].get('links', [])
        for link in links:
            if link.get('type') == 'image/jpeg' and link.get('rel') == 'enclosure':
                image_url = resize_image(link.get('href'))

        if image_url == "":
            image_url = generate_base64_image(story['title'])

        pub_date = article['data'].get('published')

        if pub_date:
            pub_datetime = parse_published_date(pub_date)
        else:
            pub_datetime = None

        return {
            "source_id": article['feed_source_id'],
            "article_url": article['data']["link"],
            "pub_date": pub_datetime,
            "source_feed_id": article['feed_source_name'] + "-" + article['data']['id'],
            "image_url": image_url,
            **story
        }


def generate_base64_image(text, width=600, height=200, font_size=16, padding_top=10):
    # Create a new image with the specified width and height
    image = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(image)

    # Load a font for drawing the text
    font = ImageFont.truetype("arial.ttf", font_size)

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


def resize_image(image_url):
    target_size_kb = 100
    try:
        # Download the image from the URL
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))

        # Calculate the current file size in KB
        current_size_kb = len(response.content) // 1024

        # Check if resizing is required
        if current_size_kb <= target_size_kb:
            # No resizing required, directly convert to base64
            base64_image = convert_image_to_base64(img)
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

def convert_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format='JPEG')
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return image_base64


def is_base64_image(data):
    try:
        decoded_data = base64.b64decode(data)
        image = Image.open(io.BytesIO(decoded_data))
        image.verify()
        return True
    except:
        return False
