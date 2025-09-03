
python3.12 -m venv .venv
Open de Command Palette

mac: ⇧⌘P

Win/Linux: Ctrl+Shift+P

Typ “Python: Select Interpreter” en druk Enter.
Kies de interpreter die bij jouw venv hoort:

Meestal zie je iets als “.venv (Python 3.x)” of “…/.venv/bin/python” (mac/Linux) of “….venv\Scripts\python.exe” (Windows).

Zie je ‘m niet? Klik “Enter interpreter path…” en blader naar:

mac/Linux: ./.venv/bin/python

Windows: .\.venv\Scripts\python.exe



source .venv/bin/activate
pip install -r requirements.txt
python Start\ Your\ Own/Trading_Script.py --file Start\ Your\ Own/chatgpt_portfolio_update.csv
