// Map-art extension: tile improvements (Interstates and major highways, railroads, ports, airports),
// military forts and restricted ground, wonders and protected land, and freight trade routes, each as a static layer
// drawn into the cached map (nothing animates; an idle map draws no frames), with a switch in the "Map" menu.
//
// Data: infrastructure.json, military.json, wonders.json and trade.json (loaded eagerly by main.js right after the
// first frame; app.loadData returns the same promise). A missing file (null) leaves its layers off and their switches
// harmless. Defaults: roads, rail, ports & airports, military and wonders on (roads, rail and hubs only from the region
// view in: see each layer's minRpx), trade routes off.
import { createModel } from "./model.js";
import { makeLayers } from "./layers.js";
import { tips } from "./tips.js";

const TOGGLES = [
  { id: "roads", label: "道路", icon: "t-road", def: true, title: "国家高速公路主干线（走向示意）", layers: ["roads"] },
  { id: "rail", label: "铁路", icon: "t-rail", def: true, title: "八纵八横高铁与主要普速干线（走向示意）", layers: ["rail"] },
  { id: "hubs", label: "港口与机场", icon: "d-harbor", def: true, title: "吞吐量前 20 港口与前 30 机场", layers: ["hubs"] },
  { id: "wonders", label: "奇观", icon: "w-landmark", def: true, title: "国家公园、5A 景区、研究型大学与地标", layers: ["wonders", "protected", "plates"] },
];

export function install(app) {
  const model = createModel(app.w);
  const on = Object.fromEntries(TOGGLES.map((t) => [t.id, t.def]));
  const layers = makeLayers(model, on, { tips, app });
  for (const l of layers) app.registerStaticLayer(l);

  for (const t of TOGGLES) {
    app.ui.addMapToggle({
      id: t.id, label: t.label, icon: t.icon, title: t.title, default: t.def,
      get: () => on[t.id],
      set: (v) => {
        on[t.id] = !!v;
        app.requestDraw();
      },
    });
  }

  const apply = (name, data) => {
    model.setData(name, data);
    app.requestDraw();
  };
  for (const name of ["infrastructure", "wonders"]) {
    if (app.data[name] !== undefined) apply(name, app.data[name]);
    else app.loadData(name).then((d) => apply(name, d), (err) => console.warn(`map layers: ${name} failed to load`, err));
  }

  // For debugging and the gallery: the model and switches.
  app.mapArt = { model, on, layers };
}
