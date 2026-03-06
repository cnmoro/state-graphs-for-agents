import asyncio
import json
import copy
import urllib.request
from openai import AsyncOpenAI
from ddgs import DDGS

STEP_UNDERSTAND = "Understand"
STEP_RESEARCH   = "Research"
STEP_BUILD      = "BuildItinerary"
STEP_REVIEW     = "Review"
STEP_END        = "END"

class StateGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.entry_point = None

    def add_node(self, name, func):
        self.nodes[name] = func
        self.edges[name] = set()

    def add_edge(self, from_node, to_node):
        self.edges[from_node].add(to_node)

    def set_entry(self, name):
        self.entry_point = name

    async def run(self, state, max_steps=50):
        """Run the state machine asynchronously."""
        current = self.entry_point
        path = []

        for _ in range(max_steps):
            path.append(current)

            allowed_steps = list(self.edges[current])
            next_node, state = await self.nodes[current](state, allowed_steps)

            if next_node == STEP_END:
                path.append(STEP_END)
                return state, path

            if next_node not in self.edges[current]:
                raise ValueError(f"Illegal transition: '{current}' -> '{next_node}'")

            current = next_node

        raise RuntimeError("Max steps reached.")

    def run_sync(self, state, max_steps=50):
        """Run the state machine synchronously (blocks until complete)."""
        return asyncio.run(self.run(state, max_steps))

    def to_mermaid(self):
        """Generates a Mermaid markdown string to visualize your graph."""
        lines = ["graph TD"]
        for node, edges in self.edges.items():
            for edge in edges:
                lines.append(f"    {node} --> {edge}")
        return "\n".join(lines)

client = AsyncOpenAI()
MODEL  = "gpt-4.1-mini"

tool_registry = {}
function_registry = {}

def tool(node: str, description: str, params: dict):
    def decorator(fn):
        tool_registry.setdefault(node, []).append({
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": params,
                    "required": list(params.keys())
                }
            }
        })
        function_registry[node] = fn 
        return fn
    return decorator

@tool(
    node=STEP_UNDERSTAND,
    description="Extract all user requirements to build a trip profile.",
    params={
        "destination":   {"type": "string"},
        "duration_days": {"type": "integer"},
        "budget":        {"type": "string", "enum": ["budget", "mid-range", "luxury"]},
        "interests":     {"type": "array", "items": {"type": "string"}}
    }
)
def build_trip_profile(destination, duration_days, budget, interests):
    daily_cost = {"budget": 50, "mid-range": 150, "luxury": 500}[budget]
    total_money = daily_cost * duration_days
    
    profile = (
        f"Trip to {destination} for {duration_days} days.\n"
        f"Total Budget: ${total_money} (${daily_cost}/day).\n"
        f"Focus heavily on: {', '.join(interests)}."
    )
    
    print(f"    [Action] Python calculated budget: ${total_money}")
    return profile

@tool(
    node=STEP_RESEARCH,
    description="Search the internet for top attractions and food.",
    params={
        "search_query": {"type": "string", "description": "What to type into the search engine"}
    }
)
def search_the_internet(search_query):
    print(f"    [Action] Python is Googling: '{search_query}'...")
    results = DDGS().text(search_query, max_results=2)
    return [website["body"] for website in results]

@tool(
    node=STEP_BUILD,
    description="Create the schedule.",
    params={
        "itinerary": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day":       {"type": "integer"},
                    "morning":   {"type": "string"},
                    "afternoon": {"type": "string"},
                    "evening":   {"type": "string"}
                }
            }
        }
    }
)
def save_schedule_to_computer(itinerary):
    file_name = "My_Vacation.txt"
    with open(file_name, "w") as file:
        file.write("--- YOUR TRIP --- \n\n")
        for day in itinerary:
            file.write(f"Day {day['day']}:\n  Morning: {day['morning']}\n  Afternoon: {day['afternoon']}\n  Evening: {day['evening']}\n\n")

    print(f"    [Action] Python created a real file on your computer named: {file_name}")
    return "File successfully created."

