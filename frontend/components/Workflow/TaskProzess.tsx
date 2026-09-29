import { gql } from "graphql-request";

import TaskForm from "./TaskForm";

import type { UpdateProzessMutation } from "@/lib/graphql";

import type { TaskProps } from "./Task";

const updateProzessMutation = gql`
  mutation updateProzess($data: UpdateProzessInput!, $updateTasks: Boolean!) {
    task: updateProzess(data: $data, updateChildTasks: $updateTasks) {
      ... on Prozess {
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

export default function TaskProzess(props: TaskProps) {
  return (
    <TaskForm<UpdateProzessMutation>
      mutation={updateProzessMutation}
      showStatusFields
      {...props}
    />
  );
}
