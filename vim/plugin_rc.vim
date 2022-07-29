"" PluginManager vim-plug {{{
" Automatically install vim-plug
let data_dir = has('nvim') ? stdpath('data') . '/site' : '~/.vim'
if empty(glob(data_dir . '/autoload/plug.vim'))
  silent execute '!curl -fLo '.data_dir.'/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

set rtp+=~/dotfiles/vim/vim_plug
call plug#begin('~/.vim/plugged')

" Color scheme plugins
Plug 'joshdick/onedark.vim'

" General plugins
Plug '907th/vim-auto-save'
Plug 'chiel92/vim-autoformat'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'neoclide/coc.nvim', {'branch': 'release', 'do': { -> coc#util#install()}}
Plug 'scrooloose/nerdtree'
Plug 'tpope/vim-commentary'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-repeat'
Plug 'tpope/vim-abolish'
Plug 'vim-airline/vim-airline'
Plug 'bkad/CamelCaseMotion'

" C-style languages plugins
Plug 'bfrg/vim-cpp-modern'
Plug 'drmikehenry/vim-headerguard', { 'for': ['cpp', 'c'] }
Plug 'lgulich/toggle-header-source.vim'
Plug 'preservim/tagbar'
Plug 'clangd/coc-clangd'
Plug 'jackguo380/vim-lsp-cxx-highlight'

" Latex plugins
Plug 'lervag/vimtex'
Plug 'rhysd/vim-grammarous'

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

"" Plugin CoC {{{
"
" Set internal encoding of vim(not needed on neovim)
set encoding=utf-8

" TextEdit might fail if hidden is not set.
set hidden

" Some servers have issues with backup files, see issue #649.
set nobackup
set nowritebackup

" Give more space for displaying messages.
set cmdheight=2

" Having longer updatetime (default is 4000 ms = 4 s) leads to noticeable
" delays and poor user experience.
set updatetime=300

" Don't pass messages to |ins-completion-menu|.
set shortmess+=c

" Always show the signcolumn, otherwise it would shift the text each time
" diagnostics appear/become resolved.
if has("patch-8.1.1564")
  " Recently vim can merge signcolumn and number column into one
  set signcolumn=number
else
  set signcolumn=yes
endif

" Else we have issue with coc lists.
let g:coc_disable_transparent_cursor = 1

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
if has('nvim')
  inoremap <silent><expr> <c-space> coc#refresh()
else
  inoremap <silent><expr> <c-@> coc#refresh()
endif

" GoTo code navigation.
nmap <silent> gd <Plug>(coc-definition)
nmap <silent> gD <Plug>(coc-type-definition)
nmap <silent> gi <Plug>(coc-implementation)
nmap <silent> gr <Plug>(coc-references)

" Symbol renaming.
nmap <leader>rn <Plug>(coc-rename)

" Remap keys for applying codeAction to the current buffer.
nmap <leader>ac <Plug>(coc-codeaction)

" Apply AutoFix to problem on the current line.
nmap <leader>qf <Plug>(coc-fix-current)

" Use K to show documentation in preview window.
nnoremap <silent> doc :call <SID>show_documentation()<CR>

function! s:show_documentation()
  if (index(['vim','help'], &filetype) >= 0)
    execute 'h '.expand('<cword>')
  elseif (coc#rpc#ready())
    call CocActionAsync('doHover')
  else
    execute '!' . &keywordprg . " " . expand('<cword>')
  endif
endfunction

" Highlight the symbol and its references when holding the cursor.
autocmd CursorHold * silent call CocActionAsync('highlight')

" Disable CoC for latex files
autocmd FileType tex,latex CocDisable

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

"" Plugin nerdtree {{{
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
