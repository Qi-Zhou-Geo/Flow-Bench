const map = L.map('map').setView([20, 0], 2);

const baseMaps = {
  "OSM Standard": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
  "OpenTopoMap": L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17 }),
  "Esri Satellite": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}')
};

baseMaps["OSM Standard"].addTo(map); // default
L.control.layers(baseMaps).addTo(map); // layer switcher


// Load and display GeoJSON
fetch('data.geojson')
  .then(res => res.json())
  .then(data => {
    const geojsonLayer = L.geoJSON(data, {
      onEachFeature: function (feature, layer) {
        const props = feature.properties;

        // First level (highlighted)
        let popup = `<strong>Catchment:</strong> ${props["Catchment"]}<br>
                     <strong>Data Uncertainty [freq]:</strong> ${props["Data Uncertainty [freq]"]}<br>
                     <strong>Data Uncertainty [time]:</strong> ${props["Data Uncertainty [time]"]}<hr>`;

        // Second level (everything else except the above 3)
        let secondLevel = "";
        for (const key in props) {
          if (["Catchment", "Data Uncertainty [freq]", "Data Uncertainty [time]"].includes(key)) {
            continue; // skip first-level fields
          }
          secondLevel += `<strong>${key}:</strong> ${props[key]}<br>`;
        }

        layer.bindPopup(popup + secondLevel);
      }
    }).addTo(map);

    // Zoom to fit all points
    map.fitBounds(geojsonLayer.getBounds());
  })
  .catch(err => console.error("Error loading data.geojson:", err));
