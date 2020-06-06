"" General {{{
set nocompatible
set autoread " Detect when a file has changed
set noswapfile " Disable swap files

" Indentation and text width
set tabstop=2
set shiftwidth=2
set shiftround
set expandtab
set autoindent
set textwidth=80

" Searching
set incsearch " Search as characters are entered.
" set hlsearch " Highlight matches.

" Backspace key
set backspace=indent,eol,start
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
set ruler " show cursor position in bottom bar.
set number " show line numbers.
set relativenumber " show relative line numbers.
set showcmd " show command in bottom bar.
set showmatch " highlight matching parentheses etc.

" Minimal lines above and below caret
set scrolloff=5
"" }}}
"" New commands {{{
"Create tags in current directory.
command MakeTags !ctags -R .<CR>
"" }}}
"" Remappings {{{
" Exit insert mode.
inoremap jj <ESC> 

" Replace all occurrences of word under carret.
nmap <Leader>s :%s/\<<C-r><C-w>\>/ 

" Toggle fold around current block.
nnoremap <space> za 

" Move vertically by visual line.
nnoremap j gj
nnoremap k gk

" Move to beginning / end of line
nnoremap B ^
nnoremap E $

" Copy / Paste from primary (selection) clipboard.
noremap <Leader>y "*y
noremap <Leader>p "*p

" Copy / Paste from clipboard (ctrl-c) clipboard.
noremap <Leader>Y "+y
noremap <Leader>P "+p
"" }}}
"" Color Setup {{{
if (empty($TMUX))
  if (has("termguicolors"))
    set termguicolors
  endif
endif

" Turn on syntax highlighting
syntax on
"" }}}
"" ROS configuration {{{
autocmd BufRead,BufNewFile *.launch setfiletype xml
autocmd BufRead,BufNewFile *.cfg setfiletype python
"" }}}

" vim:foldmethod=marker:foldlevel=0
