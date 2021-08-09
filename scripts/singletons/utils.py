import os
from collections import defaultdict
import re
from collections import OrderedDict
from warnings import warn
from nltk import Tree

def import_conll(filepath):
    '''
    This function imports a conll file into a list of dictionaries
    
    :returns data: a list of lists of dictionaries, each with information from a sentence in the file. Keys are as follows:
        file_id
        part_id
        doc_id
        tok_id
        sent_id
        word
        pos
        parse
        predicate_lemma: for each predicate, this col has the lemma
        pred_id: the frameset ID for each predicate in col predicate_lemma
            this is a bit weird: Note that predicate_lemma column contains some words that do not have frameset IDs, and that
            all and only words with frameset IDs are predicates for the sake of the pred_arguments col (so if and only if there's an entry
            in this col, then there's a column in pred_arguments for this entry)
        ne_info
        pred_arguments: a list with N entries, one for each predicate in "predicate lemma" for this sentence
        coref
    '''
    data = []
    with open(filepath, "r", encoding="utf-8") as infile:
        raw_text = infile.read()
        sentences = raw_text.split("\n\n")
    
    sent_id = 0
    part_id = "000"
    for sentence in sentences:
        sentence_list = [] # list of dicts
        lines = sentence.split("\n")
        for line in lines:
            if line == "" or line[0]=="#": # "#begin document..." and "#end document..."
                if line[0:6]=="#begin":
                    part_id = line[-3:]
                continue
            line_dict = dict()
            line_really_raw_data=line.split(" ")
            line_raw_data = []
            for entry in line_really_raw_data:
                if entry != "":
                    line_raw_data.append(entry)
            line_dict["file_id"] = line_raw_data[0]
            line_dict["part_id"] = part_id
            line_dict["doc_id"] = int(line_raw_data[1])
            line_dict["tok_id"] = int(line_raw_data[2])
            line_dict["sent_id"] = sent_id
            line_dict["word"] = line_raw_data[3]
            line_dict["pos"] = line_raw_data[4]
            line_dict["parse"] = line_raw_data[5]
            line_dict["predicate_lemma"] = line_raw_data[6]
            line_dict["pred_id"] = line_raw_data[7]
            line_dict["pred_frameset_id"] = line_raw_data[8]
            line_dict["word_sense"] = line_raw_data[9]
            line_dict["ne_info"] = line_raw_data[10]
            line_dict["pred_arguments"] = line_raw_data[11:-1]
            line_dict["coref"] = line_raw_data[-1]
            sentence_list.append(line_dict)
        if len(sentence_list)!=0:
            data.append(sentence_list)
            sent_id+=1
        
    return data

def write_conll(data, filepath):
    '''
    Given a data dict, writes a conll2012-format file.
    This function is the inverse of import_conll.
    '''
    outfile = open(filepath, "w+", encoding="utf-8")
    filename = data[0][0]["file_id"]
    current_part_id = "000"
    outfile.write(f"#begin document ({filename}); part {current_part_id}\n")
    
    for sentence in data:
        if sentence[0]["part_id"] != current_part_id:
            # found the start of a new document
            current_part_id = sentence[0]["part_id"]
            outfile.write(f"end document\n")
            outfile.write(f"#begin document ({filename}); part {current_part_id}\n")
        # Set up sentences as lists of lists, instead of lists of dicts,
        sentence_as_list = []
        for entry in sentence:
            row = []
            row.append(entry["file_id"])
            row.append(entry["doc_id"])
            row.append(entry["tok_id"])
            row.append(entry["word"])
            row.append(entry["pos"])
            row.append(entry["parse"])
            row.append(entry["predicate_lemma"])
            row.append(entry["pred_id"])
            row.append(entry["pred_frameset_id"])
            row.append(entry["word_sense"])
            row.append(entry["ne_info"])
            for i in entry["pred_arguments"]:
                row.append(i)
            row.append(entry["coref"])
            sentence_as_list.append(row)
        # This part taken from https://github.com/boberle/corefconversion/blob/master/conll_transform.py
        lengths = None
        for row in sentence_as_list:
            # first, compute longest length for each column in the sentence
            if lengths is None:
                lengths = [0]*len(row)
            for c, string in enumerate(row):
                lengths[c] = max(lengths[c], len(str(string)))
        for row in sentence_as_list:
            for c, string in enumerate(row):
                extra = 0 if c==0 else 3
                fmt = "%% %ds" % (lengths[c] + extra)
                outfile.write(fmt % string)
            outfile.write("\n")
        outfile.write("\n")

    outfile.write("#end document")
    outfile.close()
    

