" General

" Set python path for neovim"
if has("mac")
  let g:python3_host_prog="/usr/local/bin/python3"
else
  let g:python3_host_prog="/usr/bin/python3"
endif

set nocompatible " To be safe
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
set noincsearch " Do not hightligh characters while searching

" Backspace key
set backspace=indent,eol,start

" Navigation
set iskeyword+=_

" Folding
set foldenable " Enable folding.
set foldlevelstart=10 " Default fold all above level 10.
set foldnestmax=1 " Maximum number of nested folds.
set foldmethod=indent " Fold based on indent level.

" Line numbering
set number " show line numbers.
set relativenumber " show relative line numbers.

" Spellcheck
setlocal spell
set spelllang=en
set spellfile=${DOTFILES}/vim/spell/en.utf-8.add
autocmd Filetype tex,latex set spell " Enable spellcheck for .tex

" Appearance
set showmatch " highlight matching parentheses etc.
set showcmd " show command in bottom bar.
set colorcolumn=+1 " show vbar at textwidth + 1
set ruler " show cursor position in bottom bar.
set scrolloff=5 " Minimal lines above and below caret.
syntax on " Turn on syntax highlighting.

" Enable nice colors in tmux
if (empty($TMUX) && has("termguicolors"))
    set termguicolors
endif

" Change carret shape to I-beam in insert mode.
au InsertEnter * set cul
au InsertLeave * set nocul

" Automatically remove white space on file save.
au BufWritePre * :call TrimWhiteSpace()
au BufNewFile,BufRead *.jenkinsfile setf groovy

" Setup make for bazel and gcc
set makeprg=bazel\ build
set errorformat^=%*[^:]:\ %f:%l:%*[^:]:%m " match libc assert
let &efm .= ',%+GIn file included from %f:%l%*[\,:]'
