# Creating a translation

If you would like to have Flowblade translated into your language you can help by contributing a translation of Flowblade in your language.

Flowblade uses the standard [GNU "gettext" utilities](http://www.gnu.org/software/gettext/manual/gettext.html) to translate the application. GNU "gettext" is a relatively complex tool, but **Flowblade provides a set of scripts that make it easier to create translations** without using "gettext" directly.

### Steps Overview
1. Use **git** to pull repository version of Flowblade
2. Use the provided scripts to create a translation template for your language
3. Edit the created template to create the translation and compile **.mo** file from it to see your work
4. Send the created **.po** file to project lead

### 1. Use **git** to pull repository version of Flowblade

To create a translation you should probably first install the repository version of Flowblade using **git** so that you can edit and compile the translation file ``flowblade.po``, see [Install Instructions](https://github.com/jliljebl/flowblade/blob/master/flowblade-trunk/docs/INSTALLING.md).



### 2. Use the provided scripts to create a translation template for your language

  * Open Flowblade and select *Help -> Runtime Environment* from menu to see the *two letter locale code* for your OS install. For example *fr* for French, *fi* for Finnish etc. Information is under the header *General*.
  * Open terminal in folder ``.../flowblade-trunk/Flowblade/locale`` that can be found in the folder you installed repository version of Flowblade in.
  * To create a new translation give a command in the terminal:
```bash
./add_language LANGUAGE_CODE
```
 in which LANGUAGE_CODE is the two letter language code for your locale.
  
### 3. Edit the created template to create the translation and compile **.mo** file from it to see your work ###

  * A folder named with the LANGUAGE_CODE for your language can be found in the ``/locale`` folder
  * Inside that folder is a ``/LC_MESSAGES`` folder in which there is a file called ``flowblade.po``. This is the file used to create the translation.
  * You can use program **Poedit** (or **Poedit2**) to edit the ``flowblade.po`` file. These applications often compile the translation on save too, and if not, use the compile command below.
  * **or** you can open the file ``flowblade.po`` in a text editor. Translations are given by writing the the translations inside quotes on lines staring with text ``msgstr``. To traslate the menu item *Open...* you would need to fill the ``msgstr`` in example below:
```bash
#: useraction.py:489
msgid "Open.."
msgstr ""
```
  * To see the translations in the application, you need to compile them into a machine readable *.mo* file. Go to ``/locale`` folder and give command:
```bash
./compile_language LANGUAGE_CODE
```
  * Launch by running script ``../flowblade-trunk/flowblade`` that was created when you downloaded the repository version. (You may need to set it executable first)

### 4. Contributing a translation
Send the created ``flowblade.po`` file to janne.liljeblad@gmail.com or submit a Github pull request. Please mention words Flowblade, translation and the LANGUAGE_CODE in the subject line. Translation will be in the next release.


## Updating translation ##
If a translation already exists and you want to update it:

 * Go to the */locale* folder and give command:
```bash
./update_language LANGUAGE_CODE
```
 * Translate application as described above.
