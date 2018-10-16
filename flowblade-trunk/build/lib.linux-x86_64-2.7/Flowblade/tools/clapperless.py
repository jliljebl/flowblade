#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# clapperless -- automatic find sync offsets for multi source recordings
# Copyright (c) 2013, Martin Schitter <ms@mur.at>
#
# this code is based on an implementation written for PiTiVi 
# by Benjamin M. Schwartz <bens@alum.mit.edu>
# http://git.pitivi.org/?p=pitivi.git;a=blob;f=pitivi/autoaligner.py
#
# with some minor modifications for use in Flowblade by janne Liljeblad in 2017
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging, time, struct, subprocess, sys, os, array, argparse
import tempfile, hashlib, re
import numpy

import utils

OFFSETS_DATA_FILE = "audio_offsets_data"
OFFSETS_DATA_FILE_ID_DEFAULT = "idstr_default"

__version__ = "0.99.8"

"""
Algorithms for aligning (i.e. registering, synchronizing) time series
"""

## BLOCKRATE set by the comand line option --rate
"""
@ivar BLOCKRATE: The number of amplitude blocks per second.

The AutoAligner works by computing the "amplitude envelope" of each
audio stream. We define an amplitude envelope as the absolute value
of the audio samples, downsampled to a low samplerate. This
samplerate, in Hz, is given by BLOCKRATE. (It is given this name
because the downsampling filter is implemented by very simple
averaging over blocks, i.e. a box filter.) 25 Hz appears to be a
good choice because it evenly divides all common audio samplerates
(e.g. 11025 and 8000). Lower blockrate requires less CPU time but
produces less accurate alignment. Higher blockrate is the reverse
(and also cannot evenly divide all samplerates).

"""

def nextpow2(x):
    a = 1
    while a < x:
        a *= 2
    return a


def submax(left, middle, right):
    """
    Find the maximum of a quadratic function from three samples.

    Given samples from a quadratic P(x) at x=-1, 0, and 1, find the x
    that extremizes P.  This is useful for determining the subsample
    position of the extremum given three samples around the observed
    extreme.

    @param left: value at x=-1
    @type left: L{float}
    @param middle: value at x=0
    @type middle: L{float}
    @param right: value at x=1
    @type right: L{float}
    @returns: value of x that extremizes the interpolating quadratic
    @rtype: L{float}

    """
    L = middle - left   # L and R are both positive if middle is the
    R = middle - right  # observed max of the integer samples
    return 0.5 * (R - L) / (R + L)
    # Derivation: Consider a quadratic q(x) := P(0) - P(x).  Then q(x) has
    # two roots, one at 0 and one at z, and the extreme is at (0+z)/2
    # (i.e. at z/2)
    # q(x) = bx*(x-z) # a may be positive or negative
    # q(1) = b*(1 - z) = R
    # q(-1) = b*(1 + z) = L
    # (1+z)/(1-z) = L/R  (from here it's just algebra to find a)
    # z + 1 = R/L - (R/L)*z
    # z*(1+R/L) = R/L - 1
    # z = (R/L - 1)/(R/L + 1) = (R-L)/(R+L)


def rigidalign(reference, targets):
    """
    Estimate the relative shift between reference and targets.

    The algorithm works by subtracting the mean, and then locating
    the maximum of the cross-correlation.  For inputs of length M{N},
    the running time is M{O(C{len(targets)}*N*log(N))}.

    @param reference: the waveform to regard as fixed
    @type reference: Sequence(Number)
    @param targets: the waveforms that should be aligned to reference
    @type targets: Sequence(Sequence(Number))
    @returns: The shift necessary to bring each target into alignment
        with the reference.  The returned shift may not be an integer,
        indicating that the best alignment would be achieved by a
        non-integer shift and appropriate interpolation.
    @rtype: Sequence(Number)

    """
    # L is the maximum size of a cross-correlation between the
    # reference and any of the targets.
    L = len(reference) + max(len(t) for t in targets) - 1
    # We round up L to the next power of 2 for speed in the FFT.
    L = nextpow2(L)
    reference = reference - numpy.mean(reference)
    fref = numpy.fft.rfft(reference, L).conj()
    shifts = []
    for t in targets:
        t = t - numpy.mean(t)
        # Compute cross-correlation
        xcorr = numpy.fft.irfft(fref * numpy.fft.rfft(t, L))
        # shift maximizes dotproduct(t[shift:],reference)
        # int() to convert numpy.int32 to python int
        shift = int(numpy.argmax(xcorr))
        subsample_shift = submax(xcorr[(shift - 1) % L],
                                 xcorr[shift],
                                 xcorr[(shift + 1) % L])
        shift = shift + subsample_shift
        # shift is now a float indicating the interpolated maximum
        if shift >= len(t):  # Negative shifts appear large and positive
            shift -= L       # This corrects them to be negative
        shifts.append(-shift)
        # Sign reversed to move the target instead of the reference
    return shifts

