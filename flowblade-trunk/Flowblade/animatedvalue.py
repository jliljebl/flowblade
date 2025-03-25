"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2025 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

 # ------------------------------------------------------- AnimatedValue 

class AnimatedValue:
    
    def __init__(self, keyframes, active_index=0):
        self.keyframes = keyframes
        self.active_index = active_index
    
    def get_state(self):
        """
        Called after actions to get results.
        """
        return (self.keyframes, self.active_index)
    
    def add_keyframe(self, frame, value, kf_type):
        kf_index_on_frame = self.frame_has_keyframe(frame)
        if kf_index_on_frame != -1:
            # Trying add on top of existing keyframe makes it active
            self.active_kf_index = kf_index_on_frame
            return

        # Insert if not after last
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value, kf_type = self.keyframes[i]
            if kf_frame > frame:
                #prev_frame, prev_value = self.keyframes[i - 1]
                self.keyframes.insert(i, (frame, value, kf_type))
                self.active_kf_index = i
                return
        
        # Append
        self.keyframes.append((frame, value, kf_type))
        self.active_kf_index = len(self.keyframes) - 1

    def delete_active_keyframe(self):
        if self.active_kf_index == 0:
            # keyframe frame 0 cannot be removed
            return
        self.keyframes.pop(self.active_kf_index)
        self.active_kf_index -= 1
        if self.active_kf_index < 0:
            self.active_kf_index = 0

    def frame_has_keyframe(self, frame):
        """
        Returns index of keyframe if frame has keyframe or -1 if it doesn't.
        """
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value, kf_type = self.keyframes[i]
            if frame == kf_frame:
                return i

        return -1
            
# ------------------------------------------------ Utility funcs
# These all need to be doubles.
def _catmull_rom_interpolate(self, y0, y1, y2, y3, t):
    t2 = t * t
    a0 = -0.5 * y0 + 1.5 * y1 - 1.5 * y2 + 0.5 * y3
    a1 = y0 - 2.5 * y1 + 2 * y2 - 0.5 * y3
    a2 = -0.5 * y0 + 0.5 * y2
    a3 = y1
    return a0 * t * t2 + a1 * t2 + a2 * t + a3
