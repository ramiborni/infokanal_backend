# pylint: disable = no-name-in-module
"""

"""

from typing import Any, Optional

from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate, PromptTemplate,
)
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import langchain

from nltk import word_tokenize

load_dotenv()

MODEL_NAME = "gemini-pro"

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0, model_kwargs={"top_p": 0})

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
    llm=llm,
    prompt=prompt,
)


def filter_keywords(feed_text: str, keywords: list[str], negative_keywords: list[str]) -> bool:
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
