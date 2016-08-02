#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright (c) 2016 @peakbook
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Convert BeamerPDF to ODP

Usage:
    bpdf2odp.py <input> <output> [--note=<note>, --dpi=<dpi>]

Options:
    --note=<note>      Add note
    --dpi=<dpi>        DPI [default: 300]

"""

import os,sys,re
import tempfile, shutil, glob
from docopt import docopt
from PIL import Image as im
from odf.opendocument import OpenDocumentPresentation
from odf.style import Style, MasterPage, PageLayout, PageLayoutProperties, \
TextProperties, GraphicProperties, ParagraphProperties, DrawingPageProperties
from odf.text import P
from odf.draw  import Page, Frame, Image, TextBox
from odf.presentation import Notes

def getimageinfo(fname):
    img = im.open(fname)
    return img.size

def genslideimages(fname, imgdir, dpi):
    cmd = "convert -density %d %s '%s/" % (dpi, fname, imgdir) + "slide_%05d.png'"
    os.system(cmd)

def readnotesfromfile(fname):
    f = open(fname)
    data = f.read()
    f.close()

    notes = []
    idx_s = []
    idx_e = []
    framenum = []
    r = re.compile("###\s\d+")
    iterator = r.finditer(data)
    for m in iterator:
        framenum.append(int(m.group()[3:]))
        idx_s.append(m.end()+1)
        idx_e.append(m.start()-1)

    idx_e.append(len(data))
    idx_e = idx_e[1:]
    for i in range(0,len(idx_s)):
        notes.append(data[idx_s[i]:idx_e[i]].replace("\\\\","\n"))

    notedict = dict()
    offset = 0
    for (i,note) in zip(framenum,notes):
        if i+offset in notedict:
            offset+=1
        notedict[i+offset] = note

    return notedict

if __name__ == "__main__":
    args = docopt(__doc__, version="0.0.1")

    if args["--note"] != None:
        notes = readnotesfromfile(args["--note"])

    dpi = int(args["--dpi"])
    pict_dir = tempfile.mkdtemp()
    genslideimages(args["<input>"], pict_dir, dpi)

    fnames = sorted(glob.glob(os.path.join(pict_dir,"*.png")))
    if len(fnames) <= 0:
        sys.stderr.write("No images in %s\n" % pict_dir)
        sys.exit(1)

    w,h = getimageinfo(fnames[0])

    doc = OpenDocumentPresentation()

    # We must describe the dimensions of the page
    pagelayout = PageLayout(name="MyLayout")
    doc.automaticstyles.addElement(pagelayout)
    pagelayout.addElement(PageLayoutProperties(margin="0pt", pagewidth=str(w)+"pt",
        pageheight=str(h)+"pt", printorientation="landscape"))

    # Style for the image frame
    photostyle = Style(name="beamer-image", family="presentation")
    doc.styles.addElement(photostyle)

    # Create page style
    dpstyle = Style(name="dp1", family="drawing-page")
    doc.automaticstyles.addElement(dpstyle)

    prstyle = Style(name="pr1", family="presentation", parentstylename="BeamerMaster-notes")
    doc.styles.addElement(prstyle)

    # Every drawing page must have a master page assigned to it.
    masterpage = MasterPage(name="BeamerMaster", pagelayoutname=pagelayout)
    doc.masterstyles.addElement(masterpage)

    # Slides
    i = 1
    for imgfname in fnames:
        fname = os.path.join(pict_dir, imgfname)
        page = Page(stylename=dpstyle, masterpagename=masterpage)
        doc.presentation.addElement(page)

        note =  Notes(stylename=dpstyle)
        page.addElement(note)
        noteframe = Frame(stylename=prstyle, layer="layout", width="16.799cm", height="13.364cm", x="2.1cm", y="14.107cm", placeholder="true", classname="notes")
        note.addElement(noteframe)
        notetextbox = TextBox()
        notetextbox.addElement(P(text= notes[i] if (i in notes) else ""))
        noteframe.addElement(notetextbox)

        photoframe = Frame(stylename=photostyle, width=str(w)+"pt", height=str(h)+"pt", x="0pt", y="0pt")
        page.addElement(photoframe)
        href = doc.addPicture(fname)
        photoframe.addElement(Image(href=href))

        i+=1

    doc.save(args["<output>"])
    shutil.rmtree(pict_dir)
