# Vehicle Financing Bench-Screening Tool

A browser-based Chapter 13 vehicle-financing review tool. The substantive calculation and review-item logic is written in Python and runs locally in the browser through Pyodide.

The tool calculates LTV, trade-in equity, amount-financed reconciliation, equal-payment schedule checks, PTI/DTI, and user-entered APR benchmark comparisons. It does not determine whether financing should be approved or whether additional shopping is required.

No database, login, analytics, or case-history storage is used. Refreshing or closing the page clears the entries.

The KBB button opens Kelley Blue Book's consumer vehicle-value page in a separate tab. It does not scrape KBB or use an unlicensed valuation API.