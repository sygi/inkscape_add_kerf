#!/usr/bin/env python

# These two lines are only needed if you don't put the script directly into
# the installation directory
import sys
sys.path.append('/usr/share/inkscape/extensions')

# We will use the inkex module with the predefined Effect base class.
import inkex
import tempfile

try:
    from subprocess import Popen, PIPE
    bsubprocess = True
except:
    bsubprocess = False

class MetaEffect(object):
    """
    Inkscape extension running the commands from the list on the selected
    objects.
    """
    def __init__(self, command_list):
        """
        Constructor.
        """
        self._command_list = command_list


    def command_on_selection(self):
        selected = ["--select={}".format(id_)
                for id_, _ in self.selected.iteritems()]
        selected = " ".join(selected)
        verbs = ["--verb={}".format(cmd) for cmd in self._command_list]
        verbs = " ".join(verbs)
        command = "{} {}".format(selected, verbs)
        return command

    def run_file(self, filename, cmd):
        cmd += " --verb=FileSave --verb=FileQuit"
        if bsubprocess:
            p = Popen('inkscape "%s" %s' % (filename, cmd), shell=True,
                    stdout=PIPE, stderr=PIPE)  # TODO: gui-less version
            rc = p.wait()
            f = p.stdout
            err = p.stderr
        else:
            _, f, err = os.popen3("inkscape %s %s" % (filename, cmd))

        f.close()
        err.close()

    def run_commands_on_file(self, command):
        """Run the actions on the svg xml tree"""
        # First save the document
        svgfile = tempfile.mktemp(".svg")
        self.document.write(svgfile)

        # Run the action on the document
        self.run_file(svgfile, command)

        # Open the resulting file
        stream = open(svgfile, 'r')
        new_svg_doc = inkex.etree.parse(stream)
        stream.close()

        # Clean up.
        try:
            os.remove(svgfile)
        except Exception:
            pass

        # Return the new document
        return new_svg_doc

    def effect(self, document, selected, doc_ids):
        """
        Effect behaviour.
        Overrides base class' method
        """
        self.document = document
        self.selected = selected
        whole_tree = self.document.getroot()
        svg_id_id = ".//{http://www.w3.org/2000/svg}path[@id]"
        prev_ids = set(child.get('id')
                for child in whole_tree.findall(svg_id_id))

        command = self.command_on_selection()
        self.document = self.run_commands_on_file(command)

        new_ids = set(child.get('id')
                for child in self.document.getroot().findall(svg_id_id))
        diff_ids = list(new_ids.difference(prev_ids))
        self.selected = {}

        for i in diff_ids:
            path = '//*[@id="%s"]' % i
            for node in self.document.xpath(path, namespaces=inkex.NSS):
                self.selected[i] = node
        self.doc_ids = {}  
        docIdNodes = self.document.xpath('//@id', namespaces=inkex.NSS)
        for m in docIdNodes:
            self.doc_ids[m] = 1

        document._setroot(self.document.getroot())
        selected.clear()
        selected.update(self.selected)
        doc_ids.clear()
        doc_ids.update(self.doc_ids)
