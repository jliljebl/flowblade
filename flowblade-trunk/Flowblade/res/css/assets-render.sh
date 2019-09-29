#! /bin/bash

INKSCAPE="/usr/bin/inkscape"
OPTIPNG="/usr/bin/optipng"

SRC_FILE="assets.svg"
ASSETS_DIR="assets"
INDEX="assets.txt"

for i in `cat $INDEX`
do
  echo Rendering $ASSETS_DIR/$i.png
  $INKSCAPE --export-id=$i \
            --export-id-only \
            --export-png=$ASSETS_DIR/$i.png $SRC_FILE >/dev/null \
  && $OPTIPNG -o7 --quiet $ASSETS_DIR/$i.png

  echo Rendering $ASSETS_DIR/$i@2.png
  $INKSCAPE --export-id=$i \
            --export-dpi=180 \
            --export-id-only \
            --export-png=$ASSETS_DIR/$i@2.png $SRC_FILE >/dev/null \
  && $OPTIPNG -o7 --quiet $ASSETS_DIR/$i@2.png

done

exit 0
