# Norwegian model for spaCy
This project's goal is to develop a Norwegian language model for Python library **spaCy**.

## About the data
The model was based on an unpublished dataset developed by **Nasjonalbiblioteket**, **Schibsted** and **Language Technology Group** at UiO (to be published autumn 2018) in .conllu format and following Universal Dependencies annotation. It is similar to this treebank: 
https://github.com/UniversalDependencies/UD_Norwegian-Bokmaal
only it contains NER tags in the 10th column of each token line and interprets some parts of speech differently (mostly pronouns/determiners).

## How to train the model
First of all, I converted the .conllu files (train, dev and test) to .json, because that's the format **spaCy** supports:
```
python -m spacy convert path/to/train-file.conllu path/to/output/directory -m
python -m spacy convert path/to/dev-file.conllu path/to/output/directory -m
python -m spacy convert path/to/test-file.conllu path/to/output/directory -m
```
I chose the '-m' option to be able to append morphological features to POS tags, so I end up with a tag looking like this: 'NOUN__Definite=Ind|Gender=Neut|Number=Sing' instead of just plain 'NOUN'.

To train the model I run the command:
```
python -m spacy train nb path/to/output/directory path/to/train-file.json path/to/dev-file.json -n 10
```
This gave me the following results:

Itn. |  P.Loss	|	N.Loss	|	UAS	|	NER P.|	NER R.|	NER F.|	Tag % |	Token %| |
-----|----------|-----------|-------|---------|-------|-------|-------|--------|-|
0    |  17237.645|   1388.183|  84.014| 75.985| 74.985| 75.482| 93.674| 100.000|5044.2| 0.0
1    |  423.721 |	13.932  |	86.053| 78.795| 78.276| 78.535| 94.655| 100.000|5988.9| 0.0  
2    |  350.019 |	9.434   |	86.922| 77.964| 77.917| 77.941| 95.026| 100.000|6096.9| 0.0
3    |  306.036 |	7.817   |	87.333| 79.476| 78.097| 78.781| 95.146| 100.000|5308.6| 0.0
4    |  272.160 |	6.333   |	87.579| 80.036| 79.174| 79.603| 95.198| 100.000|5649.8| 0.0
5    |  247.511 |	5.729   |	87.845| 78.030| 78.217| 78.123| 95.292| 100.000|5796.3| 0.0
6    |  226.625 |	5.190   |	87.824| 78.652| 78.935| 78.793| 95.363| 100.000|5884.3| 0.0
7    |  208.418 |	4.364   |	87.852| 78.481| 77.917| 78.198| 95.308| 100.000|5853.0| 0.0
8    |  191.116 |	3.985   |	88.132| 77.718| 77.858| 77.788| 95.212| 100.000|5856.2| 0.0
9    |  178.484 |	3.454   |	88.129| 78.797| 77.618| 78.203| 47.975| 100.000|5853.8| 0.0

The best model seems to be model 6, so I turn it into a package for convenience:
```
python -m spacy package path/to/model path/to/output/directory
```
Before I do that I manually fill out information in file meta.json that lies in path/to/model (name, version, description etc). The script will throw an exception if those fields are empty.

In order to install the package I now go to the package's directory and run:
```
python setup.py sdist
```
and
```
pip install /path/to/dist/name-of-model.tar.gz
```
## Loading and using the model
I can now load the model from Python shell with:
```
spacy.load('name-of-model')
```
or evaluate it:
```
python -m spacy evaluate name-of-model path/to/test-file.json
```
which gives me the folllowing result:

    Time               5.00 s         
    Words              30034          
    Words/s            6010           
    TOK                100.00         
    POS                94.40          
    UAS                87.28          
    LAS                84.46          
    NER P              70.85          
    NER R              70.34          
    NER F              70.59   

I also added a custom pipeline component, **EntityMatcher**. Its code is based on this solution:
https://support.prodi.gy/t/adding-custom-attribute-to-doc-having-ner-use-attribute/356/6

It extracts data from various text files and labels it with an entity tag (PER, LOC, ORG or MISC). It enforces 'PROPN___' tag on all the entity tokens too (since all named entities are proper nouns). One can also check if the entity label comes from custom **EntityMatcher** or built-in **EntityRecognizer** by using the **'via_patterns'** extension, which returns True in the first case and False in the other.

Examples of use can be found in **spacy_examples.py**