@tool(
    node=STEP_REVIEW,
    description="Review the destination and check the weather.",
    params={
        "destination":     {"type": "string"}
    }
)
def check_live_weather(destination):
    print(f"    [Action] Python is checking the live weather in {destination}...")
    try:
        url = f"https://wttr.in/{destination}?format=3"
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        live_weather = urllib.request.urlopen(request).read().decode('utf-8').strip()
    except Exception:
        live_weather = "Weather API failed."
        
    print(f"    [Action] The weather right now is: {live_weather}")
    return live_weather

def make_node(node_name: str):
    async def node_fn(state: dict, allowed_steps: list) -> tuple[str, dict]:
        print(f"\n[{node_name}] AI is thinking...")

        dynamic_tools = copy.deepcopy(tool_registry[node_name])

        dynamic_tools[0]["function"]["parameters"]["properties"]["next_node"] = {
            "type": "string",
            "enum": allowed_steps,
            "description": "You MUST choose the next step from these options."
        }
        dynamic_tools[0]["function"]["parameters"]["required"].append("next_node")

        messages = [
            {"role": "system", "content": f"You are in step: '{node_name}'. Use your tool."},
            {"role": "user",   "content": state["user_request"]},
        ]
        if state["context"]:
            messages.append({"role": "system", "content": f"History: {json.dumps(state['context'])}"})

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=dynamic_tools,
            tool_choice="required",
        )

        ai_variables = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        next_node = ai_variables.pop("next_node")

        python_function = function_registry[node_name]
        python_result = await asyncio.to_thread(python_function, **ai_variables)

        state["context"][node_name] = {
            "what_the_ai_decided": ai_variables,
            "what_python_actually_did": python_result
        }

        return next_node, state

    return node_fn

def build_flow() -> StateGraph:
    flow = StateGraph()

    for node_name in function_registry.keys():
        flow.add_node(node_name, make_node(node_name))

    flow.set_entry(STEP_UNDERSTAND)

    # Create the allowed transitions between steps
    # E.g. allow a step to go back to a previous step if needed, or skip steps if the AI thinks it's best.
    # E.g. allow a step to go to itself (maybe retry or other scenario)
    flow.add_edge(STEP_UNDERSTAND, STEP_RESEARCH) # Forward
    flow.add_edge(STEP_RESEARCH,   STEP_REVIEW) # Forward
    flow.add_edge(STEP_REVIEW,     STEP_BUILD) # Forward
    flow.add_edge(STEP_BUILD,      STEP_UNDERSTAND) # Backtrack allowed
    flow.add_edge(STEP_BUILD,      STEP_RESEARCH) # Backtrack allowed
    flow.add_edge(STEP_BUILD,      STEP_END) # Finish

    return flow

async def main_async():
    """Entry point demonstrating async usage."""
    initial_state = {
        "user_request": "Plan a 3-day trip to Kyoto. Mid-range budget. I love ancient temples and local street food.",
        "context": {},
    }

    flow = build_flow()
    print(flow.to_mermaid())

    # graph TD
    #     Understand --> Research
    #     Research --> Review
    #     BuildItinerary --> Understand
    #     BuildItinerary --> END
    #     BuildItinerary --> Research
    #     Review --> BuildItinerary

    final_state, path = await flow.run(initial_state)
    return final_state, path


def main_sync():
    """Entry point demonstrating sync usage."""
    initial_state = {
        "user_request": "Plan a 3-day trip to Kyoto. Mid-range budget. I love ancient temples and local street food.",
        "context": {},
    }

    flow = build_flow()
    print(flow.to_mermaid())

    # graph TD
    #     Understand --> Research
    #     Research --> Review
    #     BuildItinerary --> Understand
    #     BuildItinerary --> END
    #     BuildItinerary --> Research
    #     Review --> BuildItinerary

    final_state, path = flow.run_sync(initial_state)
    return final_state, path
