#!/bin/bash

function sys_open() {
    if which open 2> /dev/null >&2; then
        open "$@"
    fi

    if which xdg-open 2> /dev/null >&2; then
        xdg-open "$@"
    fi
}

function tmpfile() {
    local name=$(mktemp)$1
    trap "rm -f \"$name\"" EXIT

    echo "$name"
}

html_file=$(tmpfile .html)
coords_file=$(tmpfile)

enable_path=$( (test "$1" == "--path" && echo "true") || echo "false" )

awk 'BEGIN { printf("[") }; END {print("]")}; { printf("[%s, %s, \"%s, %s\"],", $1, $2, $1, $2) }' | sed 's/,]/]/' > "$coords_file"

sed -e "/%COORDS%/ r $coords_file" -e "/%COORDS%/ d" -e "s/%PATH%/$enable_path/" > "$html_file" <<EOF
<head>
  <script src="https://unpkg.com/leaflet@1.0.3/dist/leaflet.js"
          integrity="sha512-A7vV8IFfih/D732iSSKi20u/ooOfj/AGehOKq0f4vLT1Zr2Y+RX7C+w8A1gaSasGtRUZpF/NZgzSAu4/Gc41Lg=="
          crossorigin=""></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.0.3/dist/leaflet.css"
        integrity="sha512-07I2e+7D8p6he1SIM+1twR5TIrhUQn9+I6yjqD53JQjFiMf8EtC93ty0/5vJTZGF8aAocvHYNEDJajGdNx1IsQ=="
        crossorigin=""/>
</head>

<body onload="doMap();">
  <div style="width: 100%; height: 100%;" id="mapid"></div>

  <script type="text/javascript">

var coords =
 %COORDS%
;

var path = %PATH%;

function doMap() {
    var map = L.map('mapid');
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
            '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
            'Imagery © <a href="http://mapbox.com">Mapbox</a>',
        id: 'mapbox.streets',
        accessToken: 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw'
    }).addTo(map);

    var justCoords = [];

    for (i in coords) {
        var coord = [coords[i][0], coords[i][1]];
        var text  = String(i) + ": " + coords[i][2];

        justCoords.push(coord);

        L.circleMarker(coord, {"radius": 5, "fillOpacity": 0.8}).bindPopup(text).addTo(map);
    }

    map.setView(justCoords[0], 13);

    if (path) {
        var line = L.polyline(justCoords, {"color": 'blue'}).addTo(map);

        map.fitBounds(line.getBounds());
    }
}
  </script>
<body>
EOF

sys_open "$html_file"
