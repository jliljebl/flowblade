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
Module contains objects and methods needed to create render consumers.
"""


from gi.repository import Gdk

try:
    import mlt7 as mlt
except:
    import mlt7 as mlt
import time
import threading
import xml.dom.minidom
import os
import subprocess
import editorpersistance

import mltenv
import respaths


# File describing existing encoding and quality options
RENDER_ENCODING_FILE = "/res/render/renderencoding.xml"

# Node, attribute names.
NAME = "name"
TYPE = "type"
ID = "id"
EXTENSION = "extension"
RESIZABLE = "resize"
ARGS = "args"
REPLACED_VALUES = "replvalues"
ADDED_ATTRIBUTES = "addargs"
BITRATE_OPTION = "boption"
QUALITY_GROUP = "qualityqroup"
ENCODING_OPTION = "encodingoption"
PROXY_ENCODING_OPTION = "proxyencodingoption"
QGROUP = "qgroup"
DEFAULT_INDEX = "defaultindex"
PROFILE = "profile"
QUALITY = "quality"
BITRATE = "bitrate"
AUDIO_DESCRIPTION = "audiodesc"
NON_USER = "nonuser"
PRESET_GROUP = "presetgroup"
PRESET_GROUP_H264 = "H.264, HEVC"
PRESET_GROUP_NVENC = "NVENC"
PRESET_GROUP_VAAPI = "VAAPI"
PRESET_GROUP_MPEG = "MPEG"
PRESET_GROUP_LOSSLESS = "Lossless"
PRESET_GROUP_IMAGE_SEQUENCE = "Image Sequence"
PRESET_GROUP_AUDIO = "Audio" 
PRESET_GROUP_OGG_ETC = "oggwebmetc"
PRESET_GROUP_ALPHA = "Alpha"

# ffmpeg arg values sometimes need equals signs in them.
EQUALS_SIGN_ENCODING = "@#@#"

# GPU encoding availability.
H_264_NVENC_AVAILABLE = False
H_264_NVENC_TEST = ["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "color=s=640x360", 
                    "-frames", "1", "-an", "-load_plugin", "hevc_hw", "-c:v", 
                    "h264_nvenc", "-f", "rawvideo", "pipe:"]
HEVC_NVENC_AVAILABLE = False
HEVC_NVENC_TEST = ["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "color=s=640x360", 
                    "-frames", "1", "-an", "-load_plugin", "hevc_hw", "-c:v", 
                    "hevc_nvenc", "-f", "rawvideo", "pipe:"]
H_264_VAAPI_AVAILABLE = False
H_264_VAAPI_TEST = ["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "color=s=640x360", 
                    "-frames", "1", "-an", "-init_hw_device", "vaapi=vaapi0:,connection_type=x11", 
                    "-filter_hw_device", "vaapi0", "-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi", "-f", "rawvideo", "pipe:"]

# Default encoding name.
DEFAULT_ENCODING_NAME = "H.264 / .mp4" 

# Replace strings and attribute values.
BITRATE_RPL = "%BITRATE%"
VARIABLE_VAL = "%VARIABLE%"
SCREEN_SIZE_RPL = "%SCREENSIZE%"
ASPECT_RPL = "%ASPECT%"

render_encoding_doc = None
encoding_options = []
categorized_encoding_options = []
not_supported_encoding_options = []
quality_option_groups = {}
quality_option_groups_default_index = {}
non_user_encodings = []
proxy_encodings = None

# This is used to turn performance settings off for proxy rendering.
performance_settings_enabled = True

# replace empty strings with None values
def _get_attribute(node, attr_name):
    value = node.getAttribute(attr_name)
    if value == "":
        return None
    
    return value

def get_encoding_index(encoding):
    for i in range(0, len(encoding_options)):
        if encoding == encoding_options[i]:
            return i
            
    return -1

class QualityOption:
    """
    A render quality option for an EncodingOption.
    
    Values of mlt render consumer properties (usually bitrate) that equal 
    key expressions are replaced with corresponding values.
    """
    def __init__(self, quality_node):
        self.name = _get_attribute(quality_node, NAME)
        # Replaced render arguments
        replaced_values_str = _get_attribute(quality_node, REPLACED_VALUES)
        self.replaced_expressions = []
        self.replace_map = {}
        if replaced_values_str != None:
            tokens = replaced_values_str.split(";")
            for token in tokens:
                token_sides = token.split(" ")
                self.replaced_expressions.append(token_sides[0])
                self.replace_map[token_sides[0]] = token_sides[1]
        # Added render arguments
        added_atrrs_str = _get_attribute(quality_node, ADDED_ATTRIBUTES)
        self.add_map = {}
        if added_atrrs_str != None:
            tokens = added_atrrs_str.split(" ")
            for token in tokens:
                token_sides = token.split("=")
                self.add_map[token_sides[0]] = token_sides[1]

class EncodingOption:
    """
    An object that groups together vcodoc, acodec, format and quality options group.
    Object is used to set mlt render consumer properties.
    """
    def __init__(self, option_node):
        self.name = _get_attribute(option_node, NAME)
        self.type = _get_attribute(option_node, TYPE)
        self.presetgroup = _get_attribute(option_node, PRESET_GROUP)
        self.resizable = (_get_attribute(option_node, RESIZABLE) == "True")
        self.extension = _get_attribute(option_node, EXTENSION)
        self.nonuser = _get_attribute(option_node, NON_USER)
        self.quality_qroup_id = _get_attribute(option_node, QGROUP)
        self.quality_options = quality_option_groups[self.quality_qroup_id]
        try:
            quality_default_index = int(quality_option_groups_default_index[self.quality_qroup_id])
        except KeyError:
            quality_default_index = None
        self.quality_default_index = quality_default_index
        self.audio_desc = _get_attribute(option_node, AUDIO_DESCRIPTION)
        profile_node = option_node.getElementsByTagName(PROFILE).item(0)
        self.attr_string =  _get_attribute(profile_node, ARGS)
        self.acodec = None
        self.vcodec = None
        self.format = None

        tokens = self.attr_string.split(" ")
        for token in tokens:
            token_sides = token.split("=")
            if token_sides[0] == "acodec":
                self.acodec = token_sides[1]
            elif token_sides[0] == "vcodec":
                self.vcodec = token_sides[1]
            elif token_sides[0] == "f":
                self.format = token_sides[1]

        self.supported, self.err_msg = mltenv.render_profile_supported(self.format, 
                                                         self.vcodec,
                                                         self.acodec)
                                                         
    def get_args_vals_tuples_list(self, profile, quality_option=None):
        # Encoding options
        tokens = self.attr_string.split(" ")
        args_tuples = []
        for token in tokens:
            # Get property keys and values
            token_sides = token.split("=")
            arg1 = str(token_sides[0])
            arg2 = str(token_sides[1])
            # Sometimes arg values need equals signs in them
            arg2 = arg2.replace(EQUALS_SIGN_ENCODING, "=")
            
            # Replace keyword values
            if arg2 == SCREEN_SIZE_RPL:
                arg2 = str(profile.width())+ "x" + str(profile.height())
            if arg2 == ASPECT_RPL:
                arg2 = "@" + str(profile.display_aspect_num()) + "/" + str(profile.display_aspect_den())

            # Replace keyword values from quality options values
            if quality_option != None:
                if arg2 in quality_option.replaced_expressions:
                    arg2 = str(quality_option.replace_map[arg2])
            args_tuples.append((arg1, arg2))
        
        print("args_tuples", args_tuples)
        return args_tuples

    def get_audio_description(self):
        if self.audio_desc == None:
            desc = "Not available"
        else:
            desc = self.audio_desc 
        return "<small>" + desc + "</small>"

        
def load_render_profiles():
    """
    Load render profiles from xml into DOM at start-up and build
    object tree.
    """
    print("Loading render profiles...")
    file_path = respaths.ROOT_PATH + RENDER_ENCODING_FILE
    global render_encoding_doc
    render_encoding_doc = xml.dom.minidom.parse(file_path)

    # Test GPU rendering availability
    global H_264_NVENC_AVAILABLE, H_264_VAAPI_AVAILABLE
    # h264_nvenc
    ret_code = _test_command(H_264_NVENC_TEST)
    if (ret_code == 0):
        print("h264_nvenc available")
        H_264_NVENC_AVAILABLE = True
    # hevc_nvenc
    ret_code = _test_command(HEVC_NVENC_TEST)
    if (ret_code == 0):
        print("hevc_nvenc available")
        HEVC_NVENC_AVAILABLE = True # NOT USED !
    # vaapi
    ret_code = _test_command(H_264_VAAPI_TEST)
    if (ret_code == 0):
        print("h264_vaapi available")
        H_264_VAAPI_AVAILABLE = True

    # Create quality option groups
    global quality_option_groups
    qgroup_nodes = render_encoding_doc.getElementsByTagName(QUALITY_GROUP)
    for qgnode in qgroup_nodes:
        quality_qroup = []
        group_key = _get_attribute(qgnode, ID)
        group_default_index = _get_attribute(qgnode, DEFAULT_INDEX)
        if group_default_index != None: 
            quality_option_groups_default_index[group_key] = group_default_index
        option_nodes = qgnode.getElementsByTagName(QUALITY)
        for option_node in option_nodes:
            q_option = QualityOption(option_node)
            quality_qroup.append(q_option)
        quality_option_groups[group_key] = quality_qroup

    # Create encoding options
    global encoding_options, not_supported_encoding_options, non_user_encodings
    encoding_option_nodes = render_encoding_doc.getElementsByTagName(ENCODING_OPTION)
    for eo_node in encoding_option_nodes:
        encoding_option = EncodingOption(eo_node)
        if encoding_option.supported:
            if encoding_option.nonuser == None:
                encoding_options.append(encoding_option)
            else:
                non_user_encodings.append(encoding_option) 
        else:
            msg = "...NOT available, " + encoding_option.err_msg + " missing"
            not_supported_encoding_options.append(encoding_option)

    # Create categorised structure.
    global categorized_encoding_options
    H264_encs = []
    NVENC_encs = []
    VAAPI_encs = []
    MPEG_encs = []
    OGG_ETC_encs = []
    LOSSLESS_encs = []
    IMG_SEQ_encs = []
    AUDIO_encs = []
    ALPHA_encs = []
    
    for enc in encoding_options:
        if enc.presetgroup == PRESET_GROUP_H264:
            H264_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_NVENC:
            NVENC_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_VAAPI:
            VAAPI_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_MPEG:
            MPEG_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_OGG_ETC:
            OGG_ETC_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_LOSSLESS:
            LOSSLESS_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_IMAGE_SEQUENCE:
            IMG_SEQ_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_AUDIO:
            AUDIO_encs.append((enc.name, enc))
        elif enc.presetgroup == PRESET_GROUP_ALPHA:
            ALPHA_encs.append((enc.name, enc))

    if len(H264_encs) > 0:
        categorized_encoding_options.append((PRESET_GROUP_H264, H264_encs))
    if len(NVENC_encs) > 0 and H_264_NVENC_AVAILABLE == True: # we are assuming that hevc_nvenc is also available if this is
        categorized_encoding_options.append((PRESET_GROUP_NVENC, NVENC_encs))
    if len(VAAPI_encs) > 0 and H_264_VAAPI_AVAILABLE == True:
        categorized_encoding_options.append((PRESET_GROUP_VAAPI, VAAPI_encs))
    if len(MPEG_encs) > 0:
        categorized_encoding_options.append((PRESET_GROUP_MPEG, MPEG_encs))
    if len(OGG_ETC_encs) > 0:
        categorized_encoding_options.append(("Ogg, WebM, ProRes, DNxHD", OGG_ETC_encs))
    if len(LOSSLESS_encs) > 0:
        categorized_encoding_options.append((PRESET_GROUP_LOSSLESS, LOSSLESS_encs))
    if len(IMG_SEQ_encs) > 0:
        categorized_encoding_options.append((PRESET_GROUP_IMAGE_SEQUENCE, IMG_SEQ_encs))
    if len(ALPHA_encs) > 0:
        categorized_encoding_options.append((PRESET_GROUP_ALPHA, ALPHA_encs))
    if len(AUDIO_encs) > 0:
        categorized_encoding_options.append((PRESET_GROUP_AUDIO, AUDIO_encs))

    # Proxy encoding
    proxy_encoding_nodes = render_encoding_doc.getElementsByTagName(PROXY_ENCODING_OPTION)
    found_proxy_encodings = []
    for proxy_node in proxy_encoding_nodes:
        proxy_encoding_option = EncodingOption(proxy_node)
        if proxy_encoding_option.supported:
            found_proxy_encodings.append(proxy_encoding_option)
        else:
            print("proxy encoding " + proxy_encoding_option.name + " NOT AVAILABLE.")

    global proxy_encodings
    proxy_encodings = found_proxy_encodings

def _test_command(bash_args_list):
    process = subprocess.Popen(bash_args_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out, err = process.communicate()
    return process.returncode
        
def get_default_render_consumer(file_path, profile):
    return get_render_consumer_for_encoding_and_quality(file_path, profile, 0, 10) # values get their meaning from /res/renderencoding.xml
                                                                                    # first <encodingoption> with 10th quality option
                                                                                    # should be H.264 with 10000 kb/s
    
def get_render_consumer_for_encoding_and_quality(file_path, profile, enc_opt_index, quality_opt_index):
    args_vals_list = get_args_vals_tuples_list_for_encoding_and_quality(profile,
                                                                       enc_opt_index,
                                                                       quality_opt_index)
        
    return get_mlt_render_consumer(file_path, profile, args_vals_list)

def get_render_consumer_for_encoding(file_path, profile, encoding_option):
    # Encoding options key, value list
    args_vals_list = encoding_option.get_args_vals_tuples_list(profile)

    return get_mlt_render_consumer(file_path, profile, args_vals_list)

def get_render_consumer_for_text_buffer(file_path, profile, buf):
    args_vals_list, error = get_ffmpeg_opts_args_vals_tuples_list(buf)
    if error != None:
        return (None, error)

    render_consumer = get_mlt_render_consumer(file_path, profile, args_vals_list)
    return (render_consumer, None)

def get_img_seq_render_consumer(file_path, profile, encoding_option):
    #render_path = "%1/%2-%05d.%3" + file_path
    args_vals_list = encoding_option.get_args_vals_tuples_list(profile)
    
    vcodec = None
    for arg_val in args_vals_list:
        arg, val = arg_val
        if arg == "vcodec":
            vcodec = val

    render_path = os.path.dirname(file_path) + "/" + os.path.basename(file_path).split(".")[0] + "_%05d." + encoding_option.extension
    
    consumer = mlt.Consumer(profile, "avformat", str(render_path))
    # Jan-2017 - SvdB - perf_value instead of -1
    if performance_settings_enabled == True:
        if editorpersistance.prefs.perf_drop_frames == True:
            perf_value = 1 * editorpersistance.prefs.perf_render_threads
        else:
            perf_value = -1 * editorpersistance.prefs.perf_render_threads
        consumer.set("real_time", perf_value)
    else:
        consumer.set("real_time", -1)
    consumer.set("rescale", "bicubic")
    consumer.set("vcodec", str(vcodec))

    return consumer

def get_img_seq_render_consumer_codec_ext(file_path, profile, vcodec, ext):
    render_path = os.path.dirname(file_path) + "/" + os.path.basename(file_path).split(".")[0] + "_%05d." + ext
    
    consumer = mlt.Consumer(profile, "avformat", str(render_path))
    # Jan-2017 - SvdB - perf_value instead of -1
    if performance_settings_enabled == True:
        if editorpersistance.prefs.perf_drop_frames == True:
            perf_value = 1 * editorpersistance.prefs.perf_render_threads
        else:
            perf_value = -1 * editorpersistance.prefs.perf_render_threads
        consumer.set("real_time", perf_value)
    else:
        consumer.set("real_time", -1)
    consumer.set("rescale", "bicubic")
    consumer.set("vcodec", str(vcodec))

    return consumer
    
def get_mlt_render_consumer(file_path, profile, args_vals_list):
    consumer = mlt.Consumer(profile, "avformat", str(file_path))
    # Jan-2017 - SvdB - perf_value instead of -1
    if performance_settings_enabled == True:
        if editorpersistance.prefs.perf_drop_frames == True:
            perf_value = 1 * editorpersistance.prefs.perf_render_threads
        else:
            perf_value = -1 * editorpersistance.prefs.perf_render_threads
        consumer.set("real_time", perf_value)
    else:
        consumer.set("real_time", -1)
    consumer.set("rescale", "bicubic")

    args_msg = ""
    for arg_val in args_vals_list:
        k, v = arg_val
        consumer.set(str(k), str(v))
        args_msg = args_msg + str(k) + "="+ str(v) + ", "
        
    args_msg = args_msg.strip(", ")

    return consumer

def get_args_vals_tuples_list_for_encoding_and_quality(profile, enc_opt_index, quality_opt_index):
    encoding_option = encoding_options[enc_opt_index]
    if quality_opt_index >= 0:
        quality_option = encoding_option.quality_options[quality_opt_index]
    else:
        quality_option = None

    args_vals_list = encoding_option.get_args_vals_tuples_list(profile, quality_option)
    
    # Quality options  key, value list
    if quality_option != None:
        for k, v in quality_option.add_map.items():
            args_vals_list.append((str(k), str(v)))
    
    return args_vals_list

def get_video_non_user_encodigs():
    video_non_user_encs = []
    for enc in non_user_encodings:
        if enc.type != "audio":
            video_non_user_encs.append(enc)

    return video_non_user_encs

def get_ffmpeg_opts_args_vals_tuples_list(buf):
    end = buf.get_end_iter()
    arg_vals = []
    for i in range(0, buf.get_line_count()):
        line_start = buf.get_iter_at_line(i)
        if i == buf.get_line_count() - 1:
            line_end = end
        else:
            line_end = buf.get_iter_at_line(i + 1)
        av_tuple, error = _parse_line(line_start, line_end, buf)
        if error != None:
            errs_str = _("Error on line ") + str(i + 1) + ": " + error + _("\nLine contents: ") \
                       + buf.get_text(line_start, line_end, include_hidden_chars=False)
            return (None, errs_str)
        if av_tuple != None:
            arg_vals.append(av_tuple)
    
    return (arg_vals, None)

def _parse_line(line_start, line_end, buf):
    line = buf.get_text(line_start, line_end, include_hidden_chars=False)
    if len(line) == 0:
        return (None, None)
    if line.find("=") == -1:
        return (None, _("No \'=\' found."))
    sides = line.split("=")
    if len(sides) != 2:
        k = sides[0].strip()
        rest = sides[1:len(sides)]
        v = ""
        for token in rest:
            v = v + token + "="
        v = v.strip("=")
        v = v.strip()
    else:
        k = sides[0].strip()
        v = sides[1].strip()
    if len(k) == 0:
        return (None, _("Arg name token is empty."))
    if len(v) == 0:
        return (None, _("Arg value token is empty."))
    if k.find(" ") != -1:
        return (None,  _("Whitespace in Arg name."))
    if v.find(" ") != -1:
        return (None,  _("Whitespace in Arg value."))

    return ((k,v), None)

# Convenience function needed because FileRenderPlayer no longer stops on last
# frame with 'wait_for_producer_end_stop' set True and naked producer as producer.
# With tractor we get full length rendered and player stops correctly.
def get_producer_as_tractor(producer, last_frame):
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track0 = mlt.Playlist()
    multitrack.connect(track0, 0)
    track0.insert(producer, 0, 0, last_frame)
    return tractor
            

class FileRenderPlayer(threading.Thread):
    def __init__(self, file_name, producer, consumer, start_frame, stop_frame):
        self.file_name = file_name
        self.producer = producer
        self.consumer = consumer
        self.start_frame = start_frame
        self.stop_frame = stop_frame
        self.stopped = False
        self.wait_for_producer_end_stop = True
        self.running = False
        self.has_started_running = False
        self.do_consumer_position_wait = True
        print("FileRenderPlayer started, start frame: " + str(self.start_frame) + ", stop frame: " + str(self.stop_frame))
        self.consumer_pos_stop_add = 1 # HACK!!! File renders work then this is one, screenshot render requires this to be 2 to work 
        threading.Thread.__init__(self)

    def run(self):
        # Uncomment to get debug printing.
        #import sys
        #so = se = open("/home/janne/log_renderplayer", 'w', buffering=1)
        #sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
        #os.dup2(so.fileno(), sys.stdout.fileno())
        
        self.consumer.set("plays", 1) # maybe not strictly necessary but default value here seems to  be 'None' which is wrong.
        
        self.running = True
        self.has_started_running = True
        self.connect_and_start()

        while self.running: # set false at shutdown() for abort

            if self.producer.frame() >= self.stop_frame:
                # This method of stopping makes sure that whole producer is rendered and written to disk
                # Used when producer out frame is last frame.
                if self.wait_for_producer_end_stop:

                    while self.producer.get_speed() > 0:
                        time.sleep(0.2)
                    while not self.consumer.is_stopped():
                        time.sleep(0.2)
                    
                # This method of stopping stops producer
                # and waits for consumer to reach that frame.
                # Used when producer out frame is NOT last frame.
                else:
                    self.producer.set_speed(0)
                    last_frame = self.producer.frame()
                    if self.do_consumer_position_wait == True:
                        while self.consumer.position() + self.consumer_pos_stop_add < last_frame:
                            time.sleep(0.2)

                    self.consumer.stop()
                                        
                self.running = False

            time.sleep(0.1)

        print("FileRenderPlayer stopped, producer frame: " + str(self.producer.frame()))

        self.stopped = True
                
    def shutdown(self):
        self.consumer.stop()
        self.producer.set_speed(0)
        self.running = False

    def connect_and_start(self):
        self.consumer.connect(self.producer)
        self.producer.set_speed(0)
        self.producer.seek(self.start_frame)
        self.producer.set_speed(1)
        self.consumer.start()

    def get_render_fraction(self):
        render_length = self.stop_frame - self.start_frame + 1
        if (self.producer.get_length() - 1) < 1:
            render_fraction = 1.0
        else:
            current_frame = self.producer.frame() - self.start_frame
            render_fraction = (float(current_frame)) / (float(render_length))
        if render_fraction > 1.0:
            render_fraction = 1.0
        return render_fraction


class XMLRenderPlayer(threading.Thread):
    def __init__(self, file_name, callback, data, rendered_sequence, project, player):
        self.file_name = file_name
        self.render_done_callback = callback
        self.data = data
        self.current_playback_frame = 0
        self.rendered_sequence = rendered_sequence
        self.project = project
        self.player = player
        
        threading.Thread.__init__(self)

    def run(self):
        print("Starting XML render")
        player = self.player
        
        # Don't try anything if somehow this was started 
        # while timeline rendering is running
        if player.is_rendering:
            print("Can't render XML when another render is already running!")
            return

        # Stop all playback before producer is disconnected
        self.current_playback_frame = player.producer.frame()
        player.ticker.stop_ticker()
        player.consumer.stop()
        player.producer.set_speed(0)
        player.producer.seek(0)
        
        # Wait until producer is at start
        while player.producer.frame() != 0:
            time.sleep(0.1)
        
        # Get render producer
        timeline_producer = self.rendered_sequence.tractor

        # Get render consumer
        xml_consumer = mlt.Consumer(self.project.profile, "xml", str(self.file_name))

        # Connect and start rendering
        xml_consumer.connect(timeline_producer)
        xml_consumer.start()
        timeline_producer.set_speed(1)

        # Wait until done
        while xml_consumer.is_stopped() == False:
            print("In XML render wait loop...")
            time.sleep(0.1)
    
        print("XML render done")

        # Get app player going again
        player.connect_and_start()
        player.seek_frame(0)

        self.render_done_callback(self.data)


class XMLCompoundRenderPlayer(threading.Thread):
    def __init__(self, file_name, media_name, callback, tractor, project):
        self.file_name = file_name
        self.media_name = media_name
        self.render_done_callback = callback
        self.tractor = tractor
        self.project = project

        threading.Thread.__init__(self)

    def run(self):
        tractor = self.tractor
        tractor.set_speed(0)
        tractor.seek(0)
        
        # Wait until producer is at start
        while tractor.frame() != 0:
            time.sleep(0.1)

        # Get render consumer
        xml_consumer = mlt.Consumer(self.project.profile, "xml", str(self.file_name))

        # Connect and start rendering
        xml_consumer.connect(tractor)
        xml_consumer.start()
        tractor.set_speed(1)

        # Wait until done
        while xml_consumer.is_stopped() == False:
            print("In XML render wait loop...")
            time.sleep(0.1)
    
        print("XML compound clip render done")

        self.render_done_callback(self.file_name, self.media_name)


class ProgressWindowThread(threading.Thread):
    def __init__(self, dialog, progress_bar, clip_renderer, callback):
        self.dialog = dialog
        self.progress_bar = progress_bar
        self.clip_renderer = clip_renderer
        self.callback = callback
        threading.Thread.__init__(self)
    
    def run(self):        
        self.running = True
        
        while self.running:         
            render_fraction = self.clip_renderer.get_render_fraction()
            Gdk.threads_enter()
            self.progress_bar.set_fraction(render_fraction)
            pros = int(render_fraction * 100)
            self.progress_bar.set_text(str(pros) + "%")
            Gdk.threads_leave()
            if self.clip_renderer.stopped == True:
                Gdk.threads_enter()
                self.progress_bar.set_fraction(1.0)
                self.progress_bar.set_text("Render Complete!")
                self.callback(self.dialog, 0)
                Gdk.threads_leave()
                self.running = False

            time.sleep(0.33)
