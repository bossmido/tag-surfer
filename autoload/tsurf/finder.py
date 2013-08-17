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
from datetime import datetime
from operator import itemgetter

from tsurf import exceptions as ex
from tsurf.utils import settings
from tsurf.utils import misc
from tsurf.utils import v

try:
    from tsurf.ext import search
    TSURF_SEARCH_EXT_LOADED = True
except ImportError:
    from tsurf.utils import search
    TSURF_SEARCH_EXT_LOADED = False


class Finder:

    def __init__(self, plug):
        self.plug = plug

        # `self.cache` holds all parsed tags generated from each run
        # of the ctags-compatible program. This is needed to improve
        # the efficiency of some operations in the user interface.
        self.cache = []

        # `self.old_tagfile` is needed to keep track of the temporary files
        # created to store the output of ctags-compatible programs so
        # that we can delete it when a new one is generated.
        self.old_tagfile = ""

        # Set the correct search function according to user settings
        if settings.get("smart_matching", bool):
            self._search = search.smart_search
        else:
            self._search = search.fuzzy_search

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
        try:
            os.remove(self.old_tagfile)
        except OSError:
            pass

    def find_tags(self, input, max_results=-1, rebuild_cache=True, curr_buf=None):
        """To find all matching tags."""
        # Determine for which files tags need to be generated. `input` is
        # also retruned with any modifier removed.
        start_time_tags_gen = datetime.now()
        input, files = self._get_search_scope(input, curr_buf.name)
        if rebuild_cache or not self.cache:
            tags = self._generate_tags(files=files, curr_ft=curr_buf.ft)
        else:
            tags = self.cache
        delta_tags_gen = datetime.now() - start_time_tags_gen

        start_time_tags_search = datetime.now()
        n = 0
        matches = []
        for tag in tags:
            # If `input == ""` then everything matches. Note that if `input == ""`
            # the current search scope is just the current buffer.
            score, positions = self._search(input, tag["name"])
            if positions or not input:
                matches.append({
                    "match_positions": positions,
                    "score": score,
                    "name": tag["name"],
                    "file": tag["file"],
                    "excmd": tag["excmd"],
                    "exts": tag["exts"]
                })
            n += 1
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

        if input:
            # Sort by score
            keyf = itemgetter("score")
        else:
            if len(matches) and (matches[0]["exts"].get("line") or matches[0]["excmd"].isdigit()):
                # If a line number is available for locating the tags, then sort
                # them according to their distance from the cursor. We can do
                # this because `input == ""` so only tags for the current buffer
                # are generated.
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

        return sorted(matches, key=keyf, reverse=True)[l-max_results:]

    def _get_search_scope(self, input, curr_buf_name):
        """To return all files for which tags need to be generated."""
        pmod = settings.get("project_search_modifier")
        bmod = settings.get("buffer_search_modifier")

        files = []
        if curr_buf_name and (not input or input.strip().startswith(bmod)):
            files = [curr_buf_name]
        elif input.strip().startswith(pmod):
            files = self.plug.services.curr_project.get_files()
        if not files:
            files = v.buffers()

        return input.strip(" " + bmod + pmod), files

    def _generate_tags(self, files, curr_ft=None):
        """To generate tags for all open buffers."""
        # Call the ctags-compatible program and get the output.
        out = ""
        bin, args, kinds, exclude_kinds = self._get_type_specific_settings(curr_ft)
        if os.path.exists(bin):
            # We don't really want an error message when Tag Surfer is executed and no
            # files are available
            if files:
                args = shlex.split("{} {} {}".format(
                    *(self.sanitize(s) for s in (bin, args, " ".join(files)))))
                try:
                    out, err = subprocess.Popen(args, universal_newlines=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            startupinfo=self.startupinfo).communicate()
                except Exception as e:
                    raise ex.TagSurferException("Unexpected error: " + str(e))
                if err:
                    raise ex.TagSurferException("Error: '{}' failed to generate "
                        "tags.\nCheck that it is an Exuberant Ctags "
                        "compatible program or thta the arguments provided "
                        "are valid".format(bin))
        else:
            raise ex.TagSurferException("Error: The program '{}' does not exists "
                "or cannot be found in your $PATH".format(bin))

        # Parse the ctags-compatigle program output, rebuild the cache and
        # write a copy of the output to a temporary file.
        # Why writing a copy of the output to a temporary file? We do this
        # because the temporary file is then appendend to the `tags` option
        # (set tags+=tempfile) so that the user can still use vim tag-related
        # commands for navigating tags, most notably the `CTRL+t` mapping.
        self.cache = []
        tagfile = self._generate_temporary_tagfile()
        with tagfile:
            for line in out.split("\n"):
                tagfile.write(line + "\n")
                tag = self._parse_tag_line(line, kinds)
                if tag and tag["exts"].get("kind") not in exclude_kinds:
                    self.cache.append(tag)
                    yield tag

    def _get_type_specific_settings(self, ft):
        """To get type specific binary and relative arguments."""
        types = settings.get("types")
        if ft in types:
            return (
                types[ft].get("bin", settings.get("ctags_bin")),
                types[ft].get("args", settings.get("ctags_args")),
                types[ft].get("kinds_map", {}),
                dict((k, True) for k in types[ft].get("exclude_kinds", []))
            )
        else:
            return (
                settings.get("ctags_bin"),
                settings.get("ctags_args"),
                {},
                {}
            )

    def _generate_temporary_tagfile(self):
        """To generate a new temporary tagfile and update the vim
        `tags` option."""
        try:
            os.remove(self.old_tagfile)
        except OSError:
            pass
        tagfile = tempfile.NamedTemporaryFile(delete=False)
        vim.command("set tags-={}".format(self.old_tagfile))
        vim.command("set tags+={}".format(tagfile.name))
        self.old_tagfile = tagfile.name
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
