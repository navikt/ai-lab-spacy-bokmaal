import spacy
from spacy.language import Language
from spacy.lang.nb import Norwegian
from spacy.lemmatizer import Lemmatizer
from spacy.lang.nb import LOOKUP as LOOKUP_NB
from spacy.lang.nb import LEMMA_EXC as LEMMA_EXC_NB
from spacy.lang.nb import LEMMA_INDEX as LEMMA_INDEX_NB
from spacy.lang.nb import LEMMA_RULES as LEMMA_RULES_NB

#load language model
nlp = spacy.load('nb_ud_ner')
#create a Doc object with an example sentence
doc = nlp(u'London er en stor by i Storbritannia.')

#for each token in the sentence print it's form, lemma, pos, tag, dependency relation and entity label
print("Sentence analysis:")
for token in doc:
    print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
          token.ent_iob_, token.ent_type_)

#create lemmatizer
lemmatizer = Lemmatizer(index=LEMMA_INDEX_NB, rules=LEMMA_RULES_NB, exceptions=LEMMA_EXC_NB, lookup=LOOKUP_NB)
#find lemmas for a specific word and POS, here the imperative form of a verb 'å mene'
lemmas = lemmatizer(u'men', u'VERB')
print("")
print("Lemma of a verb 'men' is:")
for lemma in lemmas:
	print(lemma)

#measure similarity
london_storbritannia = doc[0].similarity(doc[6])
by_london = doc[4].similarity(doc[0])
i_en = doc[5].similarity(doc[2])

print("")
print("Similarity:")
print("London + Storbritannia: " + str(london_storbritannia))
print("By + London: " + str(by_london))
print("I + en: " + str(i_en))