"" General {{{
set nocompatible
set autoread " Detect when a file has changed
set noswapfile " Disable swap files

" Indentation and text width
set tabstop=2 " Number of spaces a tab accounts for
set shiftwidth=2
set shiftround " Round indent to multiples of tab width
set expandtab " Use spaces instead of tabs
set autoindent " Copy indent from current line when starting new line
set textwidth=100 " Auto wrap lines after this width

" Disable auto-line-wrapping for shell scripts and javascript
autocmd FileType sh,bash,zsh,js setlocal textwidth=0

" Searching
set incsearch " Search as characters are entered.
" set hlsearch " Highlight matches.

" Backspace key
set backspace=indent,eol,start
"" }}}

"" Folding {{{
set foldenable " Enable folding.
set foldlevelstart=10 " Default fold all above level 10.
set foldnestmax=1 " Maximum number of nested folds.
set foldmethod=indent " Fold based on indent level.
"" }}}

"" Appearance {{{
" Change carret shape to I-beam in insert mode.
augroup carret_mode_shape_changer
  au!
  au VimEnter,InsertLeave * silent execute '!echo -ne "\e[2 q"' | redraw!
  au InsertEnter,InsertChange *
        \ if v:insertmode == 'i' |
        \   silent execute '!echo -ne "\e[6 q"' | redraw! |
        \ elseif v:insertmode == 'r' |
        \   silent execute '!echo -ne "\e[4 q"' | redraw! |
        \ endif
  au VimLeave * silent execute '!echo -ne "\e[ q"' | redraw!

  " Add a cursor line in insert mode.
  autocmd InsertEnter * set cul
  autocmd InsertLeave * set nocul
augroup end

" Line numbering
set ruler " show cursor position in bottom bar.
set number " show line numbers.
set relativenumber " show relative line numbers.
set showcmd " show command in bottom bar.
set showmatch " highlight matching parentheses etc.
set colorcolumn=+1 " show vbar at textwidth + 1

" Minimal lines above and below caret.
set scrolloff=5

" Turn on syntax highlighting.
syntax on

if (empty($TMUX))
  if (has("termguicolors"))
    set termguicolors
  endif
endif
"" }}}

"" New commands {{{
" Create tags in current directory.
command MakeTags !ctags -R .<CR>

" Remove trailing whitespaces.
fun! TrimWhiteSpace()
  let l:save = winsaveview()
  keeppatterns %s/\s\+$//e
  call winrestview(l:save)
endfun
"" }}}

"" Autocommands {{{
augroup lgulich_autocommands
  autocmd!
  " Automatically remove white space on file save.
  autocmd BufWritePre * :call TrimWhiteSpace()
augroup end
"
"" }}}

"" Remappings {{{
" Exit insert mode.
inoremap jk <ESC>

" Search and replace word under carret.
nnoremap <Leader>s :%s/\<<C-r><C-w>\>/
" Search and replace WORD under carret.
nnoremap <Leader>S :%s/<C-r><C-W>/
" Search and replace visual selection.
vnoremap <Leader>s :<C-u>%s/<C-r>*/

" Start global project-wide search.
noremap <C-F> :grep -r -F "

" Toggle fold around current block.
nnoremap <space> za

" Move vertically by visual line.
nnoremap j gj
nnoremap k gk

" Move to beginning / end of line
noremap B ^
noremap E $

" Copy / Paste from primary (X11) clipboard.
nnoremap <Leader>y "*y
vnoremap <Leader>y "*y
nnoremap <Leader>p "*p

" Copy / Paste from clipboard (ctrl-c) clipboard.
nnoremap <Leader>Y "+y
vnoremap <Leader>Y "+y
nnoremap <Leader>P "+p
"" }}}

"" ROS configuration {{{
autocmd BufRead,BufNewFile *.launch setfiletype xml
autocmd BufRead,BufNewFile *.test setfiletype xml
autocmd BufRead,BufNewFile *.cfg setfiletype python
"" }}}

"" Spellcheck {{{
setlocal spell
set spelllang=en
set spellfile=${HOME}/dotfiles/vim/spell/en.utf-8.add

" Automatically enable spellcheck for .tex files.
autocmd Filetype tex,latex set spell

" Autocorrect the last spell error.
inoremap <C-l> <c-g>u<Esc>[s1z=`]a<c-g>u
nnoremap <C-l> 1z=1<CR>
"" }}}

" vim:foldmethod=marker:foldlevel=0