def extract_phrases(sentence):
    '''
    Takes a list of dicts representing a single sentence in conll2012 format, as extracted by
    import_conll(), and returns a list of tuples, each representing a parse phrase.
    
    These tuples take the form (phrase_type, span)
        phrase_type: a string representing the type of arg
        span: a tuple of (start_index, end_index) of the predicate argument within the sentence (tok_id)
    '''
    
    in_string = False
    parse_tuples = []
    phrase_type = ""
    for entry in sentence:
        parse_string = entry["parse"]
        for char in parse_string:
            if in_string:
                if char in {"(", ")", "*"}:
                    in_string = False
                    parse_tuples[-1][0]=phrase_type
                    phrase_type=""
                    if char=="(":
                        in_string = True
                        parse_tuples.append(["", [entry["tok_id"]]])
                    elif char == ")":# found the end of one of our spans
                        for i in range(len(phrase_tuples)-1, -1, -1):
                            if len(phrase_tuples[i][1])==1: # top of unfinished span stack
                                phrase_tuples[i][1].append(entry["tok_id"]+1)
                                break
                    continue
                else:
                    phrase_type+=char
            else: # not in_string
                if char=="(":
                    in_string = True
                    parse_tuples.append(["", [entry["tok_id"]]])
                elif char==")": # found the end of one of our spans
                    for i in range(len(parse_tuples)-1, -1, -1):
                        if len(parse_tuples[i][1])==1: # top of unfinished span stack
                            parse_tuples[i][1].append(entry["tok_id"]+1)
                            break
                                    
    for i in range(len(parse_tuples)):
        parse_tuples[i][1] = tuple(parse_tuples[i][1]) # spans to tuples
        parse_tuples[i]=tuple(parse_tuples[i]) # arg_lists to tuples
        
    return parse_tuples

def extract_args(sentence):
    '''
    Takes a list of dicts representing a single sentence in conll2012 format, as extracted by
    import_conll(), and returns a list of tuples, each representing a predicate argument.
    
    These tuples take the form (pred_tok_id, arg_type, span)
        pred_tok_id: an integer representing the location (token_id) of the predicate
        arg_type: a string representing the type of arg
        span: a tuple of (start_index, end_index) of the predicate argument within the sentence (tok_id)
    '''
    
    pred_loc_list = []
    i = 0
    for entry in sentence:
        if entry["pred_id"] != "-": # found a real predicate
            pred_loc_list.append((entry["tok_id"], i))
            i+=1
    assert i==len(sentence[0]["pred_arguments"])
    
    in_string = False
    arg_tuples = []
    arg_type = ""
    for pred_loc, column in pred_loc_list:
        for entry in sentence:
            arg_string = entry["pred_arguments"][column]
            for char in arg_string:
                if in_string:
                    if char in {"(", ")", "*"}:
                        in_string = False
                        arg_tuples[-1][1]=arg_type
                        arg_type=""
                        if char=="(":
                            in_string=True
                            arg_tuples.append([pred_loc, "", [entry["tok_id"]]])
                        elif char == ")": # found the end of a span
                            for i in range(len(arg_tuples)-1, -1, -1):
                                if len(arg_tuples[i][2])==1: # top of unfinished span stack
                                    arg_tuples[i][2].append(entry["tok_id"]+1)
                                    break
                        continue
                    else:
                        arg_type+=char
                else: # not in_string
                    if char=="(":
                        in_string = True
                        arg_tuples.append([pred_loc, "", [entry["tok_id"]]])
                    elif char==")": # found the end of one of our spans
                        for i in range(len(arg_tuples)-1, -1, -1):
                            if len(arg_tuples[i][2])==1: # top of unfinished span stack
                                arg_tuples[i][2].append(entry["tok_id"]+1)
                                break
                                    
    for i in range(len(arg_tuples)):
        arg_tuples[i][2] = tuple(arg_tuples[i][2]) # spans to tuples
        arg_tuples[i]=tuple(arg_tuples[i]) # arg_lists to tuples
        
    return arg_tuples

