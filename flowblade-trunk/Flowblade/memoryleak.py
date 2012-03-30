"""
Most of the crashes seem to come when releasing MLT objects.

We're using this to NOT RELEASE ANYTHING that causes crashes, until we get upstream fixed.
"""

objs = []
