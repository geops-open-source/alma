import Box from "@/components/Box";
import { useI18n } from "@/lib/i18n";

export default function MissingData() {
  const { t } = useI18n();
  return (
    <Box
      className="mx-auto mt-8 w-64 text-center text-sm"
      data-test="MissingData"
    >
      {t("missingData")}
    </Box>
  );
}
