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
from __future__ import print_function

import gettext
import locale
import os

import respaths
import editorpersistance
import editorstate

APP_NAME = "flowblade"
lang = None

filter_groups = {}
filter_names = {}
param_names = {}
combo_options = {}

def init_languages():
    langs = []
    lc, encoding = locale.getdefaultlocale()
    if (lc):
        langs = [lc]
    print("Locale:", lc)

    language = os.environ.get('LANGUAGE', None)
    if (language):
        langs += language.split(":")

    if editorstate.app_running_from == editorstate.RUNNING_FROM_INSTALLATION:
        # Use /usr/share/locale first if available and running from installation
        # Look for installed translation in distro install
        # Were using Russian as test language
        if os.path.isfile("/usr/share/locale/ru/LC_MESSAGES/flowblade.mo"): # fi is the translation controlled by program author
            print("Found translations at /usr/share/locale, using those.")
            locale_path = "/usr/share/locale/"
        #  Look for installed translations in flatpak install 
        elif os.path.isfile("/app/share/flowblade/Flowblade/locale/ru/LC_MESSAGES/flowblade.mo"): # fi is the translation controlled by program author
            print("Found translations at /app/share/flowblade/Flowblade/locale, using those.")
            locale_path = "/app/share/flowblade/Flowblade/locale"
        else:
            print("Translations at /usr/share/locale were not found, using program root directory translations.")
            locale_path = respaths.LOCALE_PATH
    else:
        # Use translations in program folder first if NOT running from installation
        # Were using Russian as test language
        locale_file = respaths.LOCALE_PATH + "ru/LC_MESSAGES/flowblade.mo"
        if os.path.isfile(locale_file): # fi is the translation controlled by program author
            print("Found translations at " +  respaths.LOCALE_PATH + ", using those.")
            locale_path = respaths.LOCALE_PATH
        else:
            print("Translations at " + locale_file + " were not found, using /usr/share/locale translations.")
            locale_path = "/usr/share/locale/"

    gettext.bindtextdomain(APP_NAME, locale_path)
    gettext.textdomain(APP_NAME)

    # Get the language to use
    global lang
    if editorpersistance.prefs.use_english_always == True:
        lang_code = "English"
        editorpersistance.prefs.use_english_always = False
        editorpersistance.prefs.force_language = "English"
        editorpersistance.save()
    else:
        lang_code = editorpersistance.prefs.force_language
    
    if editorpersistance.prefs.force_language == "English":
        print("Force use English.")
        lang = gettext.translation(APP_NAME, locale_path, languages=["dummy"], fallback=True)
    elif editorpersistance.prefs.force_language != "None":
        print("Force use ", editorpersistance.prefs.force_language)
        lang = gettext.translation(APP_NAME, locale_path, languages=[str(editorpersistance.prefs.force_language)], fallback=True)
    else:
        print("Use OS locale language.")
        lang = gettext.translation(APP_NAME, locale_path, languages=langs, fallback=True)

    # Un-comment for translations tests
    #lang = gettext.translation(APP_NAME, locale_path, languages=["it"], fallback=True)

    lang.install(APP_NAME) # makes _() a build-in available in all modules without imports

def get_filter_name(f_name):
    try:
        return filter_names[f_name]
    except KeyError:
        return f_name

def get_filter_group_name(group_name):
    try:
        return filter_groups[group_name]
    except:
        return group_name

def get_param_name(name):
    try:
        return param_names[name]
    except KeyError:
        return name

def get_combo_option(c_opt):
    try:
        return combo_options[c_opt]
    except KeyError:
        return c_opt

