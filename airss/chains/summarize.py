import json
import os

import pydantic
from langchain.chains.llm import LLMChain
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, \
    HumanMessagePromptTemplate

from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai.chat_models import ChatOpenAI
from nltk import word_tokenize
import langchain

from airss.chains.retrieve_and_check_article import retrieve_and_check_article_chain
from airss.functions.scrapper import Scrapper

api_key = os.getenv("OPENAI_APIKEY")

MODEL_NAME = "gpt-4o"


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


llm = ChatOpenAI(model=MODEL_NAME, temperature=0, model_kwargs={"top_p": 0})

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
    "You are an investigative journalist for a leading Norwegian newspaper, and you have just received a detailed "
    "article that contains crucial information on a recent political scandal. Your task is to meticulously summarize "
    "this article in Norwegian. Focus on ensuring the summary is clear, concise, and free of any potentially "
    "distracting elements such as HTML, CSS, or JavaScript scripts, as well as advertisements. Your summary should "
    "consist of a compelling title (not exceeding 15 words), a concise preamble (one sentence), and an engaging "
    "article body (100 to 150 words). Ensure that the language used is uniquely styled to avoid any resemblance to "
    "the original text. Remember, the summary should be in Norwegian, and any brand names or personal names "
    "originally in English should remain unchanged. How will you craft this summary to maintain the integrity and "
    "essence of the original article while making it accessible and engaging for your Norwegian readership"
    "\nReply without additional context"
    "Only returns and replies with valid, iterable RFC8259 compliant JSON in your responses and don't make "
    "any multiple lines in the response"
    "{format_instructions}"

    "Please rewrite the following text in a unique style. The text is in Norwegian. Here is "
    "the text:{article_body}\n",

    partial_variables={
        "format_instructions": format_instructions,
    },
)

chain = LLMChain(llm=llm, prompt=prompt)


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
