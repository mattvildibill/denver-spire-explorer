import { createPlaces, extendPlaces } from "./places.mjs";
import { renderOverview } from "./overview.mjs";

// Deliberately independent of the 3D renderer, geometry, materials and imagery.
const world = JSON.parse(document.getElementById("world-data").textContent);
const places = createPlaces();
extendPlaces(places, world, { ccc: [-80.22, -262.37] });
renderOverview(world, places, "Choose a landmark to highlight it on the map.", {
  intentional: true,
});
