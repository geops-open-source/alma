import Layout from "@/components/Layout";
import Workflow from "@/components/Workflow";
import { useI18n } from "@/lib/i18n";

export default function WorkflowPage() {
  const { t } = useI18n();
  return (
    <Layout container title={t("workflow.title")}>
      <Workflow />
    </Layout>
  );
}
