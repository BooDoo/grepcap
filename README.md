## THIS IS A WORK IN PROGRESS  

Assume MKV video files with discrete SRT files in same folder:  
```
pip install videgrep  
python2 grepcap.py -i $MEDIA_PATH -s $SEARCH_TERM -o $DESTINATION_FOLDER  
```

You'll want to dry-run (`-d`) first since actual processing takes __forever__  


On my little ARM Chromebook:
```
$ time -i $MEDIA_PATH/Bakemonogatari -s '[Dd]emon'
...
[+] Search term '[Dd]emon' was found in 22 places. (across 12 files)
...
548.64s user || 81.00s system || 129% cpu || 8:05.44 total
```
This is a low-powered machine reading from a network share, but just FYI.  


#### Easy performance gain hacks:  
  - remove 'shadow'/'layer' calls from ImageMagick compositing  
  - assume or force resolution for compositing (vidclip.size in `make_sub_opts()` calls ffmpeg (twice?))  
  - run with `--raw` flag for no-subtitles output.  


#### Not as easy perforamnce gains:  
  - multi-threading?  
  - compositing clips calls ImageMagick 2x per screencap; could optimize?  


#### TODO:  
  - Support forcing consistent output resolution regardless of input video  
  - Clean/modularize code.  
  - Remove videogrep logic/settings that make less sense in this context.  
  - Different verbosity levels (even without `-v` it's pretty noisy.)  


#### Awful feature creep:  
  - script to crawl folders and extract/convert subtitles to SRT  
  - index storing subtitles & video metadata by filehash (SQLite?)  


Suggestions/Pull Requests welcome.
