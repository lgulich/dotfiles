" Automatically install vim-plug
let data_dir = has('nvim') ? stdpath('data') . '/site' : '~/.vim'
if empty(glob(data_dir . '/autoload/plug.vim'))
  silent execute '!curl -fLo '.data_dir.'/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  au VimEnter * PlugInstall --sync | source $MYVIMRC
endif

set rtp+=${DOTFILES}/vim/vim_plug
call plug#begin('~/.vim/plugged')

" Color scheme plugins
Plug 'joshdick/onedark.vim'

" General plugins
Plug '907th/vim-auto-save'
Plug 'chiel92/vim-autoformat'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'scrooloose/nerdtree'
Plug 'tpope/vim-commentary'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-repeat'
Plug 'tpope/vim-abolish'
Plug 'vim-airline/vim-airline'
Plug 'bkad/CamelCaseMotion'
Plug 'APZelos/blamer.nvim' " To see inline git blames
Plug 'earthly/earthly.vim', { 'branch': 'main' } " For earthly syntax highlighting

" AI plugins
Plug 'ssh://git@gitlab-master.nvidia.com:12051/asubramaniam/gp.nvim.git'

" LSP plugins
Plug 'neovim/nvim-lspconfig'
Plug 'hrsh7th/cmp-nvim-lsp'
Plug 'hrsh7th/cmp-buffer'
Plug 'hrsh7th/cmp-path'
Plug 'hrsh7th/cmp-cmdline'
Plug 'hrsh7th/nvim-cmp'

" C-style languages plugins
Plug 'drmikehenry/vim-headerguard', { 'for': ['cpp', 'c'] }
Plug 'lgulich/toggle-header-source.vim'
Plug 'bfrg/vim-cpp-modern' " Better syntax hightlighting

" Latex plugins
Plug 'lervag/vimtex'
Plug 'rhysd/vim-grammarous'

" Bazel plugins
Plug 'google/vim-maktaba'
Plug 'bazelbuild/vim-bazel'

" Documentation plugins
Plug 'godlygeek/tabular' " Needs to be loaded before preservim/vim-markdown
Plug 'preservim/vim-markdown'
Plug 'habamax/vim-rst'

" Protobuf plugins
Plug 'uarun/vim-protobuf'

" Beancount plugins
Plug 'nathangrigg/vim-beancount'

call plug#end()
