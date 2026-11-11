# Demo script

Five steps, in this order, from the Dashboard tab. Expected results describe what a passing run looks like. Read figures off the screen only. Never quote a number that isn't shown.

## 1. Happy path on AAPL

**Do:** Enter `AAPL` and click **Brief me** (or open `?ticker=AAPL`).

**Expect:** The status strip goes green step by step: Fetch, Validate, Summarize, Render. The quote card shows Apple's price. The briefing summarizes the latest 10-K (fiscal year ended September 26, 2026) and cites its filings by name. It ends with the "not investment advice" footer.

**Point out:** In the LangSmith trace, the model chose to call `get_stock_quote` and `get_recent_filings` itself. The run files are in `out/AAPL/`.

## 2. Follow-up question

**Ask (in the chat under the briefing):** "What were Apple's total net sales last fiscal year, and how did that compare with the year before?"

**Expect:** "$478.8 billion in fiscal 2026, up 15% from $416.2 billion," citing the AAPL 10-K. Then ask "And iPhone?" The answer ($254.1 billion, up 21%) shows the chat remembered the company and the year without being told again.

**Point out:** Chat history is passed into each answer, and every answer names its filing.

## 3. Buy-or-sell refusal

**Ask:** "Should I buy Apple stock right now?"

**Expect:** A polite refusal. The assistant doesn't give buy, sell or hold advice, and offers what the filings say instead.

## 4. TSLA fails validation

**Do:** Enter `TSLA` and click **Brief me**.

**Expect:** Fetch runs, then Validate turns red and the run stops. No summary is written, so nothing unchecked reaches the reader. The reason is shown on screen and saved in `out/TSLA/validation.json`.

**Point out:** Validation is plain Python with no AI. Summarize only runs when it passes.

## 5. Fetch failure from an empty SEC_USER_AGENT

**Setup (off camera):** Restart the app with the variable blanked for this run only: `SEC_USER_AGENT= streamlit run app/main.py`. Never open `.env` on screen.

**Do:** Enter `JPM` and click **Brief me**.

**Expect:** The SEC refuses requests without a user agent. Fetch retries 3 times, then the status shows `needs_human` and the run stops. No briefing is invented.

**Afterwards:** Restart the app normally before taking questions.
