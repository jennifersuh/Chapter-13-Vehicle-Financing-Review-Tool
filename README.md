# Vehicle Financing Bench-Screening Tool

A browser-based Chapter 13 vehicle-financing review tool. The substantive calculation and review-item logic is written in Python and runs locally in the browser through Pyodide.

The tool organizes vehicle price and value information, proposed financing terms, financed extras, financing source, and borrower credit context. It calculates price-to-value differences, LTV, down-payment share, financed-add-on and financed-extra shares, and a used-vehicle APR comparison against the Q1 2026 Experian VantageScore 4.0 tier averages documented in the accompanying research memo.

The calculated review is a screening aid, not a decision rule. Review flags identify defined arithmetic comparisons or record inconsistencies and do not determine whether financing should be approved or whether additional shopping is required.

No database, login, analytics, or case-history storage is used. Refreshing or closing the page clears the entries. A completed review can be printed for a hearing file or future reference.

The KBB button opens Kelley Blue Book's consumer vehicle-value page in a separate tab. It does not scrape KBB or use an unlicensed valuation API.