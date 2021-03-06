from __future__ import print_function
import codecs
import glob
import os
import re

from pynlpl.formats import folia

from models import PartAnnotation

CORRECTIONS_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/corrections.foliaset.xml'
SEMANTICROLES_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/semanticroles.foliaset.xml'
WHITESPACE_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/whitespace.foliaset.xml'

TAG = re.compile(r'(\w[\*\+\w]*)')
ORPHAN_TAG = re.compile(r'(^|[^\]\w\*\+])(\w+[\*\+])')


class ParseException(Exception):
    def __init__(self, error, line, offset, text):
        super(ParseException, self).__init__()
        message_start = u'[{}] line: {}, offset: {} '.format(error.upper(), line, offset)
        if len(text) > 80 and offset > 40:
            shift = offset - 40
            text = text[shift:]
            offset = 40
        self.message = message_start + text[:80].rstrip() + '\n' + (' ' * (len(message_start) + offset - 2)) + '^^^'

    def __unicode__(self):
        return self.message

def extract_annotations(n, s, pa=None):
    """
    Extracts all annotations from a (plain text) sentence.
    """
    if not pa:
        pa = PartAnnotation(s, None)

    for start, end in get_matching_brackets(s):
        sentence = s[start+1:end]
        match = ORPHAN_TAG.search(sentence)
        if match:
            raise ParseException('orphan tag', n, match.pos, sentence)

        post_sentence = s[end+1:]

        annotation_match = TAG.match(post_sentence)
        if not annotation_match:
            if not post_sentence:
                raise ParseException('no annotation', n, end+1, s)
            else:
                raise ParseException('wrong annotation format', n, end+1, s)
        annotation = annotation_match.group(1)

        p_child = PartAnnotation(sentence, annotation)
        pa.add_child(p_child, start, end + annotation_match.end(1) + 1)

        # Recurse into the annotation to find other annotations
        p_child = extract_annotations(n, sentence, p_child)

    return pa


def get_matching_brackets(s):
    """
    Finds the outer annotations in a sentence.
    """
    matches = []
    open_brackets = 0
    for n, c in enumerate(s):
        if c == '[':
            open_brackets += 1
            if open_brackets == 1:
                start = n
        if c == ']':
            open_brackets -= 1
            if open_brackets == 0:
                end = n
                matches.append((start, end))
    return matches


def count_brackets(n, line):
    """
    Matches the number of brackets on a line.
    """
    left_brackets_count = line.count('[')
    right_brackets_count = line.count(']')
    if left_brackets_count != right_brackets_count:
        raise ParseException(
            'number of brackets do not match',
            n,
            line.rfind('[' if left_brackets_count > '[' else ']'),
            line)


def check_no_annotation(n, line):
    """
    Check if there's a bracket without annotation.
    """
    no_annotation_index = line.find('] ')
    if no_annotation_index >= 0:        
        raise ParseException(
            'no annotation',
            n,
            no_annotation_index,
            line)


def start_folia_document(filename):
    """
    Creates a FoLiA document, declares the annotation types and adds a Text and Paragraph.
    TODO: set correct metadata.
    """
    doc = folia.Document(id=filename)
    doc.declare(folia.Correction, CORRECTIONS_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.declare(folia.SemanticRole, SEMANTICROLES_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.declare(folia.Whitespace, WHITESPACE_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.metadata = folia.NativeMetaData(score='88', time='3', words='110')  # TODO: set this correctly
    text = doc.append(folia.Text)
    text.add(folia.Paragraph)
    return doc


def process_line(n, line, doc):
    """
    Processes a single line from the plain-text annotation and converts that to a FoLiA Sentence.
    """
    # Strip the line and create a PartAnnotation structure
    line = line.strip()
    pa = extract_annotations(n, line)

    # Convert the PartAnnotation structure to a FoLiA Sentence
    current_paragraph = next(doc.paragraphs())
    roles = []
    if not pa.original and not pa.edited:
        whitespace = pa.to_folia_whitespace(doc, current_paragraph)
        current_paragraph.add(whitespace)
    # Create a new sentence in the document
    else:
        sentence = current_paragraph.add(folia.Sentence)
        _, roles = pa.to_folia_sentence(doc, sentence)

    # Add all collected roles to the SemanticRolesLayer
    if roles:
        layer = sentence.add(folia.SemanticRolesLayer)
        for role in roles:
            layer.add(role)


def process_file(dirname, filename):
    """
    Processes a plain-text annotation file and converts that to FoLiA XML.
    """
    with codecs.open(filename, 'rb', encoding='utf-8') as f:
        #print 'Processing', filename
        base = os.path.splitext(os.path.basename(filename))[0]
        doc = start_folia_document(base)
        parsing_failed = False
        errors = []
        for n, line in enumerate(f):
            try:
                count_brackets(n, line)
                check_no_annotation(n, line)
                process_line(n, line, doc)
            except ParseException as e:
                parsing_failed = True
                errors.append(e)
            except Exception as e:
                # other error, give information about the line
                print(filename)
                print('{0}: '.format(n), end='')
                print(line)
                raise e

        if not parsing_failed:
            outpath = os.path.join(dirname, 'out')
            outfile = base + '.xml'
            
            if not os.path.exists(outpath):
                os.makedirs(outpath)

            doc.save(os.path.join(outpath, outfile))
        else:
            print(u'Parsing failed for {}! Errors:'.format(filename))
            for e in errors:
                print(e.message)


def process_folder(dirname):
    """
    Processes a whole folder of plain-text annotation files.
    """
    for filename in glob.glob(dirname + '/*.txt'):
        process_file(dirname, filename)


if __name__ == '__main__':
    process_folder(os.path.join(os.path.dirname(__file__),'..', 'data'))