def extract_NEs(sentence):
    '''
    Takes a list of dicts representing a single sentence in conll2012 format, as extracted by
    import_conll(), and returns a list of tuples, each representing a Named Entity.
    
    These tuples take the form (NE_type, span)
        NE_type: a string representing the type of arg
        span: a tuple of (start_index, end_index) of the NE within the sentence (tok_id)
    '''
    in_string = False
    NE_tuples = []
    NE_type = ""
    for entry in sentence:
        NE_string = entry["ne_info"]
        for char in NE_string:
            if in_string:
                if char in {"(", ")", "*"}:
                    in_string = False
                    NE_tuples[-1][0]=NE_type
                    NE_type=""
                    if char == ")":# found the end of one of our spans
                        for i in range(len(NE_tuples)-1, -1, -1):
                            if len(NE_tuples[i][1])==1: # top of unfinished span stack
                                NE_tuples[i][1].append(entry["tok_id"]+1)
                                break
                    continue
                else:
                    NE_type+=char
            else: # not in_string
                if char=="(":
                    in_string = True
                    NE_tuples.append(["", [entry["tok_id"]]])
                elif char==")": # found the end of one of our spans
                    for i in range(len(NE_tuples)-1, -1, -1):
                        if len(NE_tuples[i][1])==1: # top of unfinished span stack
                            NE_tuples[i][1].append(entry["tok_id"]+1)
                            break
                                    
    for i in range(len(NE_tuples)):
        NE_tuples[i][1] = tuple(NE_tuples[i][1]) # spans to tuples
        NE_tuples[i]=tuple(NE_tuples[i]) # arg_lists to tuples
        
    return NE_tuples

### Copied from https://github.com/boberle/corefconversion/blob/master/conll_transform.py

CONLL_MENTION_PATTERN = re.compile(r'(?:\((?P<mono>\d+)\)|\((?P<start>\d+)|(?P<end>\d+)\))')

def compute_mentions(column):
    """Compute mentions from the raw last column of the conll file.
    `column` is a list:
        ['*', '(1', '*', '1)', ...]
    Return a list of tuples of the form:
        ( (START, STOP) , CHAIN)
    where CHAIN is the chain number given in the conll file.  It's an
    **integer**.
    """

    # to check for duplicated mentions
    used = set() # {(start, stop)...}
    def is_duplicated(pos):
        if pos in used:
            warn(f"Mention {pos} duplicated. Ignoring.")
            return True
        used.add(pos)

    pending = dict()
    mentions = []
    for i, cell in enumerate(column):
        for m in CONLL_MENTION_PATTERN.finditer(cell):
            if m.lastgroup == 'mono':
                pos = (i, i+1)
                chain = int(m.group(m.lastgroup))
                if not is_duplicated(pos):
                    mentions.append((pos, chain))
            elif m.lastgroup == 'start':
                chain = int(m.group(m.lastgroup))
                if not chain in pending:
                    pending[chain] = []
                pending[chain].append(i)
            elif m.lastgroup == 'end':
                chain = int(m.group(m.lastgroup))
                pos = (pending[chain].pop(), i+1)
                if not is_duplicated(pos):
                    mentions.append((pos, chain))
            else:
                assert False
    for k, v in pending.items():
        if v:
            assert False, pending
    return mentions

def extract_mentions(sentence):
    coref_column = []
    for entry in sentence:
        coref_column.append(entry["coref"])
    return compute_mentions(coref_column)


def find_head(t, sentence):
    '''
    This function takes a tree extracted from a parse string along with the sentence it comes from and returns
    the syntactic head as an integer (if the tree represents a NP, and an error otherwise.)
    The tree should be derived from a string that replaces *s in the conll parse column with integers corresponding 
    to the index within the sentence (ie "(TOP(S(ADVP 0)(VP 1 (PP 2(NP(NP 3 4 5 6)(PP 7(NP(NML 8 9) 10))))) 11))")
    '''
    head = -1
    rightmost_NP = None
    for tree in t:
        if type(tree)==str and sentence[int(tree)]["pos"] in ["NN", "NNS", "NNP"]:
            if int(tree)>head:
                head = int(tree)
        elif type(tree)!= str and tree.label() in ["NP", "NML"]:
            rightmost_NP = tree
    if head == -1: # No noun leaves
        if rightmost_NP:
            head = find_head(rightmost_NP, sentence)
        else:
            head = None
    return head

    
