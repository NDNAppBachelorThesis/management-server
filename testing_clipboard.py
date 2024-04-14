import time
import re
import pyperclip

RE_WS = re.compile(r'\s+')

RE_EMPH = re.compile(r"\\emph{([^{}]+)}", re.IGNORECASE)
RE_TEXTBF = re.compile(r"\\textbf{([^{}]+)}", re.IGNORECASE)
RE_ENQUOTE = re.compile(r"\\enquote{([^{}]+)}", re.IGNORECASE)
RE_FOOTNOTE = re.compile(r"\\footnote{([^{}]+)}", re.IGNORECASE)
RE_NEWLINE = re.compile(r"\s*\\newline\s*", re.IGNORECASE)

RE_CITE = re.compile(r"\\cite{[^{}]+}", re.IGNORECASE)
RE_REF = re.compile(r"\\ref{[^{}]+}", re.IGNORECASE)


def convert1():
    with open('tex_input.txt', 'r') as file:
        input_data = [l.strip() for l in file.readlines()]

    lines = [l for l in input_data if l and len(l) > 0]

    if len(lines) != 3:
        return False

    raw_url: str = lines[0]
    slug: str = lines[1].replace(' ', '-')
    title: str = lines[2]

    url = (raw_url
           .removesuffix('}}')
           .removesuffix('}')
           .removeprefix('\\footnote{')
           .removeprefix('\\url{')
           )

    with open('tex_output.txt', 'w') as file:
        file.write('\n'.join([
            f'@misc{{website:{slug},',
            f'  author = {{Quelle}},',
            f'  title = {{{title}}},',
            f'  howpublished = "\\url{{{url}}}",',
            f'  note = "[Abgerufen 01.2024]"',
            f'}}',
            f'',
            f'\\cite{{website:{slug}}}'
        ]))
        file.flush()

    return True


def replace_text(text: str):
    text = text.strip()
    text = text.replace('\r', '').replace('\n', ' ')
    text = RE_WS.sub(' ', text)
    text = RE_NEWLINE.sub('\n\n', text)
    text = text.replace(r'\%', '%')

    text = RE_EMPH.sub(r'\1', text)
    text = RE_TEXTBF.sub(r'\1', text)
    text = RE_ENQUOTE.sub(r'„\1“', text)
    text = RE_FOOTNOTE.sub(r'(\1)', text)

    text = RE_CITE.sub(r'<Zitat>', text)
    text = RE_REF.sub(r'1.2', text)

    text = text.strip()

    return text


def convert2():
    with open('tex_input.txt', 'r', encoding='UTF-8') as file:
        text = file.read()

    text = replace_text(text)

    with open('tex_output.txt', 'w', encoding='UTF-8') as file:
        file.write(text)

    return


def convert3():
    text_raw = pyperclip.waitForNewPaste()
    text_raw = pyperclip.paste()
    # if text_raw.endswith('\u2800'):
    #     return

    text = replace_text(text_raw)
    # text += '\u2800'

    # if text_raw != text:
    pyperclip.copy(text)

    return



if __name__ == '__main__':
    print('Starting conversion loop')

    while True:
        convert3()
        time.sleep(0.25)
