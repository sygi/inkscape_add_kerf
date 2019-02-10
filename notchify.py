#!/usr/bin/env python

# These two lines are only needed if you don't put the script directly into
# the installation directory
import sys
import simplestyle # will be needed here for styles support
sys.path.append('/usr/share/inkscape/extensions')

# We will use the inkex module with the predefined Effect base class.
import inkex
import cubicsuperpath
import simpletransform
import metaext

import os
try:
    from subprocess import Popen, PIPE
    bsubprocess = True
except:
    bsubprocess = False

class NotchifyEffect(inkex.Effect):
    """
    Example Inkscape effect extension.
    """
    def __init__(self):
        """
        Constructor.
        """
        inkex.Effect.__init__(self)

        # TODO: different options
        self.OptionParser.add_option('', '--height', action = 'store',
          type = 'float', dest = 'height', default = '10.0',
          help = 'Height in mm')

        self.OptionParser.add_option('', '--width', action = 'store',
          type = 'float', dest = 'width', default = '10.0',
          help = 'Width in mm')
        
        self.OptionParser.add_option('', '--number', action = 'store',
          type = 'int', dest = 'number', default = '1',
          help = 'Number of notches')
        # TODO: to the edge (left/up?, right/down?)

        self.OptionParser.add_option("-o", "--orientation",
                                     action="store", type="string", 
                                     dest="orientation", default='lu',
                                     help="orientation")
        
        self.OptionParser.add_option("", "--extra_distance",
                                     action="store", type="inkbool", 
                                     dest="extra_distance", default=False,
                                     help="Have extra distance")

    # TODO: sygi: simplify
    def getselected_nodes(self):
        """Collect selected path nodes."""
        self.selected_nodes = {}
        for path in self.options.selected_nodes:
            sel_data = path.rsplit(':', 2)
            path_id = sel_data[0]
            sub_path = int(sel_data[1])
            sel_node = int(sel_data[2])
            if path_id not in self.selected_nodes:
                self.selected_nodes[path_id] = {sub_path: [sel_node]}
            else:
                if sub_path not in self.selected_nodes[path_id]:
                    self.selected_nodes[path_id][sub_path] = [sel_node]
                else:
                    self.selected_nodes[path_id][sub_path].extend([sel_node])

    def get_query(self, path_id, query):
        f = self.args[-1]
        scale = self.unittouu('1px')
#        inkex.debug("scale %s" % str(scale))
        command = 'inkscape --query-%s --query-id=%s "%s"' % (query,path_id,f)
        if bsubprocess:
            p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
            rc = p.wait()
            result = scale*float(p.stdout.read())
            err = p.stderr.read()
        else:
            f,err = os.popen3(command)[1:]
            result = scale*float(f.read())
            f.close()
            err.close()

        return result

    def get_bounding_box(self, path_id):
        min_x = self.get_query(path_id, 'x')
        max_x = min_x + self.get_query(path_id, 'width')
        min_y = self.get_query(path_id, 'y')
        max_y = min_y + self.get_query(path_id, 'height')
        return min_x, max_x, min_y, max_y

    def add_rect(self, coords, size=(20, 20), corner="ul"):
        # coords of the upper-left corner
#        inkex.debug("coords %s" % coords)
        whole_tree = self.document.getroot()
        layer_id = ".//{http://www.w3.org/2000/svg}g"
        last_layer = whole_tree.findall(layer_id)[-1]
        if corner[0] == "l":
            coords[1] -= size[0]
        elif corner[0] != "u":
            inkex.errormsg("corner[0] should be u/l (is %s)" % corner[0])

        if corner[1] == "r":
            coords[0] -= size[1]
        elif corner[1] != "l":
            inkex.errormsg("corner[1] should be l/r")
        
        rect = inkex.etree.Element(inkex.addNS('rect','svg'))
        rect.set('x', str(coords[0]))
        rect.set('y', str(coords[1]))  # upper-left corner
        rect.set('height', str(size[0]))
        rect.set('width', str(size[1]))
        new_width = self.unittouu("0.5mm")
        style = {'stroke-width': new_width, 'fill': 'none',
                'stroke':'#000000'}
        rect.set('style', simplestyle.formatStyle(style))
        last_layer.append(rect)

    def add_notches(self, coords, size, num, distance=False):
        diff_x = coords[0][0] - coords[1][0]
        diff_y = coords[0][1] - coords[1][1]

        if abs(diff_x) > self.epsilon and abs(diff_y) > self.epsilon:
            inkex.errormsg("The line has to be vertical or horizontal")
            return

        if abs(diff_x) <= self.epsilon:
            vertical = True
        else:
            vertical = False
        total_width = max(abs(diff_x), abs(diff_y))
        
        # height: depth of the notch, width: width of the notch

        num_spaces = num - 1
        if distance:
            num_spaces += 2

        total_notch_width = num * size[1]
