from io import StringIO
from lxml import etree
from lxml.etree import XMLSyntaxError
from manipulations import token_mask
from collections import Counter
import re
import os

def _read_safe(path):
    with open(path) as f:
        return f.read()

class Template(object):

    def __init__(self, html_path, js_paths, css_path):
        self.template_str = _read_safe(html_path)
        self.js_content = '\n\n'.join(_read_safe(js_path) for js_path in js_paths)
        self.css_content = _read_safe(css_path)
        self.html_parser = etree.HTMLParser(recover = False)


    def render(self, variables, output_path):
        my_variables = {
            'js_content': self.js_content,
            'css_content': self.css_content,
            **variables
        }
        html = self.template_str.format(**my_variables)
        with open(output_path, 'w') as f:
            f.write(html)


def extract_plain_text(doc, sent_begin=None, sent_end=None):
    sent_begin = sent_begin or 0
    sent_end = sent_end or (len(doc.sentence_spans)-1)
    extract_sent = lambda sent: ' '.join(
            ('__' if tok == token_mask else tok)
            for tok in doc.tokens[doc.sentence_spans[sent].begin : doc.sentence_spans[sent].end+1])
    content = '<br/>'.join(extract_sent(sent) for sent in range(sent_begin, sent_end+1))
    return content


def generate_html_for_sentences(template, inp_path, out_path, conf, doc, sent_begin=None, sent_end=None):
    """ 
    Convert the document into a simple HTML representation with relevent
    mentions highlighted for manual inspection. If no mention is provided,
    highlight all mentions.
    """
    sent_begin = sent_begin or 0
    sent_end = sent_end or (len(doc.sentence_spans)-1)
    tok_begin = doc.sentence_spans[sent_begin].begin
    tok_end = doc.sentence_spans[sent_end].end
    content = doc.tokens[:]
    mention2id = {m: i for i, m in enumerate(doc.annotated_mentions)}
    included_mentions = [m for m in doc.annotated_mentions
                         if m.span.begin >= tok_begin and m.span.end <= tok_end]

    # replace masks in context with editable underscores
    content = [('<span contenteditable="true" class="blank" id="blank_token_{i}">__</span>'.format(**locals())
                if token == token_mask else token)
               for i, token in enumerate(content)]
    # mark the tokens of the underlying text
    for tok in set((tok for m in included_mentions for tok in range(m.span.begin, m.span.end+1))):
        content[tok] = '<span class="mention-text">%s</span>' %content[tok]
    # wrap mentions in HTML spans and
    # add an empty identifier (will change when mentions are linked together)
    # add them in order (shortest to longest) so that they are properly nested
    mentions_sorted_by_length = sorted(included_mentions, key=lambda m: m.span.end-m.span.begin)
    for m in mentions_sorted_by_length:
        old_begin = content[m.span.begin]
        content[m.span.begin] = '<span class="mention" id="mention_{m.span.begin}_{m.span.end}">[{old_begin}'.format(**locals())
        content[m.span.end] += ']<span class="chain-id" id="mention_{m.span.begin}_{m.span.end}_chain_id"></span></span>'.format(**locals())
    # adding sentence markers, they need to go in before speaker information because
    # we don't want to add them after a new line
    for sspan in doc.sentence_spans[sent_begin:sent_end+1]:
        content[sspan.end] += '<span class="sentence-end">&nbsp;</span>'
    # add speaker identifier in front of each sentence
    # speaker information needs to go in first (and hence wrapped in sentence spans)
    # because we want to display documents sentence-by-sentence
    for i in range(sent_begin, sent_end+1):
        sspan = doc.sentence_spans[i]
        speakers = Counter(doc.speakers[sspan.begin:sspan.end+1])
        if len(speakers) > 1:
            sys.stderr.write('WARN: Found two speakers in one sentence: %s, sentence %d\n' %(inp_path, i))
        ((speaker, _),) = speakers.most_common(1)
        if not re.match('^-$', speaker):
            content[sspan.begin] = ('<span class="speaker">%s:</span> %s' 
                                                %(speaker, content[sspan.begin]))
        content[sspan.end] += "<br/>\n"
    # mark sentences
    for sspan in doc.sentence_spans[sent_begin:sent_end+1]:
        content[sspan.begin] = '<span class="sentence">' + content[sspan.begin]
        content[sspan.end] += '</span>'
    # clip to what we need
    content = content[tok_begin:tok_end+1]
    # make string
    content = ' '.join(content)
    content_plain = extract_plain_text(doc, sent_begin, sent_end)

    out_fname = os.path.basename(out_path)
    variables = {'form_action': conf.get_string('worker_host'), **locals()}
    template.render(variables, out_path)
