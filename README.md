# Vehicle Financing Bench-Screening Tool

A browser-based Chapter 13 vehicle-financing review tool. The substantive calculation and review-item logic is written in Python and runs locally in the browser through Pyodide.

The tool organizes vehicle price and value, proposed financing terms, financed add-ons, financing path, and credit-tier context. It calculates price-to-value differences, LTV, down-payment share, financed add-on share, and a Q1 2026 Experian used-vehicle APR comparison for the selected VantageScore 4.0 tier when that comparison is applicable.

Review flags identify defined arithmetic comparisons, such as cash price above the entered supported value, LTV above 100%, APR above the selected used-vehicle tier average, or a mismatch between an entered VantageScore 4.0 score and the selected tier. The tool does not determine whether financing should be approved, whether a transaction is reasonable, or whether additional shopping is required.

No database, login, analytics, or case-history storage is used. Refreshing or closing the page clears the entries.

The KBB button opens Kelley Blue Book's consumer vehicle-value page in a separate tab. It does not scrape KBB or use an unlicensed valuation API.