def get_parse_string(sentence):
    '''
    Takes a conll sentence and returns a string representing the syntactic parse, with integers (indices) in place of stars
    '''
    parse_string = ""
    for entry in sentence:
        parse_entry = entry["parse"]
        index = entry["tok_id"]
        parse_string += parse_entry.replace("*", f" {index}")
    return parse_string

def get_NP_string(sentence, NP_span):
    '''
    Given a sentence and the span of a phrase, gets the parse string for that phrase
    '''
    raw_parse = ""
    for entry in sentence[NP_span[0]: NP_span[1]]:
        parse_entry = entry["parse"]
        index = entry["tok_id"]
        raw_parse += parse_entry.replace("*", f" {index}")
    
    open_brackets = raw_parse.count("(")
    close_brackets = raw_parse.count(")")
    
    if open_brackets > close_brackets:
        diff = open_brackets-close_brackets
        num_open_brackets = 0
        i = -1
        # find the diff+1 open bracket (that's the start of the phrase parse string)
        while num_open_brackets < diff+1:
            i += 1
            if raw_parse[i] == "(":
                num_open_brackets += 1
        # now i is the index of the diff+1 open bracket
        parse_string = raw_parse[i:]
    elif close_brackets > open_brackets:
        diff = close_brackets-open_brackets
        num_close_brackets = 0
        i = 0
        while num_close_brackets < diff+1:
            i -= 1
            if raw_parse[i] == ")":
                num_close_brackets += 1
        # now i is the (negative) index of the diff+1 close bracket from the end of the string
        parse_string = raw_parse[:i+1]
    else:
        parse_string = raw_parse
    return parse_string

def get_coref_info(mentions):
    '''
    Takes a set of mentions from extract_candidates, and
    returns a dict of coref_info with entries (file_id, sentence_id, token_id):coref_string
    
    mentions: a set of mentions of the form (file_id, sentence_id, span, mention_id)
    '''
    coref_info = defaultdict(str) # dict of (file_id, sentence_id, tok_id):coref_info
    mention_id = 0
    for mention in mentions:
        # First loop: only non-single-token-mentions. Second loop: only single-token-mentions.
        file_id = mention[0]
        sentence_id = mention[1]
        span = mention[2]
        mention_id = mention[3]
        # deal with case where there is already a coref string for this tok_id. Need single-token mention to behave
    
        if span[1]-span[0]==1:
            #special case: mention is only 1 token; string is handled differently ("(id)" instead of "(id" and "id)")
            #first pass: skip these, to get all the other info in. Then, loop through mentions again this time only
            #catching the 1-token-mentions, and adding them appropriately
            # particular behaviour: "(78|(41)" and "(42)|78)".
            continue
        else:
            start = span[0]
            # dict for first token in span
            key = (file_id, sentence_id, start)
            coref_string = f"({mention_id}"
            if key in coref_info:
                coref_info[key] += "|"+coref_string
            else:
                coref_info[key] = coref_string
            end = span[1]-1
            key = (file_id, sentence_id, end)
            coref_string = f"{mention_id})"
            if key in coref_info:
                coref_info[key] += "|"+coref_string
            else:
                coref_info[key] = coref_string
    
    for mention in mentions:
        # First loop: only non-single-token-mentions. Second loop: only single-token-mentions.
        file_id = mention[0]
        sentence_id = mention[1]
        span = mention[2]
        mention_id = mention[3]
        if span[1]-span[0]==1:
            #special case: mention is only 1 token; string is handled differently ("(id)" instead of "(id" and "id)")
            #first pass: skip these, to get all the other info in. Then, loop through mentions again this time only
            #catching the 1-token-mentions, and adding them appropriately
            # particular behaviour: "(78|(41)" and "(42)|78)".
            key = (file_id, sentence_id, span[0])
            coref_string = f"({mention_id})"
            if key in coref_info:
                if coref_info[key][0]=="(":
                    coref_info[key] += "|"+coref_string
                else:
                    coref_info[key] = coref_string + "|" + coref_info[key]
            else:
                coref_info[key] = coref_string
    return coref_info
    
    
