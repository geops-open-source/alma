import { gql } from "graphql-request";
import { usePathname } from "next/navigation";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import Button from "@/components/Button";
import Dialog from "@/components/Dialog";
import Form from "@/components/Form";
import Listbox from "@/components/Listbox";
import client from "@/lib/client";
import { useI18n } from "@/lib/i18n";

import TaskIcon from "./TaskIcon";

import type {
  CreateNotizMutation,
  StartFolgeschrittMutation,
  StartProzessMutation,
  TaskOption,
  TaskType,
} from "@/lib/graphql";

const createNotiz = gql`
  mutation createNotiz($data: CreateNotizInput!) {
    createTask: createNotiz(data: $data) {
      taskId
    }
  }
`;

const createDokument = gql`
  mutation createDokument($data: CreateDokumentInput!) {
    createTask: createDokument(data: $data) {
      taskId
    }
  }
`;

const createAufgabe = gql`
  mutation createAufgabe($data: CreateAufgabeInput!) {
    createTask: createAufgabe(data: $data) {
      taskId
    }
  }
`;

const startProzessMutation = gql`
  mutation startProzess($data: StartProzessInput!) {
    startProzess(data: $data) {
      prozess {
        taskId
      }
    }
  }
`;

const startFolgeschrittMutation = gql`
  mutation startFolgeschritt($data: StartTaskInput!) {
    startFolgeschritt(data: $data) {
      task {
        taskId
      }
    }
  }
`;

const taskTypes: TaskType[] = ["NOTIZ", "DOKUMENT", "AUFGABE"];

const kategorieVariables = {
  kategorie: null,
  oeffentlich: false,
};

export default function StartTaskDialog({
  onClose,
  options = [],
  reloadList,
  sortByTitle,
  taskId,
  vflzId,
  ...props
}: {
  isOpen: boolean;
  onClose: () => void;
  options?: TaskOption[];
  reloadList?: (taskId: string) => void;
  sortByTitle?: boolean;
  taskId?: string;
  title: string;
  vflzId?: string;
}) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();

  // Sort a copy (never mutate the prop) so that the default option is stable
  // across re-renders and refetches. Otherwise the form would be reset to a
  // different default option, overwriting the user's selection.
  const sortedOptions = useMemo(() => {
    return sortByTitle
      ? [...options].sort((a, b) => {
          return t(a.title).localeCompare(t(b.title));
        })
      : options;
  }, [options, sortByTitle, t]);

  const defaultOptionId = sortedOptions.at(0)?.optionId;

  const formValues = useMemo(() => {
    return { optionId: defaultOptionId };
  }, [defaultOptionId]);

  const createTask = useCallback(
    (taskType: TaskType) => {
      const generalVariables = {
        notiz: "",
        startDatum: new Date().toISOString().split("T")[0],
        taskId,
        title: t(`workflow.create.${taskType}`),
        vflzId,
      };
      let mutation, variables;
      if (taskType === "NOTIZ") {
        mutation = createNotiz;
        variables = { data: { ...kategorieVariables, ...generalVariables } };
      } else if (taskType === "DOKUMENT") {
        mutation = createDokument;
        variables = {
          data: { dokument: "", ...kategorieVariables, ...generalVariables },
        };
      } else if (taskType === "AUFGABE") {
        const nowPlus7Days = new Date();
        nowPlus7Days.setDate(new Date().getDate() + 7);
        const faelligkeitsDatum = nowPlus7Days.toISOString().split("T")[0];
        mutation = createAufgabe;
        variables = {
          data: { faelligkeitsDatum, ...generalVariables },
        };
      }
      if (variables && mutation) {
        client
          .request<CreateNotizMutation>(mutation, variables)
          .then((result) => {
            onClose();
            if (result.createTask.taskId) {
              void router.push(
                `${pathname}?id=${result.createTask.taskId}`,
                undefined,
                {
                  scroll: false,
                },
              );
              if (reloadList) {
                reloadList(result.createTask.taskId);
              }
            }
          })
          .catch(console.error);
      }
    },
    [onClose, pathname, reloadList, router, t, taskId, vflzId],
  );

  return (
    <Dialog onClose={onClose} {...props}>
      <Form<{ optionId: string | undefined }>
        className="flex flex-col gap-2"
        model="Task"
        onSubmit={({ optionId }) => {
          client
            .request<StartFolgeschrittMutation | StartProzessMutation>(
              taskId ? startFolgeschrittMutation : startProzessMutation,
              { data: taskId ? { optionId, taskId } : { optionId, vflzId } },
            )
            .then((result) => {
              onClose();
              const { taskId: newTaskId } =
                "startFolgeschritt" in result
                  ? result.startFolgeschritt.task
                  : result.startProzess.prozess;
              if (newTaskId) {
                void router.push(`${pathname}?id=${newTaskId}`, undefined, {
                  scroll: false,
                });
                if (reloadList) {
                  reloadList(newTaskId);
                }
              }
            })
            .catch(console.error);
        }}
        values={formValues}
      >
        {sortedOptions.length > 0 ? (
          <div className="flex w-full items-center">
            <Listbox
              className="w-96"
              name="optionId"
              options={sortedOptions.map(({ optionId, title, type }) => {
                return {
                  label: (
                    <>
                      <TaskIcon
                        className="mr-1 inline shrink-0"
                        taskType={type}
                      />
                      <span className="w-full align-middle text-sm">
                        {t(title)}
                      </span>
                    </>
                  ),
                  value: optionId,
                };
              })}
              required
            />
            <Button className="h-10" type="submit">
              {t("workflow.start")}
            </Button>
          </div>
        ) : null}
        {taskTypes.map((taskType) => {
          return (
            <Button
              data-test={`Workflow-create${taskType}`}
              key={taskType}
              onClick={() => {
                return createTask(taskType);
              }}
              plain
            >
              <TaskIcon taskType={taskType} />
              <span className="ml-2 grow text-left">
                {t(`TaskType.${taskType}`)}
              </span>
            </Button>
          );
        })}
      </Form>
    </Dialog>
  );
}
