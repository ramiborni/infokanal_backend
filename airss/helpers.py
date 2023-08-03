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

from nltk import word_tokenize

from airss.models import RssFeedAiSettings
from airss.scrapper import choose_scraping_method

# import msgspec

openai.api_key = os.getenv("OPENAI_APIKEY")

def filter_results(feed_text: str, keywords, negative_keywords) -> bool:
    for word in word_tokenize(feed_text):
        # Check if the word matches any of the negative keywords
        if any(neg_keyword.lower() == word for neg_keyword in negative_keywords):
            return False

        # Check if the word matches any of the positive keywords
        if any(keyword == word or keyword.lower() == word or keyword.replace(' ',
                                                                             '') == word or keyword.lower() == word.replace(
            "#", "").lower() or (" " in keyword and keyword.lower() in feed_text.lower()) for keyword in keywords):
            return True

    return False


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
        if entry.text:
            fe.content(entry.text + f"\nSaken var først omtalt på - {entry.source.feed_source_name}")
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


def transform_article_with_ai(article, method_name):
    transformed_article = None  # Add this line

    # Execute the appropriate scraping method based on the source of the article
    keywords_settings = RssFeedAiSettings.objects.all()
    article_body = choose_scraping_method(method_name, article)
    if article_body is not None and filter_results(article_body, keywords_settings[0].keywords,
                                                   keywords_settings[0].negative_keywords):
        # Initiate a chat with the OpenAI GPT-3.5-16K model and provide it with the instructions and the article text
        chat_log = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": "As a journalist, you are tasked with rewording a given article in Only Norwegian "
                               "language, Do not write anything in english or any other language unless the attributes. "
                               "The rephrased version should include a title, preamble, and article text, all in a unique "
                               "style that doesn't resemble the original text. The outputs should be given in three lines "
                               "with the attributes (title=...\n preamble=...\n text=...), the title should be max 15 "
                               "words and in one sentence, the preamble should be max 1 sentences and the text should be "
                               "article body and it "
                               "should be max 150 words. keep in mind that every article is sent potentially has some "
                               "html,css,js scripts and you have to remove them and keep only the a article body, "
                               "also do not ever write a text in English unless it's a brandname or person's name "
                               "that's in english, also ignore any text that may look an ad and out of context of the "
                               "article"
                },
                {
                    "role": "user",
                    "content": f"Please rewrite the following text in a unique style. The text is in Norwegian. Here is "
                               f"the text:\n{article_body}\n"
                }
            ]
        )
        # Pause for 30 seconds to wait for the AI response
        time.sleep(30)

        # Extract the AI's response and clean it
        ai_response = chat_log.choices[0].message.content.strip().replace('"', '')

        pattern = r'title=(.*?)\n{1,2}preamble=(.*?)\n{1,2}text=(.*)'

        match = re.search(pattern, ai_response)

        # If the AI response matches the expected pattern, extract the transformed title, preamble, and text
        if match:
            transformed_article = {
                'title': match.group(1),
                'preamble': match.group(2),
                'text': match.group(3),
            }

        # Try to find an image in the article links, resize it, and convert it to base64. If no image is found, generate a new image.
        image_url = ""
        links = article['data'].get('links', [])
        for link in links:
            if link.get('type') == 'image/jpeg' and link.get('rel') == 'enclosure':
                image_url = resize_image(link.get('href'))
                if image_url is None:
                    print(transformed_article['title'])
                    image_url = generate_base64_image(transformed_article['title'])

        if image_url == "":
            image_url = generate_base64_image(transformed_article['title'])

        # Parse the publication date, if it exists
        pub_date = article['data'].get('published')
        pub_datetime = parse_published_date(pub_date) if pub_date else None

        # Return the transformed article with additional information
        return {
            "source_id": article['feed_source_id'],
            "article_url": article['data']["link"],
            "pub_date": pub_datetime,
            "source_feed_id": article['feed_source_name'] + "-" + article['data']['id'],
            "image_url": image_url,
            **transformed_article
        }
    else:
        return None


def generate_base64_image(text, width=600, height=200, font_size=16, padding_top=10):
    # Create a new image with the specified width and height
    image = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(image)

    # Load a font for drawing the text
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)

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

        # If the image has an alpha channel, convert it to RGB
        if img.mode in ('RGBA', 'LA'):
            img = img.convert('RGB')

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
