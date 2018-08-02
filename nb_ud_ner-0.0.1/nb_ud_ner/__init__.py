# coding: utf8
from __future__ import unicode_literals

from pathlib import Path
from spacy.util import load_model_from_init_py, get_model_meta
from spacy.language import Language
from spacy.tokens import Span
from spacy.matcher import PhraseMatcher
from spacy.matcher import Matcher
import ujson
import os.path
from collections import defaultdict
import string
import re
import glob

__version__ = get_model_meta(Path(__file__).parent)['version']


def load(**overrides):
    Language.factories['entity_matcher'] = lambda nlp, **cfg: EntityMatcher(nlp, **cfg)
    return load_model_from_init_py(__file__, **overrides)

class EntityMatcher(object):
    name = 'entity_matcher'  # component name shown in pipeline

    def __init__(self, nlp):
        patterns = defaultdict(list)
        Span.set_extension('via_patterns', default=False)
        labels = ['ORG', 'LOC', 'PER', 'MISC']
        #get entities with given label and add to matcher for each label in list
        for label in labels:
            self.entities = self.get_entities(label)
            self.label = nlp.vocab.strings[label]  # get entity label ID
            self.matcher = PhraseMatcher(nlp.vocab)
            patterns[label] = [nlp(text) for text in self.entities]
        for label, pattern in patterns.items():
            self.matcher.add(label, None,  *pattern)
		
    def __call__(self, doc):
        matches = self.matcher(doc)
        spans = []  # keep the spans for later so we can merge them afterwards
        for _, start, end in matches:
            # create Span for matched country and assign label
            entity = Span(doc, start, end, label=self.label)
            entity._.via_patterns = True
            spans.append(entity)
        doc.ents = list(doc.ents) + spans  # overwrite doc.ents and add entities – don't replace!
        for span in spans:
            span.merge()  # merge all spans at the end to avoid mismatched indices
        return doc  # don't forget to return the Doc!

    def get_entities(self, label):
    	entity_list = []
    	#get entities tagged with that label from a file label.csv and return a list of those entities
    	filename = label.lower() + ".csv"
    	path = 'entity_matcher/'
    	filename = os.path.join(path, filename)
    	first_line_skipped = False
    	with open(filename, 'r', encoding='utf-8') as file:
    		for line in file:
    			#skip the first line containg heading etc
    			if not first_line_skipped:
    				first_line_skipped = True
    				continue
    			line = line.split(";")
    			entity = re.sub(r'[^\w\s]','',line[1])
    			#remove extra whitespace after removing punctuation, otherwise it will end up as a token
    			entity = re.sub(' +',' ',entity)
    			words = entity.split()
    			#PhraseMatcher only supports phrases up to 10 tokens
    			if len(words) <= 10:
    				entity_list.append(entity.title())
    	return entity_list
