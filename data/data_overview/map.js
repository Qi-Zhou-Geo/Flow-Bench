const map = L.map('map').setView([20, 0], 2); // global view

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

fetch('data.geojson')
  .then(res => res.json())
  .then(data => {
    L.geoJSON(data, {
      onEachFeature: function (feature, layer) {
        const props = feature.properties;
        const popup = `<strong>${props.name}</strong><br>
                       Attribute 1: ${props.attribute1}<br>
                       Attribute 2: ${props.attribute2}`;
        layer.bindPopup(popup);
      }
    }).addTo(map);
  });
