# piemaker

Blends ETFs to make a trading 212 compatible pie

## Files preperation

Works with .xls or .xlsx files only.

From the excell file remove everything except the main security table and columns' names.  
This includes anything above and below that table, excluding columns' names.

## Options

Custom securities can be added with weight and delimited by a comma. eg TSLA 3, XLNX 2.5  
Initial/Final refers to at which stage those added by the user will be incorporated.   
Entry with Final set entry will not be scaled nor averaged and will appear as entered at the end product.   
Entry with Initial set will be treated as if another excel was loaded and that was one if it's entries, if entry already exist this weight will be averaged and scaled.

ETFs can be given weights too.

Replicated/blended ETF can be split across mutliple pies, if so some pies might have unused space at the end and some securities might have been not included due to rounding pushing overall fill up.

## Troubleshooting
Checks against T212 to see whether a given security is ISA or fractional, might return a wrong result if there is another security with the same ticker on another exchange.

If nothing happens it might mean one of the excell files has columns for "ticker" and "weight" named as something I haven't come across before.
Finding columns representing "ticker"/"weight" and renaming them to "ticker"/"weight" should fix it.

There is no timeout handling so very rarely there is no response and you'd need to submit build request again.

## Running 

to run: python main_gui.py or python3 main_gui.py

It will require pandas and xlrd to be installed with pip.

There is a mac (mac_exec) and windows (windows_exec) binaries which worked natively on my mac and on windows VM. 
Not sure why the mac executable appears as a directory but it worked after cloning. Binaries were build with py installer.

pyinstaller build command windows: 
pyinstaller main_gui.py —onefile  --noconsole
pyinstaller build command mac: 
pyinstaller --onefile main_gui.py  --add-binary='/System/Library/Frameworks/Tk.framework/Tk':'tk' --add-binary='/System/Library/Frameworks/Tcl.framework/Tcl':'tcl' --noconsole


