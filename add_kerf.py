#!/usr/bin/env python

# These two lines are only needed if you don't put the script directly into
# the installation directory
import sys
import simplestyle # will be needed here for styles support
sys.path.append('/usr/share/inkscape/extensions')

# We will use the inkex module with the predefined Effect base class.
import inkex
import metaext

class AddKerf(inkex.Effect):
    """
    An Inkscape extension which joins multiple lines in one object and adds
    kerf to it.
    """
    def __init__(self):
        """
        Constructor.
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)

        # Define string option "--what" with "-w" shortcut and default value "World".
        # TODO: better name
        self.OptionParser.add_option('-w', '--what', action = 'store',
          type = 'float', dest = 'what', default = '0.0',
          help = 'Kerf in 1/10 mm.')

    def set_appropriate_width(self, kerf_in_mm):
        found = False
        for _, node in self.selected.iteritems():
            if node.tag == inkex.addNS('g', 'svg'):
                inkex.error("Can't add kerf to a group, please ungroup first.")
            if node.tag == inkex.addNS('path', 'svg'):
                style = {'stroke-width': kerf_in_mm, 'fill': 'none',
                        'stroke':'#000000'}
                style = simplestyle.formatStyle(style)
                node.set('style', style)
                found = True
        return found

    def effect(self):
        """% mod
        Effect behaviour.
        """
        # Get script's "--what" option value.
        what = self.options.what / 10.
        negative_kerf = False
        if what < 0.:
            what = -what
            negative_kerf = True

        kerf_in_mm = self.unittouu(str(what) + " mm")

        operation_list = ["StrokeToPath", "SelectionUnion",
            "SelectionBreakApart", "SelectionUnion", "SelectionBreakApart"]
        if negative_kerf:
            operation_list[-2] = "SelectionIntersect"

        join_ext = metaext.MetaEffect(operation_list)

        if not self.set_appropriate_width(kerf_in_mm):
            objectify = metaext.MetaEffect(["ObjectToPath"])
            objectify.effect(self.document, self.selected, self.doc_ids)
            if not self.set_appropriate_width(kerf_in_mm):
                inkex.error("Didn't found any selected path, breaking")
                return
        
        join_ext.effect(self.document, self.selected, self.doc_ids)

        for _, node in self.selected.iteritems():
            #inkex.debug("node %s" % inkex.etree.tostring(node))
            if node.tag == inkex.addNS('path', 'svg'):
                new_width = self.unittouu("0.5mm")
                colour = '#ff0000' if negative_kerf else '#000000'
                style = {'stroke-width': new_width, 'fill': 'none',
                        'stroke': colour}
                style = simplestyle.formatStyle(style)
                node.set('style', style)
             #   inkex.debug("node %s" % inkex.etree.tostring(node))


# Create effect instance and apply it.
effect = AddKerf()
effect.affect()
