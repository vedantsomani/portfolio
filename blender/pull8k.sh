#!/bin/bash
# Pulls the 8K HDR frames (blender/farm.py --exr --outdir /dev/shm/archive-8k on the H200) down to
# this machine as they finish, and clears each one on the server once its copy here is whole: the
# server's memory disk holds a few minutes of frames, never the whole film. A cleared frame stays as
# a 1-byte marker, so the farm (which skips frames on disk) does not render it again.
#   bash blender/pull8k.sh [D:/archive-8k]
DEST="${1:-/d/archive-8k}"
SRC=/dev/shm/archive-8k
LOG=archive-render/site/blender/out/work/logs/farm8k.log
mkdir -p "$DEST"
while true; do
  # Finished frames: over a kilobyte (not a marker) and untouched for a minute (fully written).
  list=$(ssh -o BatchMode=yes h200 "cd $SRC 2>/dev/null && find . -name '*.exr' -size +1k -mmin +1 | head -300" </dev/null)
  if [ -n "$list" ]; then
    printf '%s\n' $list > "$DEST/.batch"
    ssh -o BatchMode=yes h200 "cd $SRC && tar cf - -T -" < "$DEST/.batch" | tar xf - -C "$DEST"
    sizes=$(ssh -o BatchMode=yes h200 "cd $SRC && stat -c '%s %n' $(printf '%s ' $list)" </dev/null)
    ok=()
    while read -r size name; do
      [ -f "$DEST/$name" ] && [ "$(stat -c %s "$DEST/$name")" = "$size" ] && ok+=("$name")
    done <<< "$sizes"
    if [ ${#ok[@]} -gt 0 ]; then
      ssh -o BatchMode=yes h200 "cd $SRC && for f in ${ok[*]}; do printf x > \"\$f\"; done" </dev/null
    fi
    echo "$(date +%H:%M) pulled ${#ok[@]} frames; $(find "$DEST" -name '*.exr' -size +1k | wc -l) here"
  fi
  # Done when the farm is and nothing is left to pull.
  if ssh -o BatchMode=yes h200 "grep -qE '^[0-9:]+ done$|failed jobs' $LOG 2>/dev/null" </dev/null && [ -z "$list" ]; then
    echo "$(date +%H:%M) farm done, all frames here"
    break
  fi
  sleep 120
done
