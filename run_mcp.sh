

TARGET_DIR="src/tools/mcp"

if ! ls "$TARGET_DIR"/*.py &> /dev/null; then
    echo "Error: Could not find any Python (.py) files in the '$TARGET_DIR' directory."
    exit 1
fi

for file in "$TARGET_DIR"/*.py
do
  echo "Executing script '$file' in a new terminal window..."

  if [[ "$(uname)" == "Darwin" ]]; then

    osascript -e "tell app \"Terminal\" to do script \"python3 '$file'; echo; read -p 'Script execution finished. Press Enter to close this window...'\"" &

  else

    gnome-terminal -- bash -c "python3 '$file'; echo; read -p 'Script execution finished. Press Enter to close this window...'; exec bash" &
  fi
done

echo "All script execution requests have been sent."