# Tag Surfer

Tag search for the Vim editor.

## Installation

First thing, check if your system meets the following requirements:

* Linux, Mac OS, Windows
* Vim 7.3+ compiled with python 2.x

If the previos requirements are satisfied proceed with the following steps.

### Step 1. Install Exuberant Ctags

If you have already installed *Exuberant Ctags* then you can safely skip this step. You can easily check
if it is already installed executing in your terminal the command `ctags --version` (or `ctags-exuberant` on some systems)
and if the name *Exuberant Ctags* appears somewhere then you're done and you can proceed with step 2.
If you don't know what *Exuberant Ctags* is then you better have a look at [http://ctags.sourceforge.net](http://ctags.sourceforge.net)
and [http://en.wikipedia.org/wiki/Ctags](http://en.wikipedia.org/wiki/Ctags). 
Once you got familiar with Ctags and tags in general you can proceed with the installation:

* **Windows:** At the [Ctags homepage](http://ctags.sourceforge.net) you can find a link to download a
zipped file containig the *ctags* executable for Windows. Download it and put it where can be found in your `%PATH%` environment
variable..

* **Linux:** Most distributions provide a package for *ctags* so you need to search for instructions specific
to your distribution. Just be sure that once installed it can be found in your `$PATH`.

* **Mac OS:** On Mac OS you can find a preinstalled version of *ctags* but it's not what we are looking for
because it's not *Exuberant Ctags*. I really hope you are using *homebrew* for managing your packages,
so to get the newer version of *ctags* simly execute in your terminal:

    brew install ctags


### Step 2. Install Tag Surfer

After installing *Exuberant Ctags*, we can proceed with the installation of the
*Tag Surfer* plugin. Copy the content of the *Tag Surfer* folder into your 
`~/.vim` directory or use your favorite plugin manager, such as 
[Vundle](https://github.com/gmarik/vundle), [Pathogen](https://github.com/tpope/vim-pathogen) 
or [Neobundle](https://github.com/Shougo/neobundle.vim).

### Step3. Compile the 'search' component 

I'm sorry but if you are a Windows user there is no support for compiling the 'search' 
component on your system. This does not means that *Tag Surfer* won't work but just that 
searches won't be as fast as with this component compiled.
  
To complete the installation go to root folder the plugin and execute:

    $ ./complete-installation.sh

This script will compile some files needed for better search performances. 

### Last check

If all went well now you are ready to use *Tag Surfer*. To test if the plugin 
is woking, open a source file and execute the `Tsurf` command. If all you see 
is a disheartening error message or just *nothing found...* then skip ahead
to the *Common issues* section, otherwise, start enjoying the plugin or read 
further.


## Quick start

Using **Om** is straightforward. To search for tags in all loaded buffers execute the 
`:Om` command. With no input specified you are presented with a list of tags for the
current buffer ordered by their relative position to the cursor. 
As you start typing something you'll see the list updating with all the tags that match the 
given input. Below is list of all actions that you can performs with the tag list:

* `UP`, `TAB`, `CTRL+K`: move up.
* `DOWN`, `CTRL+J`: move down.
* `RETURN`, `CTRL+O`, `CTRL+E`: jump to the selected tag.
* `CTRL+P`: open a preview window for the selected tag.
* `CTRL+S`: split the window for the selected tag.
* `ESC`, `CTRL+C`: close the search results list.
* `CTRL+U`: clear the current search.


Note that when you jump to a tag you can jump back to the previous position
pressing `CTRL+T`, just as you would normally do in Vim! 


### Modifiers and the search scope

Searches are not limited to the loaded buffers. You can narrow or widen
the search scope using modifiers. A modifier is simply a special letter that
you prepend to your search query. Below is list of all available modifiers:

* `%`: this modifier narrows the search scope to the current buffer.
* `#`: this modifier windes the search scope to all files of the current project 
    filtered by `wildignore` and `g:om_project_search_ignore` options. Note that 
    a project root is assumed to be the folder that contains any of the file or directory
    names listed in the `g:om_root_markers` option (by default these markers are 
    `.git`, `.svn`, `.hg`, `.bzr` and `_darcs`).

### Two kinds of search

Om provides two kinds of search. By default the search is performed in a *fuzzy* fashion,
but if you set the `g:om_smart_search` option to `1` you can rely on a more "word-aware" search.
Try both and see which one fit best for you.

## Appearance


## Basic options


## Languages support


## Tag Surfer and tag files


## Common issues


## Contributing

Do not esitate to send [patches](../../issues?labels=bug&state=open), [suggestion](../../issues?labels=enhancement&state=open)
or just to ask [questions](../../issues?labels=question&state=open)! There is always room for improvement.


## Credits

See [this page](https://github.com/gcmt/tag-surfer/graphs/contributors) for all *Tag Surfer* contributors. 


## Changelog

See [CHANGELOG.txt](CHANGELOG.txt).


## License

Copyright (c) 2013 Giacomo Comitti

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
