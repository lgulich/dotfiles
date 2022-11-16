" Create tags in current directory.
command MakeTags !ctags -R .<CR>

" Remove trailing whitespaces.
fun! TrimWhiteSpace()
  let l:save = winsaveview()
  keeppatterns %s/\s\+$//e
  call winrestview(l:save)
endfun
command TrimWhiteSpace call TrimWhiteSpace()

" Insert a 128-bit uuid.
fun! InsertUuid()
  let foo = system("printf '0x%s\n' $(uuidgen -r | tr -d '-' | cut -b 1-16)")
  :put =foo
endfun
command InsertUuid call InsertUuid()

" Clang-format the selection
command ClangFormat !clang-format | == <CR>
