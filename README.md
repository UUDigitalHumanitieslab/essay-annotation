# essay-annotation
Parses essay annotation into FoLiA XML

This project contains scripts to convert Word documents with a specific markup (called essay annotation) to [FoLiA XML](https://proycon.github.io/folia/).
After the conversion is complete, there are scripts available to output the results to .csv- or .html-format.
You can find details on the scripts below.

## Requirements

Install Python 3.6 or newer. Once you have this installed, the necessary requirements can be retrieved using the following command from the root of this project:

```
pip install -r requirements.txt
```

(It is recommended but not required to do this within a [virtual environment](https://virtualenv.pypa.io/en/stable/)).

## Preprocessing

### Word to plain text

Before converting a new document it is recommended to clear/remove the `data` folder containing the output of your previous conversion.

Call `python conversions/docx2txt.py` with the specified file to convert the document to plain text files.

### Plain text to FoLiA

Call `python conversions/essay2xml.py` to convert the plain-text files to FoLiA.

## Conversions

### FoLiA to HTML

Call `python conversions/folia2html.py` to convert the plain-text files to FoLiA.

### FoLiA to .csv

Call `python conversions/xml2csv.py` to convert the plain-text files to FoLiA.

### FoLiA to .txt

Call `python conversions/xml2txt.py` to convert the FoLiA files to plain-text files.
