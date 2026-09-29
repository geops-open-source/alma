import BaseObject from "ol/Object";

import Toolbar from "./control/Toolbar";

import type BaseEvent from "ol/events/Event";
import type Map from "ol/Map";
import type oleControl from "ole/control/Control";

interface EditorOptions {
  controls: oleControl[];
}

class Editor extends BaseObject {
  private map: Map | null = null;

  private toolbar: Toolbar;

  constructor(options: EditorOptions) {
    super();
    this.toolbar = new Toolbar();
    options.controls.forEach((control) => {
      this.addControl(control);
    });
    this.toolbar.getControls().item(0)?.activate();
  }

  activeStateChange = (event: BaseEvent | Event) => {
    this.toolbar.getControls().forEach((control) => {
      if (control !== event.target) {
        control.deactivate();
      }
    });
  };

  addControl(control: oleControl) {
    this.toolbar.addControl(control);
    control.addEventListener("change:active", this.activeStateChange);
  }

  removeControl(control: oleControl) {
    this.toolbar.removeControl(control);
    control.removeEventListener("change:active", this.activeStateChange);
  }

  setMap(map?: Map) {
    if (this.map) {
      this.map.removeControl(this.toolbar);
    }
    if (map) {
      this.map = map;
      this.map.addControl(this.toolbar);
      this.toolbar.setMap(map);
    }
  }
}

export default Editor;
