"" Plugins {{{
call plug#begin('~/.vim/plugged')

" Color scheme plugins
Plug 'joshdick/onedark.vim'

" General plugins
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'preservim/nerdtree'

call plug#end()

" fzf configuration.
map <C-p> :Files<CR>

" NERDtree configuration.
map <C-n> :NERDTreeToggle<CR>

"" }}}

"" General {{{
set nocompatible
set autoread " Detect when a file has changed.
set noswapfile " Disable swap files.

" Indents and line width.
set tabstop=2 " Number of spaces a tab accounts for.
set shiftwidth=2 " Size of indents.
set shiftround " Round indent to multiples of tab width.
set expandtab " Use spaces instead of tabs.
set autoindent " Copy indent from current line when starting new line.
set textwidth=100 " Auto wrap lines after this width.

" Disable auto-line-wrapping for shell scripts.
autocmd FileType sh,bash,zsh setlocal textwidth=0

set incsearch " Search as characters are entered.

" Allow backspace key in insert mode.
set backspace=indent,eol,start
"" }}}

"" Folding {{{
set foldenable " Enable folding.
set foldlevelstart=10 " Default fold all above level 10.
set foldnestmax=10 " Maximum number of nested folds.
set foldmethod=indent " Fold based on indent level.
"" }}}

"" Appearance {{{
" Change carret shape to I-beam in insert mode.
if has("autocmd")
  au VimEnter,InsertLeave * silent execute '!echo -ne "\e[2 q"' | redraw!
  au InsertEnter,InsertChange *
        \ if v:insertmode == 'i' |
        \   silent execute '!echo -ne "\e[6 q"' | redraw! |
        \ elseif v:insertmode == 'r' |
        \   silent execute '!echo -ne "\e[4 q"' | redraw! |
        \ endif
  au VimLeave * silent execute '!echo -ne "\e[ q"' | redraw!
endif

" Line numbering
set ruler " Show cursor position in bottom bar.
set number " Show line numbers.
set relativenumber " Show relative line numbers.
set showcmd " Show command in bottom bar.
set showmatch " Highlight matching parentheses etc.
set colorcolumn=+1 " Show vbar at textwidth + 1

set scrolloff=5 " Minimal lines above and below caret
"" }}}
"
"" Remappings {{{
" Exit insert mode.
inoremap jk <ESC>
inoremap jj <ESC>

" Move to beginning / end of line.
noremap B ^
noremap E $

autocmd FileType c,cpp nnoremap <buffer> <F3> :FormatCpp
autocmd FileType python nnoremap <buffer> <F3> :FormatPython
"" }}}

"" Color setup {{{
if (empty($TMUX))
  if (has("termguicolors"))
    set termguicolors
  endif
endif

" Turn on syntax highlighting.
syntax on
"" }}}

"" New commands {{{
command FormatCpp !clang-format -i %
command FormatPython !yapf -i %
"" }}}

"" ROS configuration {{{
" Enable syntax highlighting for ROS' custom filetypes.
autocmd BufRead,BufNewFile *.launch setfiletype xml
autocmd BufRead,BufNewFile *.cfg setfiletype python
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

" vim:foldmethod=marker:foldlevel=0
