#!/usr/bin/env python2

import os
import sys
import glob
import re
from videogrep import *

from imageio import imwrite
from moviepy.video.VideoClip import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

verbose=False
font_name='Open-Sans-Semibold'

#################################################################
# ____  ____  ____  _  _   ___     _     _  _  ____  __  __
#(    \(  __)(  _ \/ )( \ / __)   ( )   / )( \(_  _)(  )(  )
# ) D ( ) _)  ) _ () \/ (( (_ \  (_ _)  ) \/ (  )(   )( / (_/\
#(____/(____)(____/\____/ \___/   (_)   \____/ (__) (__)\____/
#
#################################################################

def debug(string):
    if verbose:
        print("[.] {}".format(string))


def log(string):
    print "[+] {}".format(string)


def error(string):
    print "[!] {}".format(string)


def change_extension(inputfile, new_ext='srt'):
    dirname, basename = os.path.split(inputfile)
    label, ext = os.path.splitext(basename)
    new_base = '.'.join([label, new_ext])

    return os.path.join(dirname, new_base)

def clean_line(string):
    pattern = r'[<\{].+?[>\}]'

    return re.sub(pattern, '', string)

def aa_scale(src, factor):
    try:
        return tuple([x*factor for x in src])
    except TypeError:
        return src*factor

#################################################################
#  __   _  _  ____  ____  ____  __  ____  ____  ____     _
# /  \ / )( \(  __)(  _ \(  _ \(  )(    \(  __)/ ___)   ( )
#(  O )\ \/ / ) _)  )   / )   / )(  ) D ( ) _) \___ \  (_ _)
# \__/  \__/ (____)(__\_)(__\_)(__)(____/(____)(____/   (_)
# ____  __  ___   ___  _  _  ____   __    ___  __ _  ____
#(  _ \(  )/ __) / __)( \/ )(  _ \ / _\  / __)(  / )/ ___)
# ) __/ )(( (_ \( (_ \ )  /  ) _ (/    \( (__  )  ( \___ \
#(__)  (__)\___/ \___/(__/  (____/\_/\_/ \___)(__\_)(____/
#
#################################################################

### our PrettyTextClip is like a TextClip but supports drop shadow and antialiased rendering
### TODO: THERE'S GOT TO BE A BETTER WAY (clean up for a PR against moviepy? some kind of decorator?)
class PrettyTextClip(TextClip):
    def __init__(self, txt=None, filename=None, size=None, color='black',
                 bg_color='transparent', fontsize=None, font='Courier',
                 stroke_color=None, stroke_width=1, method='label',
                 kerning=None, align='center', interline=None,
                 tempfilename=None, temptxt=None,
                 transparent=True, remove_temp=True,
                 shadow=None, antialias=4,
                 print_cmd=False):

        import tempfile
        import subprocess as sp

        from moviepy.tools import subprocess_call
        from moviepy.config import get_setting

        # from moviepy.video.VideoClip import *

        aa_factor= 1 if not antialias else antialias

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
            size = ('' if size[0] is None else size[0],
                    '' if size[1] is None else size[1])

        if shadow is not None:
            shadow = (80 if shadow[0] is None else shadow[0],
                       1 if shadow[1] is None else shadow[1],
                       2 if shadow[2] is None else shadow[2],
                       2 if shadow[3] is None else shadow[3])

        cmd = ( [get_setting("IMAGEMAGICK_BINARY"),
               "-density", str(aa_scale(72, aa_factor)),
               "-background", bg_color,
               "-fill", color,
               "-font", font])

        if fontsize is not None:
            cmd += ["-pointsize", "%d" % fontsize]
        if kerning is not None:
            cmd += ["-kerning", "%0.1f" % aa_scale(kerning, aa_factor)]
        if stroke_color is not None:
            cmd += ["-stroke", stroke_color, "-strokewidth",
                    "%.01f" % aa_scale(stroke_width, aa_factor)]
        if size is not None:
            cmd += ["-size", "%sx%s" % aa_scale(size, aa_factor)]
        if align is not None:
            cmd += ["-gravity", align]
        if interline is not None:
            cmd += ["-interline-spacing", "%d" % interline]

        if tempfilename is None:
            tempfile_fd, tempfilename = tempfile.mkstemp(suffix='.png')
            os.close(tempfile_fd)

        if shadow is not None:
            shadow_cmd = ( ["(", "+clone",
                          "-shadow", "%sx%s+%s+%s" % (tuple([shadow[0]]) + aa_scale(shadow[1:], aa_factor)),
                          ")",
                          "-compose", "DstOver",
                          "-flatten"])

        cmd += ["%s:%s" % (method, txt)]
        cmd += shadow_cmd
        cmd += ["-resample", "72"]
        cmd += ["-type", "truecolormatte", "PNG32:%s" % tempfilename]

        if print_cmd:
            print( " ".join(cmd) )

        try:
            subprocess_call(cmd, verbose=verbose)
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

