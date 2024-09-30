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

" Clang-format the selection.
command ClangFormat !clang-format | == <CR>

" Write with sudo even when vim was not opened with sudo.
command WriteWithSudo w !sudo tee %

" Get the remote URL to the current line.
fun! GetRemoteUrl()
  let git_url = system('git config --get remote.origin.url')
  let git_url = substitute(git_url, '\n$', '', '')
  let git_url = substitute(git_url, '\(.*\)@\(.*\):\(\d*\/\)\?\(.*\)\.git', 'https://\2/\4', '')
  let branch = system('git rev-parse --abbrev-ref HEAD')
  let branch = substitute(branch, '\n$', '', '')
  let file = system('git ls-files --full-name '.expand('%'))
  let file = substitute(file, '\n$', '', '')
  let line = line('.')
  let url = git_url . '/blob/' . branch . '/' . file . '#L' . line
  echo url
endfun
command! GetRemoteUrl call GetRemoteUrl()
