
## About lemmatizer data
In order to provide a list of wordforms for spaCy's lemmatizer I used **Norsk Ordbank**:
https://www.nb.no/sprakbanken/show?serial=oai%3Anb.no%3Asbr-5&lang=en

The script that extracts the wordforms can be found in **extract_wordform_and_lemma.py**. To be able to be efficient I had to first sort the files **fullformliste.txt** and **lemma.txt** by lemmaid so that I could easily match the wordform to its lemma without having to iterate over the whole file every time. I then saved all the wordforms and their lemmas to separate files according to their POS tag: adjectives, adverbs, verbs, nouns and other POS. Those wordforms are now available in spaCy's lang/nb/lemmatizer folder in files named after their POS (e.g. **_adjectives_wordforms.py**) and in **lookup.py**.