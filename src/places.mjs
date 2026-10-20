// Landmark views use the same local coordinates as the geographic model.
export function createPlaces() {
  return [
    {
      id: "spire",
      name: "Spire",
      short: "Spire",
      kind: "01 / The center of the scene",
      text: "891 14th Street. The residential tower at the heart of downtown.",
      key: "Spire",
      stats: ["147.2 m", "modeled crown", "41", "floors"],
      fly: [-250, 220, 320],
      target: [0, 67, 0],
      walk: [-103.92, -60],
      look: [0, 52, 0],
    },
    {
      id: "larimer",
      name: "Larimer Square",
      short: "Larimer Square",
      kind: "02 / Historic downtown",
      text: "The historic block on Larimer Street, between 14th and 15th Streets.",
      key: "Larimer Square",
      stats: ["Historic", "district", "14th–15th", "Larimer Street"],
      fly: [-545, 165, -140],
      target: [-309, 15, -331],
      walk: [-323, 300],
      look: [-309, 4, -350],
    },
    {
      id: "mall",
      name: "16th Street Mall",
      short: "16th Street",
      kind: "03 / The pedestrian corridor",
      text: "The downtown promenade links the civic center with the Union Station end of the district.",
      key: "16th Street Mall",
      stats: ["16th St", "corridor", "NW ↔ SE", "street direction"],
      fly: [60, 220, 50],
      target: [70, 14, -315],
      walk: [55, 275],
      look: [-35, 3, -365],
    },
    {
      id: "arts",
      name: "Performing Arts Complex",
      short: "Performing Arts",
      kind: "04 / The arts district",
      text: "The theaters, concert halls and covered galleria along 14th Street.",
      key: "Denver Performing Arts Complex",
      stats: ["DCPA", "arts complex", "14th St", "main approach"],
      fly: [-480, 190, 280],
      target: [-235, 14, 29],
      walk: [-148, -37],
      look: [-235, 10, 29],
    },
    {
      id: "park",
      name: "Sculpture Park",
      short: "Sculpture Park",
      kind: "05 / The open-air gathering place",
      text: "The lawn beside the arts complex, near Speer Boulevard and Cherry Creek.",
      key: "Sculpture Park",
      stats: ["Open lawn", "public space", "DCPA", "next door"],
      fly: [-590, 125, 390],
      target: [-310, 4, 166],
      walk: [-310, -175],
      look: [-244, 10, 68],
    },
  ];
}

export function extendPlaces(places, world, data) {
  const [x, y] = data.ccc;
  world.landmarks["Colorado Convention Center"] = [x, y];
  places.push({
    id: "convention",
    name: "Colorado Convention Center",
    short: "Convention Center",
    kind: "06 / The convention district",
    text: "700 14th Street. The expansive exhibition complex southwest of Spire, across 14th Street. Later rooftop additions are not fully captured by the source mapping.",
    key: "Colorado Convention Center",
    stats: ["2022", "roof mapping", "700", "14th Street"],
    fly: [220, 240, 510],
    target: [x, 24, -y],
    walk: [26, -146],
    look: [x, 15, -y],
  });
  places[0].text =
    "Start at 891 14th Street, then discover the theaters, historic blocks and pedestrian corridor around Spire.";
  places[2].name = "16th Street corridor";
}
