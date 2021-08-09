from cort.core import corpora
import codecs
import re
import os
import sys

def read_corpus():
    dev_all = 'data/conll-2012-flat/dev-all/all.v4_auto_conll'
    dev_small = 'data/conll-2012/v4/data/development/data/english/annotations//mz/sinorama/10/ectb_1010.v4_auto_conll'
    with codecs.open(dev_all, 'r', "utf-8") as f: 
        corpus = corpora.Corpus.from_file("reference", f)
    for doc in corpus: 
        doc.system_mentions = doc.annotated_mentions
        for m in doc.system_mentions: 
            m.attributes['set_id'] = m.attributes['annotated_set_id']
    return corpus

def to_html(doc, highlighted_mentions):
    """ 
    Convert the document into a simple HTML representation with relevent
    mentions highlighted for manual inspection.
    """
    content = doc.tokens[:]
    for mention in highlighted_mentions:
        tag_begin = "<span style=\"color:red\" title=\""
        tag_begin += "e:" + str(mention.attributes["set_id"]) + " "
        tag_begin += "\">"
        old_begin = content[mention.span.begin]
        content[mention.span.begin] = tag_begin + old_begin
        content[mention.span.end] += "</span>"
    return "<br/>\n".join(" ".join(content[sentence_span.begin:sentence_span.end+1])
                          for sentence_span in doc.sentence_spans)

def measure_gender_stats(corpus=None):
    corpus = corpus or read_corpus()
    male_total = 0
    female_total = 0
    for _, doc in enumerate(corpus):
        gender = {}
        for m in doc.system_mentions:
            e = m.attributes['set_id']
            if e not in gender or m.attributes['type'] == 'PRO':
                gender[e] = m.attributes['gender']
        male_count = sum(1 for k in gender if gender[k] == 'MALE')
        female_count = sum(1 for k in gender if gender[k] == 'FEMALE')
        print('%02d vs %02d' %(male_count, female_count))
        male_total += male_count
        female_total += female_count
    print('Total: %02d vs %02d' %(male_total, female_total))

def set_token(doc, pos, new_token, logger, erase=False):
    doc.tokens[pos] = doc.document_table[pos][3] = new_token
    if erase:
        pass
#         doc.document_table[pos][4] = '_'
#         doc.document_table[pos][5] = 0
#         doc.document_table[pos][6] = '_'
    logger.write('%s\t%d\n' %(doc.identifier, pos))

