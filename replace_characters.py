import os

# Файли, в яких будемо робити заміни
files = ['en.csv', 'en_conversations.csv']

# Словник замін
replacements = {
    'і': 'i',
    'І': 'I',
    'ї': 'ï',
    'є': 'е',
    'Є': 'E',
    'ґ': 'г',
    'Ґ': 'Г',
}

def replace_characters(text):
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text

for filename in files:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = replace_characters(content)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✔ Заміни виконано у файлі: {filename}")
    else:
        print(f"⚠ Файл не знайдено: {filename}")
