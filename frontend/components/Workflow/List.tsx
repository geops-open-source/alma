import { usePathname } from "next/navigation";
import { useRouter } from "next/router";
import { Fragment, useEffect, useMemo, useRef, useState } from "react";

import ChevronIcon from "@/components/icons/ChevronIcon";
import Spinner from "@/components/Spinner";
import { FaelligkeitStatus, TaskType } from "@/lib/graphql";
import { useI18n } from "@/lib/i18n";
import toLocaleDateString from "@/lib/toLocaleDateString";
import tw from "@/lib/tw";
import useDocumentFile from "@/lib/useDocumentFile";

import TaskIcon from "./TaskIcon";

import type { TaskStatus, WorkflowItemFragment } from "@/lib/graphql";

const showAllDates: TaskType[] = [TaskType.Aufgabe, TaskType.Prozess];

function IconAvatar({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 128 128"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="64" cy="64" fill="currentColor" r="64" />
      <g fill="#fff">
        <path d="M103 102.139C93.094 111.92 79.35 118 64.164 118c-15.358 0-29.235-6.232-39.164-16.21V95.2C25 86.81 31.981 80 40.6 80h46.8c8.619 0 15.6 6.81 15.6 15.2v6.939ZM63.996 24C51.294 24 41 34.294 41 46.996 41 59.706 51.294 70 63.996 70 76.7 70 87 59.706 87 46.996 87 34.294 76.699 24 63.996 24" />
      </g>
    </svg>
  );
}

function getFaelligkeitStatusColor(
  faelligkeitsStatus: FaelligkeitStatus,
): "green" | "red" | "yellow" {
  switch (faelligkeitsStatus) {
    case FaelligkeitStatus.FaelligNaechsteWoche:
      return "yellow";
    case FaelligkeitStatus.FaelligSpaeter:
      return "green";
    case FaelligkeitStatus.Ueberfaellig:
      return "red";
    default:
      return "green";
  }
}

function getColorClasses(color?: "green" | "red" | "yellow") {
  switch (color) {
    case "green":
      return tw`text-green-9 border-green-3 bg-green-1`;
    case "red":
      return tw`text-red-6 border-red-3 bg-red-2`;
    case "yellow":
      return tw`text-orange-7 border-orange-3 bg-orange-1`;
    default:
      return tw`text-gray-7 border-gray-4 bg-gray-2`;
  }
}

function StatusPill({
  faelligkeitsStatus,
  status,
}: {
  faelligkeitsStatus?: FaelligkeitStatus;
  status: TaskStatus;
}) {
  const { t } = useI18n();
  let color = getColorClasses();
  if (status === "OFFEN" && faelligkeitsStatus) {
    color = getColorClasses(getFaelligkeitStatusColor(faelligkeitsStatus));
  }
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs ${color}`}>
      {t(`TaskStatus.${status}`)}
    </span>
  );
}

function DatePill({
  color,
  date,
  label,
}: {
  color?: "green" | "red" | "yellow";
  date: string;
  label?: string;
}) {
  const colors = getColorClasses(color);
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-xs text-nowrap ${colors}`}
    >
      {label && `${label}: `}
      {toLocaleDateString(date)}
    </span>
  );
}

interface TaskTree {
  children: TaskTree[];
  task: WorkflowItemFragment;
}

function getItemTree(
  items: WorkflowItemFragment[],
  parentId: string,
): TaskTree[] {
  return items
    .filter((task) => {
      return task.parentId === parentId;
    })
    .map((task) => {
      return {
        children: getItemTree(items, task.taskId),
        task: task,
      };
    });
}

function hasSelectedDescendant(
  subItems: TaskTree[],
  selectedTaskId?: string,
): boolean {
  if (!selectedTaskId) {
    return false;
  }

  return subItems.some((subItem): boolean => {
    return (
      subItem.task.taskId === selectedTaskId ||
      hasSelectedDescendant(subItem.children, selectedTaskId)
    );
  });
}