def load_filters_translations():

    # filter group names
    global filter_groups
    filter_groups["Color"] = _("Color")
    filter_groups["Color Effect"] = _("Color Effect")
    filter_groups["Audio"] = _("Audio")
    filter_groups["Audio Filter"] = _("Audio Filter")
    filter_groups["Blur"] = _("Blur")
    filter_groups["Distort"] = _("Distort")
    filter_groups["Alpha"] = _("Alpha")
    filter_groups["Movement"] = _("Movement")
    filter_groups["Transform"] = _("Transform")
    filter_groups["Edge"] = _("Edge")
    filter_groups["Fix"] = _("Fix")
    filter_groups["Artistic"] = _("Artistic")

    # filter names
    global filter_names
    filter_names["Alpha Gradient"] = _("Alpha Gradient")
    filter_names["Crop"] = _("Crop")
    filter_names["Alpha Shape"]= _("Alpha Shape")

    filter_names["Volume"]= _("Volume")
    filter_names["Pan"]= _("Pan")
    filter_names["Pan Keyframed"]= _("Pan Keyframed")
    filter_names["Mono to Stereo"]= _("Mono to Stereo")
    filter_names["Swap Channels"]= _("Swap Channels")

    filter_names["Pitchshifter"]= _("Pitchshifter")
    filter_names["Distort - Barry's Satan"]= _("Distort - Barry's Satan")
    filter_names["Frequency Shift - Bode/Moog"]= _("Frequency Shift - Bode/Moog")
    filter_names["Equalize - DJ 3-band"]= _("Equalize - DJ 3-band")
    filter_names["Flanger - DJ"]= _("Flanger - DJ")
    filter_names["Declipper"]= _("Declipper")
    filter_names["Delayorama"]= _("Delayorama")
    filter_names["Distort - Diode Processor"]= _("Distort - Diode Processor")
    filter_names["Distort - Foldover"]= _("Distort - Foldover")
    filter_names["Highpass - Butterworth"]= _("Highpass - Butterworth")
    filter_names["Lowpass - Butterworth"]= _("Lowpass - Butterworth")
    filter_names["GSM Simulator"]= _("GSM Simulator")
    filter_names["Reverb - GVerb"]= _("Reverb - GVerb")
    filter_names["Noise Gate"]= _("Noise Gate")
    filter_names["Bandpass"]= _("Bandpass")
    filter_names["Pitchscaler - High Quality"]= _("Pitchscaler - High Quality")
    filter_names["Equalize - Multiband"]= _("Equalize - Multiband")
    filter_names["Reverb - Plate"]= _("Reverb - Plate")
    filter_names["Distort - Pointer cast"]= _("Distort - Pointer cast")
    filter_names["Rate Shifter"]= _("Rate Shifter")
    filter_names["Signal Shifter"]= _("Signal Shifter")
    filter_names["Distort - Sinus Wavewrap"]= _("Distort - Sinus Wavewrap")
    filter_names["Vinyl Effect"]= _("Vinyl Effect")
    filter_names["Chorus - Multivoice"]= _("Chorus - Multivoice")

    filter_names["Charcoal"]= _("Charcoal")
    filter_names["Glow"]= _("Glow")
    filter_names["Old Film"]= _("Old Film")
    filter_names["Scanlines"]= _("Scanlines")
    filter_names["Cartoon"]= _("Cartoon")

    filter_names["Pixelize"]= _("Pixelize")
    filter_names["Blur"]= _("Blur")
    filter_names["Grain"]= _("Grain")

    filter_names["Grayscale"]= _("Grayscale")
    filter_names["Contrast"]= _("Contrast")
    filter_names["Saturation"]= _("Saturation")
    filter_names["Invert"]= _("Invert")
    filter_names["Hue"]= _("Hue")
    filter_names["Brightness"]= _("Brightness")
    filter_names["Sepia"]= _("Sepia")
    filter_names["Tint"]= _("Tint")
    filter_names["White Balance"]= _("White Balance")
    filter_names["Levels"]= _("Levels")

    filter_names["Color Clustering"]= _("Color Clustering")
    filter_names["Chroma Hold"]= _("Chroma Hold")
    filter_names["Three Layer"]= _("Three Layer")
    filter_names["Threshold0r"]= _("Threshold0r")
    filter_names["Technicolor"]= _("Technicolor")
    filter_names["Primaries"]= _("Primaries")
    filter_names["Color Distance"]= _("Color Distance")
    filter_names["Threshold"]= _("Threshold")

    filter_names["Waves"]= _("Waves")
    filter_names["Lens Correction"]= _("Lens Correction")
    filter_names["Flip"]= _("Flip")
    filter_names["Mirror"]= _("Mirror")
    filter_names["V Sync"]= _("V Sync")

    filter_names["Edge Glow"]= _("Edge Glow")
    filter_names["Sobel"]= _("Sobel")

    filter_names["Denoise"]= _("Denoise")
    filter_names["Sharpness"]= _("Sharpness")
    filter_names["Letterbox"]= _("Letterbox")

    filter_names["Baltan"]= _("Baltan")
    filter_names["Vertigo"]= _("Vertigo")
    filter_names["Nervous"]= _("Nervous")
    filter_names["Freeze"]= _("Freeze")

    filter_names["Rotate"]= _("Rotate")
    filter_names["Shear"]= _("Shear")
    filter_names["Translate"]= _("Translate")

    # 0.8 added
    filter_names["Color Select"]= _("Color Select")
    filter_names["Alpha Modify"]= _("Alpha Modify")
    filter_names["Spill Supress"]= _("Spill Supress")
    filter_names["RGB Noise"]= _("RGB Noise")
    filter_names["Box Blur"]= _("Box Blur")
    filter_names["IRR Blur"]= _("IRR Blur")
    filter_names["Color Halftone"]= _("Color Halftone")
    filter_names["Dither"]= _("Dither")
    filter_names["Vignette"]= _("Vignette")
    filter_names["Vignette Advanced"]= _("Vignette Advanced")
    filter_names["Emboss"]= _("Emboss")
    filter_names["3 Point Balance"]= _("3 Point Balance")
    filter_names["Colorize"]= _("Colorize")
    filter_names["Brightness Keyframed"]= _("Brightness Keyframed")
    filter_names["RGB Adjustment"]= _("RGB Adjustment")
    filter_names["Color Tap"]= _("Color Tap")
    filter_names["Posterize"]= _("Posterize")
    filter_names["Soft Glow"]= _("Soft Glow")
    filter_names["Newspaper"]= _("Newspaper")

    # 0.16 added
    filter_names["Luma Key"] = _("Luma Key")
    filter_names["Chroma Key"] = _("Chroma Key")
    filter_names["Affine"] = _("Affine")
    filter_names["Color Adjustment"] = _("Color Adjustment")
    filter_names["Color Grading"] = _("Color Grading")
    filter_names["Curves"] = _("Curves")
    filter_names["Lift Gain Gamma"] = _("Lift Gain Gamma")
    filter_names["Image Grid"] = _("Image Grid")

    # Later
    filter_names["Color Lift Gain Gamma"] = _("Color Lift Gain Gamma")
    filter_names["Color Channel Mixer"] = _("Color Channel Mixer")
    filter_names["Lens Correction AV"] = _("Lens Correction AV")
    filter_names["Perspective"] = _("Perspective")
    filter_names["Translate"] = _("Translate")
    filter_names["Lut3D"] = _("Lut3D")
    filter_names["Normalize"] = _("Normalize")
    filter_names["File Luma to Alpha"] = _("File Luma to Alpha") 
    filter_names["Gradient Tint"] = _("Gradient Tint")
    
    # param names
    global param_names

    # param names for filters
    param_names["Position"] = _("Position")
    param_names["Grad width"] = _("Grad width")
    param_names["Tilt"] = _("Tilt")
    param_names["Min"] = _("Min")
    param_names["Max"] = _("Max")
    param_names["Left"] = _("Left")
    param_names["Right"] = _("Right")
    param_names["Top"] = _("Top")
    param_names["Bottom"] = _("Bottom")
    param_names["Shape"] = _("Shape")
    param_names["Pos X"] = _("Pos X")
    param_names["Pos Y"] = _("Pos Y")
    param_names["Size X"] = _("Size X")
    param_names["Size Y"] = _("Size Y")
    param_names["Tilt"] = _("Tilt")
    param_names["Trans. Width"] = _("Trans. Width")
    param_names["Volume"] = _("Volume")
    param_names["Left/Right"] = _("Left/Right")
    param_names["Left/Right"] = _("Left/Right")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Pitch Shift"] = _("Pitch Shift")
    param_names["Buffer Size"] = _("Buffer Size")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Decay Time(samples)"] = _("Decay Time(samples)")
    param_names["Knee Point(dB)"] = _("Knee Point(dB)")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Frequency shift"] = _("Frequency shift")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Low Gain(dB)"] = _("Low Gain(dB)")
    param_names["Mid Gain(dB)"] = _("Mid Gain(dB)")
    param_names["High Gain(dB)"] = _("High Gain(dB)")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Oscillation period(s)"] = _("Oscillation period(s)")
    param_names["Oscillation depth(ms)"] = _("Oscillation depth(ms)")
    param_names["Feedback%"] = _("Feedback%")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Random seed"] = _("Random seed")
    param_names["Input Gain(dB)"] = _("Input Gain(dB)")
    param_names["Feedback(%)"] = _("Feedback(%)")
    param_names["Number of taps"] = _("Number of taps")
    param_names["First Delay(s)"] = _("First Delay(s)")
    param_names["Delay Range(s)"] = _("Delay Range(s)")
    param_names["Delay Change"] = _("Delay Change")
    param_names["Delay Random(%)"] = _("Delay Random(%)")
    param_names["Amplitude Change"] = _("Amplitude Change")
    param_names["Amplitude Random(%)"] = _("Amplitude Random(%)")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Amount"] = _("Amount")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Drive"] = _("Drive")
    param_names["Skew"] = _("Skew")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Cutoff Frequency(Hz)"] = _("Cutoff Frequency(Hz)")
    param_names["Resonance"] = _("Resonance")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Cutoff Frequency(Hz)"] = _("Cutoff Frequency(Hz)")
    param_names["Resonance"] = _("Resonance")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Passes"] = _("Passes")
    param_names["Error Rate"] = _("Error Rate")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Roomsize"] = _("Roomsize")
    param_names["Reverb time(s)"] = _("Reverb time(s)")
    param_names["Damping"] = _("Damping")
    param_names["Input bandwith"] = _("Input bandwith")
    param_names["Dry signal level(dB)"] = _("Dry signal level(dB)")
    param_names["Early reflection level(dB)"] = _("Early reflection level(dB)")
    param_names["Tail level(dB)"] = _("Tail level(dB)")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["LF keyfilter(Hz)"] = _("LF keyfilter(Hz)")
    param_names["HF keyfilter(Hz)"] = _("HF keyfilter(Hz)")
    param_names["Threshold(dB)"] = _("Threshold(dB)")
    param_names["Attack(ms)"] = _("Attack(ms)")
    param_names["Hold(ms)"] = _("Hold(ms)")
    param_names["Decay(ms)"] = _("Decay(ms)")
    param_names["Range(dB)"] = _("Range(dB)")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Center Frequency(Hz)"] = _("Center Frequency(Hz)")
    param_names["Bandwidth(Hz)"] = _("Bandwidth(Hz)")
    param_names["Stages"] = _("Stages")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Pitch-coefficient"] = _("Pitch-coefficient")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["50Hz gain"] = _("50Hz gain")
    param_names["100Hz gain"] = _("100Hz gain")
    param_names["156Hz gain"] = _("156Hz gain")
    param_names["220Hz gain"] = _("220Hz gain")
    param_names["311Hz gain"] = _("311Hz gain")
    param_names["440Hz gain"] = _("440Hz gain")
    param_names["622Hz gain"] = _("622Hz gain")
    param_names["880Hz gain"] = _("880Hz gain")
    param_names["1250Hz gain"] = _("1250Hz gain")
    param_names["1750Hz gain"] = _("1750Hz gain")
    param_names["2500Hz gain"] = _("2500Hz gain")
    param_names["3500Hz gain"] = _("3500Hz gain")
    param_names["5000Hz gain"] = _("5000Hz gain")
    param_names["100000Hz gain"] = _("100000Hz gain")
    param_names["200000Hz gain"] = _("200000Hz gain")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Reverb time"] = _("Reverb time")
    param_names["Damping"] = _("Damping")
    param_names["Dry/Wet mix"] = _("Dry/Wet mix")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Effect cutoff(Hz)"] = _("Effect cutoff(Hz)")
    param_names["Dry/Wet mix"] = _("Dry/Wet mix")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Rate"] = _("Rate")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Sift"] = _("Sift")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Amount"] = _("Amount")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Year"] = _("Year")
    param_names["RPM"] = _("RPM")
    param_names["Surface warping"] = _("Surface warping")
    param_names["Cracle"] = _("Cracle")
    param_names["Wear"] = _("Wear")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["Number of voices"] = _("Number of voices")
    param_names["Delay base(ms)"] = _("Delay base(ms)")
    param_names["Voice separation(ms)"] = _("Voice separation(ms)")
    param_names["Detune(%)"] = _("Detune(%)")
    param_names["Oscillation frequency(Hz)"] = _("Oscillation frequency(Hz)")
    param_names["Output attenuation(dB)"] = _("Output attenuation(dB)")
    param_names["Dry/Wet"] = _("Dry/Wet")
    param_names["X Scatter"] = _("X Scatter")
    param_names["Y Scatter"] = _("Y Scatter")
    param_names["Scale"] = _("Scale")
    param_names["Mix"] = _("Mix")
    param_names["Invert"] = _("Invert")
    param_names["Blur"] = _("Blur")
    param_names["Delta"] = _("Delta")
    param_names["Duration"] = _("Duration")
    param_names["Bright. up"] = _("Bright. up")
    param_names["Bright. down"] = _("Bright. down")
    param_names["Bright. dur."] = _("Bright. dur.")
    param_names["Develop up"] = _("Develop up")
    param_names["Develop down"] = _("Develop down")
    param_names["Develop dur."] = _("Develop dur.")
    param_names["Triplevel"] = _("Triplevel")
    param_names["Difference Space"] = _("Difference Space")
    param_names["Block width"] = _("Block width")
    param_names["Block height"] = _("Block height")
    param_names["Size"] = _("Size")
    param_names["Noise"] = _("Noise")
    param_names["Contrast"] = _("Contrast")
    param_names["Brightness"] = _("Brightness")
    param_names["Contrast"] = _("Contrast")
    param_names["Saturation"] = _("Saturation")
    param_names["Hue"] = _("Hue")
    param_names["Brightness"] = _("Brightness")
    param_names["Brightness"] = _("Brightness")
    param_names["U"] = _("U")
    param_names["V"] = _("V")
    param_names["Black"] = _("Black")
    param_names["White"] = _("White")
    param_names["Amount"] = _("Amount")
    param_names["Neutral Color"] = _("Neutral Color")
    param_names["Input"] = _("Input")
    param_names["Input"] = _("Input")
    param_names["Gamma"] = _("Gamma")
    param_names["Black"] = _("Black")
    param_names["White"] = _("White")
    param_names["Num"] = _("Num")
    param_names["Dist. weight"] = _("Dist. weight")
    param_names["Color"] = _("Color")
    param_names["Variance"] = _("Variance")
    param_names["Threshold"] = _("Threshold")
    param_names["Red Saturation"] = _("Red Saturation")
    param_names["Yellow Saturation"] = _("Yellow Saturation")
    param_names["Factor"] = _("Factor")
    param_names["Source color"] = _("Source color")
    param_names["Threshold"] = _("Threshold")
    param_names["Amplitude"] = _("Amplitude")
    param_names["Frequency"] = _("Frequency")
    param_names["Rotate"] = _("Rotate")
    param_names["Tilt"] = _("Tilt")
    param_names["Center Correct"] = _("Center Correct")
    param_names["Edges Correct"] = _("Edges Correct")
    param_names["Flip"] = _("Flip")
    param_names["Axis"] = _("Axis")
    param_names["Invert"] = _("Invert")
    param_names["Position"] = _("Position")
    param_names["Edge Lightning"] = _("Edge Lightning")
    param_names["Edge Brightness"] = _("Edge Brightness")
    param_names["Non-Edge Brightness"] = _("Non-Edge Brightness")
    param_names["Spatial"] = _("Spatial")
    param_names["Temporal"] = _("Temporal")
    param_names["Amount"] = _("Amount")
    param_names["Size"] = _("Size")
    param_names["Border width"] = _("Border width")
    param_names["Phase Incr."] = _("Phase Incr.")
    param_names["Zoom"] = _("Zoom")
    param_names["Freeze Frame"] = _("Freeze Frame")
    param_names["Freeze After"] = _("Freeze After")
    param_names["Freeze Before"] = _("Freeze Before")
    param_names["Angle"] = _("Angle")
    param_names["transition.geometry"] = _("transition.geometry")
    param_names["Shear X"] = _("Shear X")
    param_names["Shear Y"] = _("Shear Y")
    param_names["transition.geometry"] = _("transition.geometry")
    param_names["transition.geometry"] = _("transition.geometry")
    param_names["Left"] = _("Left")
    param_names["Right"] = _("Right")
    param_names["Top"] = _("Top")
    param_names["Bottom"] = _("Bottom")
    param_names["Invert"] = _("Invert")
    param_names["Blur"] = _("Blur")
    param_names["Opacity"] = _("Opacity")
    param_names["Opacity"] = _("Opacity")
    param_names["Rotate X"] = _("Rotate X")
    param_names["Rotate Y"] = _("Rotate Y")
    param_names["Rotate Z"] = _("Rotate Z")
    # added 0.8
    param_names["Edge Mode"] = _("Edge Mode")
    param_names["Sel. Space"] = _("Sel. Space")
    param_names["Operation"] = _("Operation")
    param_names["Hard"] = _("Hard")
    param_names["Selection subspace"] = _("Selection subspace")
    param_names["R/A/Hue"] = _("R/A/Hue")
    param_names["G/B/Chroma"] = _("G/B/Chroma")
    param_names["B/I/I"] = _("B/I/I")
    param_names["Supress"] = _("Supress")
    param_names["Horizontal"] = _("Horizontal")
    param_names["Vertical"] = _("Vertical")
    param_names["Type"] = _("Type")
    param_names["Edge"] = _("Edge")
    param_names["Dot Radius"] = _("Dot Radius")
    param_names["Cyan Angle"] = _("Cyan Angle")
    param_names["Magenta Angle"] = _("Magenta Angle")
    param_names["Yellow Angle"] = _("Yellow Angle")
    param_names["Levels"] = _("Levels")
    param_names["Matrix Type"] = _("Matrix Type")
    param_names["Aspect"] = _("Aspect")
    param_names["Center Size"] = _("Center Size")
    param_names["Azimuth"] = _("Azimuth")
    param_names["Lightness"] = _("Lightness")
    param_names["Bump Height"] = _("Bump Height")
    param_names["Gray"] = _("Gray")
    param_names["Split Preview"] = _("Split Preview")
    param_names["Source on Left"] = _("Source on Left")
    param_names["Lightness"] = _("Lightness")
    param_names["Channel"] = _("Channel")
    param_names["Input black level"] = _("Input black level")
    param_names["Input white level"] = _("Input white level")
    param_names["Black output"] = _("Black output")
    param_names["White output"] = _("White output")
    param_names["Red"] = _("Red")
    param_names["Green"] = _("Green")
    param_names["Blue"] = _("Blue")
    param_names["Action"] = _("Action")
    param_names["Keep Luma"] = _("Keep Luma")
    param_names["Luma Formula"] = _("Luma Formula")
    param_names["Effect"] = _("Effect")
    param_names["Sharpness"] = _("Sharpness")
    param_names["Blend Type"] = _("Blend Type")
    # added 0.16
    param_names["Key Color"] = _("Key Color")
    param_names["Pre-Level"] = _("Pre-Level")
    param_names["Post-Level"] = _("Post-Level")
    param_names["Slope"] = _("Slope")
    param_names["Luma Band"] = _("Luma Band")
    param_names["Lift"] = _("Lift")
    param_names["Gain"] = _("Gain")
    param_names["Input White Level"] = _("Input White Level")
    param_names["Input Black Level"] = _("Input Black Level")
    param_names["Black Output"] = _("Black Output")
    param_names["White Output"] = _("White Output")
    param_names["Rows"] = _("Rows")
    param_names["Columns"] = _("Columns")
    param_names["Color Temperature"] = _("Color Temperature")
    param_names["Select .cube file"] = _("Select .cube file")
    param_names["Red Ch. Red Gain"] = _("Red Ch. Red Gain")
    param_names["Red Ch. Green Gain"] = _("Red Ch. Green Gain")
    param_names["Red Ch. Blue Gain"] = _("Red Ch. Blue Gain")
    param_names["Green Ch. Red Gain"] = _("Green Ch. Red Gain")
    param_names["Green Ch. Green Gain"] = _("Green Ch. Green Gain")
    param_names["Green Ch. Blue Gain"] = _("Green Ch. Blue Gain")
    param_names["Blue Ch. Red Gain"] = _("Blue Ch. Red Gain")
    param_names["Blue Ch. Green Gain"] = _("Blue Ch. Green Gain")
    param_names["Blue Ch. Blue Gain"] = _("Blue Ch. Blue Gain")
    param_names["Center X"] = _("Center X")
    param_names["Center Y"] = _("Center Y")
    param_names["Quad Distortion"] = _("Quad Distortion")
    param_names["Double Quad Distortion"] = _("Double Quad Distortion")
    param_names["Level"] = _("Level")
    param_names["Select .cube file"] = _("Select .cube file")
    
    # param names for compositors
    param_names["Opacity"] = _("Opacity")
    param_names["Shear X"] = _("Shear X")
    param_names["Shear Y"] = _("Shear Y")
    param_names["Distort"] = _("Distort")
    param_names["Opacity"] = _("Opacity")
    param_names["Wipe Type"] = _("Wipe Type")
    param_names["Invert"] = _("Invert")
    param_names["Softness"] = _("Softness")
    param_names["Wipe Amount"] = _("Wipe Amount")
    param_names["Wipe Type"] = _("Wipe Type")
    param_names["Invert"] = _("Invert")
    param_names["Softness"] = _("Softness")
    param_names["Fade Out Length"] = _("Fade Out Length")
    param_names["Fade In Length"] = _("Fade In Length")
    param_names["Wipe Direction"] = _("Wipe Direction")
    param_names["Blend Mode"] = _("Blend Mode")
    param_names["Target Loudness"] = _("Blend Mode")
    param_names["Analysis Length"] = _("Analysis Length")
    param_names["Max Gain"] = _("Max Gain")
    param_names["Min Mode"] = _("Min Mode")
    param_names["Select file"] = _("Select file")
    param_names["Smooth"] = _("Smooth")
    param_names["Radius"] = _("Radius")
    param_names["Fade"] = _("Fade")
    param_names["Start Opacity"] = _("Start Opacity")
    param_names["End Opacity"] = _("End Opacity")
    param_names["End Color"] = _("End Color")
    param_names["Start Color"] = _("Start Color")
    param_names["Start X"] = _("Start X")
    param_names["Start Y"] = _("Start Y")
    param_names["End Y"] = _("End Y")
    param_names["End X"] = _("End X")
    param_names["Gradient Type"] = _("Gradient Type")
    param_names["Radial Offset"] = _("Radial Offset")
    
    
    # Combo options
    global combo_options
    combo_options["Shave"] = _("Shave")
    combo_options["Rectangle"] = _("Rectangle")
    combo_options["Ellipse"] = _("Ellipse")
    combo_options["Triangle"] = _("Triangle")
    combo_options["Box"] = _("Box")
    combo_options["Diamond"] = _("Diamond")
    combo_options["Shave"] = _("Shave")
    combo_options["Shrink Hard"] = _("Shrink Hard")
    combo_options["Shrink Soft"] = _("Shrink Soft")
    combo_options["Grow Hard"] = _("Grow Hard")
    combo_options["Grow Soft"] = _("Grow Soft")
    combo_options["RGB"] = _("RGB")
    combo_options["ABI"] = _("ABI")
    combo_options["HCI"] = _("HCI")
    combo_options["Hard"] = _("Hard")
    combo_options["Fat"] = _("Fat")
    combo_options["Normal"] = _("Normal")
    combo_options["Skinny"] = _("Skinny")
    combo_options["Ellipsoid"] = _("Ellipsoid")
    combo_options["Diamond"] = _("Diamond")
    combo_options["Overwrite"] = _("Overwrite")
    combo_options["Max"] = _("Max")
    combo_options["Min"] = _("Min")
    combo_options["Add"] = _("Add")
    combo_options["Subtract"] = _("Subtract")
    combo_options["Green"] = _("Green")
    combo_options["Blue"] = _("Blue")
    combo_options["Sharper"] = _("Sharper")
    combo_options["Fuzzier"] = _("Fuzzier")
    combo_options["Luma"] = _("Luma")
    combo_options["Red"] = _("Red")
    combo_options["Green"] = _("Green")
    combo_options["Blue"] = _("Blue")
    combo_options["Add Constant"] = _("Add Constant")
    combo_options["Change Gamma"] = _("Change Gamma")
    combo_options["Multiply"] = _("Multiply")
    combo_options["XPro"] = _("XPro")
    combo_options["OldPhoto"] = _("OldPhoto")
    combo_options["Sepia"] = _("Sepia")
    combo_options["Heat"] = _("Heat")
    combo_options["XRay"] = _("XRay")
    combo_options["RedGreen"] = _("RedGreen")
    combo_options["YellowBlue"] = _("YellowBlue")
    combo_options["Esses"] = _("Esses")
    combo_options["Horizontal"] = _("Horizontal")
    combo_options["Vertical"] = _("Vertical")
    combo_options["Shadows"] = _("Shadows")
    combo_options["Midtones"] = _("Midtones")
    combo_options["Highlights"] = _("Highlights")
    combo_options["Forward"] = _("Forward")
    combo_options["Backward"] = _("Backward")
    combo_options["Add"] = _("Add")
    combo_options["Saturate"] = _("Saturate")
    combo_options["Multiply"] = _("Multiply")    
    combo_options["Screen"] = _("Screen")   
    combo_options["Overlay"] = _("Overlay")
    combo_options["Darken"] = _("Darken")
    combo_options["Lighten"] = _("Lighten")
    combo_options["ColorDodge"] = _("ColorDodge")
    combo_options["Colorburn"] = _("Colorburn")
    combo_options["Hardlight"] = _("Hardlight")
    combo_options["Softlight"] = _("Softlight")
    combo_options["Difference"] = _("Difference")
    combo_options["Exclusion"] = _("Exclusion")
    combo_options["HSLHue"] = _("HSLHue")
    combo_options["HSLSaturation"] = _("HSLSaturation")
    combo_options["HSLColor"] = _("HSLColor")
    combo_options["HSLLuminosity"] = _("HSLLuminosity")
    combo_options["Cos"] = _("Cos")
    combo_options["Linear"] = _("Linear")
    combo_options["Radial"] = _("Radial")
