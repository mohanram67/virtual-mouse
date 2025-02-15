import os

if os.path.exists('paste.txt'):
    with open('paste.txt', 'r', encoding='utf-8') as file:
        app_code = file.read()
else:
    app_code = "# paste.txt file not found."

with open('application.py', 'w', encoding='utf-8') as file:
    file.write(app_code)

print("Created application.py from paste.txt")