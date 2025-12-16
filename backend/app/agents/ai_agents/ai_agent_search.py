from dotenv import load_dotenv, find_dotenv

import os
from typing import Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from .web_operations import serp_search, reddit_search_api, reddit_post_retrieval
from .prompts import (
    get_reddit_analysis_messages, 
    get_google_analysis_messages,
    get_bing_analysis_messages,
    get_baidu_analysis_messages,
    get_reddit_url_analysis_messages,
    get_synthesis_messages
)

from typing import cast

load_dotenv(find_dotenv(usecwd=True), override=True)

#log("API KEY:", os.getenv("OPENAI_API_KEY"))
api_key = os.getenv("OPENAI_API_KEY")

llm = init_chat_model(
    "gpt-4o",
    model_provider="openai",
    api_key=api_key,
)

# -----------------------------------------------
#  Logging helper
# -----------------------------------------------
def log(message: str) -> None:
    log(f"[AGENT SEARCH] {message}")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_question: str | None
    google_results: str | None
    bing_results: str | None
    baidu_results: str | None
    reddit_results: str | None
    selected_reddit_urls: list[str] | None
    reddit_post_data: list | None
    google_analysis: str | None
    bing_analysis: str | None
    baidu_analysis: str | None
    reddit_analysis: str | None
    final_answer: str | None


class RedditURLAnalysis(BaseModel):
    selected_urls: List[str] = Field(description="List of Reddit URLs that contain valuable information for answering the user's question")


async def google_search(state: State):
    user_question = state.get("user_question", "")
    log(f"Searching Google for: {user_question}")

    google_results = await serp_search(user_question, engine="google")

    return {"google_results": google_results}


async def bing_search(state: State):
    user_question = state.get("user_question", "")
    log(f"Searching Bing for: {user_question}")

    bing_results = await serp_search(user_question, engine="bing")

    return {"bing_results": bing_results}

async def baidu_search(state: State):
    user_question = state.get("user_question", "")
    log(f"Searching Baidu for: {user_question}")

    baidu_results = await serp_search(user_question, engine="baidu")

    return {"baidu_results": baidu_results}


async def reddit_search(state: State):
    user_question = state.get("user_question", "")
    log(f"Searching Reddit for: {user_question}")

    reddit_results = await reddit_search_api(keyword=user_question)
    log(reddit_results)

    return {"reddit_results": reddit_results}

# The code snippet you provided is a Python script that sets up a chatbot capable of conducting
# multi-source research. Here is a breakdown of the key components and functionalities:

async def analyze_reddit_posts(state: State):
    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")

    if not reddit_results:
        return {"selected_reddit_urls": []}

    structured_llm = llm.with_structured_output(RedditURLAnalysis)
    messages = get_reddit_url_analysis_messages(user_question, reddit_results) 

    try:
        analysis_raw = structured_llm.invoke(messages) 
        analysis = RedditURLAnalysis.model_validate(analysis_raw)
        selected_urls = analysis.selected_urls 

        log("Selected URLs:")
        for i, url in enumerate(selected_urls, 1):
            log(f"   {i}. {url}")

    except Exception as e:
        log(e)
        selected_urls = []

    return {"selected_reddit_urls": selected_urls}


async def retrieve_reddit_posts(state: State):
    log("Getting reddit post comments")

    selected_urls = state.get("selected_reddit_urls", [])

    if not selected_urls:
        return {"reddit_post_data": []}

    log(f"Processing {len(selected_urls)} Reddit URLs")

    reddit_post_data = await reddit_post_retrieval(selected_urls)

    if reddit_post_data:
        log(f"Successfully got {len(reddit_post_data)} posts")
    else:
        log("Failed to get post data")
        reddit_post_data = []

    log(reddit_post_data)
    return {"reddit_post_data": reddit_post_data}


async def analyze_google_results(state: State):
    log("Analyzing google search results")

    user_question = state.get("user_question", "")
    google_results = state.get("google_results", "")

    messages = get_google_analysis_messages(user_question, google_results) 
    reply = await llm.ainvoke(messages)

    return {"google_analysis": reply.content}


async def analyze_bing_results(state: State):
    log("Analyzing bing search results")

    user_question = state.get("user_question", "")
    bing_results = state.get("bing_results", "")

    messages = get_bing_analysis_messages(user_question, bing_results)
    reply = await llm.ainvoke(messages)

    return {"bing_analysis": reply.content}

