import Layout from "@/components/Layout";
import { useI18n } from "@/lib/i18n";

export default function NotFoundPage() {
  const { t } = useI18n();
  return <Layout error={{}} title={t("notFound")} />;
}
