
# State Graph Agents

A **minimal framework for building structured AI agents** using a **state graph**—with **no external dependencies required**.

This project was implemented to **simplify agentic control** by avoiding heavy libraries and unnecessary complexity. Instead of letting an AI agent run uncontrolled loops or opaque chains, this project forces the agent to move through **explicit states with clearly defined transitions**. Each state can call tools, update context, and decide what step should happen next.

The result is an agent that is:

* **Deterministic in structure**
* **Flexible in reasoning**
* **Easy to debug**
* **Easy to visualize**

All of this is implemented in a single file: **`state_graph_agents.py`** (with a basic example).

---

# The Problem

Most AI agent frameworks today fall into one of these patterns:

| Pattern                          | Problem                                     |
| -------------------------------- | ------------------------------------------- |
| Free-loop agents                 | Hard to control, unpredictable execution    |
| Chain pipelines                  | Too rigid, no branching or backtracking     |
| Complex orchestration frameworks | Heavy abstractions and steep learning curve |

In real-world systems you often need something in between:

* An **AI that can reason**
* But within a **controlled workflow**
* With **clear allowed transitions**

Examples:

* Data pipelines
* Research assistants
* Autonomous tool workflows
* Structured LLM applications
* Multi-step reasoning systems

This project provides a **simple solution**: a **state graph agent**.

---

# What This Project Does

It lets you define:

* **States** (nodes)
* **Allowed transitions** (edges)
* **Tools available per state**

The AI:

1. Runs inside a specific state
2. Uses a tool
3. Chooses the next allowed state
4. Moves through the graph until it finishes

The graph acts as **guardrails** for the agent.

---

# Example Workflow

This demo agent plans a trip:

```
Understand → Research → Review → BuildItinerary → END
```

But the agent can also **backtrack** if needed.

Graph visualization:

```
graph TD
    Understand --> Research
    Research --> Review
    Review --> BuildItinerary
    BuildItinerary --> Understand
    BuildItinerary --> Research
    BuildItinerary --> END
```

Example reasoning path:

```
Understand
Research
Review
BuildItinerary
END
```

Or a more complex one:

```
Understand
Research
Review
BuildItinerary
Research
Review
BuildItinerary
END
```

---

# Why This Is Useful

This architecture solves several real-world problems.

### Controlled AI Autonomy

The model can reason freely, but **only within allowed transitions**.

No infinite loops.
No unexpected steps.

---

### Tool Execution

Each state exposes specific tools.

Example tools in this demo:

* Extract trip requirements
* Search the internet
* Check live weather
* Save itinerary to a file

---

### Observability

Each step stores:

```
state["context"]
```

Which contains:

```
{
  step_name: {
      what_the_ai_decided,
      what_python_actually_did
  }
}
```

This makes debugging extremely easy.

---

### Graph Visualization

You can export the workflow to **Mermaid diagrams**.

```
print(flow.to_mermaid())
```

Output:

```
graph TD
    Understand --> Research
    Research --> Review
    Review --> BuildItinerary
    BuildItinerary --> END
```

---

# Project Structure

The entire framework lives in one file:

```
state_graph_agents.py
```

Open this file to see:

* The **StateGraph engine**
* The **tool decorator**
* Example tools
* Node execution logic
* Example workflow

The code is intentionally compact so it is easy to understand.

---


# Installation

No installation or external libraries are required. This project is **dependency-free** and runs out of the box with standard Python.

---


# Running the Example

Run the demo (requires duckduckgo search - just for the example).

```python
python state_graph_agents.py
```

The agent will:

1. Understand the trip request
2. Search for attractions
3. Check live weather
4. Build an itinerary
5. Save it to a file

Example output:

```
[Understand] AI is thinking...
[Action] Python calculated budget: $450

[Research] AI is thinking...
[Action] Python is Googling...

[Review] AI is thinking...
[Action] Python is checking the live weather...

[BuildItinerary] AI is thinking...
[Action] Python created a real file on your computer named: My_Vacation.txt
```

---

# How It Works

## 1 — Define States

Each state has a node function.

```
flow.add_node("Understand", make_node("Understand"))
```

---

## 2 — Define Transitions

Control how the agent can move:

```
flow.add_edge("Understand", "Research")
flow.add_edge("Research", "Review")
flow.add_edge("Review", "BuildItinerary")
flow.add_edge("BuildItinerary", "END")
```

You can also allow backtracking.

---

## 3 — Define Tools

Tools are attached to states using a decorator.

Example:

```
@tool(
    node="Research",
    description="Search the internet",
    params={
        "search_query": {"type": "string"}
    }
)
def search_the_internet(search_query):
```

The AI must call this tool when inside that state.

---

## 4 — Run the Graph

Async:

```
final_state, path = await flow.run(initial_state)
```

Sync:

```
final_state, path = flow.run_sync(initial_state)
```

---

# Why This Approach Is Powerful

This design provides:

**Structure from graphs**

```
State → Allowed Transitions → State
```

**Flexibility from LLM reasoning**

```
LLM decides which edge to follow
```

**Safety from constraints**

```
Illegal transitions are rejected
```

---

# Ideal Use Cases

This pattern works well for:

* AI research agents
* Data analysis workflows
* Multi-step tool orchestration
* ETL reasoning pipelines
* Autonomous assistants with guardrails
* Experimenting with agent architectures

---

# If You Want to Understand Everything

Open:

```
state_graph_agents.py
```

The entire framework is implemented there and designed to be **readable in one sitting**.

---


# Philosophy

The goal of this project is to **avoid heavy frameworks and dependencies**. It demonstrates that **structured AI agents can be extremely simple** when built on top of a clear concept:

**AI + State Graphs**

---

# License

MIT
