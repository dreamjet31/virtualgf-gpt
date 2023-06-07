'''

This is a library for formatting text outputs as nice HTML.

'''

import os
import re
import time
from pathlib import Path

import markdown
from PIL import Image, ImageOps

# This is to store the paths to the thumbnails of the profile pictures
image_cache = {}

with open(Path(__file__).resolve().parent / '../css/html_readable_style.css', 'r') as f:
    readable_css = f.read()
with open(Path(__file__).resolve().parent / '../css/html_4chan_style.css', 'r') as css_f:
    _4chan_css = css_f.read()
with open(Path(__file__).resolve().parent / '../css/html_cai_style.css', 'r') as f:
    cai_css = f.read()
with open(Path(__file__).resolve().parent / '../css/html_bubble_chat_style.css', 'r') as f:
    bubble_chat_css = f.read()
with open(Path(__file__).resolve().parent / '../css/html_instruct_style.css', 'r') as f:
    instruct_css = f.read()


def fix_newlines(string):
    string = string.replace('\n', '\n\n')
    string = re.sub(r"\n{3,}", "\n\n", string)
    string = string.strip()
    return string


def replace_blockquote(m):
    return m.group().replace('\n', '\n> ').replace('\\begin{blockquote}', '').replace('\\end{blockquote}', '')


def convert_to_markdown(string):

    # Blockquote
    pattern = re.compile(r'\\begin{blockquote}(.*?)\\end{blockquote}', re.DOTALL)
    string = pattern.sub(replace_blockquote, string)

    # Code
    string = string.replace('\\begin{code}', '```')
    string = string.replace('\\end{code}', '```')
    string = re.sub(r"(.)```", r"\1\n```", string)

    result = ''
    is_code = False
    for line in string.split('\n'):
        if line.lstrip(' ').startswith('```'):
            is_code = not is_code

        result += line
        if is_code:
            result += '\n'
        else:
            result += '\n\n'

    if is_code:
        result = result + '```'  # Unfinished code block

    string = result.strip()
    return markdown.markdown(string, extensions=['fenced_code'])


def generate_basic_html(string):
    string = convert_to_markdown(string)
    string = f'<style>{readable_css}</style><div class="container">{string}</div>'
    return string


def process_post(post, c):
    t = post.split('\n')
    number = t[0].split(' ')[1]
    if len(t) > 1:
        src = '\n'.join(t[1:])
    else:
        src = ''
    src = re.sub('>', '&gt;', src)
    src = re.sub('(&gt;&gt;[0-9]*)', '<span class="quote">\\1</span>', src)
    src = re.sub('\n', '<br>\n', src)
    src = f'<blockquote class="message">{src}\n'
    src = f'<span class="name">Anonymous </span> <span class="number">No.{number}</span>\n{src}'
    return src


def generate_4chan_html(f):
    posts = []
    post = ''
    c = -2
    for line in f.splitlines():
        line += "\n"
        if line == '-----\n':
            continue
        elif line.startswith('--- '):
            c += 1
            if post != '':
                src = process_post(post, c)
                posts.append(src)
            post = line
        else:
            post += line
    if post != '':
        src = process_post(post, c)
        posts.append(src)

    for i in range(len(posts)):
        if i == 0:
            posts[i] = f'<div class="op">{posts[i]}</div>\n'
        else:
            posts[i] = f'<div class="reply">{posts[i]}</div>\n'

    output = ''
    output += f'<style>{_4chan_css}</style><div id="parent"><div id="container">'
    for post in posts:
        output += post
    output += '</div></div>'
    output = output.split('\n')
    for i in range(len(output)):
        output[i] = re.sub(r'^(&gt;(.*?)(<br>|</div>))', r'<span class="greentext">\1</span>', output[i])
        output[i] = re.sub(r'^<blockquote class="message">(&gt;(.*?)(<br>|</div>))', r'<blockquote class="message"><span class="greentext">\1</span>', output[i])
    output = '\n'.join(output)

    return output


def make_thumbnail(image):
    image = image.resize((350, round(image.size[1] / image.size[0] * 350)), Image.Resampling.LANCZOS)
    if image.size[1] > 470:
        image = ImageOps.fit(image, (350, 470), Image.ANTIALIAS)

    return image


def get_image_cache(path):
    cache_folder = Path("cache")
    if not cache_folder.exists():
        cache_folder.mkdir()

    mtime = os.stat(path).st_mtime
    if (path in image_cache and mtime != image_cache[path][0]) or (path not in image_cache):
        img = make_thumbnail(Image.open(path))
        output_file = Path(f'cache/{path.name}_cache.png')
        img.convert('RGB').save(output_file, format='PNG')
        image_cache[path] = [mtime, output_file.as_posix()]

    return image_cache[path][1]


def generate_instruct_html(history):
    output = f'<style>{instruct_css}</style><div class="chat" id="chat">'
    for i, _row in enumerate(history[::-1]):
        row = [convert_to_markdown(entry) for entry in _row]

        output += f"""
              <div class="assistant-message">
                <div class="text">
                  <div class="message-body">
                    {row[1]}
                  </div>
                </div>
              </div>
            """

        if len(row[0]) == 0:  # don't display empty user messages
            continue

        output += f"""
              <div class="user-message">
                <div class="text">
                  <div class="message-body">
                    {row[0]}
                  </div>
                </div>
              </div>
            """

    output += "</div>"

    return output


def generate_cai_chat_html(history, name1, name2, reset_cache=False):
    output = f'<style>{cai_css}</style><div class="chat" id="chat">'

    # We use ?name2 and ?time.time() to force the browser to reset caches
    img_bot = f'<img src="file/cache/pfp_character.png?{name2}">' if Path("cache/pfp_character.png").exists() else ''
    img_me = f'<img src="file/cache/pfp_me.png?{time.time() if reset_cache else ""}">' if Path("cache/pfp_me.png").exists() else ''

    for i, _row in enumerate(history[::-1]):
        row = [convert_to_markdown(entry) for entry in _row]

        output += f"""
              <div class="message">
                <div class="circle-bot">
                  {img_bot}
                </div>
                <div class="text">
                  <div class="username">
                    {name2}
                  </div>
                  <div class="message-body">
                    {row[1]}
                  </div>
                </div>
              </div>
            """

        if len(row[0]) == 0:  # don't display empty user messages
            continue

        output += f"""
              <div class="message">
                <div class="circle-you">
                  {img_me}
                </div>
                <div class="text">
                  <div class="username">
                    {name1}
                  </div>
                  <div class="message-body">
                    {row[0]}
                  </div>
                </div>
              </div>
            """

    output += "</div>"
    return output


def generate_chat_html(history, name1, name2, reset_cache=False):
    output = f'<style>{bubble_chat_css}</style><div class="chat" id="chat">'

    for i, _row in enumerate(history[::-1]):
        row = [convert_to_markdown(entry) for entry in _row]

        output += f"""
              <div class="message">
                <div class="text-bot">
                  <div class="message-body">
                    {row[1]}
                  </div>
                </div>
              </div>
            """

        if len(row[0]) == 0:  # don't display empty user messages
            continue

        output += f"""
              <div class="message">
                <div class="text-you">
                  <div class="message-body">
                    {row[0]}
                  </div>
                </div>
              </div>
            """

    output += "</div>"
    return output


def chat_html_wrapper(history, name1, name2, mode, reset_cache=False):
    if mode == "cai-chat":
        return generate_cai_chat_html(history, name1, name2, reset_cache)
    elif mode == "chat":
        return generate_chat_html(history, name1, name2)
    elif mode == "instruct":
        return generate_instruct_html(history)
    else:
        return ''
