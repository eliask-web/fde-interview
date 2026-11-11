# Rubric checklist

The review step checks every item below before the prototype is called done. Each item needs a yes, plus where it lives in the code.

| # | Item | What counts as done | Where |
|---|---|---|---|
| 1 | Deployment | Runs locally with one command, and is deployed on Railway with a working URL. Repo pushed to GitHub. | |
| 2 | LLM evaluation | A golden set of 8 to 10 questions, scored with DeepEval, with a printed results table. | |
| 3 | Multi-agent orchestration | At least two agents with different jobs, routed by a LangGraph graph. | |
| 4 | Embedding model | Documents chunked and embedded, stored in Chroma, and retrieved by meaning. | |
| 5 | Framework | LangGraph used for the flow. Able to explain why it was chosen. | |
| 6 | Memory | Short-term: the conversation history carries across turns. Long-term, if time allows: a saved fact about the user. | |
| 7 | Guardrails | Input: off-topic and prompt injection handling. Output: answers only from sources, with citations. Low confidence goes to a human. | |
| 8 | Front end | A Streamlit chat that a client could use. | |
| 9 | Non-technical visual | A page with no technical words: the manual process before, and how the agent makes it easier after. | |
| 10 | Tool call | At least one real tool call, where the model decides to call a function. | |

## Questions the architect may ask

- Why this framework, and what else did you consider?
- Why this embedding model and this chunk size?
- How do you know the answers are right?
- What happens when retrieval finds nothing?
- How would this scale to a real client, and what would it cost?
- How would you secure it: data access, prompt injection, and leakage?
- What would you build next with one more week?
