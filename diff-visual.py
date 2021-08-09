from docopt import docopt
import os

_tex_conv = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '<': r'\textless ',
    '>': r'\textgreater ',
}
_tex_regex = re.compile('|'.join(re.escape(key) 
                                 for key in sorted(_tex_conv.keys(), 
                                                   key = lambda item: - len(item))))

def tex_escape(text):
    """
        Borrow from Mark: https://stackoverflow.com/a/25875504/217802
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    return _tex_regex.sub(lambda match: _tex_conv[match.group()], text)


def iter_docs(file_path):
    with codecs.open(file_path, 'r', "utf-8") as f: 
        current_document = []
        for line in f.readlines():
            if line.startswith("#begin") and current_document:
                yield documents.CoNLLDocument(''.join(current_document))
                current_document = []
            current_document.append(line)
        if current_document: 
            yield documents.CoNLLDocument(''.join(current_document))


def visualize(out_dir, *paths, max_docs=3, doc_names=None):
    paths = [p for p in paths if os.path.exists(p)]
    assert paths
    out_path = os.path.join(out_dir, 'diff.tex')
    with codecs.open(out_path, 'w', "utf-8") as f: 
        f.write(r'''
\documentclass{article}
\usepackage[landscape]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{tikz-qtree}
\begin{document}
''')
        if doc_names:
            docs = [[(d,p) for d in iter_docs(p) if d.identifier in doc_names] for p in paths]
        else:
            docs = [[(d,p) for d in itertools.islice(iter_docs(p), max_docs)] for p in paths]
        for compared_docs in zip(*docs):
            id = set(dp[0].identifier for dp in compared_docs)
            assert len(id) == 1, "Identifiers don't match: %s" %id
            id = next(iter(id))
            f.write('\section{%s}\n' %tex_escape(id))
            max_sents = max(len(dp[0].sentence_spans) for dp in compared_docs)
            for i in range(max_sents):
                f.write('\subsection*{Sentence \#%d}\n' %(i+1))
                for d, p in compared_docs:
                    if i < len(d.sentence_spans):
                        f.write('%s\n\n ' %tex_escape(p))
                        tree_str = d.parse[i].pformat_latex_qtree()
                        tree_str = re.sub(r'MASKED|NOPARSE', '_', tree_str) # save some space
                        f.write('%s\n\n' %tree_str)
        f.write('\end{document}')
    subprocess.call('latex %s' %out_path, shell=True)

if __name__ == '__main__':
    doc = """Show a visual comparison between CoNLL files.

Usage:
  diff-visual.py [--output-dir=<out>] [--docs=<docs> | --max-docs=<num>] <inputs>...
  
Options:
  --output-dir=<out>   The directory to store output latex and dvi files [default: output/]
  --docs=<docs>        Name of documents of interest (separated by comman)
  --max-docs=<num>     Number of documents to compare (starting from the first in the corpus) [default: 3]
  
"""
    args = docopt(doc)
    doc_names=args.get('--docs') 
    if doc_names: doc_names = doc_names.split(',')
    assert len(args['<inputs>']) >= 2, 'Need at least 02 input files'
    visualize(args['--output-dir'], *args['<inputs>'], 
              max_docs=int(args['--max-docs']), doc_names=doc_names)