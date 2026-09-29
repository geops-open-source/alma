import { gql } from "graphql-request";

import TaskForm from "./TaskForm";

import type { UpdateAufgabeMutation } from "@/lib/graphql";

import type { TaskProps } from "./Task";

const updateAufgabeMutation = gql`
  mutation updateAufgabe($data: UpdateAufgabeInput!, $updateTasks: Boolean!) {
    task: updateAufgabe(data: $data, updateParentTasks: $updateTasks) {
      ... on Aufgabe {
        __typename
        ...TaskEvents
      }
      ... on WorkflowProblemGroup {
        ...ProblemTasks
      }
    }
  }
  ${TaskForm.eventsFragment}
  ${TaskForm.problemTasksFragment}
`;

export default function TaskAufgabe(props: TaskProps) {
  return (
    <TaskForm<UpdateAufgabeMutation>
      mutation={updateAufgabeMutation}
      showStatusFields
      {...props}
    />
  );
}
