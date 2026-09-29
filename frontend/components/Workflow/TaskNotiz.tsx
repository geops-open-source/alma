import { gql } from "graphql-request";

import ClickableUrlField from "../ClickableUrlField";

import TaskForm from "./TaskForm";

import type { UpdateNotizMutation } from "@/lib/graphql";

import type { TaskProps } from "./Task";

const updateNotizMutation = gql`
  mutation updateNotiz($data: UpdateNotizInput!) {
    task: updateNotiz(data: $data) {
      ... on Notiz {
        __typename
        ...TaskEvents
      }
    }
  }
  ${TaskForm.eventsFragment}
`;

export default function TaskNotiz(props: TaskProps) {
  return (
    <TaskForm<UpdateNotizMutation>
      mutation={updateNotizMutation}
      showKategorieFields
      {...props}
    >
      <ClickableUrlField name="url" />
    </TaskForm>
  );
}
