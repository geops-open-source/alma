import { gql } from "graphql-request";
import useSWR from "swr";

import Spinner from "@/components/Spinner";
import { useI18n } from "@/lib/i18n";

import TaskAufgabe from "./TaskAufgabe";
import TaskDokument from "./TaskDokument";
import TaskForm from "./TaskForm";
import TaskFormular from "./TaskFormular";
import TaskNotiz from "./TaskNotiz";
import TaskProzess from "./TaskProzess";

import type { KeyedMutator } from "swr";

import type { TaskQuery, VflzWorkflowLayoutQuery } from "@/lib/graphql";

export interface TaskProps {
  mutatePage?: KeyedMutator<VflzWorkflowLayoutQuery>;
  mutateTask: KeyedMutator<TaskQuery>;
  reloadList?: (taskId?: string) => void;
  task: TaskQuery["task"];
}

const queryTask = gql`
  query task($taskId: ID!, $withVflzInfo: Boolean!) {
    task(taskId: $taskId) {
      type
      ...TaskForm
    }
  }
  ${TaskForm.fragment}
`;

export default function Task({
  taskId,
  withVflzInfo = false,
  ...props
}: {
  mutatePage?: KeyedMutator<VflzWorkflowLayoutQuery>;
  reloadList?: (taskId?: string) => void;
  taskId?: null | string;
  withVflzInfo?: boolean;
}) {
  const { t } = useI18n();
  const { data, isLoading, mutate } = useSWR<TaskQuery>(
    taskId && [queryTask, { taskId, withVflzInfo }],
  );

  if (isLoading) {
    return (
      <div className="flex justify-center">
        <Spinner className="size-6" />
      </div>
    );
  }

  if (!data) {
    return <span>{t("workflow.noneSelected")}</span>;
  }

  switch (data.task.type) {
    case "AUFGABE":
      return <TaskAufgabe mutateTask={mutate} task={data.task} {...props} />;
    case "DOKUMENT":
      return <TaskDokument mutateTask={mutate} task={data.task} {...props} />;
    case "FORMULAR":
      return <TaskFormular mutateTask={mutate} task={data.task} {...props} />;
    case "NOTIZ":
      return <TaskNotiz mutateTask={mutate} task={data.task} {...props} />;
    case "PROZESS":
      return <TaskProzess mutateTask={mutate} task={data.task} {...props} />;
  }
}
