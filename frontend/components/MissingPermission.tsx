import Box from "@/components/Box";
import { useI18n } from "@/lib/i18n";
import useCurrentUser from "@/lib/useCurrentUser";

export default function MissingPermission() {
  const currentUser = useCurrentUser();
  const { t } = useI18n();
  return currentUser.isLoading ? null : (
    <Box
      className="mx-auto mt-8 w-64 text-center text-sm"
      data-test="MissingPermission"
    >
      {t("missingPermission")}
    </Box>
  );
}
