"" ColorScheme onedark {{{
" Allow to fail when color scheme not yet downloaded.
try
  colorscheme onedark
catch /^Vim\%((\a\+)\)\=:E185/
  colorscheme default
  set background=dark
endtry
"" }}}

"" Plugin toggle-header-source {{{
" Remap for switching between header / src file.
map <F5> :call ToggleHeaderSource()<CR>
"" }}}

"" Plugin fzf {{{
" Remap to find files.
map <C-p> :Files<CR>
"" }}}

"" Plugin CamelCaseMotion {{{
" Remap to move in word.
map <silent> w <Plug>CamelCaseMotion_w
map <silent> b <Plug>CamelCaseMotion_b
map <silent> e <Plug>CamelCaseMotion_e
map <silent> ge <Plug>CamelCaseMotion_ge
sunmap w
sunmap b
sunmap e
sunmap ge
"" }}}

"" Plugin NERDTree {{{
" Remap for toggling tree.
map <C-n> :NERDTreeToggle<CR>
map <leader>f :NERDTreeFind<CR>

" Show file previews in NERDTree
let g:nerd_preview_enabled = 0
let g:preview_last_buffer  = 0

function! NERDTreePreview()
  " Only on nerdtree window
  if (&ft ==# 'nerdtree')
    " Get filename
    let l:filename = substitute(getline("."), "^\\s\\+\\|\\s\\+$","","g")

    " Preview if it is not a folder
    let l:lastchar = strpart(l:filename, strlen(l:filename) - 1, 1)
    if (l:lastchar != "/" && strpart(l:filename, 0 ,2) != "..")

      let l:store_buffer_to_close = 1
      if (bufnr(l:filename) > 0)
        " Don't close if the buffer is already open
        let l:store_buffer_to_close = 0
      endif

      " Do preview
      execute "normal go"

      " Close previews buffer
      if (g:preview_last_buffer > 0)
        execute "bwipeout " . g:preview_last_buffer
        let g:preview_last_buffer = 0
      endif

      " Set last buffer to close it later
      if (l:store_buffer_to_close)
        let g:preview_last_buffer = bufnr(l:filename)
      endif
    endif
  elseif (g:preview_last_buffer > 0)
    " Close last previewed buffer
    let g:preview_last_buffer = 0
  endif
endfunction

function! NERDTreePreviewToggle()
  if (g:nerd_preview_enabled)
    let g:nerd_preview_enabled = 0
    augroup nerdpreview
      autocmd!
    augroup END
  else
    let g:nerd_preview_enabled = 1
    augroup nerdpreview
      autocmd!
      autocmd CursorMoved * nested call NERDTreePreview()
    augroup END
  endif
endfunction

call NERDTreePreviewToggle()
"" }}}

"" Plugin vim-auto-save {{{
" Enable autosave on startup.
let g:auto_save = 1
"" }}}

"" Plugin vim-autoformat {{{
" Remap to run autoformat on current file.
map <F3> :Autoformat<CR>
"" }}}

"" Plugin vim-commentary {{{
" Set comment style for c / cpp
autocmd FileType c,cpp setlocal commentstring=//\ %s
"" }}}

"" Plugin vim-fugitive {{{
nnoremap <leader>gd :Gvdiff<CR>
nnoremap dgh :diffget //2<CR>
nnoremap dgl :diffget //3<CR>
"" }}}

"" Plugin vim-headerguard {{{
function! g:HeaderguardName()
  let prefix = 'NVIDIA_ISAAC'
  let project_name = expand('%:p:gs@.*sdk/\(.*\)/.*@\1@g')
  let project_name = substitute(project_name, '[^0-9a-zA-Z_]', '_', 'g')
  let project_name = toupper(project_name)
  let file_name = toupper(expand('%:t:gs/[^0-9a-zA-Z_]/_/g'))
  return prefix . "_" . project_name . "_" . file_name . "_"
endfunction

function! g:HeaderguardLine3()
  return "#endif  // " . g:HeaderguardName() . ""
endfunction
"" }}}

"" Plugin vimtex {{{
let g:tex_flavor='latex'
let g:vimtex_view_method='zathura'
let g:vimtex_quickfix_mode=0
set conceallevel=0
let g:tex_conceal='abdmg'
"" }}}

" vim:foldmethod=marker:foldlevel=0
