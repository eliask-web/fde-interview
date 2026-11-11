# Company briefing assistant

## Problem

Analysts read 100-plus-page 10-Ks and 10-Qs by hand to brief on a company. It takes hours, is hard to check, and is easy to get wrong.

## Flow

**Fetch → Validate → Summarize → Render**, one LangGraph graph:

1. **Fetch:** Claude decides to call `get_stock_quote` (yfinance) and `get_recent_filings` (SEC EDGAR), with retries.
2. **Validate:** Plain Python checks the data. A failure stops the run.
3. **Summarize:** Claude writes the briefing from the filings only, with citations.
4. **Render:** Streamlit shows the status strip, the quote, the briefing, and a follow-up chat.

## Why it's trustworthy

- Nothing is summarized until validation passes.
- Every briefing and chat answer cites its filing. If the answer isn't there, it says "not in the filings."
- No buy, sell or hold advice. Instructions hidden in filing text are ignored.
- After 3 failed fetches it stops and flags `needs_human` instead of guessing.
- Every run leaves files in `out/<TICKER>/`, and LangSmith traces each step.

## Next steps

- More tickers, plus 8-Ks and earnings call transcripts.
- Side-by-side comparisons across companies and years.
- A scored evaluation on the golden set of 10 questions (already written).
- Scheduled refresh when new filings land.
