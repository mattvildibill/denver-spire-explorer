const byId = (id) => document.getElementById(id);

/** The 2D overview also remains available when a device cannot create WebGL. */
export function renderOverview(
  world,
  places,
  reason,
  { intentional = false } = {},
) {
  document.querySelectorAll("dialog[open]").forEach((dialog) => dialog.close());
  byId("loading").classList.add("hidden");
  const overview = byId("fallback");
  overview.hidden = false;
  for (const node of document.body.children) {
    if (node !== overview) node.inert = true;
  }
  overview.focus({ preventScroll: true });
  byId("fallback-reason").textContent = reason;
  byId("labels").hidden = true;
  byId("overview-download").hidden = location.protocol === "file:";
  byId("retry-3d").textContent = intentional
    ? "Open 3D explorer"
    : "Try 3D again";
  byId("fallback-list").replaceChildren();

  const canvas = byId("fallback-map");
  const context = canvas.getContext("2d");
  const bounds = world.bounds;
  const scale = Math.min(
    (canvas.width - 60) / (bounds[2] - bounds[0]),
    (canvas.height - 60) / (bounds[3] - bounds[1]),
  );
  const offset = [
    (canvas.width - (bounds[2] - bounds[0]) * scale) / 2,
    (canvas.height - (bounds[3] - bounds[1]) * scale) / 2,
  ];
  const point = (x, y) => [
    offset[0] + (x - bounds[0]) * scale,
    offset[1] + (bounds[3] - y) * scale,
  ];
  let selected = 0;
  const buttons = [];

  function draw() {
    context.fillStyle = "#122631";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#71919f";
    for (const building of world.buildings) {
      context.beginPath();
      for (const ring of building.rings) {
        ring.forEach(([x, y], index) =>
          index
            ? context.lineTo(...point(x, y))
            : context.moveTo(...point(x, y)),
        );
        context.closePath();
      }
      context.fill("evenodd");
    }
    places.forEach((place, index) => {
      const position = point(...world.landmarks[place.key]);
      context.fillStyle = index === selected ? "#ffffff" : "#b5efd2";
      context.beginPath();
      context.arc(...position, index === selected ? 11 : 7, 0, Math.PI * 2);
      context.fill();
      context.font = "bold 16px system-ui";
      context.fillStyle = "#ffffff";
      context.fillText(String(index + 1), position[0] + 13, position[1] - 9);
      buttons[index]?.setAttribute("aria-pressed", String(index === selected));
    });
    context.font = "14px system-ui";
    context.fillStyle = "#ffffff";
    context.fillText("N ↑ · mapped footprints · level terrain", 24, 30);
  }

  places.forEach((place, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.className = "map-place";
    button.textContent = place.name;
    button.onclick = () => {
      selected = index;
      draw();
    };
    item.appendChild(button);
    item.appendChild(document.createTextNode(place.text));
    byId("fallback-list").appendChild(item);
    buttons.push(button);
  });
  draw();

  byId("retry-3d").onclick = () => {
    const url = new URL(location.href);
    url.searchParams.delete("view");
    url.searchParams.set("quality", "low");
    location.assign(url.href);
  };
}
