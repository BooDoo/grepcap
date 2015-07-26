#!/usr/bin/env python2

import os
import sys
import glob
import re
# import png
from imageio import imwrite
from videogrep import *
from moviepy.video.VideoClip import VideoClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

debug=True
font_dir='/usr/share/fonts/TTF/'
font_path=os.path.join(font_dir, 'OpenSans-Semibold.ttf')

class ShadowedTextClip(TextClip):
    def __init__(self, txt=None, filename=None, size=None, color='black',
                 bg_color='transparent', fontsize=None, font='Courier',
                 stroke_color=None, stroke_width=1, method='label',
                 kerning=None, align='center', interline=None,
                 tempfilename=None, temptxt=None,
                 transparent=True, remove_temp=True,
                 shadow=None, print_cmd=False):

        import tempfile
        import subprocess as sp

        from moviepy.tools import subprocess_call
        from moviepy.config import get_setting

        from moviepy.video.VideoClip import *

        if txt is not None:
            if temptxt is None:
                temptxt_fd, temptxt = tempfile.mkstemp(suffix='.txt')
                try:  # only in Python3 will this work
                    os.write(temptxt_fd, bytes(txt, 'UTF8'))
                except TypeError:  # oops, fall back to Python2
                    os.write(temptxt_fd, txt)
                os.close(temptxt_fd)
            txt = '@' + temptxt
        else:
            # use a file instead of a text.
            txt = "@%" + filename

        if size is not None:
            size = ('' if size[0] is None else str(size[0]),
                    '' if size[1] is None else str(size[1]))

        if shadow is not None:
            shadow = (90 if shadow[0] is None else str(shadow[0]),
                       1 if shadow[1] is None else str(shadow[1]),
                       2 if shadow[2] is None else str(shadow[2]),
                       2 if shadow[3] is None else str(shadow[3]))

        cmd = ( [get_setting("IMAGEMAGICK_BINARY"),
               "-background", bg_color,
               "-fill", color,
               "-font", font])

        if fontsize is not None:
            cmd += ["-pointsize", "%d" % fontsize]
        if kerning is not None:
            cmd += ["-kerning", "%0.1f" % kerning]
        if stroke_color is not None:
            cmd += ["-stroke", stroke_color, "-strokewidth",
                    "%.01f" % stroke_width]
        if size is not None:
            cmd += ["-size", "%sx%s" % (size[0], size[1])]
        if align is not None:
            cmd += ["-gravity", align]
        if interline is not None:
            cmd += ["-interline-spacing", "%d" % interline]

        if tempfilename is None:
            tempfile_fd, tempfilename = tempfile.mkstemp(suffix='.png')
            os.close(tempfile_fd)

        if shadow is not None:
            shadow_cmd = ["(", "+clone", "-shadow", "%sx%s+%s+%s" % shadow, ")", "-compose",  "DstOver", "-flatten"]

        cmd += ["%s:%s" % (method, txt)]
        cmd += shadow_cmd
        cmd += ["-type", "truecolormatte", "PNG32:%s" % tempfilename]

        if print_cmd:
            print( " ".join(cmd) )

        try:
            subprocess_call(cmd, verbose=True )
        except (IOError,OSError) as err:
            error = ("MoviePy Error: creation of %s failed because "
              "of the following error:\n\n%s.\n\n."%(filename, str(err))
               + ("This error can be due to the fact that "
                    "ImageMagick is not installed on your computer, or "
                    "(for Windows users) that you didn't specify the "
                    "path to the ImageMagick binary in file conf.py, or."
                    "that the path you specified is incorrect" ))
            raise IOError(error)

        ImageClip.__init__(self, tempfilename, transparent=transparent)
        self.txt = txt
        self.color = color
        self.stroke_color = stroke_color

        if remove_temp:
            if os.path.exists(tempfilename):
                os.remove(tempfilename)
            if os.path.exists(temptxt):
                os.remove(temptxt)


#### To strip SRT formatting tags:
def clean_line(string):
    pattern = r'[<\{].+?[>\}]'

    return re.sub(pattern, '', string)

def sub_generator(txt, **kwargs):
    kwargs.setdefault('method', 'caption')
    kwargs.setdefault('align', 'south')
    kwargs.setdefault('fontsize', 38)
    kwargs.setdefault('color', 'white')
    kwargs.setdefault('stroke_color', 'black')
    kwargs.setdefault('stroke_width', 2)
    kwargs.setdefault('size', (1280,695))
    kwargs.setdefault('font', font_path)
    kwargs.setdefault('shadow', (90, 1, 2, 2))
    kwargs.setdefault('print_cmd', debug) # for debugging....

    txt = clean_line(txt)
    return ShadowedTextClip(txt, **kwargs)

def get_mid_frame(clip):
    return clip.get_frame(clip.duration * .5)

def write_mid_frame(clip, outpath):
    imwrite(outpath, get_mid_frame(clip))
    return outpath

def compose_subs(vid_file, sub_file):
    vidclip = VideoFileClip(vid_file)
    txtclip = SubtitlesClip(sub_file, sub_generator)
    return CompositeVideoClip([vidclip, txtclip])

def test_run():
    ### Get a shot from the "cheerio/chesto" scene
    inputpath='/home/boodoo/network/WORKGROUP/RT-N65U/Media/Videos/Television/Katanagatari/Season 01/'
    label='Katanagatari S01EP08'
    vid_file=os.path.join(inputpath, "{}.mkv".format(label))
    sub_file=os.path.join(inputpath, "{}.srt".format(label))
    cstart, cend = (434, 438)

    comp = compose_subs(vid_file, sub_file).subclip(cstart, cend)
    write_mid_frame(comp, '/home/boodoo/src/GitHub/grepcap/output.png')