### THIS OVERRIDES THE BUILT-IN FROM VIDEOGREP ###
def get_subtitle_files(inputpaths):
    """Return a list of subtitle files."""
    srts = []
    for p in inputpaths:
        debug("GET_SUBTITLE_FILES working on: {}".format(p))
        srts.extend(srts_from_path(p))

    if len(srts) == 0:
        print "[!] No subtitle files were found."
        return False

    return srts


#################################################################
#  ___  __  ____  ____
# / __)/  \(  _ \(  __)
#( (__(  O ))   / ) _)
# \___)\__/(__\_)(____)
# _  _  ____  ____  _  _   __  ____  ____
#( \/ )(  __)(_  _)/ )( \ /  \(    \/ ___)
#/ \/ \ ) _)   )(  ) __ ((  O )) D (\___ \
#\_)(_/(____) (__) \_)(_/ \__/(____/(____/
#
#################################################################

def sub_generator(txt, **kwargs):
    kwargs.setdefault('method', 'caption')
    kwargs.setdefault('align', 'south')
    kwargs.setdefault('fontsize', 38)
    kwargs.setdefault('color', 'white')
    kwargs.setdefault('stroke_color', 'black')
    kwargs.setdefault('stroke_width', 2)
    kwargs.setdefault('size', (1280,695))
    kwargs.setdefault('font', font_name)
    kwargs.setdefault('shadow', (90, 1, 2, 2)) # Need option to disable this for fast render
    kwargs.setdefault('antialias', 2) # Can be set to False, or to something like 4

    txt = clean_line(txt)
    return PrettyTextClip(txt, **kwargs)

def get_mid_frame(clip):
    return clip.get_frame(clip.duration * .5)

def write_mid_frame(clip, outpath):
    imwrite(outpath, get_mid_frame(clip))
    return outpath

def compose_subs(vid_file, sub_file):
    vidclip = VideoFileClip(vid_file)
    txtclip = SubtitlesClip(sub_file, sub_generator)
    return CompositeVideoClip([vidclip, txtclip])

def videos_from_path(inputpath):
    """Take directory or file path and return list of valid video files"""
    """TODO: Directory recursion! (?)"""
    inputpath = os.path.expanduser(inputpath)
    isdir = os.path.isdir(inputpath)
    video_files = []
    debug("VIDEOS_FROM_PATH parsed out: {}, (is directory? {})".format(inputpath, isdir))
    if isdir:
        """Check for valid formats within directory"""
        """TODO: Be case-insensitive!"""
        for root, dirs, files in os.walk(inputpath):
            print("Checking {}".format(root))
            vids = glob.glob(os.path.join(root, '*.mkv'))
            if len(vids) > 0:
                debug("Found {} vids: {}".format(len(vids), [os.path.basename(vid) for vid in vids]))
            video_files.extend(vids)
            ## TODO: Restore suport for muliple extensions?
            # for ext in usable_extensions:
            #     vids = glob.glob(os.path.join(root, '*.{}'.format(ext)))
            #     if len(vids) > 0:
            #         debug("Found {} vids: {}".format(len(vids), [os.path.basename(vid) for vid in vids]))
            #     video_files.extend(vids)
    else:
        """Check that file requested is a usable format"""
        ext = os.path.splitext(inputpath)[-1][1:].lower()
        debug("CHECKING VIDEO FILE WITH EXTENSION: {}".format(ext))
        if ext in usable_extensions:
            debug("THAT EXTENSION IS GOOD")
            video_files.append(inputpath)
            debug("VIDEO_FILES is now: {}".format(video_files))

    return video_files


def srts_from_path(inputpath):
    """Find SRTs for a video or for a directory"""
    return list([change_extension(vid, 'srt') for vid in videos_from_path(inputpath) if os.path.isfile(vid)])

def create_screencaps(composition, out_path=None, raw=False):
    out_path = out_path or os.path.join(os.environ['HOME'], 'grepcap')
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    all_videofiles = set([c['file'] for c in composition])
    # all_subtitlefiles = set([change_extension(c['file']) for c in composition])

    if raw:
        # No need to make subtitle clips for --raw output
        debug("GENERATING 'outputclips' for raw output (no subs)....")
        outputclips = dict([(f, VideoFileClip(f)) for f in all_videofiles])
    else:
        # Generate CompositeVideoClip per video file to include subtitles:
        debug("GENERATING 'outputclips' dict for screen cap generation..........")
        outputclips = dict([ (f, compose_subs(f, change_extension(f)) ) for f in all_videofiles ])
    debug("GENERATING 'mid_frames' list of frame image data from outputclips.......")
    mid_frames = [outputclips[c['file']].get_frame( (c['start'] + c['end']) / 2) for c in composition]
    for i, frame in enumerate(mid_frames):
        debug("Writing {0} of {1:03d}...".format(i, len(mid_frames)) )
        imwrite(os.path.join(out_path, "cap_{0:03d}.png".format(i) ), frame)
    #.subclip(c['start'], c['end']) for c in composition]


