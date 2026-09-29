import Collection from "ol/Collection";
import GroupLayer from "ol/layer/Group";
import VectorLayer from "ol/layer/Vector";
import WebGLVectorLayer from "ol/layer/WebGLVector";
import VectorSource from "ol/source/Vector";
import { createDefaultStyle } from "ol/style/flat";

import {
  layerTreeReducer,
  restoreLayerTree,
  type Tree,
  tree2Items,
  tree2Settings,
} from "./tree";

describe("Map layer tree helper", () => {
  const toItemIds = (tree: Tree) => {
    return tree2Items(tree).map((item) => {
      return item.id;
    });
  };

  const createLayer = (id: string, title = id, visible = true) => {
    return new VectorLayer({
      properties: { id, title },
      visible,
    });
  };

  const createGroup = (
    id: string,
    title: string,
    layers: VectorLayer[],
    readonly = false,
  ) => {
    return new GroupLayer({
      layers,
      properties: { collapsed: false, id, readonly, title },
    });
  };

  describe("addLayer", () => {
    it("adds a new layer at the end of titled root layers", () => {
      const existingLayer = createLayer("existing", "Existing");
      const tree = new Collection([existingLayer]);
      const addedLayer = createLayer("added", "Added");

      const changedTree = layerTreeReducer(tree, {
        payload: { layer: addedLayer },
        type: "addLayer",
      });

      expect(toItemIds(changedTree)).to.deep.equal(["added", "existing"]);
    });

    it("does not add the same layer instance twice", () => {
      const existingLayer = createLayer("existing", "Existing");
      const tree = new Collection([existingLayer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { layer: existingLayer },
        type: "addLayer",
      });

      expect(changedTree.getLength()).to.equal(1);
      expect(toItemIds(changedTree)).to.deep.equal(["existing"]);
    });
  });

  describe("removeLayer", () => {
    it("removes a root layer by id", () => {
      const bottom = createLayer("bottom", "Bottom");
      const top = createLayer("top", "Top");
      const tree = new Collection([bottom, top]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "top" },
        type: "removeLayer",
      });

      expect(toItemIds(changedTree)).to.deep.equal(["bottom"]);
    });

    it("removes a group sub layer and keeps the group when siblings remain", () => {
      const first = createLayer("first", "First");
      const second = createLayer("second", "Second");
      const group = createGroup("group", "Group", [first, second]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "first" },
        type: "removeLayer",
      });

      expect(toItemIds(changedTree)).to.deep.equal(["group", "second"]);
    });

    it("removes the whole group when deleting its only sub layer", () => {
      const only = createLayer("only", "Only");
      const group = createGroup("group", "Group", [only]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "only" },
        type: "removeLayer",
      });

      expect(changedTree.getLength()).to.equal(0);
      expect(toItemIds(changedTree)).to.deep.equal([]);
    });
  });

  describe("renameLayer", () => {
    it("renames a root layer", () => {
      const layer = createLayer("root", "Root");
      const tree = new Collection([layer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "root", title: "Root Renamed" },
        type: "renameLayer",
      });

      expect(changedTree.item(0).get("title") as string).to.equal(
        "Root Renamed",
      );
    });

    it("renames a sub layer", () => {
      const sub = createLayer("sub", "Sub");
      const group = createGroup("group", "Group", [sub]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "sub", title: "Sub Renamed" },
        type: "renameLayer",
      });

      expect(
        (changedTree.item(0) as GroupLayer).getLayers().item(0).get("title"),
      ).to.equal("Sub Renamed");
    });
  });

  describe("setCollapsed", () => {
    it("sets collapsed on a group", () => {
      const sub = createLayer("sub", "Sub");
      const group = createGroup("group", "Group", [sub]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { collapsed: true, id: "group" },
        type: "setCollapsed",
      });

      expect(changedTree.item(0).get("collapsed") as boolean).to.equal(true);
    });

    it("does nothing when target is not a group", () => {
      const layer = createLayer("layer", "Layer");
      const tree = new Collection([layer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { collapsed: true, id: "layer" },
        type: "setCollapsed",
      });

      expect(changedTree.item(0).get("collapsed")).to.equal(undefined);
    });
  });

  describe("setVisible", () => {
    it("sets visible on a root layer", () => {
      const layer = createLayer("layer", "Layer", true);
      const tree = new Collection([layer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "layer", visible: false },
        type: "setVisible",
      });

      expect(changedTree.item(0).getVisible()).to.equal(false);
    });

    it("sets all sub layers visible state when toggling a group", () => {
      const first = createLayer("first", "First", true);
      const second = createLayer("second", "Second", true);
      const group = createGroup("group", "Group", [first, second]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "group", visible: false },
        type: "setVisible",
      });

      const changedGroup = changedTree.item(0) as GroupLayer;
      expect(changedGroup.getLayers().item(0).getVisible()).to.equal(false);
      expect(changedGroup.getLayers().item(1).getVisible()).to.equal(false);
      expect(changedGroup.getVisible()).to.equal(false);
      expect(changedGroup.get("indeterminate")).to.equal(false);
    });

    it("updates group indeterminate state when toggling one sub layer", () => {
      const first = createLayer("first", "First", true);
      const second = createLayer("second", "Second", true);
      const group = createGroup("group", "Group", [first, second]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "first", visible: false },
        type: "setVisible",
      });

      const changedGroup = changedTree.item(0) as GroupLayer;
      expect(changedGroup.getLayers().item(0).getVisible()).to.equal(false);
      expect(changedGroup.getLayers().item(1).getVisible()).to.equal(true);
      expect(changedGroup.getVisible()).to.equal(true);
      expect(changedGroup.get("indeterminate")).to.equal(true);
    });

    it("updates visibility on an empty group", () => {
      const emptyGroup = createGroup("group", "Group", []);
      const tree = new Collection([emptyGroup]);

      const hiddenTree = layerTreeReducer(tree, {
        payload: { id: "group", visible: false },
        type: "setVisible",
      });

      expect(hiddenTree.item(0).getVisible()).to.equal(false);
      expect(hiddenTree.item(0).get("indeterminate")).to.equal(false);

      const visibleTree = layerTreeReducer(hiddenTree, {
        payload: { id: "group", visible: true },
        type: "setVisible",
      });

      expect(visibleTree.item(0).getVisible()).to.equal(true);
      expect(visibleTree.item(0).get("indeterminate")).to.equal(false);
    });
  });

  describe("setOpacity", () => {
    it("sets opacity on a root layer", () => {
      const layer = createLayer("layer", "Layer");
      const tree = new Collection([layer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "layer", opacity: 0.5 },
        type: "setOpacity",
      });

      expect(changedTree.item(0).getOpacity()).to.equal(0.5);
    });

    it("sets opacity on a sub layer", () => {
      const sub = createLayer("sub", "Sub");
      const group = createGroup("group", "Group", [sub]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "sub", opacity: 0.3 },
        type: "setOpacity",
      });

      expect(
        (changedTree.item(0) as GroupLayer).getLayers().item(0).getOpacity(),
      ).to.equal(0.3);
    });
  });

  describe("setScaleRange", () => {
    it("sets scaleRange on a root layer and applies maxResolution", () => {
      const layer = createLayer("layer", "Layer");
      const tree = new Collection([layer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "layer", scaleRange: "large" },
        type: "setScaleRange",
      });

      expect(changedTree.item(0).getMaxResolution()).to.equal(5);
    });

    it("clears scaleRange and resets maxResolution to Infinity", () => {
      const layer = createLayer("layer", "Layer");
      layer.set("scaleRange", "large");
      layer.setMaxResolution(100);
      const tree = new Collection([layer]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "layer", scaleRange: undefined },
        type: "setScaleRange",
      });

      expect(changedTree.item(0).getMaxResolution()).to.equal(Infinity);
    });

    it("sets scaleRange on a sub layer", () => {
      const sub = createLayer("sub", "Sub");
      const group = createGroup("group", "Group", [sub]);
      const tree = new Collection([group]);

      const changedTree = layerTreeReducer(tree, {
        payload: { id: "sub", scaleRange: "large" },
        type: "setScaleRange",
      });

      const subLayer = (changedTree.item(0) as GroupLayer).getLayers().item(0);
      expect(subLayer.getMaxResolution()).to.equal(5);
    });
  });

  describe("moveLayer", () => {
    it("moves root layer below group when dropped below one of its sub layers", () => {
      const subLayer = new VectorLayer({
        properties: { id: "sub", title: "Sub" },
      });
      const localGroupLayer = new GroupLayer({
        layers: [subLayer],
        properties: { collapsed: false, id: "group", title: "Group" },
      });
      const localBottomLayer = new VectorLayer({
        properties: { id: "bottom", title: "Bottom" },
      });
      const localTopLayer = new VectorLayer({
        properties: { id: "top", title: "Top" },
      });

      const tree = new Collection([
        localBottomLayer,
        localGroupLayer,
        localTopLayer,
      ]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "move-top-below-group",
          id: "top",
          level: 0,
          overId: "sub",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "group",
        "sub",
        "top",
        "bottom",
      ]);
    });

    it("moves sub layer one level up below its parent group", () => {
      const subLayer = new VectorLayer({
        properties: { id: "sub", title: "Sub" },
      });
      const siblingSubLayer = new VectorLayer({
        properties: { id: "subSibling", title: "Sub Sibling" },
      });
      const localGroupLayer = new GroupLayer({
        layers: [subLayer, siblingSubLayer],
        properties: { collapsed: false, id: "group", title: "Group" },
      });
      const localBottomLayer = new VectorLayer({
        properties: { id: "bottom", title: "Bottom" },
      });
      const localTopLayer = new VectorLayer({
        properties: { id: "top", title: "Top" },
      });

      const tree = new Collection([
        localBottomLayer,
        localGroupLayer,
        localTopLayer,
      ]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "move-sub-up",
          id: "sub",
          level: 0,
          overId: "subSibling",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "top",
        "group",
        "subSibling",
        "sub",
        "bottom",
      ]);
    });

    it("does not apply the same move action twice", () => {
      const first = createLayer("first", "First");
      const second = createLayer("second", "Second");
      const tree = new Collection([first, second]);

      const onceMoved = layerTreeReducer(tree, {
        payload: {
          actionId: "dedupe-action",
          id: "second",
          level: 0,
          overId: "first",
        },
        type: "moveLayer",
      });

      const twiceMoved = layerTreeReducer(onceMoved, {
        payload: {
          actionId: "dedupe-action",
          id: "second",
          level: 0,
          overId: "first",
        },
        type: "moveLayer",
      });

      expect(toItemIds(twiceMoved)).to.deep.equal(toItemIds(onceMoved));
    });

    it("applies subsequent root-level moves after deduping a duplicate action", () => {
      const first = createLayer("first", "First");
      const second = createLayer("second", "Second");
      const third = createLayer("third", "Third");
      const tree = new Collection([first, second, third]);

      const actionA = {
        actionId: "strict-mode-double-dispatch",
        id: "third",
        level: 0,
        overId: "first",
      };

      const onceMoved = layerTreeReducer(tree, {
        payload: actionA,
        type: "moveLayer",
      });

      const dedupedMove = layerTreeReducer(onceMoved, {
        payload: actionA,
        type: "moveLayer",
      });

      const actionB = {
        actionId: "next-user-interaction",
        id: "second",
        level: 0,
        overId: "third",
      };
      const nextMove = layerTreeReducer(dedupedMove, {
        payload: actionB,
        type: "moveLayer",
      });

      expect(toItemIds(onceMoved)).to.deep.equal(["second", "first", "third"]);
      expect(toItemIds(dedupedMove)).to.deep.equal([
        "second",
        "first",
        "third",
      ]);
      expect(toItemIds(nextMove)).to.deep.equal(["first", "third", "second"]);
    });

    it("does not move a root layer into a readonly group", () => {
      const sub = createLayer("sub", "Sub");
      const readonlyGroup = createGroup("group", "Group", [sub], true);
      const moving = createLayer("moving", "Moving");
      const tree = new Collection([readonlyGroup, moving]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "readonly-move",
          id: "moving",
          level: 1,
          overId: "sub",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal(["moving", "group", "sub"]);
      const groupLayer = movedTree.getArray().find((layer) => {
        return layer.get("id") === "group";
      }) as GroupLayer;
      expect(groupLayer.getLayers().getLength()).to.equal(1);
    });

    it("moves a root layer into the hovered group (not the previous group)", () => {
      const firstSub = createLayer("firstSub", "First Sub");
      const firstGroup = createGroup("firstGroup", "First Group", [firstSub]);
      const secondSub = createLayer("secondSub", "Second Sub");
      const secondGroup = createGroup("secondGroup", "Second Group", [
        secondSub,
      ]);
      const moving = createLayer("moving", "Moving");
      const tree = new Collection([firstGroup, secondGroup, moving]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "into-hovered-group",
          id: "moving",
          level: 1,
          overId: "secondGroup",
        },
        type: "moveLayer",
      });

      const movedFirstGroup = movedTree.item(0) as GroupLayer;
      const movedSecondGroup = movedTree.item(1) as GroupLayer;

      expect(
        movedFirstGroup
          .getLayers()
          .getArray()
          .map((layer) => {
            return layer.get("id") as string;
          }),
      ).to.deep.equal(["firstSub"]);
      expect(
        movedSecondGroup
          .getLayers()
          .getArray()
          .map((layer) => {
            return layer.get("id") as string;
          }),
      ).to.deep.equal(["secondSub", "moving"]);
    });

    it("moves root layer from below into group above hovered sublayer", () => {
      const targetSub = createLayer("targetSub", "Target Sub");
      const targetGroup = createGroup("targetGroup", "Target Group", [
        targetSub,
      ]);
      const moving = createLayer("moving", "Moving");
      const bottom = createLayer("bottom", "Bottom");
      const tree = new Collection([moving, targetGroup, bottom]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "root-below-into-group-over-sub",
          id: "moving",
          level: 1,
          overId: "targetSub",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "bottom",
        "targetGroup",
        "moving",
        "targetSub",
      ]);
    });

    it("moves root layer from above into group over hovered sublayer", () => {
      const top = createLayer("top", "Top");
      const targetSub = createLayer("targetSub", "Target Sub");
      const targetGroup = createGroup("targetGroup", "Target Group", [
        targetSub,
      ]);
      const moving = createLayer("moving", "Moving");
      const tree = new Collection([top, targetGroup, moving]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "root-above-into-group-over-sub",
          id: "moving",
          level: 1,
          overId: "targetSub",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "targetGroup",
        "moving",
        "targetSub",
        "top",
      ]);
    });

    it("moves a sub layer to previous group without duplicating it", () => {
      const moving = createLayer("moving", "Moving");
      const sourceSibling = createLayer("sourceSibling", "Source Sibling");
      const sourceGroup = createGroup("sourceGroup", "Source Group", [
        moving,
        sourceSibling,
      ]);
      const targetSub = createLayer("targetSub", "Target Sub");
      const targetGroup = createGroup("targetGroup", "Target Group", [
        targetSub,
      ]);
      const anchor = createLayer("anchor", "Anchor");
      const tree = new Collection([sourceGroup, targetGroup, anchor]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "move-sublayer-no-duplicate",
          id: "moving",
          level: 1,
          overId: "anchor",
        },
        type: "moveLayer",
      });

      const movedSourceGroup = movedTree.item(0) as GroupLayer;
      const movedTargetGroup = movedTree.item(1) as GroupLayer;

      expect(
        movedSourceGroup
          .getLayers()
          .getArray()
          .map((layer) => {
            return layer.get("id") as string;
          }),
      ).to.deep.equal(["sourceSibling"]);
      expect(
        movedTargetGroup
          .getLayers()
          .getArray()
          .map((layer) => {
            return layer.get("id") as string;
          }),
      ).to.deep.equal(["targetSub", "moving"]);
    });

    it("moves a sub layer out above hovered root item", () => {
      const moving = createLayer("moving", "Moving");
      const sourceSibling = createLayer("sourceSibling", "Source Sibling");
      const sourceGroup = createGroup("sourceGroup", "Source Group", [
        moving,
        sourceSibling,
      ]);
      const targetRoot = createLayer("targetRoot", "Target Root");
      const otherRoot = createLayer("otherRoot", "Other Root");
      const tree = new Collection([sourceGroup, targetRoot, otherRoot]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "move-sublayer-out-over-root",
          id: "moving",
          level: 0,
          overId: "targetRoot",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "otherRoot",
        "moving",
        "targetRoot",
        "sourceGroup",
        "sourceSibling",
      ]);

      const movedSourceGroup = movedTree.item(0) as GroupLayer;
      expect(
        movedSourceGroup
          .getLayers()
          .getArray()
          .map((layer) => {
            return layer.get("id") as string;
          }),
      ).to.deep.equal(["sourceSibling"]);
    });

    it("moves a sub layer out above a hovered group item", () => {
      const moving = createLayer("moving", "Moving");
      const sourceSibling = createLayer("sourceSibling", "Source Sibling");
      const sourceGroup = createGroup("sourceGroup", "Source Group", [
        moving,
        sourceSibling,
      ]);

      const targetSub = createLayer("targetSub", "Target Sub");
      const targetGroup = createGroup("targetGroup", "Target Group", [
        targetSub,
      ]);
      const topRoot = createLayer("topRoot", "Top Root");
      const tree = new Collection([sourceGroup, targetGroup, topRoot]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "move-sublayer-out-over-group",
          id: "moving",
          level: 0,
          overId: "targetGroup",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "topRoot",
        "moving",
        "targetGroup",
        "targetSub",
        "sourceGroup",
        "sourceSibling",
      ]);
    });

    it("moves a sub layer out below target group when hovering its sub layer", () => {
      const moving = createLayer("moving", "Moving");
      const sourceSibling = createLayer("sourceSibling", "Source Sibling");
      const sourceGroup = createGroup("sourceGroup", "Source Group", [
        moving,
        sourceSibling,
      ]);

      const targetSub = createLayer("targetSub", "Target Sub");
      const targetGroup = createGroup("targetGroup", "Target Group", [
        targetSub,
      ]);
      const topRoot = createLayer("topRoot", "Top Root");
      const tree = new Collection([sourceGroup, targetGroup, topRoot]);

      const movedTree = layerTreeReducer(tree, {
        payload: {
          actionId: "move-sublayer-out-over-target-sub",
          id: "moving",
          level: 0,
          overId: "targetSub",
        },
        type: "moveLayer",
      });

      expect(toItemIds(movedTree)).to.deep.equal([
        "topRoot",
        "targetGroup",
        "targetSub",
        "moving",
        "sourceGroup",
        "sourceSibling",
      ]);
    });
  });

  describe("tree2Settings", () => {
    it("serializes a WFS layer (WebGLVectorLayer) with type WFS", () => {
      const wfsLayer = new WebGLVectorLayer({
        properties: {
          id: "wfs1",
          title: "My WFS Layer",
          url: "https://example.com/wfs?service=WFS&request=GetFeature",
        },
        source: new VectorSource(),
        style: createDefaultStyle(),
        visible: true,
      });
      const tree = new Collection([wfsLayer]);

      const settings = tree2Settings(tree);

      expect(settings).to.have.length(1);
      expect(settings[0]).to.deep.include({
        id: "wfs1",
        title: "My WFS Layer",
        type: "WFS",
        url: "https://example.com/wfs?service=WFS&request=GetFeature",
      });
    });
  });

  describe("restoreLayerTree", () => {
    it("restores nested group child visibility and order", () => {
      const livePublished = createLayer(
        "vflzSearchLayerGroup.published",
        "Published",
        false,
      );
      const liveNotPublished = createLayer(
        "vflzSearchLayerGroup.notPublished",
        "Not Published",
        true,
      );
      const liveSearch = createLayer("vflzSearchLayer", "Search", true);
      const liveGroup = new GroupLayer({
        layers: [liveNotPublished, livePublished, liveSearch],
        properties: {
          collapsed: true,
          hiddenLayers: ["vflzSearchLayer"],
          id: "vflzSearchLayerGroup",
          readonly: true,
          title: "VFLZ Search Group",
        },
      });
      const liveTree = new Collection([liveGroup]);

      const savedPublished = createLayer(
        "vflzSearchLayerGroup.published",
        "Published",
        true,
      );
      const savedNotPublished = createLayer(
        "vflzSearchLayerGroup.notPublished",
        "Not Published",
        false,
      );
      const savedSearch = createLayer("vflzSearchLayer", "Search", false);
      const savedGroup = new GroupLayer({
        layers: [savedNotPublished, savedPublished, savedSearch],
        properties: {
          collapsed: false,
          id: "vflzSearchLayerGroup",
          title: "VFLZ Search Group",
        },
        visible: true,
      });
      const savedTree = new Collection([savedGroup]);

      const restoredTree = restoreLayerTree(savedTree, liveTree);
      const restoredGroup = restoredTree.item(0) as GroupLayer;

      expect(restoredGroup.get("collapsed")).to.equal(false);
      expect(restoredGroup.getVisible()).to.equal(true);
      expect(
        restoredGroup
          .getLayers()
          .getArray()
          .map((layer) => {
            return layer.get("id") as string;
          }),
      ).to.deep.equal([
        "vflzSearchLayerGroup.notPublished",
        "vflzSearchLayerGroup.published",
        "vflzSearchLayer",
      ]);
      expect(liveNotPublished.getVisible()).to.equal(false);
      expect(livePublished.getVisible()).to.equal(true);
      expect(liveSearch.getVisible()).to.equal(false);
    });
  });
});