function Item({
  compact = false,
  level = 0,
  onClick,
  selectedTaskId,
  subItems,
  task,
  withVflzInfo = false,
}: {
  compact?: boolean;
  level?: number;
  onClick?: (taskId?: string) => void;
  selectedTaskId?: string;
  subItems: TaskTree[];
  task: WorkflowItemFragment;
  withVflzInfo?: boolean;
}) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const path =
    pathname?.split("/").pop() === "workflow"
      ? pathname
      : `/vflz/${task.vflz.vflzId}/workflow`;
  const defaultExpanded = useMemo(() => {
    if (compact) {
      return task.status !== "ABGESCHLOSSEN";
    }
    return true;
  }, [compact, task.status]);
  const [expanded, setExpanded] = useState(defaultExpanded);
  const itemRef = useRef<HTMLDivElement>(null);
  const isSelected = task.taskId === selectedTaskId;
  const documentFile = useDocumentFile(
    task.type === TaskType.Dokument && "dokument" in task
      ? task.dokument
      : null,
  );
  const hasUploadedDocument = documentFile !== null;
  const containsSelectedTask = useMemo(() => {
    return hasSelectedDescendant(subItems, selectedTaskId);
  }, [selectedTaskId, subItems]);
  const isExpanded = expanded || (compact && containsSelectedTask);

  const openTask = () => {
    void router.push(`${path}?id=${task.taskId}`, undefined, {
      scroll: false,
    });
    onClick?.(task.taskId);
  };

  const triggerDocumentDownload = () => {
    if (!documentFile) {
      return false;
    }
    const link = document.createElement("a");
    link.href = `/api/documents/${documentFile.id}/file`;
    link.download = documentFile.metadata.title;
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    link.remove();
    return true;
  };

  useEffect(() => {
    if (!isSelected) {
      return;
    }

    itemRef.current?.scrollIntoView({ block: "nearest" });
  }, [isSelected]);

  return (
    <div className="group">
      <div
        className={`hover:bg-gray-3 flex ${isSelected ? "" : "cursor-pointer"} items-start gap-2 ${level === 2 && !compact ? "pt-1" : "pt-2"} ${level === 0 ? "group-first:pt-4" : ""} ${isSelected ? "bg-gray-3" : ""}`}
        data-test={`Workflow-item-${task.type}`}
        onClick={() => {
          if (isSelected) {
            return;
          }
          openTask();
        }}
        onKeyDown={(event) => {
          if (isSelected) {
            return;
          }
          if (event.key !== "Enter") {
            return;
          }

          openTask();
        }}
        ref={itemRef}
        role="link"
        style={{ paddingLeft: level * 40 }}
        tabIndex={0}
      >
        <div className="flex">
          {compact && subItems.length > 0 ? (
            <button
              className="z-40 px-1.5 py-2.5"
              onClick={() => {
                return setExpanded(!expanded);
              }}
            >
              <ChevronIcon
                className={`text-gray-6 transition-transform ${isExpanded ? "rotate-180" : "rotate-90"}`}
              />
            </button>
          ) : (
            <div className="size-6" />
          )}
          <div
            className={`z-10 rounded-full p-0.5 ${task.faelligkeitsDatum && task.status === "OFFEN" ? getColorClasses(getFaelligkeitStatusColor(task.faelligkeitsStatus)) : "text-gray-7 bg-gray-1"} ${
              level > 0 &&
              "before:content-[] before:border-gray-5 before:absolute before:top-0" +
                " before:left-(--left-offset) before:h-5.5 before:w-2 before:rounded-bl-sm before:border-b before:border-l"
            } ${compact && subItems.length > 0 ? "before:w-2" : "before:w-6"} `}
            data-test="Task-Icon"
            style={
              {
                "--left-offset": `${36 + (level > 0 ? (level - 1) * 40 : 0)}px`,
              } as React.CSSProperties
            }
          >
            <TaskIcon taskType={task.type} />
          </div>
        </div>
        <div
          // eslint-disable-next-line no-nested-ternary
          className={`relative pr-2 ${compact ? "pb-3" : level === 2 ? "pb-0" : "pb-1"}`}
        >
          <div
            className={`pt-1 text-sm ${isSelected ? "font-bold" : "font-medium"} ${hasUploadedDocument ? "text-blue-7" : ""}`}
          >
            {hasUploadedDocument ? (
              <a
                className="text-blue-7"
                href={`/api/documents/${documentFile.id}/file`}
                onClick={(event) => {
                  event.stopPropagation();
                  event.preventDefault();
                  triggerDocumentDownload();
                  openTask();
                }}
              >
                {t(task.title) || task.title}
              </a>
            ) : (
              t(task.title) || task.title
            )}
          </div>
          {withVflzInfo && level === 0 ? (
            <div className="text-gray-7 pt-1 text-xs font-medium">
              {task.vflz.combinedId} {task.vflz.bezeichnung}
            </div>
          ) : null}
          <div
            className={
              subItems.length > 0 && isExpanded
                ? "before:content-[] before:border-gray-5 before:absolute before:top-0 before:-ml-6" +
                  " before:h-full before:border-l"
                : ""
            }
          >
            {compact ? null : (
              <div className="flex flex-wrap items-center gap-2 py-2">
                {showAllDates.includes(task.type) && task.status && (
                  <StatusPill
                    faelligkeitsStatus={task.faelligkeitsStatus}
                    status={task.status}
                  />
                )}
                {task.startDatum && (
                  <DatePill
                    date={task.startDatum}
                    label={
                      showAllDates.includes(task.type)
                        ? t("workflow.date.start")
                        : undefined
                    }
                  />
                )}
                {showAllDates.includes(task.type) && task.endDatum && (
                  <DatePill
                    date={task.endDatum}
                    label={t("workflow.date.end")}
                  />
                )}
                {showAllDates.includes(task.type) && task.faelligkeitsDatum && (
                  <DatePill
                    color={
                      task.status === "OFFEN"
                        ? getFaelligkeitStatusColor(task.faelligkeitsStatus)
                        : undefined
                    }
                    date={task.faelligkeitsDatum}
                    label={t("workflow.date.due")}
                  />
                )}
              </div>
            )}
            {(!compact ||
              task.type === TaskType.Dokument ||
              task.type === TaskType.Notiz) &&
              task.notiz && (
                <div
                  className={`text-gray-6 w-full pt-1 pr-2 text-sm italic ${
                    compact ? "line-clamp-1" : "mb-2 line-clamp-2"
                  }`}
                >
                  {task.notiz.split("\n").map((line, i) => {
                    return (
                      <Fragment key={i}>
                        {line}
                        <br />
                      </Fragment>
                    );
                  })}
                </div>
              )}
            {!compact &&
              task.sachbearbeitung &&
              task.sachbearbeitung.length > 0 && (
                <div className="text-gray-6 flex items-center gap-2 pb-1 text-xs font-medium">
                  <IconAvatar className="size-5" />
                  {task.sachbearbeitung
                    .map(({ subjekt: s }) => {
                      return [s.vorname, s.name].filter(Boolean).join(" ");
                    })
                    .join(", ")}
                </div>
              )}
          </div>
        </div>
      </div>
      {isExpanded &&
        subItems.map((c, i) => {
          return (
            <div
              className={`${subItems.at(i + 1) ? "before:border-l" : ""} before:border-gray-5 before:content-[] relative border-0 before:absolute before:top-0 before:left-(--before-padding) before:z-10 before:h-full before:pl-(--before-padding)`}
              key={`${c.task.taskId}-${c.task.status}-${compact ? "compact" : "full"}`}
              style={
                {
                  "--before-padding": `${level * 40 + 36}px`,
                } as React.CSSProperties
              }
            >
              <Item
                compact={compact}
                level={level + 1}
                onClick={onClick}
                selectedTaskId={selectedTaskId}
                subItems={c.children}
                task={c.task}
              />
            </div>
          );
        })}
    </div>
  );
}