#        inkex.debug("Total width %f, total notch width %f" % (total_width, total_notch_width))
        if vertical:
            size[0], size[1] = size[1], size[0]

        total_spacing = total_width - total_notch_width
        one_space = total_spacing / num_spaces

        if vertical:
            # TODO: fix naming
            lower, upper = coords[0], coords[1]
            if diff_y > 0:
                lower, upper = upper, lower
            if self.options.orientation == "lu":
                corner = "lr"
            else:
                corner = "ll"
            position = upper
            if distance:
                position[1] -= one_space
            for i in range(num):
                self.add_rect(list(position), size, corner=corner)
#                inkex.debug("Drawing rect at %s" % position)
#                inkex.debug("size[1]: %f, one space: %f" % (size[0], one_space))
                position[1] -= size[0]
#                inkex.debug("Drawing rect at %s" % position)
                position[1] -= one_space
        else:
            left, right = coords[0], coords[1]
            if diff_x > 0:
                left, right = right, left
            if self.options.orientation == "lu":
                corner = "ll"
            else:
                corner = "ul"

            position = left
            if distance:
                position[0] += one_space
            for i in range(num):
                self.add_rect(list(position), size, corner=corner)
                position[0] += size[1]
                position[0] += one_space


    def effect(self):
        """
        Effect behaviour.
        """
        # Get script's "--what" option value.
#        inkex.debug(str(self.options))

        self.getselected_nodes()
        # TODO: make epsilon smaller after tests
        self.epsilon = self.unittouu("0.2mm")
#        inkex.debug("Document unit %s" % self.getDocumentUnit())
#        inkex.debug("Epsilon %f" % self.epsilon)

#        inkex.debug(
#            'Number of selected objects: {0}'.format(
#                len(self.selected)))
#        inkex.debug(
#            'Number of paths with selected nodes: {0}'.format(
#                len(self.selected_nodes)))

        for id_, node in self.selected.iteritems():
            if node.tag == inkex.addNS('path', 'svg'):
#                inkex.debug("my node: %s" % inkex.etree.tostring(node))
                my_path = cubicsuperpath.parsePath(node.get('d'))
                if 'transform' in node.keys():
                    simpletransform.fuseTransform(node)
                #inkex.debug("my path %s" % my_path)
#            inkex.debug("bounding box: %s" % str(self.get_bounding_box(id_)))

        coords = []
        for path, sel in self.selected_nodes.iteritems():
            ele = self.getElementById(path)
            csp = cubicsuperpath.parsePath(ele.get('d'))
            for sub in sel:
#                inkex.debug(
 #                   '{0} - selected nodes of subpath {1}: {2}'.format(
#                        path, sub, sel[sub]))
                if not len(sel[sub]) == 2:
                    inkex.errormsg("Select exactly 2 nodes (currently %d)" %
                            len(sel[sub]))
                    return
                for node in sel[sub]:
                    coords.append(csp[sub][node][1])
#                    inkex.debug(
#                        '{0} - selected node {1}: {2}'.format(
#                            path, node, coords[-1]))
        coords = [[self.uutounit(c, "px") for c in point] for point in coords]
#        inkex.debug("both coords %s "% coords)
#        inkex.debug(str(self.options.selected_nodes))
        self.add_notches(coords, size=[self.options.height, self.options.width],
                num=self.options.number, distance=self.options.extra_distance)


effect = NotchifyEffect()
effect.affect()
