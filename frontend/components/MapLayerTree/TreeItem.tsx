import { Checkbox, Field, Label } from "@headlessui/react";
import { forwardRef, useEffect, useRef, useState } from "react";

import CheckboxIcon from "@/components/icons/CheckboxIcon";
import EditIcon from "@/components/icons/EditIcon";
import HandleIcon from "@/components/icons/HandleIcon";
import TrashIcon from "@/components/icons/TrashIcon";
import { useI18n } from "@/lib/i18n";
import useMap from "@/packages/react-spatial/useMap";

import { SCALE_RANGE_MAX_RESOLUTION } from "./tree";

import type { DraggableAttributes } from "@dnd-kit/core";

import type { GroupItem, LayerItem } from "./tree";

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M9.6096 11.817c.2104.244.5704.244.7808 0l2.4675-2.8614c.3144-.3646.073-.9556-.3904-.9556h-4.935c-.4634 0-.7048.591-.3904.9556l2.4675 2.8614Z"
        fill="#98A2B3"
      />
    </svg>
  );
}

function InfoCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      height="20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clipPath="url(#a)">
        <path
          d="M10 13.33V10m0-3.33h0M18.34 10a8.33 8.33 0 1 1-16.66 0 8.33 8.33 0 0 1 16.66 0Z"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.67"
        />
      </g>
      <defs>
        <clipPath id="a">
          <path d="M0 0h20v20H0z" fill="#fff" />
        </clipPath>
      </defs>
    </svg>
  );
}

function TreeCheckbox({
  checked,
  indeterminate,
  isRenaming,
  label,
  muted,
  onBlur,
  onChange,
  outline,
}: {
  checked?: boolean;
  indeterminate?: boolean;
  isRenaming?: boolean;
  label: string;
  muted?: boolean;
  onBlur?: (value: string) => void;
  onChange?: (checked: boolean) => void;
  outline?: boolean;
}) {
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isRenaming && divRef.current) {
      divRef.current.focus();
      // move cursor to the end
      const range = document.createRange();
      const sel = window.getSelection();
      range.selectNodeContents(divRef.current);
      range.collapse(false);
      sel?.removeAllRanges();
      sel?.addRange(range);
    }
  }, [isRenaming]);

  return (
    <Field className="flex items-center space-x-0.5 overflow-hidden">
      <Checkbox
        checked={checked}
        className={`group border-gray-5 flex size-4 shrink-0 items-center justify-center rounded-sm border bg-white ${outline ? "" : "data-checked:border-blue-6 data-checked:bg-blue-6"}`}
        onChange={onChange}
      >
        <CheckboxIcon
          className={`opacity-0 group-data-checked:opacity-100 ${outline ? "text-blue-6" : "text-white"}`}
          indeterminate={indeterminate}
        />
      </Checkbox>
      {isRenaming ? (
        <div
          className={`${muted ? "text-gray-5 focus:text-gray-8" : "text-gray-8"} max-w-64 p-1 text-xs font-medium`}
          contentEditable
          onBlur={(e) => {
            return onBlur?.(e.currentTarget.textContent ?? "");
          }}
          ref={divRef}
          title={label}
        >
          {label}
        </div>
      ) : (
        <Label
          className={`${muted ? "text-gray-5" : "text-gray-8"} truncate p-1 text-xs font-medium`}
          title={label}
        >
          {label}
        </Label>
      )}
    </Field>
  );
}

export type TreeItemProps = {
  ghost?: boolean;
  handleProps?: DraggableAttributes;
  onChange?: (id: string, checked: boolean) => void;
  onCollapse?: (id: string, collapsed: boolean) => void;
  onDelete?: (id: string) => void;
  onOpacityChange?: (id: string, opacity: number) => void;
  onRename?: (id: string, name: string) => void;
  onScaleRangeChange?: (id: string, scaleRange?: "large") => void;
  style?: React.CSSProperties;
} & (GroupItem | LayerItem);

