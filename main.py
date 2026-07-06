import os
import uuid
import requests
import json
from groq import Groq
from dotenv import load_dotenv
from database.mongo import (
    load_session,save_session,get_cached_result,save_cached_result,save_report
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def calculate(expression: str) -> str:
    try:
        expression = expression.replace(",", "")
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


def search_web(query: str) -> str:
    url = "https://api.tavily.com/search"
    
    payload = {
        "api_key": os.getenv("TAVILY_API_KEY"),
        "query": query,
        "max_results": 3,
        "include_answer": True
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append(
                f"Title: {item['title']}\n"
                f"URL: {item['url']}\n"
                f"Summary: {item['content']}\n"
            )
        
        return "\n".join(results)
    
    except Exception as e:
        return f"Search error: {str(e)}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for current, real-time information. Use when the user asks about recent events, live data, or anything not in your training knowledge. Do NOT use for mathematical calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform mathematical calculations. ALWAYS use this tool for any arithmetic, formula, or numerical computation — never calculate in your head, even for simple expressions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate, e.g. '47 * 89'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

session_id = str(uuid.uuid4())
print(f"Session ID: {session_id}\n")
user_input = input("What would you like to research? ")

existing_messages = load_session(session_id)

if existing_messages:
    messages = existing_messages
    messages.append({'role':'user','content':user_input})
else:
    messages = [
        {
            "role": "system",
            "content": """You are a helpful research assistant with access to two tools:
    1. search_web — use for current, real-time information
    2. calculate — use for ANY mathematical computation, never compute in your head

    Think step by step before deciding which tool to use.
    If you can answer directly from your training knowledge, do so without calling any tool.
    Always cite your sources when you use search_web.
    For questions requiring external facts combined with math, ALWAYS search for the fact first, then calculate.
    Never assume numerical values from your training data — always verify with search_web first.
    Always use the exact number returned by the calculate tool in your final answer, never round it."""
        },
        {
            "role": "user",
            "content": user_input
        }
    ]
max_iterations = 10
iterations = 0

print("\nAgent is thinking...\n")

while iterations < max_iterations:
    iterations += 1
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    # Did the model want to call a tool or give a final answer?
    if response_message.tool_calls:
        
        # Append model's decision to history
        messages.append(response_message)
        
        # Execute each tool call
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"Calling tool: {tool_name}")
            print(f"Arguments: {tool_args}\n")
            
            if tool_name == "search_web":
                query = tool_args["query"]
                # Check cache first
                cached = get_cached_result("search_web", query)
                if cached:
                    print("Cache hit — skipping Tavily call\n")
                    result = cached
                else:
                    result = search_web(query)
                    save_cached_result("search_web", query, result)

            elif tool_name == "calculate":
                expression = tool_args["expression"]
                # Check cache first
                cached = get_cached_result("calculate", expression)
                if cached:
                    print("Cache hit — skipping calculation\n")
                    result = cached
                else:
                    result = calculate(expression)
                    save_cached_result("calculate", expression, result)

            else:
                result = "Tool not found"
                print(f"Observation: {result[:200]}...\n")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
    
    else:
        # Final answer
        print("=" * 50)
        print("FINAL ANSWER:")
        print("=" * 50)
        print(response_message.content)
        break

else:
    # Loop hit max_iterations without a final answer
    print("Agent reached max iterations without a final answer.")
    print("Last observation was:", messages[-1]["content"][:300])