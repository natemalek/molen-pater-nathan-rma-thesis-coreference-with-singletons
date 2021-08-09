from random import Random
import re
import os

# for explanation, see http://natural-language-understanding.wikia.com/wiki/OntoNotes#Genres
genres = ('bc', 'bn', 'mz', 'nw', 'pt', 'tc', 'wb')

scorer = 'data/conll-2012/scorer/v8.01/scorer.pl'

score_pattern = re.escape('Final conll score ((muc+bcub+ceafe)/3) = ') + r'([\d\.]+)'