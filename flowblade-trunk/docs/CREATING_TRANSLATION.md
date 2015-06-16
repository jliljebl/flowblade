# Contributing a translation

If you would like to have Flowblade translated into your language you can help by contributing a translation of Flowblade in your language.

### Installing developer version of Flowblade

To create a translation you should probably first install the repository version of Flowblade so that you can edit and compile the translation file ``Flowblade.po``, see [Install Instructions](https://github.com/jliljebl/flowblade/blob/master/flowblade-trunk/docs/INSTALLING.md).

Flowblade uses the standard [GNU "gettext" utilities](http://www.gnu.org/software/gettext/manual/gettext.html) to translate the application. GNU "gettext" is a relatively complex tool, but **Flowblade provides a set of scripts that make it easier to create translations** without using "gettext" directly.

### Creating a translation ###

  * Launch repository version of Flowblade and select *Help -> Environment* from menu to see the two letter locale code for your OS install. For example *fr* for French, *fi* for Finnish etc. Information is under the header *General*.
  * Open terminal in folder ``.../flowblade-trunk/Flowblade/locale`` that can be found in the folder you installed repository version of Flowblade in.
  * To create a new translation give a command in the terminal:
```bash
./add_language LANGUAGE_CODE
```
 in which LANGUAGE_CODE is the two letter language code for your locale.
  
### Editing translation ###

  * A folder named with the LANGUAGE_CODE for your language can be found in the ``/locale`` folder
  * Inside that folder is a ``/LC_MESSAGES`` folder in which there is a file called ``Flowblade.po``. This is the file used to create the translation.
  * Open the file ``Flowblade.po`` in a text editor. Translations are given by writing the the translations inside quotes on lines staring with text ``msgstr``. To traslate the menu item *Open...* you would need to fill the ``msgstr`` in example below:
```bash
#: useraction.py:489
msgid "Open.."
msgstr ""
```
  * To see the translations in the application, you need to compile them into a machine readable *.mo* file. Go to ``/locale`` folder and give command:
```bash
./compile_language LANGUAGE_CODE
```
  * Launch repository version of Flowblade to view your translations.

### Updating translation ###
 * Go to the */locale* folder and give command:
```bash
./update_language LANGUAGE_CODE
```
 * Translate application as described above in paragraph **Editing translation**

### Contributing a translation
Send the created ``Flowblade.po`` file to janne.liljeblad@gmail.com or submit a Github pull request. Please mention words Flowblade, translation and the LANGUAGE_CODE in the subject line. Translation will be in the next release.
