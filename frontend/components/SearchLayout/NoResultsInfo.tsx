import NoResultsIcon from "@/components/icons/NoResultsIcon";
import { useI18n } from "@/lib/i18n";

export function NoResultsInfo() {
  const { t } = useI18n();
  return (
    <div className="text-blue-8 flex gap-2 bg-white p-5">
      <NoResultsIcon className="text-blue-7 shrink-0" />
      <div>
        <h3 className="font-semibold">{t("search.noResults.heading")}</h3>
        <p className="mt-2 max-w-xl text-xs">{t("search.noResults.verbose")}</p>
      </div>
    </div>
  );
}