def change_gender(out_path='output/gender_changed'):
    corpus = read_corpus()
    with open(out_path + '.target', 'wt') as target, \
            open(out_path + '.modified', 'wt') as modified:
        os.makedirs(out_path + '_docs', exist_ok=True)
        for doc in corpus:
            altered_mentions = []
            altered_entities = set()
            for m in doc.system_mentions:
                if m.attributes['gender'] == 'FEMALE' and m.attributes['type'] == 'PRO':
                    try:
                        if m.attributes['tokens_as_lowercase_string'] == 'she':
                            set_token(doc, m.span.begin, 'he', modified)
                        elif m.attributes['deprel'] in ('nmod:poss',):
                            set_token(doc, m.span.begin, 'his', modified)
                        elif m.attributes['deprel'] in ('dobj', 'iobj', 'nmod'):
                            set_token(doc, m.span.begin, 'him', modified)
                        else:
                            raise ValueError("Don't know what to do with %s" %m.attributes['deprel'])
                        target.write('%s\t%d\t%d\n' %(doc.identifier, m.span.begin, m.span.end))
                        altered_mentions.append(m)
                        altered_entities.add(m.attributes['set_id'])
                    except ValueError:
                        sys.stderr.write('Ignored one mention: %s (%d:%d in %s)\n' 
                                         %(' '.join(m.attributes['head']), 
                                           m.span.begin, m.span.end, doc.identifier))
            # replace names
            name_mentions = [m for m in doc.system_mentions
                             if m.attributes['type'] == 'NAM' 
                             and m.attributes['set_id'] in altered_entities]
            if name_mentions:
                male_names = set(tuple(name.split(' ')) for name in 
                                 ('Joseph Addison', 'Theodor Ludwig Wiesengrund', 
                                  'Oswald de Andrade', 'Walter Bagehot', 
                                  'Jorge Luis Borges', 'William Brandon', 
                                  'Alfred Brendel', 'Anthony Burgess', 
                                  'Charles Caleb Colton', 'Femi Fani - Kayode',
                                  'Benito Jerónimo Feijoo e Montenegro', 
                                  'Karl - Markus Gauß', 'Thomas de Quincey',
                                  'Gordon', 'David', 'Frank', 'Richard'))
                existing_names = set()
                for m in doc.system_mentions:
                    if m.attributes['type'] == 'NAM':
                        existing_names.update(t for t in m.attributes['tokens']
                                              if re.match(r'\w+$', t))
                new_names = {}
                for e in altered_entities:
                    mentions = [m for m in name_mentions if m.attributes['set_id'] == e]
                    if mentions:
                        aligned_name = None
                        for m in mentions:
                            head = m.attributes['head']
                            deps = doc.dep[m.attributes['sentence_id']]
                            head_span = m.attributes['head_span']
                            head_pos = set(deps[i].pos for i in doc.in_sentence_ids[head_span.begin:head_span.end+1])
                            if head_pos == {'NNP'}:
                                if aligned_name is None or len(head) > len(aligned_name):
                                    aligned_name = head
                            else:
                                sys.stderr.write('Ignored one mention: %s (%d:%d in %s)\n' 
                                                 %(' '.join(m.attributes['head']), 
                                                   m.span.begin, m.span.end, doc.identifier))
                        if aligned_name:
                            name = next(n for n in male_names 
                                        if len(n) == len(aligned_name) 
                                        and not existing_names.intersection(n))
                            assert name
                            male_names.remove(name)
                            new_names[e] = dict(zip(aligned_name, name))
                        else:
                            sys.stderr.write('Ignore one entity: %s (%s)\n' 
                                             %(str([' '.join(m.attributes['tokens']) 
                                                   for m in mentions]), doc.identifier))
                for m in name_mentions:
                    new_name = new_names.get(m.attributes['set_id'])
                    for i in range(m.span.begin, m.span.end+1):
                        if new_name and doc.tokens[i] in new_name:
                            set_token(doc, i, new_name[doc.tokens[i]], modified)
            # replace some common nouns
            replacements = {'chairwoman': 'chairman', 'Chairwoman': 'Chairman',
                            'mother': 'father', 'Mother': 'Father',
                            'wife': 'husband', 'Wife': 'Husband', 
                            'woman': 'man', 'Woman': 'Man',
                            'women': 'men', 'Women': 'Men',
                            'girl': 'boy', 'Girl': 'Boy', 
                            'girls': 'boys', 'Girls': 'Boys', 
                            'Mrs.': 'Mr.', 'Ms.': 'Mr.',
                            'daughter': 'son', 'Daughter': 'Son',
                            'daughters': 'sons', 'Daughters': 'Sons',
                            'sister': 'brother', 'Sister': 'Brother',
                            'sisters': 'brothers', 'Sisters': 'Brothers',}
            for i in range(len(doc.tokens)):
                t = doc.tokens[i]
                if t in replacements:
                    set_token(doc, i, replacements[t], modified)
            if altered_mentions:
                path = os.path.join(out_path + "_docs", 
                                    re.sub('[/(); ]', '_', doc.identifier) + '.html')
                with codecs.open(path, 'w', "utf-8") as f:
                    f.write(to_html(doc, altered_mentions))
    with codecs.open(out_path + '.changed_auto_conll', 'w', "utf-8") as f: 
        corpus.write_to_file(f)
    return corpus
                                
if __name__ == '__main__':
    print("*** before ***")
    measure_gender_stats(read_corpus())
    print("*** after ***")
    measure_gender_stats(change_gender())
