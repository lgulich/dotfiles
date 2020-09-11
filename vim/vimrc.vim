source ~/dotfiles/vim/vanillavimrc.vim

"" PluginManager {{{
set rtp+=~/dotfiles/vim/vim_plug
call plug#begin('~/.vim/plugged')

" Color scheme plugins
Plug 'joshdick/onedark.vim'

" General plugins
Plug '907th/vim-auto-save'
Plug 'chiel92/vim-autoformat'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'scrooloose/nerdtree'
Plug 'tpope/vim-commentary'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'

" C-style languages plugins
Plug 'bfrg/vim-cpp-modern'
Plug 'drmikehenry/vim-headerguard', { 'for': ['cpp', 'c'] }
Plug 'ericcurtin/CurtineIncSw.vim' " Switch between header and src.

Plug 'taketwo/vim-ros'

call plug#end()
"" }}}

"" ColorScheme onedark {{{
" Allow to fail when color scheme not yet downloaded.
try
  colorscheme onedark
catch /^Vim\%((\a\+)\)\=:E185/
  colorscheme default
  set background=dark
endtry
"" }}}

"" Plugin coc {{{
set hidden
set nobackup
set nowritebackup
set cmdheight=2
set updatetime=300
set shortmess+=c
set signcolumn=yes

" Use tab for trigger completion with characters ahead and navigate.
inoremap <silent><expr> <TAB>
      \ pumvisible() ? "\<C-n>" :
      \ <SID>check_back_space() ? "\<TAB>" :
      \ coc#refresh()
inoremap <expr><S-TAB> pumvisible() ? "\<C-p>" : "\<C-h>"

function! s:check_back_space() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

" Use <c-space> to trigger completion.
inoremap <silent><expr> <c-space> coc#refresh()

" Use <cr> to confirm completion.
" if exists('*complete_info')
"   inoremap <expr> <cr> complete_info()["selected"] != "-1" ? "\<C-y>" : "\<C-g>u\<CR>"
" else
"   imap <expr> <cr> pumvisible() ? "\<C-y>" : "\<C-g>u\<CR>"
" endif

" Highlight symbol under cursor on CursorHold.
autocmd CursorHold * silent call CocActionAsync('highlight')

" Remappings for GoTo code navigation.
nnoremap <silent> gd <Plug>(coc-definition)
nnoremap <silent> gtd <Plug>(coc-type-definition)
nnoremap <silent> gi <Plug>(coc-implementation)
nnoremap <silent> gr <Plug>(coc-references)

" Remap for renaming current symbol.
nnoremap <leader>rn <Plug>(coc-rename)
nnoremap <leader>cf <Plug>(cof-fix-current)

" Remap for showing documentation.
nnoremap <silent> doc :call <SID>show_documentation()<CR>

function! s:show_documentation()
  if (index(['vim','help'], &filetype) >= 0)
    execute 'h '.expand('<cword>')
  else
    call CocAction('doHover')
  endif
endfunction
"" }}}

"" Plugin CurtineIncSw {{{
" Remap for switching between header / src file.
map <F5> :call CurtineIncSw()<CR>
"" }}}

"" Plugin fzf {{{
" Remap to find files.
map <C-t> :Files<CR>
"" }}}

"" Plugin nerdtree {{{
" Remap for toggling tree.
map <C-n> :NERDTreeToggle<CR>

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
nnoremap gdh :diffget //2<CR>
nnoremap gdl :diffget //3<CR>
"" }}}

"" Plugin vim-headerguard {{{
function! g:HeaderguardName()
  let project_name = expand('%:p:gs@.*include/\(.*\)/.*@\1@g')
  let project_name = substitute(project_name, '[^0-9a-zA-Z_]', '_', 'g')
  let project_name = toupper(project_name)
  let file_name = toupper(expand('%:t:gs/[^0-9a-zA-Z_]/_/g'))
  return project_name . "_" . file_name . "_"
endfunction

function! g:HeaderguardLine3()
  return "#endif  // " . g:HeaderguardName() . ""
endfunction
"" }}}

"" Plugin vim-ros {{{
let g:ros_build_system="catkin-tools"

command! CatkinBuildThis execute ":! cd $(dirname %) && catkin build --this --no-deps"
command! CatkinBuildFromThis execute ":! cd $(dirname %) && catkin build --start-with-this"
command! CatkinBuildAll execute ":! cd $(dirname %) && catkin build --this"
command! CatkinTestThis execute ":! cd $(dirname %) && catkin run_tests --this --no-deps"
command! -nargs=+ CatkinBuild execute ":! cd $(dirname %) && catkin build --no-deps " . <f-args>
command! -nargs=+ CatkinBuildWithDeps execute ":! cd $(dirname %) && catkin build " . <f-args>
nmap <leader>bt :CatkinBuildThis<CR>
nmap <leader>ba :CatkinBuildAll<CR>
nmap <leader>tt :CatkinTestThis<CR>"
"" }}}


" vim:foldmethod=marker:foldlevel=0