def extract_candidates(data):
    '''
    Extracts high-level candidate mentions from conll data, as imported by utils.import_conll
    
    Mentions are returned in a set. Mentions take the form of tuples of (file_id, sentence_id, span, mention_id)
    
    :param data: a data dict as returned by import_conll()
    
    :returns mentions: a set of tuples representing mentions
    '''
    all_mentions = dict() # Intermediate data structure: {(file_id, sentence_id, span):mention_id, ...}
    mention_id = 0
    mention_ids_used = set()
    
    for sentence in data:
        # Need to add all gold mentions first, for the sake of mention ids (need to assign singleton mentions
        # ids that do not appear for any gold mention in the document)
        if len(sentence)==0:
            continue
        file_id = sentence[0]["file_id"]
        sentence_id = sentence[0]["sent_id"]
        
        ## Add gold mentions
        gold_mentions = extract_mentions(sentence)
        for mention in gold_mentions:
            all_mentions[(file_id, sentence_id, mention[0])]=int(mention[1])
            mention_ids_used.add(int(mention[1]))

    for sentence in data:
        mentions = dict() # Intermediate data structure: {(file_id, sentence_id, span):mention_id, ...}
        
        if len(sentence)==0:
            continue
        file_id = sentence[0]["file_id"]
        sentence_id = sentence[0]["sent_id"]
        
        ## NPs
        phrases = extract_phrases(sentence)
        for phrase in phrases:
            if phrase[0]=="NP":
                #print(phrase)
                if (file_id, sentence_id, phrase[1]) not in mentions:
                    while mention_id in mention_ids_used:
                        mention_id+=1
                    mentions[(file_id, sentence_id, phrase[1])]=mention_id
                    mention_ids_used.add(mention_id)
        
        ## Filter nested NPs with same syntactic head
        new_mentions = dict()
        heads = dict() # head_loc:(length, mention)
        for mention, mention_ID in mentions.items():
            span = mention[2]
            parse_string = get_NP_string(sentence, span)
            t = Tree.fromstring(parse_string)
            head_loc = find_head(t, sentence)
            if head_loc in heads:
                if span[1]-span[0]>heads[head_loc][0]:
                    new_mentions.pop(heads[head_loc][1])
                    #print(f"removed: {heads[head_loc][1]}, {head_loc})")
                    new_mentions[mention]=mention_ID
                    heads[head_loc]=(span[1]-span[0], mention)
                    #print(f"Added: ({mention}, {head_loc})")
            else:
                #print(f"Added: ({mention}, {head_loc})")
                new_mentions[mention]=mention_ID
                heads[head_loc] = (span[1]-span[0], mention)
        mentions=new_mentions.copy()
        
        ## Pronouns
        for entry in sentence:
            if entry["pos"] in ["PRP", "PRP$"]: #penn treebank pronouns
                if (file_id, sentence_id, (entry["tok_id"], entry["tok_id"]+1)) not in mentions:
                    while mention_id in mention_ids_used:
                        mention_id+=1
                    mentions[(file_id, sentence_id, (entry["tok_id"], entry["tok_id"]+1))]= mention_id
                    mention_ids_used.add(mention_id)
                
        ## Filter quantity NEs
        NEs = extract_NEs(sentence)
        new_mentions = mentions.copy()
        for mention, mention_ID in mentions.items():
            span = mention[2]
            for NE in NEs:
                NE_type, NE_span = NE[0], NE[1]
                if NE_span == span:
                    if NE_type in ["MONEY", "PERCENT", "QUANTITY", "ORDINAL", "CARDINAL"]:
                        # mention matches a NE span (is a NE), and is a numeric entity
                        new_mentions.pop(mention)
                        break
                        #print(f"removing {mention}")
        mentions=new_mentions.copy()
        
        ## Filter stop words (there, ltd., etc., ’s, hmm)
        ## Removes only mentions that consist entirely (only) of the stop words
        stop_words = {"there", "ltd.", "etc.", "’s", "hmm"}
        new_mentions = mentions.copy()
        for mention, mention_ID in mentions.items():
            span = mention[2]
            if span[1]-span[0]==1:
                entry = sentence[span[0]]
                token = entry["word"].lower()
                if token in stop_words:
                    new_mentions.pop(mention)
        mentions=new_mentions.copy()

        
        ## Add this sentences mentions to the full set of mentions
        for mention, mention_ID in mentions.items():
            if mention not in all_mentions:
                all_mentions[mention]=mention_ID
        
    # convert to set of tuples
    return_mentions = set()
    for mention, mention_ID in all_mentions.items():
        return_mentions.add((mention[0], mention[1], mention[2], mention_ID))
    return return_mentions

