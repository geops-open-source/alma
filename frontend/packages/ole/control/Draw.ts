import DrawInteraction from "ol/interaction/Draw";
import oleControl from "ole/control/Control";

import type { Options as ControlOptions } from "ol/control/Control";
import type { Options as DrawInteractionOptions } from "ol/interaction/Draw";

interface DrawControlOptions {
  className?: string;
  condition?: DrawInteractionOptions["condition"];
  freehandCondition?: DrawInteractionOptions["freehandCondition"];
  source: DrawInteractionOptions["source"];
  target?: ControlOptions["target"];
  trace?: DrawInteractionOptions["trace"];
  traceSource?: DrawInteractionOptions["traceSource"];
  type: DrawInteractionOptions["type"];
}

class DrawControl extends oleControl {
  drawInteraction: DrawInteraction;

  constructor(options: DrawControlOptions) {
    super({
      element: document.createElement("div"),
      target: options?.target,
    });

    this.element.className =
      options?.className ?? `ole-draw ole-draw-${options.type}`;

    this.drawInteraction = new DrawInteraction({
      condition: options.condition,
      freehandCondition: options.freehandCondition,
      source: options.source,
      trace: options.trace,
      traceSource: options.traceSource,
      type: options.type,
    });
  }

  activate() {
    this.getMap()?.addInteraction(this.drawInteraction);
    super.activate();
  }

  deactivate() {
    this.getMap()?.removeInteraction(this.drawInteraction);
    super.deactivate();
  }
}

export default DrawControl;
