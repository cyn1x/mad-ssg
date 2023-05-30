import os
import shutil
import time

import markdown
import sass

from jinja2 import Environment, FileSystemLoader

from config import OUTPUT_DIR, INPUT_DIR, STATIC_DIR
from util import read_file, write_file

# Define the Jinja2 environment and file system loader
env = Environment(loader=FileSystemLoader('templates'))


def build_site():
    build_start = time.perf_counter()

    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    os.makedirs(OUTPUT_DIR)

    convert_markdown()
    copy_scripts()
    compile_sass()

    build_finish = time.perf_counter()
    print(f'Finished site build in {round(build_finish-build_start, 3)} second(s)')


def convert_markdown():
    """Loop through input Markdown files and dispatch for conversion"""
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.md'):
            markdown_input = read_file(os.path.join(INPUT_DIR, filename))
            metadata, html = convert_to_html(markdown_input)
            output_text = render(metadata, html)

            if filename.split('.')[0] == 'index':
                output_text = inject_utils(output_text)

            write_file(os.path.join(OUTPUT_DIR, filename.replace('.md', '.html')), output_text)


def copy_scripts():
    """Copy all static files to their appropriate directories"""
    scripts_src = os.path.join(STATIC_DIR, 'js')
    scripts_dst = os.path.join(OUTPUT_DIR, 'js')
    os.mkdir(scripts_dst)

    for filename in os.listdir(scripts_src):
        shutil.copyfile(
            os.path.join(scripts_src, filename),
            os.path.join(scripts_dst, filename),
            follow_symlinks=True
        )


def compile_sass():
    try:
        sass.compile(
            dirname=(os.path.join(STATIC_DIR, 'scss'), os.path.join(OUTPUT_DIR, 'css')),
            output_style='expanded',
        )
    except sass.CompileError as e:
        print(e)


def convert_to_html(input_text):
    """Compile Markdown files to HTML using Python-Markdown"""
    count = 0
    metadata = {}
    lines = input_text.split('\n')
    for line in lines:
        if line.startswith('---'):
            count += 1
            if count == 2:
                break
            continue
        parts = line.split(':', 1)
        if len(parts) == 2:
            metadata[parts[0].strip()] = parts[1].strip()

    # Parse input text to HTML
    html = markdown.markdown('\n'.join(lines[len(metadata) + 2:]))

    return metadata, html


def render(metadata, html):
    """Use Jinja2 to render the HTML template with the Markdown content"""
    template = env.get_template(metadata.get('template', 'default.html'))
    output_text = template.render(content=html, **metadata)

    return output_text


def inject_utils(input_text):
    """Inject client-side development tools if in development mode"""
    contents = ''
    lines = input_text.split('\n')
    for line in lines:
        if line.__contains__('</body>'):
            contents += line.split('<')[0] + '<script type=\'module\' src="js/dev.js"></script>\n' + line + '\n'
        else:
            contents += line + '\n'

    return contents