const TreeItem = forwardRef<HTMLLIElement, TreeItemProps>(
  (
    {
      ghost,
      handleProps,
      id,
      level = 0,
      onChange,
      onCollapse,
      onDelete,
      onOpacityChange,
      onRename,
      onScaleRangeChange,
      opacity,
      readonly,
      scaleRange,
      title,
      visible,
      ...props
    },
    ref,
  ) => {
    const isGroup = "collapsed" in props && props.collapsed !== undefined;
    const map = useMap();
    const { t } = useI18n();
    const [isEditing, setIsEditing] = useState(false);
    const [legendVisible, setLegendVisible] = useState(false);
    const [checked, setChecked] = useState(visible);
    const [resolution, setResolution] = useState(() => {
      return map.getView().getResolution() ?? 0;
    });

    useEffect(() => {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setChecked(visible);
    }, [visible]);

    useEffect(() => {
      const view = map.getView();
      const onResolutionChange = () => {
        setResolution(view.getResolution() ?? 0);
      };
      view.on("change:resolution", onResolutionChange);
      return () => {
        view.un("change:resolution", onResolutionChange);
      };
    }, [map]);

    const scaleRangeHidden =
      scaleRange !== undefined &&
      resolution > SCALE_RANGE_MAX_RESOLUTION[scaleRange];

    return (
      <li key={id} ref={ref} style={props.style}>
        <div
          className={`group hover:bg-blue-1 ${ghost ? "opacity-50" : ""}`}
          style={{
            paddingLeft: `${level * 2.5 + (!isGroup && level === 0 ? 1.25 : 0)}rem`,
          }}
        >
          <div className="flex min-h-7.5 items-center justify-between">
            <div className="flex overflow-hidden">
              {isGroup && onCollapse ? (
                <button
                  onClick={() => {
                    return onCollapse(id, !props.collapsed);
                  }}
                  type="button"
                >
                  <ChevronDownIcon
                    className={`transform transition-transform ${props.collapsed ? "-rotate-90" : "rotate-0"} `}
                  />
                </button>
              ) : null}
              <TreeCheckbox
                checked={checked}
                indeterminate={isGroup && props.indeterminate}
                isRenaming={isEditing}
                label={title}
                muted={scaleRangeHidden}
                onBlur={(value) => {
                  onRename?.(id, value);
                }}
                onChange={(value) => {
                  setChecked(value);
                  onChange?.(id, value);
                }}
                outline={level > 0}
              />
            </div>
            <div className="text-gray-7 mr-2 hidden space-x-1 group-hover:flex">
              {props.legend ? (
                <button
                  className="hover:text-gray-8"
                  onClick={() => {
                    return setLegendVisible(!legendVisible);
                  }}
                  type="button"
                >
                  <InfoCircleIcon />
                </button>
              ) : null}
              {onRename && readonly !== true ? (
                <button
                  className="hover:text-gray-8"
                  data-test="MapLayerTree-item-edit"
                  onClick={() => {
                    setIsEditing((prev) => {
                      return !prev;
                    });
                  }}
                  type="button"
                >
                  <EditIcon className="h-5 w-5" />
                </button>
              ) : null}
              {onDelete && readonly !== true ? (
                <button
                  className="hover:text-gray-8"
                  data-test="MapLayerTree-item-delete"
                  onClick={() => {
                    return onDelete(id);
                  }}
                  type="button"
                >
                  <TrashIcon />
                </button>
              ) : null}
              {handleProps && (level === 0 || readonly !== true) ? (
                <div
                  {...handleProps}
                  className="hover:text-gray-8 cursor-move"
                  data-test="MapLayerTree-item-move"
                >
                  <HandleIcon className="w-4" />
                </div>
              ) : null}
            </div>
          </div>
          {props.legend && legendVisible ? (
            <img
              alt={t("MapLayerTree.legendAlt", { title })}
              className="pb-1"
              src={props.legend}
            />
          ) : null}
          {isEditing && onOpacityChange ? (
            <div
              className="flex flex-col space-y-1 pt-1 pr-2 pb-2 pl-6"
              data-test="MapLayerTree-item-opacity"
            >
              <label
                className="text-gray-6 text-xs font-medium"
                htmlFor={`opacity-${id}`}
              >
                {t("MapLayerTree.opacity")}
              </label>
              <input
                className="accent-blue-6 cursor-pointer"
                id={`opacity-${id}`}
                max="1"
                min="0"
                onChange={(e) => {
                  onOpacityChange(id, Number(e.target.value));
                }}
                step="0.01"
                type="range"
                value={opacity}
              />
            </div>
          ) : null}
          {isEditing && onScaleRangeChange ? (
            <Field
              className="flex items-center space-x-0.5 pr-2 pb-2 pl-6"
              data-test="MapLayerTree-item-scaleRange"
            >
              <Checkbox
                checked={scaleRange === "large"}
                className="group border-gray-5 flex size-4 shrink-0 items-center justify-center rounded-sm border bg-white"
                onChange={(value) => {
                  onScaleRangeChange(id, value ? "large" : undefined);
                }}
              >
                <CheckboxIcon className="text-blue-6 opacity-0 group-data-checked:opacity-100" />
              </Checkbox>
              <Label className="text-gray-6 p-1 text-xs font-medium">
                {t("MapLayerTree.scaleRange.large")}
              </Label>
            </Field>
          ) : null}
        </div>
      </li>
    );
  },
);
TreeItem.displayName = "TreeItem";

export default TreeItem;
