import { gql } from "graphql-request";

import Checkbox from "@/components/Checkbox";
import DatePicker from "@/components/DatePicker";
import Input from "@/components/Input";
import RadioGroup from "@/components/RadioGroup";
import { useI18n } from "@/lib/i18n";

import TaskForm from "./TaskForm";

import type { FormularFeld, UpdateFormularMutation } from "@/lib/graphql";

import type { TaskProps } from "./Task";

const updateFormularMutation = gql`
  mutation updateFormular($data: UpdateFormularInput!) {
    task: updateFormular(data: $data) {
      ... on Formular {
        __typename
        ...TaskEvents
      }
      ... on ProblemGroup {
        __typename
      }
    }
  }
  ${TaskForm.eventsFragment}
`;

function FormularFeld({ type, ...props }: FormularFeld) {
  const { t } = useI18n();
  const label = props.label ? t(props.label) || props.label : "";
  const name = `eingaben.${props.name}`;
  if (type === "bool") {
    return <Checkbox label={label} name={name} />;
  } else if (type === "date") {
    return <DatePicker label={label} name={name} required />;
  } else if (type === "int") {
    return <Input label={label} name={name} required type="integer" />;
  } else if (type === "str") {
    return "choices" in props && props.choices && props.choices.length > 0 ? (
      <RadioGroup
        label={label || t("workflow.radioGroupLabel")}
        name={name}
        options={props.choices.map((c) => {
          return {
            label: t(c.label) || c.label,
            value: c.value,
          };
        })}
        required
      />
    ) : (
      <Input label={label || name.split(".").pop()} name={name} required />
    );
  } else if (type === "title") {
    return <div className="text-gray-7 text-sm">{label}</div>;
  }
  return null;
}

export default function TaskFormular({ task, ...props }: TaskProps) {
  return (
    <TaskForm<UpdateFormularMutation>
      mutation={updateFormularMutation}
      task={task}
      {...props}
    >
      {task && "felder" in task
        ? task.felder.map((feld) => {
            return <FormularFeld key={feld.name} {...feld} />;
          })
        : null}
    </TaskForm>
  );
}
