import sys
import re
import os.path

adjs = []
advs = []
substs = []
verbs = {}


def save_to_file(wordform, lemma, filename):
	pos_categories = ["adj", "adv", "subst", "verb"]
	#save all files in a folder "wordforms"
	path = 'wordforms/'
	#separate files for adj, adv, subst and verb
	if filename in pos_categories:
		filename = filename + ".txt"
		filename = os.path.join(path, filename)
		outputfile = open(filename, 'a', encoding='latin-1')
		outputfile.write("'" + wordform + "': ('" + lemma + "',),")
		outputfile.write("\n")
	else:
		filename = "other.txt"
		filename = os.path.join(path, filename)
		outputfile = open(filename, 'a', encoding='latin-1')
		outputfile.write("'" + wordform + "': '" + lemma + "',")
		outputfile.write("\n")

def save_to_common_file(wordform, lemma):
	#save all files in a folder "wordforms"
	path = 'wordforms/'
	#separate files for adj, adv, subst and verb
	filename = "all.txt"
	filename = os.path.join(path, filename)
	outputfile = open(filename, 'a', encoding='latin-1')
	outputfile.write("'" + wordform + "': '" + lemma + "',")
	outputfile.write("\n")

def extract_from_file():
	counter = 0
	with open(sys.argv[1], 'r', encoding='latin-1') as wordform_file:
		with open(sys.argv[2], 'r', encoding='latin-1') as lemma_file:
			previous_wordform = ""
			previous_lemmaid = 0
			previous_lemma = ""
			previous_pos = ""
			for wordform_line in wordform_file:
				# I skip suffixes ("words" beginning with "-"), like "-abel"
				linematch = re.match('([0-9]+)\t([0-9]+)\t(\w.*?)\t(\w.*?)\t.*', wordform_line)
				#if the line has 2 columns with numbers and the 3rd begins with a word or number
				if linematch:
					lemmaid_wordform_file = linematch.group(2)
					wordform = linematch.group(3)
					if "'" in wordform:
						wordform = re.sub("'", "\\'", wordform)
					#only keep the first word, which indicates pos
					pos = linematch.group(4).split()[0]
					#check if we moved on to next lexeme (wordform with different lemma)
					if lemmaid_wordform_file != previous_lemmaid:
						for lemma_line in lemma_file:
							#same match for lemma (the files have similar structure), but I need to run it again to catch new groups
							linematch_lemma = re.match('([0-9]+)\t([0-9]+)\t(\w.*?)\t.*', lemma_line)
							if linematch_lemma:
								lemmaid_lemma_file = linematch_lemma.group(2)
								lemma = linematch_lemma.group(3)
								if "'" in lemma:
									lemma = re.sub("'", "\\'", lemma)
								#if it's the same lemmaid it's the matching wordform and lemma pair
								if lemmaid_lemma_file == lemmaid_wordform_file:
									save_to_file(wordform, lemma, pos)
									save_to_common_file(wordform, lemma)
									previous_lemma = lemma
									previous_lemmaid = lemmaid_wordform_file
									break
						previous_wordform = wordform
						previous_pos = pos
					#if it's still the same lemmaid (so the same lexeme)
					#check if the previous wordform was the same to not keep duplicates
					elif wordform != previous_wordform:
						save_to_file(wordform, previous_lemma, pos)
						save_to_common_file(wordform, lemma)
						previous_wordform = wordform
						previous_pos = pos

					elif wordform == previous_wordform and pos != previous_pos:
						save_to_file(wordform, previous_lemma, pos)
						previous_wordform = wordform
						previous_pos = pos


extract_from_file()