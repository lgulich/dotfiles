current="$(InputSourceSelector current)"
if [ "${current}" == "com.apple.keylayout.SwissGerman (Swiss German)" ]; then
  echo "Switching to US keyboard."
  InputSourceSelector select com.apple.keylayout.US
else
  echo "Switching to Swiss keyboard."
  InputSourceSelector select com.apple.keylayout.SwissGerman
fi