class Envelope:
    
    def __init__(self, filename, args):
        
        "read and generate envelope for filename" 
        
        self.args = args
        self.envelope = None

        # handle time slice
        parts = re.findall(r'(^[^[]+|\[.*?\])', filename)
        if len(parts) == 2:
            ss = parts[-1][1:-1]
            duration = 0
        elif len(parts) > 2:
            ss = parts[-2][1:-1]
            duration = parts[-1][1:-1]
        else:
            ss = 0
            duration = 0

        self.filename = parts[0]
        
        # use filename with optionale time slice info for caching
        if args.use_cache:
            self.read_cache(filename)
        if self.envelope:
            return

        logging.info("read file: %s" % filename)

        ffmpeg_call = ["ffmpeg"]
        
        if ss:
            ffmpeg_call += ["-ss", ss]
        if duration:
            ffmpeg_call += ["-t", duration]
            
        ffmpeg_call += ["-i", self.filename,
                        "-vn",      # Drop any video streams if there are any
                        "-ac", "1", # mix down to mono
                        "-f:a", "wav",
                        "-sample_fmt", "s16",
                        "-loglevel", "error",
                        "-" ]

        try:
            logging.debug('ffmpeg call: "%s"' % ffmpeg_call)
            sp = subprocess.Popen(ffmpeg_call,
                                  bufsize=-1,
                                  stdout=subprocess.PIPE,
                                  # stderr=open(os.devnull)
                                  )                
        except:
            logging.error("could not start 'ffmpeg' subprocess") 
            sys.exit(2)
            
        data = sp.stdout.read(12)
        if len(data) < 12:
            logging.error("error reading data from FFmpeg")
            sys.exit(1)
        riff_h = struct.unpack('4si4s', data)
        if riff_h[0] != b"RIFF" or riff_h[2] != b"WAVE":
            logging.error("data not in WAV format (%s)" % repr(riff_h))
            sys.exit(1)
        data = sp.stdout.read(24)
        fmt_h = struct.unpack('4sihhiihh', data)
        fmt_size = fmt_h[1]
        logging.debug("fmt_size: %d" % fmt_size)
        logging.debug("format: %02x" % fmt_h[2])
        logging.debug("channels: %d" % fmt_h[3])
        samplerate = fmt_h[4]
        logging.info("samplerate: %d" % samplerate)
        framesize = fmt_h[6]
        logging.debug("framesize: %d" % framesize)
        logging.debug("samplesize: %d" % fmt_h[7])

        # fix fmt_section allignment
        if fmt_size > 16:
            logging.debug("fix allignment for fmt_size: %d" % fmt_size)
            data = sp.stdout.read(fmt_size - 16)

        while True:
            data = sp.stdout.read(8)
            data_h = struct.unpack('4si', data)
            if data_h[0] == b"data":
                logging.debug("data size: %d" % data_h[1])
                break
            elif data_h[0].lower() in [b"list"]:
                logging.debug("found segment: %s of size %d" %
                              (data_h[0], data_h[1]))
                sp.stdout.read(data_h[1])
            else:
                logging.error("segment unknown (%s)" % repr(data_h))
                sys.exit(1)

        blocksize=int((samplerate/args.rate))

        self.envelope = array.array('f')
        sec = 0
        fframes = args.rate
        while fframes == args.rate:
            sz = blocksize * framesize * fframes # = 1sec
            data = sp.stdout.read(sz)
            if len(data) < sz:
                fframes = int(len(data) / (blocksize * framesize))
                data = data[:(fframes * blocksize * framesize)]
            sec +=1
            sys.stderr.write(time.strftime('\r%H:%M:%S', time.gmtime(sec)))
            a = array.array('h', data)
            a_abs =  numpy.abs(a)
            a_abs.shape = (fframes, blocksize)
            a_mean = numpy.mean(a_abs, 1)
            self.envelope.extend(a_mean)
        sys.stderr.write('\n')

        fframes = len(self.envelope)
        duration_hms =  time.strftime('%H:%M:%S',
                                      time.gmtime(fframes/args.rate))
        duration_f = fframes % args.rate
        logging.debug("final duration: %s:%02d" % (duration_hms, duration_f))
            
        if args.use_cache:
            self.write_cache()
            
    def read_cache(self, name):
        hash = "%s-%s" % (os.path.basename(sys.argv[0]),
                          hashlib.md5(name.encode('utf-8')).hexdigest())
        self.cachename = os.path.join(self.args.cache_dir[0], hash)
        if os.access(self.cachename, os.R_OK):
            #size = os.stat(self.cachename)[stat.ST_SIZE] / 4
            logging.debug("use cache file: %s" % self.cachename)
            f = open(self.cachename, 'rb')
            size = struct.unpack('L', f.read(struct.calcsize('L')))[0]
            self.envelope = array.array('f')
            self.envelope.fromfile(f, size)
            #logging.debug("cache of size %d ends with: %s" %
            #              (size,  self.envelope[-10:]))
        else:
            logging.debug("no envelope cache found")
            self.envelope = None

    def write_cache(self):
        # cachename is still calculated by search... 
        logging.debug("write to cachefile: %s" % self.cachename)
        if os.path.isdir(self.args.cache_dir[0]):
            f = open(self.cachename, 'wb')
            f.write(struct.pack('L', len(self.envelope)))
            self.envelope.tofile(f)
            #logging.debug("write cache of size %d ends with: %s" %
            #              (len(self.envelope),  self.envelope[-10:]))
            f.close()
        else:
            logging.error("cache_dir ist no directory: %s" %
                          self.args.cache_dir[0])

