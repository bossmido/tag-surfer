" ============================================================================
" File: plugin/tagsurfer.vim
" Description: Tag surfing for vim
" Mantainer: Giacomo Comitti (https://github.com/gcmt)
" Url: https://github.com/gcmt/tsurf
" License: MIT
" Version: 1.0
" Last Changed: 17 Aug 2013
" ============================================================================


" Init
" ----------------------------------------------------------------------------

if  v:version < 703 || !has('python') || exists("g:tsurf_loaded") || &cp
    finish
endif

" The `sys` module is automatically imported by vim, check with
" `:py print globals()`
let s:current = pyeval("sys.version_info[0]")
if s:current != 2
    echohl WarningMsg |
        \ echomsg "[tsurf] Tag Surfer unavailable: requires python 2.x" |
        \ echohl None
    finish
endif
let g:tsurf_loaded = 1

" On non-Windows plarforms, tell the user that he can have better search
" prformances compiling the C extension module.
if !has("win32")
    let s:plugin_root = expand("<sfile>:p:h:h")
    if !filereadable(s:plugin_root."/autoload/tsurf/ext/search.so")
        echohl WarningMsg |
            \ echomsg "[tsurf] For better search performances go to the plugin "
                \ "root directory and excute `./complete-installation`." |
            \ echohl None
    endif
endif


" Help functions
" ----------------------------------------------------------------------------

" This function try to automatically spot the `ctags` program location
fu! s:find_ctags_bin(bin)
    let pathsep = has("win32") ? '\' : '/'
    if match(a:bin, pathsep) != -1
        return a:bin
    endif
    " Try to automatically discover Exuberant Ctags
    if has("win32")
        " globpath() wants forward slashes even on Windows
        let places = split(substitute($PATH, '\', '/', 'g'), ";")
    else
        let commons = ["/usr/local/bin", "/opt/local/bin", "/usr/bin"]
        let places = extend(split($PATH, ":"), commons)
    endif
    for bin in split(globpath(join(places, ","), a:bin), "\n")
        let out = system(bin . " --version")
        if v:shell_error == 0 && match(out, "Exuberant Ctags") != -1
            return bin
        endif
    endfor
    return a:bin
endfu


" Initialize settings
" ----------------------------------------------------------------------------

let g:tsurf_debug =
    \ get(g:, "tsurf_debug", 0)

" Core options

let g:tsurf_ctags_bin =
    \ s:find_ctags_bin(get(g:, "tsurf_ctags_bin", has("win32") ? "ctags.exe" : "ctags"))

let g:tsurf_ctags_args =
    \ get(g:, "tsurf_ctags_args", "-f - --format=2 --excmd=pattern --sort=yes --extra= --fields=nKzmafilmsSt")

" Search type and scope

let g:tsurf_smart_matching =
    \ get(g:, "tsurf_smart_matching", 0)

let g:tsurf_buffer_search_modifier =
    \ get(g:, "tsurf_buffer_search_modifier", "%")

let g:tsurf_project_search_modifier =
    \ get(g:, "tsurf_project_search_modifier", "#")

let g:tsurf_root_markers =
    \ extend(get(g:, 'tsurf_root_markers', []), ['.git', '.svn', '.hg', '.bzr', '_darcs'])

let g:tsurf_project_search_ignore =
    \ get(g:, 'tsurf_project_search_ignore', "") . &wildignore

" Appearance

let g:tsurf_max_results =
    \ get(g:, "tsurf_max_results", 15)

let g:tsurf_prompt =
    \ get(g:, "tsurf_prompt", " @ ")

let g:tsurf_prompt_color =
    \ get(g:, "tsurf_prompt_color", "")

let g:tsurf_current_line_indicator =
    \ get(g:, "tsurf_current_line_indicator", " > ")

let g:tsurf_line_format =
    \ get(g:, "tsurf_line_format", ["{file}", " | {kind}"])

let g:tsurf_tag_file_full_path =
    \ get(g:, "tsurf_tag_file_full_path", 0)

let g:tsurf_tag_file_custom_depth =
    \ get(g:, "tsurf_tag_file_custom_depth", -1)

let g:tsurf_nothing_found_msg =
    \ get(g:, "tsurf_nothing_found_msg", " nothing found...")


" TODO: is it better to just use colorscheme-dependent colors ?

let g:tsurf_shade_color =
    \ get(g:, 'tsurf_shade_color', 'gui=NONE guifg=#999999 cterm=NONE ctermfg=245')

let g:tsurf_shade_color_darkbg =
    \ get(g:, 'tsurf_shade_color_darkbg', g:tsurf_shade_color)

let g:tsurf_matches_color =
    \ get(g:, 'tsurf_matches_color', 'gui=NONE guifg=#ff6155 cterm=NONE ctermfg=203')

let g:tsurf_matches_color_darkbg =
    \ get(g:, 'tsurf_matches_color_darkbg', g:tsurf_matches_color)

" Custom languages support

let g:tsurf_types =
    \ get(g:, "tsurf_types", {})


" Commands
" ----------------------------------------------------------------------------

command! Tsurf call tsurf#Open()
command! -nargs=? -complete=file TsurfSetRoot call tsurf#SetProjectRoot(<q-args>)
command! TsurfUnsetRoot call tsurf#UnsetProjectRoot()
