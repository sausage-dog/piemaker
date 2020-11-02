# piemaker
Blends ETFs to make a trading 212 compatible pie

Works with .xls or .xlsx files.

Remove except everything except the main security table including the columns' names.
This includes anything above and below that table.

You can select to split the replicated/blended ETF across mutliple pies.
If so some pies might have unused space at the end and some securities might have been not included due to rounding pushing overall fill up.

Checks against T212 to see whether a given security is ISA or fractional, might return a wrong result if there is another security with the same ticker on another exchange.

If nothing happens it might mean one of the excell files has columns for "ticker" and "weight" named as something I haven't come across before.
Finding columns representing "ticker"/"weight" and renaming them to "ticker"/"weight" should fix it.

Also there is no timeout handling so very rarely there is no response and you'd need to submit build request again.