export default function List({
  asTree,
  compactView = false,
  isLoading,
  items = [],
  onTaskSelect,
  selectedTaskId,
  withVflzInfo = false,
}: {
  asTree?: boolean;
  compactView?: boolean;
  isLoading?: boolean;
  items?: WorkflowItemFragment[];
  onTaskSelect?: (taskId?: string) => void;
  selectedTaskId?: string;
  withVflzInfo?: boolean;
}) {
  const { t } = useI18n();
  const taskItems = asTree
    ? items
        .filter((g) => {
          return g.parentId === null;
        })
        .map((g) => {
          return {
            children: getItemTree(items, g.taskId),
            task: g,
          };
        })
    : items.map((g) => {
        return { children: [], task: g };
      });

  if (isLoading) {
    return (
      <div className="flex justify-center p-4">
        <Spinner className="size-6" />
      </div>
    );
  }

  return taskItems.length === 0 ? (
    <div className="p-4 text-sm">{t("workflow.noResults")}</div>
  ) : (
    taskItems.map((g) => {
      return (
        <Item
          compact={compactView}
          key={`${g.task.taskId}-${g.task.status}-${compactView ? "compact" : "full"}`}
          onClick={onTaskSelect}
          selectedTaskId={selectedTaskId}
          subItems={g.children}
          task={g.task}
          withVflzInfo={withVflzInfo}
        />
      );
    })
  );
}
