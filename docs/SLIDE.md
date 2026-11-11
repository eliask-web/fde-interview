# SEC filings assistant

## Problem

Analysts read 100-plus-page 10-Ks and 10-Qs by hand to answer simple questions. It's slow, hard to check, and easy to get wrong.

## Flow

**Gather → Check → Summarize → Show**

1. **Gather:** The action agent decides to call the SEC fetch tool for the ticker.
2. **Check:** The ticker is validated against the covered set (AAPL, NVDA, JPM), and failed fetches are caught.
3. **Summarize:** The retriever agent pulls the relevant passages from Chroma, and Claude answers from those passages only.
4. **Show:** The reviewer agent checks the answer against its sources. The Streamlit chat shows the answer with the filings it came from.

## Why it's trustworthy

- Every answer cites the filing it came from.
- When the filings don't answer the question, it says so instead of guessing.
- It refuses buy-or-sell advice, off-topic requests, and instructions hidden in documents.
- Low-confidence answers come with a note to check with a person.
- DeepEval scores faithfulness and relevancy on a golden set, and LangSmith traces every run.

## Next steps

- More tickers, plus 8-Ks and earnings call transcripts.
- Side-by-side comparisons across companies and years.
- Long-term memory for each analyst's watchlist.
- Scheduled refresh when new filings land.
