#!/usr/bin/python

# depgraph
# Copyright (C) 2008 Stefano Zacchiroli <zack@debian.org>
# Copyright (C) 2017 Sandro Knauß <hefee@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Graph the dependencies of all packages contained in a given Sources
file.

The dependencies are minimized, so that only direct dependencies are shown.
The green dots are packages without depdencies inside the set.
The lightblue dots are one end of the build chain.

If you have something like this:

    a -> b -> c
    a -> c
the second depdency is not shown.

You can enable the full dependency if you replace sgraph -> graph in the last for loop.

This file is optimized for the kde-pim build depenency."""

from __future__ import print_function

import sys
import copy
from debian import deb822

__fresh_id = 0

def main():
    def get_id():
        global __fresh_id
        __fresh_id += 1
        return ("NODE_%d" % __fresh_id)

    def emit_arc(node1, node2):
        print('  "%s" -> "%s" ;' % (node1, node2))
    def emit_node(node, dsc):
        print('  "%s" [label="%s"] ;' % (node, dsc))
    def emit_nodecolor(node, color):
        print('  "%s" [fillcolor="%s", style="filled"] ;' % (node, color))

    sources={pkg['package']:[] for pkg in deb822.Sources.iter_paragraphs(open('Sources'))}
    p2s = {}

    for pkg in deb822.Sources.iter_paragraphs(open('Packages')):
       if 'Source' in pkg and pkg['Source'] in sources:
           sources[pkg['Source']].append(pkg['Package'])
           p2s[pkg['Package']] = pkg['Source']
       elif pkg['Package'] in sources:
           p2s[pkg['Package']] = pkg['Package']
       #else:
       #    print("Package will not processed", pkg['Package'])


    graph = {}    # full graph

    for pkg in deb822.Sources.iter_paragraphs(open('Sources')):
        name = pkg['package']
        rels = pkg.relations
        sDeps = set()
        for deps in rels['build-depends']:
            if len(deps) == 1:
                if deps[0]['name'] not in p2s:
                    continue
                sDeps.add(p2s[deps[0]['name']])

        graph[name] = sDeps

    sgraph = {}     # minimized graph
    ograph = graph
    fgraph = {}     # full dependency graph

    for i in range(10):
        changed = False
        for pkg in ograph:
            deps = copy.copy(ograph[pkg])
            for dep in ograph[pkg]:
                deps |= ograph[dep]
            if deps != ograph[pkg]:
                changed = True
            fgraph[pkg] = deps

        if not changed:
            break
        ograph = fgraph

    for pkg in fgraph:
        deps = copy.copy(graph[pkg])
        for dep in graph[pkg]:
            deps -= fgraph[dep]
        sgraph[pkg] = deps

    print("digraph pim {")
    for pkg in graph:
        name = pkg
        sDeps = sgraph[pkg]
        if sDeps == set():
            emit_nodecolor(name, 'darkgreen')
        else:
            for p in sgraph:
                if p == pkg:
                    continue
                if pkg in sgraph[p]:
                    break
            else:
                emit_nodecolor(name, 'lightblue')

    for pkg in graph:
        name = pkg
        sDeps = sgraph[pkg]
        for dep in sDeps:
            emit_arc(dep, name)
    print("}")

if __name__ == '__main__':
    main()

