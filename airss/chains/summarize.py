import json
import os

import pydantic
from google.auth.transport.urllib3 import Request
from langchain.chains.llm import LLMChain
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, \
    HumanMessagePromptTemplate

from langchain_core.runnables import RunnableLambda
from nltk import word_tokenize
import langchain

import vertexai
from vertexai.preview.generative_models import GenerativeModel

from airss.chains.retrieve_and_check_article import retrieve_and_check_article_chain
from airss.functions.scrapper import Scrapper
from google.oauth2.service_account import Credentials

PROJECT_ID = "api-project-794879078210"  # @param {type:"string"}
REGION = "us-central1"  # @param {type:"string"}
MODEL_NAME = "gemini-1.5-flash-001"

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


class SummarizeInput(pydantic.BaseModel):
    url: str
    source_id: str
    source_name: str
    is_require_login: str
    summarize_from_rss_feed: str
    keywords: list[str]
    negative_keywords: list[str]
    feed_body: str
    require_keywords_verification: bool
    is_manual_selection: bool


report_schemas = [
    ResponseSchema(
        name="title",
        description="News Story's title"
    ),
    ResponseSchema(
        name="preamble",
        description="News Story preamble",
    ),
    ResponseSchema(
        name="news_body",
        description="News Story Text",
    ),
]
output_parser = StructuredOutputParser.from_response_schemas(report_schemas)
format_instructions = output_parser.get_format_instructions()

prompt = langchain.PromptTemplate(
    input_variables=["article_body"],
    template=
    '''
    "As a journalist, you are tasked with rewording a given article in Only Norwegian "

                                   "language, Do not write anything in english or any other language unless the attributes. "

                                   "The rephrased version should include a title, preamble, and article text, all in a unique "

                                   "style that doesn't resemble the original text. The outputs should be given in three lines "

                                   "with the attributes (title=...\n preamble=...\n news_body=...), the title should be max 15 "

                                   "words and in one sentence, the preamble should be max 1 sentences and the text should be "

                                   "article body and it "

                                   "should be max 150 words. keep in mind that every article is sent potentially has some "

                                   "html,css,js scripts and you have to remove them and keep only the a article body, "

                                   "also do not ever write a text in English unless it's a brandname or person's name "

                                   "that's in english, also ignore any text that may look an ad and out of context of the "

                                   "article"

You shouldn't reply with something like "Politisk skandale ryster Norge: Nye avsløringer avdekket"

and Always try to understand the news article

Reply without additional context

    "\nReply without additional context"
    "Only returns and replies with valid, iterable RFC8259 compliant JSON in your responses and don't make "
    "any multiple lines in the response"
    "{format_instructions}"

    "Please rewrite the following text in a unique style. The text is in Norwegian. Here is "
    "the text:{article_body}\n"
    ''',

    partial_variables={
        "format_instructions": format_instructions,
    },
)

chain = LLMChain(llm=model, prompt=prompt)


def check_article_with_ai(text: str, keywords: list[str], negative_keywords: list[str] = ['None']):
    result = retrieve_and_check_article_chain.invoke({
        "article": text,
        "required_keywords": ", ".join(keywords),
        "exclusion_keywords": ", ".join(negative_keywords)
    })

    return result["text"].lower() == "true"


def filter_results(feed_text: str, keywords, negative_keywords) -> bool:
    try:
        result = check_article_with_ai(feed_text, keywords, negative_keywords)
        return result
    except Exception as e:
        print(e)
        return None


def summarize_news(data: SummarizeInput):
    try:
        """summarize_news function for only parsing json in the returned output
            by the langchain

            Args:
                data (SummarizeInput): [description]

            Returns:
                dict[str, Any]
            """

        article_body = None

        scrapper = Scrapper()

        if data["summarize_from_rss_feed"] == True:
            if data["is_require_login"]:
                source_name = data["source_name"]
                url = data["url"]
                article_body = scrapper.filter_article_body_source(source=source_name, url=url)
            else:
                article_body = scrapper.scrape_without_source(source_name=data["source_name"], source_url=data["url"])
        else:
            article_body = data["feed_body"]

        filter_result = False

        if data["require_keywords_verification"] is True and data["is_manual_selection"] is False:
            filter_result = filter_results(article_body, data["keywords"], data["negative_keywords"])
        else:
            filter_result = True

        if article_body is not None and filter_result is True:
            result = chain.invoke({"article_body": article_body})

            print(result)

            return json.loads(
                str(result["text"]).replace("\n", "").replace("json", "").replace("```", "").replace("\n", "").replace(
                    "```", "")
            )

        return None

    except Exception as e:
        print("SUMMARIZE LANGCHAIN ERROR:")
        print(e)
        return None


summarize_agent_executor_chain = RunnableLambda(summarize_news).with_types(
    input_type=SummarizeInput,
)

'''

report_schemas = [
    ResponseSchema(name="SEO Analysis", description="Detailed analysis of the website's SEO performance"),
    ResponseSchema(
        name="Keyword Optimization",
        description="Recommendations for keyword usage and optimization",
    ),
    ResponseSchema(
        name="Readability Improvements",
        description="Suggestions to improve the readability of the website's content",
    ),
    ResponseSchema(
        name="Content Structure Optimization",
        description="Guidelines to optimize the structure of the website's content",
    ),
    ResponseSchema(
        name="Actionable Recommendations",
        description="Practical steps to improve SEO, content, and technical aspects of the website",
    ),
]
output_parser = StructuredOutputParser.from_response_schemas(report_schemas)
format_instructions = output_parser.get_format_instructions()

prompt = ChatPromptTemplate(
    messages=[
        SystemMessage(content=SEO_CHECKER_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{url}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ],
    partial_variables={
        "format_instructions": format_instructions,
    },
)

'''
