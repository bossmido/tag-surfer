# -*- coding: utf-8 -*-
"""
tsurf.finder
~~~~~~~~~~~~

This module defines the Finder class. This class is responsible for
generating and searching tags for the current file, open buffers or project.
"""

import os
import vim
import shlex
import tempfile
import subprocess
from itertools import imap
from datetime import datetime
from operator import itemgetter
from collections import defaultdict

from tsurf.utils import v
from tsurf.utils import misc
from tsurf.utils import settings
from tsurf import exceptions as ex

try:
    from tsurf.ext import search
    TSURF_SEARCH_EXT_LOADED = True
except ImportError:
    from tsurf.utils import search
    TSURF_SEARCH_EXT_LOADED = False


class Finder:

    def __init__(self, plug):
        self.plug = plug

        # `self.rebuild_tags` is True when tags need to be re-generated.
        # at the moment tags are regenerated everytime the user closes
        # Tag Surfer or change the search scope.
        self.rebuild_tags = True
        # `self.tags_cache` holds all parsed tags generated from the execution
        # of the ctags program. This attribute works in conjunction with the
        # attribute `self.rebuild_tags`
        self.tags_cache = []

        # `self.find_tags` is True when a new search needs to be done.
        # The only time this is set to `False` is when the user moves around
        # in the search results window.
        self.refind_tags = True
        # `self.last_search_results` holds the last search. This attribute
        # works in conjunction with the attribute `self.refind_tags`
        self.last_search_results = []

        # `self.old_tagfiles` is needed to keep track of the temporary files
        # created to store the output of ctags-compatible programs so
        # that we can delete it when a new ones are generated.
        self.old_tagfiles = []

        # Some stuff required by Windows
        self.startupinfo = None
        self.sanitize = lambda s: s
        if os.name == 'nt':
            # Hide the window openend by processes created on Windows
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # Escape path separators
            self.sanitize = lambda s: s.replace("\\", "\\\\")

    def close(self):
        """To perform cleanup actions."""
        self._remove_tagfiles()

    def find_tags(self, query, max_results=-1, curr_buf=None):
        """To find all matching tags for the given `query`."""
        # Do not perform a new search if the user is just moving around
        # in the search results window.
        if not self.refind_tags and self.last_search_results:
            return self.last_search_results

        # debug
        start_time_tags_gen = datetime.now()

        # Determine for which files tags need to be generated. `query` is
        # also retruned with any modifier removed. Th `query` is also cleaned
        # from the mofifier if present.
        query, files = self._get_search_scope(query, curr_buf.name)

        # Generate tags for all given `files` or return cached results if
        # possible.
        if self.rebuild_tags or not self.tags_cache:
            tags = self._generate_tags(files=files, curr_ft=curr_buf.ft)
        else:
            tags = self.tags_cache

        # debug
        delta_tags_gen = datetime.now() - start_time_tags_gen

        # debug
        start_time_tags_search = datetime.now()
        n = 0

        # Match each tag against the give query
        matches = []
        for tag in tags:
            # If `query == ""` then everything matches. Note that if `query == ""`
            # the current search scope is just the current buffer.
            similarity, positions = search.search(
                    query, tag["name"], settings.get("smart_case", int))
            if positions or not query:
                if tag["excmd"].isdigit():
                    context = tag["excmd"]
                else:
                    context = tag["excmd"][2:-2]
                matches.append({
                    "match_positions": positions,
                    "similarity": similarity,
                    "name": tag["name"],
                    "file": tag["file"],
                    "excmd": tag["excmd"],
                    "context": context,
                    "exts": tag["exts"]
                })

            n += 1

        # debug
        delta_tags_search = datetime.now() - start_time_tags_search

        # In debug mode, display some statistics in the statusline
        if settings.get("debug", bool):
            time_gen = misc.millis(delta_tags_gen)
            time_search = misc.millis(delta_tags_search)
            s = ("debug info => files: {} | tags: {} | matches: {} | "
                "gen: {}ms | search: {}ms | C ext: {}".format(
                 len(files), n, len(matches), time_gen, time_search,
                 TSURF_SEARCH_EXT_LOADED))
            vim.command("setl stl={}".format(s.replace(" ", "\ ").replace("|", "\|")))

        # Sort the search results according to the similarity value if
        # the `query` string is non-empty, otherwise sort the search results
        # by name or line number (if available). Remember that if the query
        # is epty the only tags for the curretn buffer are generate.
        if query:
            keyf = itemgetter("similarity")
        else:
            if len(matches) and (matches[0]["exts"].get("line") or matches[0]["excmd"].isdigit()):
                # If a line number is available for locating the tags, then sort
                # them according to their distance from the cursor.
                curr_line = curr_buf.cursor[0]
                if matches[0]["exts"].get("line"):
                    keyf = lambda m: abs(curr_line - int(m["exts"]["line"]))
                else:
                    keyf = lambda m: abs(curr_line - int(m["excmd"]))
            else:
                # Sort by tag name (case-insensitive)
                keyf = lambda m: m["name"].lower()

        l = len(matches)
        if max_results < 0 or max_results > l:
            max_results = l

        # Retrun only `max-results` search results.
        self.last_search_results = sorted(matches, key=keyf, reverse=True)[l-max_results:]
        return self.last_search_results

    def _remove_tagfiles(self):
        """To delete all temporary tagfiles created previously."""
        for tagfile in self.old_tagfiles:
            # Don't forget to clean up the `tag` vim option
            vim.command("set tags-={}".format(tagfile))
            try:
                os.remove(tagfile)
            except OSError:
                pass

    def _get_search_scope(self, query, curr_buf_name):
        """To return all files for which tags need to be generated."""
        pmod = settings.get("project_search_modifier")
        bmod = settings.get("buffer_search_modifier")
        files = []
        if curr_buf_name and (not query or query.strip().startswith(bmod)):
            # Retrun only the current buffer
            files = [curr_buf_name]
        elif query.strip().startswith(pmod):
            # Retrun all files of the current project. If the project root
            # cannot be located, the retruned list is empty.
            files = self.plug.services.curr_project.get_files()
        if not files:
            # Retrun all loaded buffers
            files = v.buffers()

        return query.strip(" " + bmod + pmod), files

    def _generate_tags(self, files, curr_ft=None):
        """To generate tags for files in `files`.

        If a filetype isn't supported by Exuberant Ctags, then use the custom
        ctags executable provided via the `tsurf_custom_languages` option.
        """
        # Clean old tagfiles
        self._remove_tagfiles()

        custom_langs = settings.get("custom_languages")

        # Create a map where each file extension points to
        # a specific filetype.
        extensions_map = {}
        for ft, options in custom_langs.items():
            for ext in options.get("extensions", []):
                extensions_map[ext] = ft

        # Group files according to their filetype. The filetype "*"
        # groups all files that will be parsed by Exuberant Ctags.
        # Note that filetype groups different from "*" are generated
        # only for filetypes found in `tsurf_custom_languages`
        groups = defaultdict(list)
        for f in files:
            ext = os.path.splitext(f)[1]
            groups[extensions_map.get(ext, "*")].append(f)

        self.tags_cache = []
        # For each filetype group, generate tags according to the ctags
        # program specified for that filetype. Doind so ensures that
        # if the user is working with different filetypes at the same time,
        # tags are generated transparently for each different (possibly
        # not supported by Exuberant Ctags) filetype.
        for ft, file_group in groups.items():

            if ft == "*":
                # use the official ctags
                bin = settings.get("ctags_bin")
                args = settings.get("ctags_args")
                custom_args = settings.get("ctags_custom_args")
                kinds = {}
                exclude_kinds = {}
            else:
                bin = custom_langs[ft].get("bin", "")
                args = custom_langs[ft].get("args", "")
                custom_args = ""
                kinds = custom_langs[ft].get("kinds_map", {})
                exclude_kinds = dict((k, True) for k in custom_langs[ft].get("exclude_kinds", []))

            out = ""
            if os.path.exists(bin):
                # We don't really want an error message when Tag Surfer is executed and no
                # files are available
                if file_group:
                    files = imap(lambda f: '"{}"'.format(f) if " " in f else f, file_group)
                    cmd = shlex.split("{} {} {} {}".format(self.sanitize(bin),
                        self.sanitize(args), self.sanitize(custom_args),
                        self.sanitize(" ".join(files))))

                    try:
                        out, err = subprocess.Popen(cmd, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                startupinfo=self.startupinfo).communicate()
                    except Exception as e:
                        raise ex.TagSurferException("Unexpected error: " + str(e))

                    if err:
                        raise ex.TagSurferException("Error: '{}' failed to generate "
                            "tags.\nCheck that it's an Exuberant Ctags "
                            "compatible program or that the arguments provided "
                            "are valid".format(bin))
            else:
                raise ex.TagSurferException("Error: The program '{}' does not exists "
                    "or cannot be found in your $PATH".format(bin))

            # Parse the ctags program output, rebuild the cache and write
            # a copy of the output to a temporary file.  Why writing a copy of
            # the output to a temporary file? We do this because the temporary
            # file is appendend to the `tags` option (set tags+=tempfile) so
            # that the user can still use vim tag-related commands for
            # navigating tags, most notably the `CTRL+t` mapping.
            tagfile = self._generate_temporary_tagfile()
            with tagfile:
                for line in out.split("\n"):
                    tagfile.write(line + "\n")
                    tag = self._parse_tag_line(line, kinds)
                    if tag and tag["exts"].get("kind") not in exclude_kinds:
                        self.tags_cache.append(tag)
                        yield tag

    def _generate_temporary_tagfile(self):
        """To generate a new temporary tagfile and update the vim
        `tags` option."""
        tagfile = tempfile.NamedTemporaryFile(delete=False)
        vim.command("set tags+={}".format(tagfile.name))
        self.old_tagfiles.append(tagfile.name)
        return tagfile

    def _parse_tag_line(self, line, kinds):
        """To parse a line from a tag file.

        Valid tag line format:

            tagName<TAB>tagFile<TAB>exCmd;"<TAB>extensions

        Where `extensions` is a list of <TAB>-separated fields that can be:

            1) a single letter
            2) a string `attribute:value`

        If the fields is a single letter, then the fields is interpreted as
        the kind attribute.

        NOTE: `kinds` is a dictionary of the form:

            {"shortTypeName": "longTypeName", ...}
        """
        try:
            fields, rawexts = line.strip(" \n").split(';"', 1)
            name, file, excmd = (f.decode("utf-8") for f in fields.split("\t"))
            exts = {}
            for ext in rawexts.strip("\t").split("\t"):
                if (len(ext) == 1 and ext.isalpha()) or ":" not in ext:
                    exts["kind"] = kinds.get(ext, ext).decode("utf-8")
                else:
                    t, val = ext.split(":", 1)
                    exts[t] = val.decode("utf-8")
            return {'name': name, 'file': file, 'excmd': excmd, 'exts': exts}
        except ValueError:
            return
