# Getting stacktrace with gdb #

If the problem when running Flowblade happens when native code is executed, the information needed to debug the issue can usually be collected using a program called **gdb**.


## Steps ##

**1. Install gdb debugger.**

To install **gdb** give command on terminal:

```
sudo apt-get install gdb
```
and give your password to allow install to take place.

**2. Run gdb on python interpreter running Flowblade**

On terminal give command:

```
gdb python
```

This starts gdb running python interpreter. Now you need to run Flowblade inside debugger. You'll see text (gdb), this is the command prompt for debugger. Now give command:

```
run /usr/bin/flowblade
```

This runs Flowblade. After program has crashed give command:

```
backtrace
```

**3. Copy/paste output to a text file**

Use mouse to select printed output on terminal, and press SHIFT+CONTROL+C to copy text.

Open a text file and paste text - with CONTROL+V or  SHIFT+CONTROL+V - into it, and provide the text file as an attachment with the Issue report or comment.