epilog="""
the first FILE in list is taken as main reference.
the FILE input accepts the ffmpeg catenate syntax
"concat:input1.mpg|input2.mpg|input3.mpg" and time silices of the form:
FILE[start] and FILE[start][length]. start and length can be given as
hh:mm:ss or amount in seconds.
"""

def cl_parser():
    parser = argparse.ArgumentParser(
        description="automaticly find sync offsets",
        epilog=epilog
        )
    parser.add_argument('files', nargs='+', help="FILE FILE [FILES]")
    parser.add_argument('-r', '--rate', default=25, type=int,
        help="should be equal to frames per second [default: 25]")
    parser.add_argument('--idstr',  default="idstr_default", type=str,
        help="id for file used to cimmunicate result [default: idstr_default]")
    parser.add_argument('-c', '--use-cache', action='store_true')
    parser.add_argument('--cache-dir', nargs=1,default=[tempfile.gettempdir()],
                        help="default: %s" % tempfile.gettempdir())
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-V','--version',version=__version__, action='version') 
    args = parser.parse_args()

    return args

def process_files(args):
    envelopes = [Envelope(n, args) for n in args.files]
    reference = envelopes[0].envelope

    envelopes_envelope = list(map(lambda x: x.envelope, envelopes))
    logging.info("calculate offsets...")
    offsets = rigidalign(reference, envelopes_envelope)
    logging.debug("got offsets: %s" % offsets) 

    for n in range(len(offsets)):
        envelopes[n].offset = offsets[n]
      
    offsets_output = []
    for e in envelopes[1:]:
        offset = e.offset
        offsets_output.append((e.filename, offset))
    
    return offsets_output

def main():
    args = cl_parser()
    print args.idstr
    
    offsets_output = process_files(args)

    # Write out offsets data
    out_str = ""
    for file_offset in offsets_output:
        f, offset = file_offset
        out_str = out_str + f + " " + str(offset) + "\n"
    
    output_file = utils.get_hidden_user_dir_path() + OFFSETS_DATA_FILE + "_"+ args.idstr
    f = open(output_file, 'w')
    f.write(out_str)
    f.close()
        
if __name__ == '__main__':
    main()



    