def extract_final_candidates(data):
    '''
    Extracts final candidate mentions from conll data, as imported by utils.import_conll
    Functionally filters the mentions from extract_candidates() to include: gold mentions, NEs, mentions
    that fill the role of main args, and mentions that are NPs within PP main args.
    
    Mentions are returned in a set. Mentions take the form of tuples of (file_id, sentence_id, span, mention_id)
    
    :param data: a data dict as returned by import_conll()
    
    :returns mentions: a set of tuples representing mentions
    '''
    cand_mentions = extract_candidates(data)
    final_mentions = set()
    arguments = list() # list of lists of arguments in each sentence
    named_entities = list()
    phrases = list()
    gold_mentions = list()
    for sentence in data:
        phrases.append(extract_phrases(sentence))
        arguments.append(extract_args(sentence))
        named_entities.append(extract_NEs(sentence))
        gold_mentions.append(extract_mentions(sentence))
    for mention in cand_mentions:
        added=False
        sentence_id = mention[1]
        sentence = data[sentence_id]
        args = arguments[sentence_id]
        NEs = named_entities[sentence_id]
        GMs = gold_mentions[sentence_id]
        mention_span = mention[2]
        
        for gold_mention in GMs:
            if mention_span == gold_mention[0]:
                final_mentions.add(mention)
                added=True
                break
                
        if added:
            continue
            
        for NE in NEs:
            if mention_span==NE[1]:
                # mention span matches exactly a NE span
                final_mentions.add(mention)
                added=True
                break
        if added:
            continue
            
        for arg in args:
            if mention_span==arg[2] and arg[1] in ["ARG0", "ARG1", "ARG2", "ARG3", "ARG4"]:
                # mention span matches exactly a main argument span
                final_mentions.add(mention)
                added=True
                break
        if added:
            continue
           
        # Not an exact match of a main argument nor a NE. Test for "is NP within main arg PP".
        phrase_list = phrases[sentence_id]
        phrase_spans = dict()
        for phrase in phrase_list:
            # turn phrases into dicts for easy, quick access (span tuples as keys=hashed, phrase types as values)
            phrase_spans[phrase[1]]=phrase[0]
        containing_span = None
        min_span_size = 100
        
         # If mention is an NP and not already added, figure out if this mention is the largest
            # NP within a main arg PP
        for phrase_span, phrase_type in phrase_spans.items():
            # Finds the smallest phrase that contains the mention
            span_size = phrase_span[1]-phrase_span[0]
            if phrase_span[0]<=mention_span[0] and phrase_span[1]>=mention_span[1]:
                if span_size<min_span_size and span_size!=mention_span[1]-mention_span[0]:
                    containing_span = (phrase_span, phrase_type)
        if containing_span:
            phrase_type = containing_span[1]
            phrase_span = containing_span[0]
            if phrase_type == "PP":
                # smallest containing phrase is a PP
                for arg in args:
                    arg_span=arg[2]
                    arg_type = arg[1]
                    if arg_span==phrase_span and arg_type in {"ARG0", "ARG1", "ARG2", "ARG3", "ARG4"}:
                        # smallest containing phrase is a main arg
                        if mention_span in phrase_spans and phrase_spans[mention_span]=="NP":
                            final_mentions.add(mention)
                            added=True
                    
    return final_mentions