async def analyze_baidu_results(state: State):
    log("Analyzing baidu search results")

    user_question = state.get("user_question", "")
    baidu_results = state.get("baidu_results", "")

    messages = get_baidu_analysis_messages(user_question, baidu_results) 
    reply = await llm.ainvoke(messages)

    return {"baidu_analysis": reply.content}


async def analyze_reddit_results(state: State):
    log("Analyzing reddit search results")

    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")
    reddit_post_data = state.get("reddit_post_data", "")

    messages = get_reddit_analysis_messages(user_question, reddit_results, reddit_post_data)
    reply = await llm.ainvoke(messages)

    return {"reddit_analysis": reply.content}


async def synthesize_analyses(state: State):
    log("Combine all results together")

    user_question = state.get("user_question", "")
    google_analysis = state.get("google_analysis", "")
    bing_analysis = state.get("bing_analysis", "")
    baidu_analysis = state.get("baidu_analysis", "")
    reddit_analysis = state.get("reddit_analysis", "")

    messages = get_synthesis_messages(
        user_question, google_analysis, bing_analysis, baidu_analysis, reddit_analysis 
    )

    reply = await llm.ainvoke(messages)
    final_answer = reply.content

    return {"final_answer": final_answer, "messages": [{"role": "assistant", "content": final_answer}]}


graph_builder = StateGraph(State)

graph_builder.add_node("google_search", google_search)
graph_builder.add_node("bing_search", bing_search)
graph_builder.add_node("baidu_search", baidu_search)
graph_builder.add_node("reddit_search", reddit_search)
graph_builder.add_node("analyze_reddit_posts", analyze_reddit_posts)
graph_builder.add_node("retrieve_reddit_posts", retrieve_reddit_posts)
graph_builder.add_node("analyze_google_results", analyze_google_results)
graph_builder.add_node("analyze_bing_results", analyze_bing_results)
graph_builder.add_node("analyze_baidu_results", analyze_baidu_results)
graph_builder.add_node("analyze_reddit_results", analyze_reddit_results)
graph_builder.add_node("synthesize_analyses", synthesize_analyses)

graph_builder.add_edge(START, "google_search")
graph_builder.add_edge(START, "bing_search")
graph_builder.add_edge(START, "baidu_search")
graph_builder.add_edge(START, "reddit_search")

graph_builder.add_edge("google_search", "analyze_reddit_posts")
graph_builder.add_edge("bing_search", "analyze_reddit_posts")
graph_builder.add_edge("baidu_search", "analyze_reddit_posts")
graph_builder.add_edge("reddit_search", "analyze_reddit_posts")
graph_builder.add_edge("analyze_reddit_posts", "retrieve_reddit_posts")

graph_builder.add_edge("retrieve_reddit_posts", "analyze_google_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_bing_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_baidu_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_reddit_results")

graph_builder.add_edge("analyze_google_results", "synthesize_analyses")
graph_builder.add_edge("analyze_bing_results", "synthesize_analyses")
graph_builder.add_edge("analyze_baidu_results", "synthesize_analyses")
graph_builder.add_edge("analyze_reddit_results", "synthesize_analyses")

graph_builder.add_edge("synthesize_analyses", END)

graph = graph_builder.compile()


async def run_chatbot(user_input):
    log("Multi-Source Research Agent")


    #Cast the dict to the State type
    """     
        initial_state : State = cast(State, {
        "messages": [{"role": "user", "content": user_input}],
        "user_question": user_input,
        "google_results": None,
        "bing_results": None,
        "baidu_results": None,
        "reddit_results": None,
        "selected_reddit_urls": None,
        "reddit_post_data": None,
        "google_analysis": None,
        "bing_analysis": None,
        "baidu_analysis": None,
        "reddit_analysis": None,
        "final_answer": None,
    })
    
    """   
    initial_state : State = {
        "messages": [{"role": "user", "content": user_input}],
        "user_question": user_input,
        "google_results": None,
        "bing_results": None,
        "baidu_results": None,
        "reddit_results": None,
        "selected_reddit_urls": None,
        "reddit_post_data": None,
        "google_analysis": None,
        "bing_analysis": None,
        "baidu_analysis": None,
        "reddit_analysis": None,
        "final_answer": None,
    }
    


    log("\nStarting parallel research process...")
    log("Launching Google, Bing, and Reddit searches...\n")
    final_state = await graph.ainvoke(initial_state) 

    if final_state.get("final_answer"):
        log(f"\nFinal Answer:\n{final_state.get('final_answer')}\n")
        return final_state.get('final_answer')
    log("-" * 80)

