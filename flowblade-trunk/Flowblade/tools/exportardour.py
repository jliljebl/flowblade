#!/usr/bin/env python3

"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2019 Janne Liljeblad and contributors.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
exportardour.py
by Nathan Rosenquist

Exports a Flowblade MLT XML file into a new Ardour project.

Extracts all of the audio assets it can find, transcodes them into WAV
files, and creates the Ardour project structure and metadata in a new
Ardour project.

https://github.com/jliljebl/flowblade/issues/666

"""

import atomicfile
import editorstate

import os
import subprocess
import sys
import xml.etree.ElementTree

##############################################################################
# CONSTANTS                                                                  #
##############################################################################

# path to ffmpeg program
CMD_FFMPEG = 'ffmpeg'

# Flowblade does not have a project-level audio sample rate
# 48kHz is extremely common on film and TV projects around the world
DEFAULT_SAMPLE_RATE = 48000

# the number of beats per minute
# this is meaningless for an NLE audio export, but we have to use it to
# calculate some additional region position information in the Ardour project
BPM = 120

##############################################################################
# MODEL                                                                      #
##############################################################################

class Profile:
    """
    Project profile.

    Calculates the project-level frame rate from a frame rate numerator and
    denominator.

    Also keeps track of how many video and audio tracks were used on the
    Flowblade sequence timeline, so we can decode the playlist numbering
    in the XML file and map it back to the original track names
    (e.g. MLT XML "playlist5" becomes "V1" in the Ardour export)

    """

    def __init__(self,
                 frame_rate_num, frame_rate_den,
                 video_tracks, audio_tracks):

        # frame rate numerator and denominator
        # (to support fractional frame rates)
        # with sensible frame rates like PAL, you might get 25000/1000 == 25,
        # but with NTSC you could end up with 24000/1001 == 23.976
        self.frame_rate_num = int(frame_rate_num)
        self.frame_rate_den = int(frame_rate_den)
        self.fps = self.frame_rate_num / self.frame_rate_den

        # video/audio track counts
        self.video_tracks = int(video_tracks)
        self.audio_tracks = int(audio_tracks)

        # create a map of MLT playlist ID to flowblade track name
        # e.g. "playlist5" -> "V1"
        self.mlt_playlist_to_flowblade_track_map = {}

        # the first MLT playlist that could contain a video or audio track is 1
        mlt_playlist_num = 1

        # audio tracks
        # (added to sequentially named MLT playlist entries first, in reverse order,
        #  e.g. A4 = playlist1, A3 = playlist2, etc.)
        if self.audio_tracks > 0:
            for flowblade_track_num in reversed(range(1, (self.audio_tracks + 1))):
                mlt_playlist = "playlist" + str(mlt_playlist_num)
                flowblade_track = "A" + str(flowblade_track_num)

                self.mlt_playlist_to_flowblade_track_map[mlt_playlist] = flowblade_track

                mlt_playlist_num += 1

        # video tracks
        # (added to sequentially named MLT playlist entries after all the audio tracks
        #  are done, in forward order (e.g. V1 = playlist5, V2 = playlist6, etc.)
        for flowblade_track_num in range(1, (self.video_tracks + 1)):
            mlt_playlist = "playlist" + str(mlt_playlist_num)
            flowblade_track = "V" + str(flowblade_track_num)

            self.mlt_playlist_to_flowblade_track_map[mlt_playlist] = flowblade_track

            mlt_playlist_num += 1

    def get_flowblade_track_by_mlt_playlist_id(self, mlt_playlist_id):
        """
        Attempt to get the original Flowblade track name (e.g. V1) by the MLT XML
        playlist ID (e.g. playlist5).

        If that doesn't work, we'll just return "Audio", which is a sensible base
        name for an Ardour track.

        """

        if mlt_playlist_id in self.mlt_playlist_to_flowblade_track_map:
            return self.mlt_playlist_to_flowblade_track_map[mlt_playlist_id]

        return "Audio"

    def __str__(self):
        return "profile: " + str(round(self.fps, 3)) + " fps, V" + \
            str(self.video_tracks) + "/A" + str(self.audio_tracks)


class Media:
    """
    A single media asset (e.g. a movie or sound file).

    In and out points represent the beginning and end of the file.
    For example, if a Quicktime movie file is one second long at
    24 fps, then in will be 0 and out will be 23.

    """

    def __init__(self, in_frame, out_frame):
        self.in_frame = int(in_frame)
        self.out_frame = int(out_frame)

        # full path to input media (e.g. Flowblade Quicktime, WAV, etc)
        self.source_media = None

        # base name to use for transcoded files/regions/etc in Ardour
        self.transcode_media_basename = None

        # sample rate (e.g. 48000)
        self.sample_rate = None

        # number of channels in the original input media (e.g. 1, 2, etc.)
        self.channels = None

        # a list of Ardour Source IDs associated with this media as an
        # Ardour "Source". One Source ID is set per channel, and they can
        # be retrieved by using ardour_source_ids as a zero-based list
        # (e.g. the Ardour Source ID for channel 1 == ardour_source_ids[0]
        self.ardour_source_ids = []

    def get_source_media_basename(self):
        """
        Get the source media filename, without the path or file extension.

        For example, "/path/to/media/6B-1.MOV" would become "6B-1".

        """

        (head, tail) = os.path.split(self.source_media)
        if '' == tail:
            raise Exception("could not extract source media basename")

        parts = tail.split('.')

        if len(parts) > 1:
            parts = parts[:-1]

        return ".".join(parts)

    def set_ardour_source_ids(self, seq):
        """
        Claim an Ardour "Source" ID for each channel in this media file.

        The IDs are placed in a zero based list.

        The Source ID for channel 1 can be retrieved from
        ardour_source_ids[0], etc.

        """

        for channel in range(0, self.channels):
            self.ardour_source_ids.append(seq.next())

    def __str__(self):
        return "media: " + \
               str(self.in_frame + self.out_frame + 1) + " frames, " + \
               str(self.channels) + " channels, " + \
               str(self.sample_rate) + " Hz, " + "'" + self.source_media + "'"


class Clip:
    """
    Represents the placement of a media file within a playlist.

    In and out points represent the in and out points within the media
    file. For example, if a WAV file is one minute long but only a one
    second clip of the full file is placed into a playlist, and it
    starts at the first second (at 24 fps), then in would be 24, and
    out would be 47.

    """

    def __init__(self, media, timeline_start_frame, in_frame, out_frame):
        self.media = media
        self.timeline_start_frame = int(timeline_start_frame)
        self.in_frame = int(in_frame)
        self.out_frame = int(out_frame)
        self.length = self.out_frame - self.in_frame + 1

    def __str__(self):
        return "clip: " + self.media.source_media + \
               ", timeline start " + str(self.timeline_start_frame) + \
               ", clip in " + str(self.in_frame) + \
               ", clip out " + str(self.out_frame)


class Playlist:
    """
    Represents a channel in Flowblade and in Ardour, containing
    a sequence of clips that appear on that channel in order.

    """

    def __init__(self, id):
        self.id = str(id)
        self.clips = []
        self.ardour_route_id = None
        self.ardour_route_name = None
        self.ardour_playlist_name = None

    def add_clip(self, media, timeline_start_frame, in_frame, out_frame):
        """
        Add a Clip to the Playlist.

        Accepts the Media instance associated with the clip, the
        timeline start frame, and the clip in and out frames.

        """

        clip = Clip(media, timeline_start_frame, in_frame, out_frame)
        self.clips.append(clip)

    def get_length_in_frames(self):
        """
        Get the length of this playlist in frames.

        """

        highest_end_frame = 0

        for clip in self.clips:
            clip_end_frame = clip.timeline_start_frame + clip.length

            if clip_end_frame > highest_end_frame:
                highest_end_frame = clip_end_frame

        return highest_end_frame

    def set_ardour_route_id(self, id):
        """
        Set the Ardour Route ID associated with this Playlist.

        """

        self.ardour_route_id = int(id)

    def set_ardour_route_name(self, name):
        """
        Set the Ardour Route Name associated with this Playlist.

        """

        self.ardour_route_name = name

    def set_ardour_playlist_name(self, name):
        """
        Set the Ardour Playlist Name associated with this Playlist.

        """

        self.ardour_playlist_name = name

    def get_channel_count(self):
        """
        Get the channel count for this playlist, which is defined as the
        maximum number of channels used by any of the underlying media.

        """

        channel_count = 0

        for clip in self.clips:
            clip_channel_count = clip.media.channels
            if clip_channel_count > channel_count:
                channel_count = clip_channel_count

        return channel_count

    def __str__(self):
        return "playlist: " + self.id + ", " + \
               str(len(self.clips)) + " clips"


class Project:
    """
    Top-level container object for all of the other classes associated with
    the project.

    """

    def __init__(self, profile, sample_rate, media_pool, playlists):
        self.profile = profile
        self.sample_rate = int(sample_rate)
        self.media_pool = media_pool
        self.playlists = playlists

        # figure out how many samples per frame, since we'll have to do
        # a lot of calculations that use this later
        self.fps = profile.frame_rate_num / profile.frame_rate_den
        self.samples_per_frame = self.sample_rate / self.fps

        # give every piece of media a globally unique base name, so that
        # when media is transcoded and stuck in one directory, no file
        # naming conflicts will arise
        self._set_unique_transcode_basepaths()

    def frame_to_sample(self, frame):
        """
        Turn the given frame number into the equivalent number of samples,
        taking the project frame rate into account

        """

        return round(frame * self.samples_per_frame)

    def frame_to_beat(self, frame):
        """
        Turn the given frame number into the Ardour beat, taking the project
        frame rate into account.

        """

        seconds = (frame / self.fps)

        beats_per_second = BPM / 60

        return seconds * beats_per_second

    def get_length_in_frames(self):
        """
        Get the length of the project, in frames

        """

        highest_length = 0

        for playlist in self.playlists:
            length = playlist.get_length_in_frames()
            if length > highest_length:
                highest_length = length

        return highest_length

    def get_length_in_samples(self):
        """
        Get the length of the project, in samples

        """

        return self.frame_to_sample(self.get_length_in_frames())

    def _set_unique_transcode_basepaths(self):
        """
        Each Media instance needs to have a globally unique base name,
        because they all end up getting transcoded and stuck in a
        single directory under the Ardour project.

        This method examines all of the Media instances, and assigns
        them unique transcode media basenames. These are mostly based
        on the original filenames, but can be modified with appended
        numbers to make them unique in the case of naming conflicts.

        """

        # keep track of all the transcode base names we've seen so far
        reserved = set()

        # go through everything in the media pool
        for media in self.media_pool:
            # get the source media base name
            source_name = media.get_source_media_basename()

            # if the source media name has already been used (because
            # there are two files from different directories with the
            # same name), then append a number to the source name
            # so that it's globally unique within the media pool
            if source_name in reserved:
                count = 2
                while True:
                    candidate_name = source_name + "-" + str(count)
                    if candidate_name not in reserved:
                        source_name = candidate_name
                        break

            # set the unique base name to use for transcoded media
            media.transcode_media_basename = source_name

            # add the unique name to the set, so that nothing else
            # in the media pool can reuse it and cause a conflict
            reserved.add(source_name)


##############################################################################
# MLT XML                                                                    #
##############################################################################

def create_project_from_mlt_xml(xml_file,
                                project_sample_rate,
                                video_tracks,
                                audio_tracks):
    """
    Parses an MLT XML file, and returns a Project containing
    the project metadata elements we care about.

    """

    if not os.path.isfile(xml_file):
        raise Exception("MLT XML file not found: '" + xml_file + "'")

    if project_sample_rate < 1:
        raise Exception("invalid sample rate")

    # project profile
    profile = None

    # list of all playlists
    playlists = []

    # producer id -> source media path
    producer_to_path = {}

    # source media path -> Media instance
    path_to_media = {}

    tree = xml.etree.ElementTree.parse(xml_file)

    root = tree.getroot()

    for element in root:
        if "profile" == element.tag:
            profile = Profile(element.attrib['frame_rate_num'],
                              element.attrib['frame_rate_den'],
                              video_tracks,
                              audio_tracks)

        if "producer" == element.tag:
            producer_id = element.attrib['id']

            # in and out point for producers are always the first and
            # last frame of the media file
            in_point = int(element.attrib['in'])
            out_point = int(element.attrib['out'])

            source_media = None
            sample_rate = None
            channels = None

            for sub_element in element:
                if "property" == sub_element.tag:
                    name = sub_element.attrib['name']
                    value = sub_element.text

                    if "resource" == name:
                        source_media = value

                    # sample rate and channels can come from individual
                    # channels inside of the clip, but this code assumes there
                    # will only be one logical audio track within the
                    # meta.media.*.* entries. at least we'll raise an
                    # exception if more than one part of the media file has
                    # separate audio channel designations we don't understand
                    if name.endswith(".sample_rate"):
                        if sample_rate:
                            raise Exception(
                                "multiple sample rates in media")

                        sample_rate = int(value)

                    if name.endswith(".channels"):
                        if channels:
                            raise Exception(
                                "can not interpret channels in media")

                        channels = int(value)

            # if we have a complete set of producer/property/resource
            # entries, remember this producer and media file
            if source_media and sample_rate and channels:
                # if the same clip shows up more than once in a flowblade
                # timeline, each instance will get its own separate
                # producer instance referring to the same underlying
                # file. but what we want to do here is de-dupe those
                # entries so that we only have one media instance per
                # source media file.
                if source_media not in path_to_media:
                    media = Media(in_point, out_point)
                    media.source_media = source_media
                    media.sample_rate = sample_rate
                    media.channels = channels

                    # add this unique Media instance to the path to media map
                    path_to_media[source_media] = media

                # add this producer to the producer to path map
                producer_to_path[producer_id] = source_media

        if "playlist" == element.tag:
            playlist_id = element.attrib['id']
            playlist = Playlist(playlist_id)

            # keep track of how many frames we have move forward in this
            # playlist, so that we can assign timeline in points to
            # each clip
            timeline_start_frame = 0

            for sub_element in element:
                length = 0

                # blank frames in playlist
                if "blank" == sub_element.tag:
                    length = int(sub_element.attrib['length'])

                    timeline_start_frame += length

                # clip in playlist
                if "entry" == sub_element.tag:
                    producer_id = sub_element.attrib['producer']

                    # playlist in and out points are the in and out points on
                    # the underlying media file
                    in_point = int(sub_element.attrib['in'])
                    out_point = int(sub_element.attrib['out'])
                    length = out_point - in_point + 1

                    # in the common case, the producer will reference a media
                    # clip that we're going to transcode. but we might also
                    # get a producer entry that doesn't directly reference a
                    # media clip, but has in and out points (like a compound
                    # clip that is actually a reference to an external MLT XML
                    # file). we can't extract the compound clip into the
                    # timeline, but we can at least respect the length of the
                    # clip so that the other elements come through. there is
                    # also a "producer0" clip with zero length and a black
                    # frame, but this is neatly ignored by the length
                    # calculations anyway

                    # if this entry has an actual media file with audio
                    # backing it, then add it to the playlist
                    if producer_id in producer_to_path:
                        path = producer_to_path[producer_id]
                        media = path_to_media[path]

                        playlist.add_clip(media,
                                          timeline_start_frame,
                                          in_point,
                                          out_point)

                    # compound clip, or something else we don't understand
                    elif producer_id.startswith("tractor"):
                        sys.stderr.write("warning: can not transcode media ")
                        sys.stderr.write("for compound clip: '")
                        sys.stderr.write(producer_id)
                        sys.stderr.write("'\n")

                    # extend the timeline start frame counter
                    # regardless of whether we could transcode the underlying
                    # media or not
                    timeline_start_frame += length

            playlists.append(playlist)

    # reverse the playlist order, because the playlists come out of Flowblade
    # in reverse order: A4, A3, A2, A1, V1, V2, V3, V4, V5
    # but in ardour we want them
    # in forward order: V5, V4, V3, V2, V1, A1, A2, A3, A4
    #
    # N.B. reverse() reverses the list IN PLACE
    playlists.reverse()

    # create the media pool as a de-duplicated list of all Media instances
    media_pool = []
    for path in path_to_media:
        media = path_to_media[path]
        media_pool.append(media)

    return Project(profile, project_sample_rate, media_pool, playlists)

def print_project_details(project):
    """
    Prints (some) project details (mainly for debugging)

    """

    print(project.profile)

    for media in project.media_pool:
        print(media)

    for playlist in project.playlists:
        if len(playlist.clips) > 0:
            matches = False

            for media in project.media_pool:
                for clip in playlist.clips:
                    if clip.media == media:
                        matches = True
                        break

            if matches:
                print(playlist)
                for clip in playlist.clips:
                    print("  " + str(clip))

##############################################################################
# ARDOUR                                                                     #
##############################################################################

def _create_ardour_project_dirs(basedir):
    """
    Create the directories for an Ardour project, starting with the
    given base directory.

    The base directory must already exist, but be empty, because GTK only
    enables selecting existing directories.

    """

    # get the directory name without any other path information
    (head, subdir) = os.path.split(basedir)
    if '' == subdir:
        raise Exception("could not extract base directory")

    os.mkdir(os.path.join(basedir, "analysis"))
    os.mkdir(os.path.join(basedir, "dead"))
    os.mkdir(os.path.join(basedir, "export"))
    os.mkdir(os.path.join(basedir, "externals"))
    os.mkdir(os.path.join(basedir, "interchange"))
    os.mkdir(os.path.join(basedir, "interchange", subdir))
    os.mkdir(os.path.join(basedir, "interchange", subdir, "audiofiles"))
    os.mkdir(os.path.join(basedir, "interchange", subdir, "midifiles"))
    os.mkdir(os.path.join(basedir, "peaks"))
    os.mkdir(os.path.join(basedir, "plugins"))

def _get_ardour_audiofiles_dir(basedir):
    """
    Convenience method to get the path to the Ardour audio files directory.

    """

    # get the directory name without any other path information
    (head, subdir) = os.path.split(basedir)
    if '' == subdir:
        raise Exception("could not extract base directory")

    return os.path.join(basedir, "interchange", subdir, "audiofiles")

def _get_audio_channel_name(media, channel, num_channels):
    """
    Add a suffix to each exported mono channel if the input media has
    multiple channels. This is done in a determinstic way, so that
    this method can be called from various parts of the export
    process and get the same results.

    """

    # add a suffix to each exported mono channel
    # if the input media has multiple channels
    if 1 == num_channels:
        suffix = ""
    elif 2 == num_channels:
        if 1 == channel:
            suffix = "%L"
        if 2 == channel:
            suffix = "%R"
    else:
        suffix = "%" + str(channel)

    return media.transcode_media_basename + suffix

def _is_audio_file(path):
    """
    Is the given filename an audio file?

    Returns True if it is an audio file, or False otherwise.

    """

    audio_file_exts = [
        'wav',
        'wave',
        'aif',
        'aiff',
        'mp3',
        'ogg',
        'flac',
    ]

    parts = path.split('.')
    ext = parts[-1]
    if '' == ext:
        raise Exception("could not find file extension for '" + path + "'")

    ext = ext.lower()

    if ext in audio_file_exts:
        return True

    return False

def _transcode_ardour_audio_channel(basedir,
                                    sample_rate,
                                    media,
                                    channel,
                                    num_channels):

    """
    Transcode a single mono channel from the input media file into a wav file.

    """

    audiofiles_dir = _get_ardour_audiofiles_dir(basedir)
    dest_file = _get_audio_channel_name(media, channel, num_channels) + ".wav"
    dest_path = os.path.join(audiofiles_dir, dest_file)

    # N.B. we're using heuristics here, and it isn't perfect
    # ffmpeg map channel format: [file.stream.channel]
    # we're assuming that if we have a video, then it will have sound on
    # ffmpeg stream 1, and if we have an audio file, it will have sound on
    # ffmpeg stream 0. this will basically work for a lot of common formats,
    # but would probably not withstand anything slightly unusual
    audio = _is_audio_file(media.source_media)
    if audio:
        map_channel = "0.0." + str(channel - 1)
    else:
        map_channel = "0.1." + str(channel - 1)

    cmd_stack = [CMD_FFMPEG,
                 "-hide_banner",
                 "-loglevel", "error",
                 "-i", media.source_media,
                 "-vn",
                 "-acodec", "pcm_s24le",
                 "-ar", str(sample_rate),
                 "-map_channel", map_channel, dest_path]

    print(" ".join(cmd_stack))

    result = subprocess.call(cmd_stack)
    if 0 != result:
        raise Exception("error transcoding '" + media.source_media +
                        "' to '" + dest_path + "'")

def _transcode_ardour_media_pool(basedir, project):
    """
    Transcode all of the media pool files from the project, and place the
    results in the Ardour audiofiles directory.

    """

    dest_dir = _get_ardour_audiofiles_dir(basedir)

    for media in project.media_pool:
        for channel in range(1, (media.channels + 1)):
            _transcode_ardour_audio_channel(basedir,
                                            project.sample_rate,
                                            media,
                                            channel,
                                            media.channels)

def create_ardour_project(basedir, project):
    """
    Create an Ardour project, using the given base directory and Project

    """

    # strip trailing slashes from basedir if necessary
    while True:
        if '/' == basedir[-1]:
            basedir = basedir[:-1]
            continue

        break

    # if there isn't anything left after stripping all the slashes,
    # stop here
    if '' == basedir:
        raise Exception("invalid base directory")

    # create the ardour project directory hierarchy
    _create_ardour_project_dirs(basedir)

    # transcode input media files for ardour
    _transcode_ardour_media_pool(basedir, project)

    # create the ardour XML project file
    _create_ardour_project_file(basedir, project)

##############################################################################
# ARDOUR XML                                                                 #
##############################################################################

class Sequence:
    """
    Hands out monotonically increasing sequence values.

    Ardour XML project files assign unique IDs to just about every object of
    any consequence.

    """

    def __init__(self, start):
        self.value = start

    def next(self):
        self.value += 1
        return self.value

    def __str__(self):
        return str(self.value)

def _escape(value):
    """
    Escape value for inclusion as a double quoted XML string

    """

    if value is None:
        return ""

    value = str(value)

    value = value.replace('"', '&quot;')

    return value

def _get_ardour_xml_header():
    return '<?xml version="1.0" encoding="UTF-8"?>\n'

def _get_ardour_session_open(name, project, id_counter):
    s = []

    s.append('<Session version="3002" name="')
    s.append(_escape(name))
    s.append('" sample-rate="')
    s.append(_escape(project.sample_rate))
    s.append('" end-is-free="1" id-counter="')
    s.append(_escape(id_counter))
    s.append('" name-counter="1" event-counter="226" vca-counter="1">\n')

    return ''.join(s)

def _get_ardour_session_close():
    return '</Session>\n'

def _get_ardour_program_version():
    s = []

    s.append('  <ProgramVersion created-with="Flowblade ')
    s.append(_escape(editorstate.appversion))
    s.append('" modified-with="Flowblade ')
    s.append(_escape(editorstate.appversion))
    s.append('"/>\n')

    return ''.join(s)

def _get_ardour_midi_ports():
    return '''  <MIDIPorts>
    <Port name="MIDI Clock in" direction="input"/>
    <Port name="MIDI Clock out" direction="output"/>
    <Port name="MIDI control in" direction="input"/>
    <Port name="MIDI control out" direction="output"/>
    <Port name="MMC in" direction="input"/>
    <Port name="MMC out" direction="output"/>
    <Port name="MTC in" direction="input"/>
    <Port name="MTC out" direction="output"/>
    <Port name="Scene in" direction="input"/>
    <Port name="Scene out" direction="output"/>
  </MIDIPorts>\n'''

def _get_ardour_config(project):
    # frame rate numerator and denominator
    # (to support NTSC fractional frame rates)
    frame_rate_num = project.profile.frame_rate_num
    frame_rate_den = project.profile.frame_rate_den

    fps_int = 0

    # frame rates with nice round numbers
    if 1000 == frame_rate_den:
        if (24000 == frame_rate_num) or \
           (25000 == frame_rate_num) or \
           (30000 == frame_rate_num) or \
           (60000 == frame_rate_num):

            fps_int = int(frame_rate_num / 1000)
    elif 1 == frame_rate_den:
        fps_int = frame_rate_num
    # NTSC frame rates
    elif 1001 == frame_rate_den:
        if 24000 == frame_rate_num:
            fps_int = 23976
        elif 30000 == frame_rate_num:
            fps_int = 2997
        elif 60000 == frame_rate_num:
            fps_int = 5994

    if 0 == fps_int:
        raise Exception("unsupported frame rate: " + str(project.profile.fps))

    ardour_timecode_format = "timecode_" + str(fps_int)

    s = []

    s.append('  <Config>\n')

    s.append('    <Option name="native-file-data-format" ')
    s.append('value="FormatFloat"/>\n')

    s.append('    <Option name="native-file-header-format" value="WAVE"/>\n')

    s.append('    <Option name="timecode-format" value="')
    s.append(ardour_timecode_format)
    s.append('"/>\n')

    s.append('''    <Option name="destructive-xfade-msecs" value="2"/>
    <Option name="use-region-fades" value="1"/>
    <Option name="use-transport-fades" value="1"/>
    <Option name="use-monitor-fades" value="1"/>
    <Option name="auto-play" value="0"/>
    <Option name="auto-return" value="0"/>
    <Option name="auto-input" value="1"/>
    <Option name="punch-in" value="0"/>
    <Option name="punch-out" value="0"/>
    <Option name="count-in" value="0"/>
    <Option name="session-monitoring" value=""/>
    <Option name="layered-record-mode" value="0"/>
    <Option name="subframes-per-frame" value="100"/>
    <Option name="minitimeline-span" value="120"/>
    <Option name="raid-path" value=""/>
    <Option name="audio-search-path" value=""/>
    <Option name="midi-search-path" value=""/>
    <Option name="track-name-number" value="0"/>
    <Option name="track-name-take" value="0"/>
    <Option name="take-name" value="Take1"/>
    <Option name="jack-time-master" value="1"/>
    <Option name="use-video-sync" value="0"/>
    <Option name="video-pullup" value="0"/>
    <Option name="external-sync" value="0"/>
    <Option name="insert-merge-policy" value="InsertMergeRelax"/>
    <Option name="timecode-offset" value="0"/>
    <Option name="timecode-offset-negative" value="1"/>
    <Option name="slave-timecode-offset" value=" 00:00:00:00"/>
    <Option name="timecode-generator-offset" value=" 00:00:00:00"/>
    <Option name="glue-new-markers-to-bars-and-beats" value="0"/>
    <Option name="midi-copy-is-fork" value="0"/>
    <Option name="glue-new-regions-to-bars-and-beats" value="0"/>
    <Option name="realtime-export" value="0"/>
    <Option name="use-video-file-fps" value="0"/>
    <Option name="videotimeline-pullup" value="1"/>
    <Option name="wave-amplitude-zoom" value="0"/>
    <Option name="wave-zoom-factor" value="2"/>
    <Option name="show-summary" value="1"/>
    <Option name="show-group-tabs" value="1"/>
    <Option name="show-region-fades" value="1"/>
    <Option name="show-busses-on-meterbridge" value="0"/>
    <Option name="show-master-on-meterbridge" value="1"/>
    <Option name="show-midi-on-meterbridge" value="1"/>
    <Option name="show-rec-on-meterbridge" value="1"/>
    <Option name="show-mute-on-meterbridge" value="0"/>
    <Option name="show-solo-on-meterbridge" value="0"/>
    <Option name="show-monitor-on-meterbridge" value="0"/>
    <Option name="show-name-on-meterbridge" value="1"/>
    <Option name="meterbridge-label-height" value="0"/>\n''')

    s.append('  </Config>\n')

    return ''.join(s)

def _get_ardour_metadata():
    return '  <Metadata/>\n'

def _get_ardour_sources(project, seq):
    s = []

    s.append('  <Sources>\n')

    for media in project.media_pool:
        media.set_ardour_source_ids(seq)

        for channel in range(1, (media.channels+1)):
            source_filename = _get_audio_channel_name(media,
                                                      channel,
                                                      media.channels)

            s.append('    ')
            s.append('<Source ')
            s.append('name="')
            s.append(_escape(source_filename))
            s.append('.wav')
            s.append('" type="audio" flags="" id="')
            s.append(str(media.ardour_source_ids[channel - 1]))
            s.append('" gain="1"/>\n')

    s.append('  </Sources>\n')

    return ''.join(s)

def _get_ardour_regions(project, seq):
    s = []

    s.append('  <Regions>\n')

    for media in project.media_pool:
        s.append('    ')
        s.append('<Region name="')
        s.append(_escape(media.transcode_media_basename))
        s.append('" muted="0" opaque="1" locked="0" video-locked="0" ')
        s.append('automatic="1" whole-file="1" import="0" external="0" ')
        s.append('sync-marked="0" left-of-split="0" right-of-split="0" ')
        s.append('hidden="0" position-locked="0" valid-transients="0" ')
        s.append('start="0" length="')
        s.append(_escape(project.frame_to_sample(media.out_frame)))
        s.append('" position="0" beat="0" sync-position="0" ')
        s.append('ancestral-start="0" ancestral-length="0" stretch="1" ')
        s.append('shift="1" positional-lock-style="AudioTime" ')
        s.append('layering-index="0" envelope-active="0" default-fade-in="0" ')
        s.append('default-fade-out="0" fade-in-active="1" ')
        s.append('fade-out-active="1" scale-amplitude="1" id="')
        s.append(str(seq.next()))
        s.append('" type="audio" first-edit="nothing" ')

        for channel in range(0, media.channels):
            s.append('source-')
            s.append(_escape(channel))
            s.append('="')
            s.append(_escape(media.ardour_source_ids[channel]))
            s.append('" ')

            s.append('master-source-')
            s.append(_escape(channel))
            s.append('="')
            s.append(_escape(media.ardour_source_ids[channel]))
            s.append('" ')

        s.append('channels="')
        s.append(_escape(media.channels))
        s.append('"')

        s.append('/>\n')

    s.append('  </Regions>\n')

    return ''.join(s)

def _get_ardour_locations(project, seq):
    s = []

    s.append('  <Locations>\n')

    s.append('    <Location id="')
    s.append(_escape(seq.next()))
    s.append('" name="session" start="0" end="')
    s.append(_escape(project.get_length_in_samples()))
    s.append('" flags="IsSessionRange" locked="0" ')
    s.append('position-lock-style="AudioTime"/>\n')

    s.append('  </Locations>\n')

    return ''.join(s)

def _get_ardour_bundles():
    return '  <Bundles/>\n'

def _shift_indent(input_string, spaces):
    """
    Shift the input multi-line string to the right by the specified number
    of spaces.

    """

    s = input_string.split('\n')

    # if the last character is a newline, remove the last empty line
    # so the formatting looks cleaner
    if '' == s[-1]:
        s = s[:-1]

    for index in range(0, len(s)):
        line = (' ' * spaces) + s[index]
        s[index] = line

    return '\n'.join(s) + '\n'

def _get_ardour_pannable(seq):
    s = []

    s.append('<Pannable>\n')

    # controllable
    s.append('  <Controllable name="pan-azimuth" id="')
    s.append(_escape(seq.next()))
    s.append('" flags="" value="0.5"/>\n')
    s.append('  <Controllable name="pan-width" id="')
    s.append(_escape(seq.next()))
    s.append('" flags="" value="1"/>\n')
    s.append('  <Controllable name="pan-elevation" id="')
    s.append(_escape(seq.next()))
    s.append('" flags="" value="0"/>\n')
    s.append('  <Controllable name="pan-frontback" id="')
    s.append(_escape(seq.next()))
    s.append('" flags="" value="0"/>\n')
    s.append('  <Controllable name="pan-lfe" id="')
    s.append(_escape(seq.next()))
    s.append('" flags="" value="0"/>\n')

    # automation
    s.append('  <Automation>\n')
    s.append('    <AutomationList automation-id="pan-azimuth" id="')
    s.append(_escape(seq.next()))
    s.append('" interpolation-style="Linear" state="Off"/>\n')
    s.append('    <AutomationList automation-id="pan-elevation" id="')
    s.append(_escape(seq.next()))
    s.append('" interpolation-style="Linear" state="Off"/>\n')
    s.append('    <AutomationList automation-id="pan-width" id="')
    s.append(_escape(seq.next()))
    s.append('" interpolation-style="Linear" state="Off"/>\n')
    s.append('    <AutomationList automation-id="pan-frontback" id="')
    s.append(_escape(seq.next()))
    s.append('" interpolation-style="Linear" state="Off"/>\n')
    s.append('    <AutomationList automation-id="pan-lfe" id="')
    s.append(_escape(seq.next()))
    s.append('" interpolation-style="Linear" state="Off"/>\n')
    s.append('  </Automation>\n')

    s.append('</Pannable>\n')

    return ''.join(s)

def _get_ardour_routes(project, seq):
    s = []

    s.append('  <Routes>\n')

    # master bus
    s.append('''    <Route id="54" name="Master" default-type="audio" strict-io="0" active="1" denormal-protection="0" meter-point="MeterPostFader" meter-type="MeterK20">
      <PresentationInfo order="0" flags="MasterOut,OrderSet" color="1927666431"/>
      <Controllable name="solo" id="62" flags="Toggle,RealTime" value="0" self-solo="0" soloed-by-upstream="0" soloed-by-downstream="0"/>
      <Controllable name="solo-iso" id="68" flags="Toggle,RealTime" value="0" solo-isolated="0"/>
      <Controllable name="solo-safe" id="70" flags="Toggle" value="0" solo-safe="0"/>
      <IO name="Master" id="82" direction="Input" default-type="audio" user-latency="0">
        <Port type="audio" name="Master/audio_in 1"/>
        <Port type="audio" name="Master/audio_in 2"/>
      </IO>
      <IO name="Master" id="83" direction="Output" default-type="audio" user-latency="0">
        <Port type="audio" name="Master/audio_out 1">
          <Connection other="Monitor/audio_in 1"/>
        </Port>
        <Port type="audio" name="Master/audio_out 2">
          <Connection other="Monitor/audio_in 2"/>
        </Port>
      </IO>
      <MuteMaster mute-point="PostFader,Listen,Main" muted="0"/>
      <Controllable name="mute" id="64" flags="Toggle,RealTime" value="0"/>
      <Controllable name="phase" id="66" flags="Toggle" value="0" phase-invert="00"/>
      <Automation>
        <AutomationList automation-id="solo" id="61" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="solo-iso" id="67" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="solo-safe" id="69" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="mute" id="63" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="phase" id="65" interpolation-style="Discrete" state="Off"/>
      </Automation>
      <Pannable>
        <Controllable name="pan-azimuth" id="73" flags="" value="0.5"/>
        <Controllable name="pan-width" id="77" flags="" value="1"/>
        <Controllable name="pan-elevation" id="75" flags="" value="0"/>
        <Controllable name="pan-frontback" id="79" flags="" value="0"/>
        <Controllable name="pan-lfe" id="81" flags="" value="0"/>
        <Automation>
          <AutomationList automation-id="pan-azimuth" id="72" interpolation-style="Linear" state="Off"/>
          <AutomationList automation-id="pan-elevation" id="74" interpolation-style="Linear" state="Off"/>
          <AutomationList automation-id="pan-width" id="76" interpolation-style="Linear" state="Off"/>
          <AutomationList automation-id="pan-frontback" id="78" interpolation-style="Linear" state="Off"/>
          <AutomationList automation-id="pan-lfe" id="80" interpolation-style="Linear" state="Off"/>
        </Automation>
      </Pannable>
      <Processor id="85" name="Amp" active="1" user-latency="0" type="trim">
        <Automation>
          <AutomationList automation-id="trim" id="59" interpolation-style="Linear" state="Off"/>
        </Automation>
        <Controllable name="trimcontrol" id="60" flags="GainLike" value="1"/>
      </Processor>
      <Processor id="84" name="Amp" active="1" user-latency="0" type="amp">
        <Automation>
          <AutomationList automation-id="gain" id="57" interpolation-style="Linear" state="Off"/>
        </Automation>
        <Controllable name="gaincontrol" id="58" flags="GainLike" value="1"/>
      </Processor>
      <Processor id="86" name="meter-Master" active="1" user-latency="0" type="meter"/>
      <Processor id="87" name="Master" active="1" user-latency="0" own-input="1" own-output="0" output="Master" type="main-outs" role="Main">
        <PannerShell bypassed="0" user-panner="" linked-to-route="1"/>
        <Pannable>
          <Controllable name="pan-azimuth" id="73" flags="" value="0.5"/>
          <Controllable name="pan-width" id="77" flags="" value="1"/>
          <Controllable name="pan-elevation" id="75" flags="" value="0"/>
          <Controllable name="pan-frontback" id="79" flags="" value="0"/>
          <Controllable name="pan-lfe" id="81" flags="" value="0"/>
          <Automation>
            <AutomationList automation-id="pan-azimuth" id="72" interpolation-style="Linear" state="Off"/>
            <AutomationList automation-id="pan-elevation" id="74" interpolation-style="Linear" state="Off"/>
            <AutomationList automation-id="pan-width" id="76" interpolation-style="Linear" state="Off"/>
            <AutomationList automation-id="pan-frontback" id="78" interpolation-style="Linear" state="Off"/>
            <AutomationList automation-id="pan-lfe" id="80" interpolation-style="Linear" state="Off"/>
          </Automation>
        </Pannable>
      </Processor>
      <Slavable/>
    </Route>\n''')

    # monitor bus
    s.append('''    <Route id="90" name="Monitor" default-type="audio" strict-io="0" active="1" denormal-protection="0" meter-point="MeterPostFader" meter-type="MeterPeak">
      <PresentationInfo order="0" flags="MonitorOut" color="0"/>
      <Controllable name="solo" id="98" flags="Toggle,RealTime" value="0" self-solo="0" soloed-by-upstream="0" soloed-by-downstream="0"/>
      <Controllable name="solo-iso" id="104" flags="Toggle,RealTime" value="0" solo-isolated="0"/>
      <Controllable name="solo-safe" id="106" flags="Toggle" value="0" solo-safe="0"/>
      <IO name="Monitor" id="107" direction="Input" default-type="audio" user-latency="0">
        <Port type="audio" name="Monitor/audio_in 1">
          <Connection other="Master/audio_out 1"/>
          <Connection other="auditioner/audio_out 1"/>
        </Port>
        <Port type="audio" name="Monitor/audio_in 2">
          <Connection other="Master/audio_out 2"/>
          <Connection other="auditioner/audio_out 2"/>
        </Port>
      </IO>
      <IO name="Monitor" id="108" direction="Output" default-type="audio" user-latency="0">
        <Port type="audio" name="Monitor/audio_out 1">
          <Connection other="system:playback_1"/>
        </Port>
        <Port type="audio" name="Monitor/audio_out 2">
          <Connection other="system:playback_2"/>
        </Port>
      </IO>
      <MuteMaster mute-point="PostFader,Listen,Main" muted="0"/>
      <Controllable name="mute" id="100" flags="Toggle,RealTime" value="0"/>
      <Controllable name="phase" id="102" flags="Toggle" value="0" phase-invert="00"/>
      <Automation>
        <AutomationList automation-id="solo" id="97" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="solo-iso" id="103" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="solo-safe" id="105" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="mute" id="99" interpolation-style="Discrete" state="Off"/>
        <AutomationList automation-id="phase" id="101" interpolation-style="Discrete" state="Off"/>
      </Automation>
      <Processor id="113" name="return 2" active="1" user-latency="0" own-input="1" own-output="1" type="intreturn" bitslot="1">
        <Automation>
          <AutomationList automation-id="gain" id="114" interpolation-style="Linear" state="Off"/>
        </Automation>
      </Processor>
      <Processor id="118" name="MonitorOut" active="1" user-latency="0" type="monitor" dim-level="0.25118863582611084" solo-boost-level="1" cut-all="0" dim-all="0" mono="0" channels="2">
        <Channel id="0" cut="0" invert="0" dim="0" solo="0"/>
        <Channel id="1" cut="0" invert="0" dim="0" solo="0"/>
      </Processor>
      <Processor id="109" name="Amp" active="1" user-latency="0" type="amp">
        <Automation>
          <AutomationList automation-id="gain" id="93" interpolation-style="Linear" state="Off"/>
        </Automation>
        <Controllable name="gaincontrol" id="94" flags="GainLike" value="1"/>
      </Processor>
      <Processor id="111" name="meter-Monitor" active="1" user-latency="0" type="meter"/>
      <Processor id="112" name="Monitor" active="1" user-latency="0" own-input="1" own-output="0" output="Monitor" type="main-outs" role="Main"/>
      <Slavable/>
    </Route>\n''')

    presentation_order = 0

    # route names (and such) must be unique
    route_names = set()

    # go through all the flowblade playlists
    for playlist in project.playlists:
        # only evaluate playlists that have media with audio
        if 0 == len(playlist.clips):
            continue

        # try to use the Flowblade channel name for the route,
        # but make sure it's unique within the Ardour project
        route_name = project.profile.get_flowblade_track_by_mlt_playlist_id(playlist.id)
        if route_name in route_names:
            found_unique_name = False
            for i in range(2, 1000000):
                candidate_route_name = route_name + " " + str(i)
                if candidate_route_name not in route_names:
                    route_name = candidate_route_name
                    found_unique_name = True
                    break

            if not found_unique_name:
                raise Exception("could not create unique route name")

        # set the ardour route name, and add the unique route name to the
        # unique set
        playlist.set_ardour_route_name(route_name)
        route_names.add(route_name)

        # set the ardour playlist name
        playlist_name = route_name + ".1"
        playlist.set_ardour_playlist_name(playlist_name)

        # incrementing number controlling track display order
        presentation_order += 1

        # get a route_id for this route, and save it for later
        route_id = seq.next()
        playlist.set_ardour_route_id(route_id)

        # these are leaf nodes, but there are duplicate correlated entries
        # the same XML block is repeated more than once (but must have
        # correlated IDs between instances of this same XML fragment)
        pannable = _get_ardour_pannable(seq)

        # route
        s.append('    <Route id="')
        s.append(_escape(route_id))
        s.append('" name="')
        s.append(_escape(route_name))
        s.append('" default-type="audio" strict-io="1" active="1" ')
        s.append('denormal-protection="0" meter-point="MeterPostFader" ')
        s.append('meter-type="MeterPeak" saved-meter-point="MeterPostFader" ')
        s.append('mode="Normal">\n')

        # presentation info
        s.append('      <PresentationInfo order="')
        s.append(_escape(presentation_order))
        s.append('" flags="AudioTrack,OrderSet" color="3030641919"/>\n')

        # solo
        s.append('      <Controllable name="solo" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle,RealTime" value="0" self-solo="0" ')
        s.append('soloed-by-upstream="0" soloed-by-downstream="0"/>\n')
        s.append('      <Controllable name="solo-iso" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle,RealTime" value="0" solo-isolated="0"/>\n')
        s.append('      <Controllable name="solo-safe" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle" value="0" solo-safe="0"/>\n')

        # I/O
        s.append('      <IO name="')
        s.append(_escape(route_name))
        s.append('" id="')
        s.append(_escape(seq.next()))
        s.append('" direction="Input" default-type="audio" ')
        s.append('user-latency="0">\n')

        for channel in range(1, (playlist.get_channel_count() + 1)):
            s.append('        <Port type="audio" name="')
            s.append(_escape(route_name))
            s.append('/audio_in ')
            s.append(_escape(channel))
            s.append('">\n')
            s.append('          <Connection other="system:capture_')
            s.append(_escape(channel))
            s.append('"/>\n')
            s.append('        </Port>\n')

        s.append('      </IO>\n')
        s.append('      <IO name="')
        s.append(_escape(route_name))
        s.append('" id="')
        s.append(_escape(seq.next()))
        s.append('" direction="Output" default-type="audio" ')
        s.append('user-latency="0">\n')
        s.append('        <Port type="audio" name="')
        s.append(_escape(route_name))
        s.append('/audio_out 1">\n')
        s.append('          <Connection other="Master/audio_in 1"/>\n')
        s.append('        </Port>\n')
        s.append('        <Port type="audio" name="')
        s.append(_escape(route_name))
        s.append('/audio_out 2">\n')
        s.append('          <Connection other="Master/audio_in 2"/>\n')
        s.append('        </Port>\n')
        s.append('      </IO>\n')

        # mute
        s.append('      <MuteMaster mute-point="PostFader,Listen,Main" ')
        s.append('muted="0"/>\n')
        s.append('      <Controllable name="mute" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle,RealTime" value="0"/>\n')
        s.append('      <Controllable name="phase" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle" value="0" phase-invert="0"/>\n')

        # automation
        s.append('      <Automation>\n')
        s.append('        <AutomationList automation-id="solo" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="solo-iso" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="solo-safe" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="mute" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="rec-enable" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="rec-safe" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="phase" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('        <AutomationList automation-id="monitor" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Discrete" state="Off"/>\n')
        s.append('      </Automation>\n')
        s.append(_shift_indent(pannable, 6))

        # Processor: Amp/trim
        s.append('      <Processor id="')
        s.append(_escape(seq.next()))
        s.append('" name="Amp" active="1" user-latency="0" type="trim">\n')
        s.append('        <Automation>\n')
        s.append('          <AutomationList automation-id="trim" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Linear" state="Off"/>\n')
        s.append('        </Automation>\n')
        s.append('        <Controllable name="trimcontrol" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="GainLike" value="1"/>\n')
        s.append('      </Processor>\n')

        # Processor: Amp/amp
        s.append('      <Processor id="')
        s.append(_escape(seq.next()))
        s.append('" name="Amp" active="1" user-latency="0" type="amp">\n')
        s.append('        <Automation>\n')
        s.append('          <AutomationList automation-id="gain" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Linear" state="Off"/>\n')
        s.append('        </Automation>\n')
        s.append('        <Controllable name="gaincontrol" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="GainLike" value="1"/>\n')
        s.append('      </Processor>\n')

        # Processor: meter-$ROUTE_NAME
        s.append('      <Processor id="')
        s.append(_escape(seq.next()))
        s.append('" name="meter-')
        s.append(_escape(route_name))
        s.append('" active="1" user-latency="0" type="meter"/>\n')

        # Processor: $ROUTE_NAME
        s.append('      <Processor id="')
        s.append(_escape(seq.next()))
        s.append('" name="')
        s.append(_escape(route_name))
        s.append('" active="1" user-latency="0" own-input="1" ')
        s.append('own-output="0" output="Audio" type="main-outs" ')
        s.append('role="Main">\n')
        s.append('        <PannerShell bypassed="0" user-panner="" ')
        s.append('linked-to-route="1"/>\n')
        s.append(_shift_indent(pannable, 8))
        s.append('      </Processor>\n')

        # Processor: Monitor
        s.append('      <Processor id="')
        s.append(_escape(seq.next()))
        s.append('" name="Monitor" active="0" user-latency="0" own-input="1" ')
        s.append('own-output="1" type="intsend" role="Listen" ')
        s.append('selfdestruct="0" target="90" allow-feedback="0">\n')
        s.append('        <Automation>\n')
        s.append('          <AutomationList automation-id="gain" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Linear" state="Off"/>\n')
        s.append('        </Automation>\n')
        s.append('        <PannerShell bypassed="0" user-panner="" ')
        s.append('linked-to-route="1"/>\n')
        s.append(_shift_indent(pannable, 8))
        s.append('        <Processor id="')
        s.append(_escape(seq.next()))
        s.append('" name="Amp" active="0" user-latency="0" type="amp">\n')
        s.append('          <Automation>\n')
        s.append('            <AutomationList automation-id="gain" id="')
        s.append(_escape(seq.next()))
        s.append('" interpolation-style="Linear" state="Off"/>\n')
        s.append('          </Automation>\n')
        s.append('          <Controllable name="gaincontrol" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="GainLike" value="1"/>\n')
        s.append('        </Processor>\n')
        s.append('      </Processor>\n')

        # slavable
        s.append('      <Slavable/>\n')

        # Controllable
        s.append('      <Controllable name="monitor" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="RealTime" value="0" monitoring=""/>\n')
        s.append('      <Controllable name="rec-safe" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle,RealTime" value="0"/>\n')
        s.append('      <Controllable name="rec-enable" id="')
        s.append(_escape(seq.next()))
        s.append('" flags="Toggle,RealTime" value="0"/>\n')

        # Diskstream
        s.append('      <Diskstream flags="Recordable" playlist="')
        s.append(_escape(playlist_name))
        s.append('" name="Audio" id="')
        s.append(_escape(seq.next()))
        s.append('" speed="1" capture-alignment="Automatic" record-safe="0" ')
        s.append('channels="')
        s.append(_escape(playlist.get_channel_count()))
        s.append('"/>\n')

        s.append('    </Route>\n')

    s.append('  </Routes>\n')

    return ''.join(s)

def _get_ardour_playlists(project, seq):
    s = []

    s.append('  <Playlists>\n')

    for playlist in project.playlists:
        if 0 == len(playlist.clips):
            continue

        s.append('    <Playlist id="')
        s.append(_escape(seq.next()))
        s.append('" name="')
        s.append(_escape(playlist.ardour_playlist_name))
        s.append('" type="audio" orig-track-id="')
        s.append(_escape(playlist.ardour_route_id))
        s.append('" shared-with-ids="" frozen="0" combine-ops="0">\n')

        # media.transcode_media_basename -> clip instance counter
        #
        # if the media.transcode_media_basename is "foo", this lets us name
        # our clips "foo.1", "foo.2", etc.
        clip_name_count = {}

        for clip in playlist.clips:
            basename = clip.media.transcode_media_basename

            # set region name and counter number in clip name count
            if basename not in clip_name_count:
                clip_name_count[basename] = 1
            else:
                clip_name_count[basename] += 1

            region_name = basename + "." + str(clip_name_count[basename])

            # start
            start_in_samples = project.frame_to_sample(clip.in_frame)

            # length
            length_in_samples = project.frame_to_sample(clip.length)

            # position
            position_in_samples = project.frame_to_sample(
                clip.timeline_start_frame)

            # beat
            beat = project.frame_to_beat(clip.timeline_start_frame)

            s.append('      <Region name="')
            s.append(_escape(region_name))
            s.append('" muted="0" opaque="1" locked="0" video-locked="0" ')
            s.append('automatic="0" whole-file="0" import="0" external="0" ')
            s.append('sync-marked="0" left-of-split="0" right-of-split="0" ')
            s.append('hidden="0" position-locked="0" valid-transients="0" ')
            s.append('start="')
            s.append(_escape(start_in_samples))
            s.append('" length="')
            s.append(_escape(length_in_samples))
            s.append('" position="')
            s.append(_escape(position_in_samples))
            s.append('" beat="')
            s.append(_escape(beat))
            s.append('" sync-position="0" ancestral-start="0" ')
            s.append('ancestral-length="0" stretch="1" shift="1" ')
            s.append('positional-lock-style="AudioTime" layering-index="0" ')
            s.append('envelope-active="0" default-fade-in="0" ')
            s.append('default-fade-out="0" fade-in-active="1" ')
            s.append('fade-out-active="1" scale-amplitude="1" id="')
            s.append(_escape(seq.next()))
            s.append('" type="audio" first-edit="nothing" ')

            for channel in range(0, clip.media.channels):
                s.append('source-')
                s.append(_escape(channel))
                s.append('="')
                s.append(_escape(clip.media.ardour_source_ids[channel]))
                s.append('" ')
        
                s.append('master-source-')
                s.append(_escape(channel))
                s.append('="')
                s.append(_escape(clip.media.ardour_source_ids[channel]))
                s.append('" ')

            s.append('channels="')
            s.append(_escape(clip.media.channels))
            s.append('"/>\n')

        s.append('    </Playlist>\n')

    s.append('  </Playlists>\n')

    return ''.join(s)

def _get_ardour_route_groups():
    return '  <RouteGroups/>\n'

def _get_ardour_click():
    s = []

    s.append('  <Click>\n')
    s.append('    <IO name="Click" id="51" direction="Output" ')
    s.append('default-type="audio" user-latency="0">\n')
    s.append('      <Port type="audio" name="Click/audio_out 1">\n')
    s.append('        <Connection other="system:playback_1"/>\n')
    s.append('      </Port>\n')
    s.append('      <Port type="audio" name="Click/audio_out 2">\n')
    s.append('        <Connection other="system:playback_2"/>\n')
    s.append('      </Port>\n')
    s.append('    </IO>\n')
    s.append('    <Processor id="52" name="Amp" active="1" user-latency="0" ')
    s.append('type="amp">\n')
    s.append('      <Automation>\n')
    s.append('        <AutomationList automation-id="gain" id="49" ')
    s.append('interpolation-style="Linear" state="Off"/>\n')
    s.append('      </Automation>\n')
    s.append('      <Controllable name="gaincontrol" id="50" ')
    s.append('flags="GainLike" value="1"/>\n')
    s.append('    </Processor>\n')
    s.append('  </Click>\n')

    return ''.join(s)

def _get_ardour_ltc():
    return '''  <LTC-In>
    <IO name="LTC In" id="47" direction="Input" default-type="audio" user-latency="0">
      <Port type="audio" name="LTC-in">
        <Connection other="system:capture_1"/>
      </Port>
    </IO>
  </LTC-In>
  <LTC-Out>
    <IO name="LTC Out" id="48" direction="Output" default-type="audio" user-latency="0">
      <Port type="audio" name="LTC-out"/>
    </IO>
  </LTC-Out>\n'''

def _get_ardour_speakers():
    return '''  <Speakers>
    <Speaker azimuth="240" elevation="0" distance="1"/>
    <Speaker azimuth="120" elevation="0" distance="1"/>
  </Speakers>\n'''

def _get_ardour_tempo_map():
    s = []

    s.append('  <TempoMap>\n')

    s.append('    <Tempo pulse="0" frame="0" movable="0" ')
    s.append('lock-style="AudioTime" beats-per-minute="')
    s.append(str(BPM))
    s.append('" note-type="4" clamped="0" end-beats-per-minute="120" ')
    s.append('active="1" locked-to-meter="1"/>\n')

    s.append('    <Meter pulse="0" frame="0" movable="0" ')
    s.append('lock-style="AudioTime" bbt="1|1|0" beat="0" ')
    s.append('note-type="4" divisions-per-bar="4"/>\n')

    s.append('  </TempoMap>\n')

    return ''.join(s)

def _get_ardour_extra():
    s = []

    s.append('  <Extra>\n')
    s.append('    <ClockModes>\n')
    s.append('      <Clock name="primary" mode="Timecode" on="1"/>\n')
    s.append('      <Clock name="secondary" mode="BBT" on="1"/>\n')
    s.append('      <Clock name="bigclock" mode="Timecode" on="1"/>\n')
    s.append('      <Clock name="nudge" mode="Timecode" on="1"/>\n')
    s.append('    </ClockModes>\n')
    s.append('  </Extra>\n')

    return ''.join(s)

def _create_ardour_project_file(basedir, project):
    # get the path to the ardour project file
    (head, basename) = os.path.split(basedir)
    if '' == basename:
        raise Exception("could not extract base filename")

    ardour_project_filename = basename + ".ardour"
    ardour_project_file_path = os.path.join(basedir, ardour_project_filename)

    # Ardour assigns unique IDs to just about everything of any importance in
    # the Ardour project file. Our approach is to hard-code IDs for things
    # that only appear once (all of these IDs are less than 500). Then we
    # generate dynamic IDs for the things that can appear a varying number
    # of times. The dynamic IDs start at 500 and go up from there.
    seq = Sequence(500)

    # write the middle of the Ardour project file into a temporary buffer.
    # we have to do this first, because the opening XML Session tag has
    # to include information that we'll only know after we're done generating
    # all of this stuff.
    s = []
    s.append(_get_ardour_program_version())
    s.append(_get_ardour_midi_ports())
    s.append(_get_ardour_config(project))
    s.append(_get_ardour_metadata())
    s.append(_get_ardour_sources(project, seq))
    s.append(_get_ardour_regions(project, seq))
    s.append(_get_ardour_locations(project, seq))
    s.append(_get_ardour_bundles())
    s.append(_get_ardour_routes(project, seq))
    s.append(_get_ardour_playlists(project, seq))
    s.append(_get_ardour_route_groups())
    s.append(_get_ardour_click())
    s.append(_get_ardour_ltc())
    s.append(_get_ardour_speakers())
    s.append(_get_ardour_tempo_map())
    s.append(_get_ardour_extra())

    # write the ardour project file
    with atomicfile.AtomicFileWriter(ardour_project_file_path, "w") as afw:
        # get a reference to the temp file we're writing
        f = afw.get_file()

        # XML header
        f.write(_get_ardour_xml_header())

        # session open
        # (seq.next() is being passed in as the highest ID found in the
        #  entire project, which is why this part is generated last)
        f.write(_get_ardour_session_open(basename, project, seq.next()))

        # write the bulk of the file that we already generated from the buffer
        f.write(''.join(s))

        # session close
        f.write(_get_ardour_session_close())

##############################################################################
# FLOWBLADE EXPORT LAUNCH                                                    #
##############################################################################

def launch_export_ardour_session_from_flowblade(mlt_xml_file,
                                                ardour_project_dir,
                                                sample_rate=None):

    if sample_rate == None:
        sample_rate = DEFAULT_SAMPLE_RATE

    # get the number of audio and video tracks from the current sequence
    (video_tracks_count, audio_tracks_count) = \
        editorstate.current_sequence().get_track_counts()

    # create a Project instance from a Flowblade MLT XML file
    project = create_project_from_mlt_xml(mlt_xml_file,
                                          sample_rate,
                                          video_tracks_count,
                                          audio_tracks_count)

    # create a new Ardour project, using our Project instance
    create_ardour_project(ardour_project_dir, project)

