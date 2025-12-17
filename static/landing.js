// AfroED landing map (Leaflet + OpenStreetMap)

// Initialize map (centered roughly on West Africa; adjust as you like)
const map = L.map("map", { scrollWheelZoom: false }).setView([7.54, -5.55], 6);

// OpenStreetMap tiles
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Example marker (placeholder)
L.marker([5.35, -4.01]).addTo(map)
  .bindPopup("<b>Abidjan</b><br>AfroED seed location (example).");

// Optional: enable scroll zoom only after user clicks map (nice UX)
map.on("click", () => {
  map.scrollWheelZoom.enable();
});
