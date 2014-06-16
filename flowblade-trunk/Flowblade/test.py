"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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
import app
import timeit
import edit
import utils
import persistance
import projectdata
import editorwindow
import mltplayer
import mltprofiles
import sequence
import updater
import mlt
import os

value = 0

def buildProject(project):
    app.project = project
    sequence = project.c_seq
    edit.set_edit_context(sequence)
    
    project.add_unnamed_bin()
    
    track = sequence.tracks[1]
    track2 = sequence.tracks[2]
    
    media_file1 = project.media_files[1]
    media_file2 = project.media_files[2]
    media_file3 = project.media_files[3]
    media_file4 = project.media_files[4]

    clip1 = sequence.create_file_producer_clip(media_file1.path)
    data1 = {"track": track,
             "clip":clip1,
             "clip_in":30,
             "clip_out":30}
    action1 = edit.append_action(data1)
    action1.do_edit()
    
    for i in range(0, 3):
        clip2 = sequence.create_file_producer_clip(media_file2.path)
        data2 = {"track": track,
                 "clip":clip2,
                 "clip_in":30,
                 "clip_out":90}
        action2 = edit.append_action(data2)
        action2.do_edit()
        clip12 = sequence.create_file_producer_clip(media_file4.path)
        data12 = {"track": track,
                 "clip":clip12,
                 "clip_in":10,
                 "clip_out":30}
        action12 = edit.append_action(data12)
        action12.do_edit()
    
    print track.count()

def load_save(project, path):
    persistance.save_project(project, path)
    return persistance.load_project(path)

def load_clips(project):
    clip_path = "/home/janne/test/clipit/sekalaista"
    count = 9;
    file_list = os.listdir(clip_path)
    if len(file_list) < count:
        count = len(file_list) 

    for i in range(count):
        file_path = clip_path + "/" + file_list[i]
        print file_path
        project.add_media_file(file_path)
        
def get_render_options_test():
    # Create render options object
    render_options = {}
    render_options["file_path"] = "/home/janne/test/pyrender.mp4"
    render_options["render_type"] = "VIDEO_AUDIO"
    render_options["f"] = "mp4" # format
    
    render_options["vcodec"] = "mpeg4" # vidoe codec
    render_options["b"] = "2500k" # video bitrate
    
    render_options["acodec"] = "libmp3lame" # audion codec
    render_options["ar"] = "44100" # audio sampling frequency
    render_options["ac"] = "2" # number of audio channels
    render_options["ab"] = "128k"
    
    return render_options
    
def get_seq_render_options_test():
    render_options = {}
    render_options["render_type"] = "IMAGE_SEQUENCE"
    render_options["vcodec"] = "png" # vidoe codec
    render_options["file_path"] = "/home/janne/test/rend/frame_%d.png"
    
    return render_options
"""
"""
typedef struct
{
	int clip;                 /**< the index of the clip within the playlist */
	mlt_producer producer;    /**< the clip's producer (or parent producer of a cut) */
	mlt_producer cut;         /**< the clips' cut producer */
	mlt_position start;       /**< the time this begins relative to the beginning of the playlist */
	char *resource;           /**< the file name or address of the clip */
	mlt_position frame_in;    /**< the clip's in point */
	mlt_position frame_out;   /**< the clip's out point */
	mlt_position frame_count; /**< the duration of the clip */
	mlt_position length;      /**< the unedited duration of the clip */
	float fps;                /**< the frame rate of the clip */
	int repeat;               /**< the number of times the clip is repeated */
}
mlt_playlist_clip_info;
"""
