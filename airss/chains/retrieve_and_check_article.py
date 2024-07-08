# pylint: disable = no-name-in-module
"""

"""
import os
from typing import Any, Optional

from dotenv import load_dotenv
from google.auth.transport.urllib3 import Request
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate, PromptTemplate,
)
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
import langchain
import vertexai

from nltk import word_tokenize
from vertexai.preview.generative_models import GenerativeModel
from langchain_google_vertexai import ChatVertexAI

from google.oauth2.service_account import Credentials

load_dotenv()

PROJECT_ID = "api-project-794879078210"  # @param {type:"string"}
REGION = "us-central1"  # @param {type:"string"}
MODEL_NAME = "gemini-1.5-flash-001"

dir_path = str(os.path.dirname(os.path.realpath(__file__)))

key_path = os.path.join(os.path.dirname(__file__), 'api-project-794879078210-49cbe6a49fd0.json')

credentials = Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
if credentials.expired:
    credentials.refresh(Request())

# Initialize Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=REGION)

model = ChatVertexAI(
    model=MODEL_NAME,
    temperature=0,
    max_tokens=None,
    max_retries=6,
    stop=None,
)

system_prompt = """
I will provide you with text scraped using BeautifulSoup4 from a news website. Please perform following checks, 
focusing on Norwegian and English texts, but applicable to other languages as well: 

1. Ensure that at least one of the 'required_keywords' I provide is found within the text. This search must be case-sensitive and confirm to the 
semantic meaning of the keyword. For example, accept 'Skjold' when it refers to a city, not a shield. 

2. Confirm that none of the 'exclusion_keywords' are present in the text, bearing the same case sensitivity and contextual accuracy. 
Return a boolean value based on these conditions: - True if at least one 'required_keyword' is correctly found and no 
'exclusion_keywords' are detected. - False if these conditions are not met.

============================================
article = {article}
required_keywords = {required_keywords}
exclusion_keywords = {exclusion_keywords}
============================================

RETURN ONLY TRUE OR FALSE
"""

report_schemas = [
    ResponseSchema(
        name="keyword_found",
        description="Keyword has been found in the article"
    )
]

output_parser = StructuredOutputParser.from_response_schemas(report_schemas)
format_instructions = output_parser.get_format_instructions()

prompt = PromptTemplate(
    input_variables=[
        "article",
        "required_keywords",
        "exclusion_keywords"
    ],
    template=system_prompt,
    partial_variables={
        "format_instructions": format_instructions,
    },
)


class RetrieveCheckArticleInput(BaseModel):
    article: str
    required_keywords: str
    exclusion_keywords: str


class RetrieveCheckArticleOutput(BaseModel):
    output: Any


retrieve_and_check_article_chain = LLMChain(
    llm=model,
    prompt=prompt,
)


def filter_keywords(feed_text: str, keywords: list[str], negative_keywords: list[str]) -> bool:
    if len(keywords) < 0 and len(negative_keywords) < 0:
        return True

    for word in word_tokenize(feed_text):
        # Check if the word matches any of the negative keywords
        if any(neg_keyword.lower() == word for neg_keyword in negative_keywords):
            return False

        # Check if the word matches any of the positive keywords
        checker = (keyword == word or keyword.lower() == word or keyword.replace(' ',
                                                                                 '') == word or keyword.lower() == word.replace(
            "#", "").lower() or (" " in keyword and keyword.lower() in feed_text.lower()) for keyword in keywords)
        if any(checker):
            return True

    return False


def filter_articles(data: RetrieveCheckArticleInput):
    first_filter = filter_keywords(feed_text=data["article"], keywords=data["required_keywords"],
                                   negative_keywords=data["exclusion_keywords"])

    if first_filter is True:
        return retrieve_and_check_article_chain.invoke({
            **data
        })

    return first_filter


retrieve_and_check_article_runnable = RunnableLambda(filter_articles).with_types(
    input_type=RetrieveCheckArticleInput,
)
