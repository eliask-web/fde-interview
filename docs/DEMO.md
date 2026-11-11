# Demo script

Five steps, in this order. Run them in one chat session so step 2 can use the memory from step 1. Expected answers describe what a passing run looks like. Confirm the exact figures against the cited filing during the dry run and never read a number out loud that isn't on screen.

## 1. Happy path on AAPL

**Ask:** "What were Apple's main risks in its latest annual report?"

**Expect:** A short answer listing the main risk factors from Apple's latest 10-K, with the filing named under the answer in the Sources list (for example, the AAPL 10-K and its filing date). Confidence is high, with no note to check with a person.

**Point out:** The sources line. Every claim comes from a named filing.

## 2. Follow-up question (memory)

**Ask:** "How does that compare with the quarter before?"

**Expect:** The assistant knows "that" means Apple's risks from step 1 without being told the company again. It answers from the latest 10-Q and the 10-K and cites both. If the quarterly filing says nothing new, it says so instead of inventing a change.

**Point out:** The conversation carries across turns through the checkpointer.

## 3. Buy-or-sell refusal (guardrail)

**Ask:** "Should I buy NVDA stock right now?"

**Expect:** A polite refusal: the assistant summarizes what the filings say and does not give investment advice. It offers a related question it can answer, such as NVIDIA's reported revenue trend, with sources.

**Point out:** Off-topic and advice requests are refused before any retrieval or tool call.

## 4. TSLA fails validation

**Ask:** "Summarize Tesla's latest 10-K."

**Expect:** The ticker check rejects TSLA because it isn't in the covered set (AAPL, NVDA, JPM). The assistant says it doesn't cover that company and lists the companies it does cover. It does not guess or answer from general knowledge.

**Point out:** The input check runs before retrieval, so an unsupported ticker never reaches the model as a "fact."

## 5. Fetch failure from an empty SEC_USER_AGENT

**Setup (before the demo, off camera):** Restart the app with `SEC_USER_AGENT` set to an empty value. Do not open or show `.env` on screen. Set it in the shell for this run only, for example `SEC_USER_AGENT= streamlit run app/main.py`.

**Ask:** "Get JPMorgan's latest quarterly filing."

**Expect:** The model calls the fetch tool. The SEC refuses requests without a user agent, so the tool returns an error. The assistant says plainly that it couldn't reach the SEC filings service and suggests checking the configuration or asking a person. It does not make up a filing or cite one it didn't get. Confidence is low.

**Point out:** A failed tool call is reported as a failure, not hidden behind a confident answer.

**Afterwards:** Restart the app with the normal environment before taking questions.
