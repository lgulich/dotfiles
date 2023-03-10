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

" Autocorrect the last spell error.
inoremap <C-l> <c-g>u<Esc>[s1z=`]a<c-g>u
nnoremap <C-l> 1z=1<CR>

" Reformat the selection
vnoremap <F4> :!clang-format
nnoremap <F6> :%!pandoc -s --from markdown --to rst <CR>