### LIFTED WHOLESALE FROM videogrep
## TODO: Tailor to actual usecase
def grepcap(inputfile, outputfile, search, searchtype, maxclips=0, padding=0, test=False, randomize=False, sync=0, use_transcript=False, raw=False):
    """Search through and find all instances of the search term in an srt or transcript,
    output screenshots for each instance found.
    """

    padding = padding / 1000.0
    sync = sync / 1000.0
    composition = []
    foundSearchTerm = False

    if use_transcript:
        composition = compose_from_transcript(inputfile, search, searchtype)
    else:
        srts = get_subtitle_files(inputfile)
        composition = compose_from_srts(srts, search, searchtype, padding=padding, sync=sync)
        debug( "WITHIN GREPCAP(), composition: {}".format(composition) )


    # If the search term was not found in any subtitle file...
    if len(composition) == 0:
        print "[!] Search term '" + search + "'" + " was not found in any file."
        exit(1)

    else:
        print "[+] Search term '" + search + "'" + " was found in " + str(len(composition)) + " places."

        # apply padding and sync
        for c in composition:
            c['start'] = c['start'] + sync - padding
            c['end'] = c['end'] + sync + padding

        if randomize is True:
            random.shuffle(composition)

        if maxclips > 0:
            composition = composition[:maxclips]

        if test:
            demo_supercut(composition, padding)
        else:
            create_screencaps(composition, outputfile, raw)


#################################################################
# _  _   __   __  __ _
#( \/ ) / _\ (  )(  ( \
#/ \/ \/    \ )( /    /
#\_)(_/\_/\_/(__)\_)__)
# ____  __ _  ____  ____  _  _
#(  __)(  ( \(_  _)(  _ \( \/ )
# ) _) /    /  )(   )   / )  /
#(____)\_)__) (__) (__\_)(__/
#
#################################################################
### This is pretty much taken wholesale from videogrep
## TODO: Tailor to my actual usecases
def main():
    import argparse
    global verbose

    parser = argparse.ArgumentParser(description='Generate a gallery of screencaps of search term being used in subtitle tracks.')
    parser.add_argument('--input', '-i', dest='inputfile', nargs='*', required=True, help='video or subtitle file, or folder')
    parser.add_argument('--search', '-s', dest='search', help='search term')
    parser.add_argument('--search-type', '-st', dest='searchtype', default='re', choices=['re', 'pos', 'hyper', 'fragment', 'franken', 'word'], help='type of search')
    # parser.add_argument('--use-transcript', '-t', action='store_true', dest='use_transcript', help='Use a transcript generated by pocketsphinx instead of srt files')
    parser.add_argument('--max-clips', '-m', dest='maxclips', type=int, default=0, help='maximum number of clips to use for the supercut')
    parser.add_argument('--output', '-o', dest='outputfile', default=os.path.join(os.environ['HOME'], 'output'), help='path for output files (defaults to ~/grepcap)')
    parser.add_argument('--demo', '-d', dest='test', action='store_true', help='show results without making the supercut')
    parser.add_argument('--randomize', '-r', action='store_true', help='randomize the clips')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose/debug output to stdout')
    parser.add_argument('--padding', '-p', dest='padding', default=0, type=int, help='padding in milliseconds to add to the start and end of each clip')
    parser.add_argument('--no-subs', '--raw', '-ns', action='store_true', dest='raw', help='create output without burning subtitles')
    parser.add_argument('--resyncsubs', '-rs', dest='sync', default=0, type=int, help='Subtitle re-synch delay +/- in milliseconds')
    parser.add_argument('--transcribe', '-tr', dest='transcribe', action='store_true', help='Transcribe the video using audiogrep. Requires pocketsphinx')

    args = parser.parse_args()
    verbose = args.verbose

    if not args.transcribe:
        if args.search is None:
             parser.error('argument --search/-s is required')

    if args.transcribe:
        create_timestamps(args.inputfile)
    else:
        ## Create a dict of the args, remove 'transcribe'/'verbose' flags
        dargs = vars(args)
        dargs.pop('transcribe', None)
        dargs.pop('verbose', None)

        debug("MAIN() working with: {}".format(args.inputfile))
        # print(get_subtitle_files(args.inputfile))
        grepcap(**dargs)
        # videogrep(args.inputfile, args.outputfile, args.search, args.searchtype, args.maxclips, args.padding, args.demo, args.randomize, args.sync, args.use_transcript)


if __name__ == '__main__':
    main()
