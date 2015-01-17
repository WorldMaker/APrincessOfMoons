# Inform 7 "Stanza Format" extension for musdex by Max Battcher
# Some Rights Reserved. Licensed for use under CC0, Public Domain, or
# the MIT License, whichever grants more rights in your jurisdiction.
import codecs
import datetime
import logging
import os.path
import re
import textwrap
import yaml

HEADINGS = re.compile(r'^(Volume|Book|Part|Chapter|Section)(\s*\d+)?(.*)', re.IGNORECASE)
['Volume', 'Book', 'Part', 'Chapter', 'Section']
PILCROW = u'\u00b6'
I7MANIFEST = 'manifest.yaml'
I7EXT = '.txt'
I7FRONTMATTER = 'frontmatter'

_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def _slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    
    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)

class I7StanzaHandler:
    def __init__(self, archive, location, manifest={}):
        self.archive = archive
        self.location = location
        self.manifest = manifest

    def check(self):
        return True

    def extract(self, force=True):
        # No incremental extract, so we ignore force
        manifestfiles = set(self.manifest.keys())
        files = []

        logging.info("Extracting all of %s" % self.archive)
        arc = open(self.archive)
        fname = I7FRONTMATTER + I7EXT
        path = os.path.relpath(os.path.join(self.location, fname))
        out = codecs.open(path, 'w', 'utf8')
        files.append(fname)
        if path in manifestfiles: manifestfiles.remove(path)
        yield (path, datetime.datetime.now())

        for line in arc:
            m = HEADINGS.match(line)
            if m is not None:
                out.close()
                slug = _slugify(m.group(3))
                fname = slug + I7EXT
                i = 1
                while fname in files:
                    fname = "%s%s%s" % (slug, i, I7EXT)
                    i += 1
                path = os.path.relpath(os.path.join(self.location, fname))
                out = codecs.open(path, 'w', 'utf8')
                files.append(fname)
                if path in manifestfiles: manifestfiles.remove(path)

            line = line.replace(PILCROW, '\\' + PILCROW)
            line = line.replace('\n', PILCROW)
            line = line.replace('\t', '\t\n')

            out.write(textwrap.fill(line, 72))
        
        out.close()

        # Order manifest
        path = os.path.relpath(os.path.join(self.location, I7MANIFEST))
        if path in manifestfiles: manifestfiles.remove(path)
        out = open(path, 'w')
        yaml.dump(files)
        out.close()

        # Check for removed files
        if manifestfiles:
            for f in manifestfiles:
                yield (f, None)

    def combine(self, force=True):
        # No incremental combine, so we ignore force
        logging.info("Combining %s" % self.archive)

        # Order matters, so we will rely on our own special manifest
        # rather than self.manifest
        manfile = open(os.path.join(self.location, I7MANIFEST))
        manifest = yaml.load(f)
        manfile.close()

        out = open(self.archive, 'w')

        for f in manifest:
            inf = open(os.path.join(self.location, f))
            for line in inf:
                line = line.replace('\n', '')
                line = re.replace(r'(?<!\\)' + PILCROW, '\n')
                line = line.replace('\\' + PILCROW, PILCROW)
                out.write(line)

        out.close()
        yield (self.location, datetime.datetime.now())

# vim: ai et ts=4 sts=4 sw=4
