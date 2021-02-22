"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2021 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

#script_running_stub = \


def print_names(input_string):
    #allowed_names = {"sum": sum}
    code = compile(input_string, "<string>", "exec")
    names = []
    for name in code.co_names:
        names.append(name)
        #if name not in allowed_names:
        #    raise NameError(f"Use of {name} not allowed")

    try:
        #eval(code)
        namespace = {}
        exec(code, namespace)
        init_msg = namespace['init_script'](None)
        #init_msg = init_script(None)
        names.append(init_msg)
    except Exception as e:
        return "EORORORORO" + str(e)
    
    return names
