import { useI18n } from "@/lib/i18n";

export default function PasswordRules() {
  const { t } = useI18n();
  return (
    <ul className="bg-yellow-9 text-gray-7 list-disc rounded-lg p-4 pl-8 text-sm">
      <li>{t("PasswordRules.length")}</li>
      <li>{t("PasswordRules.symbols")}</li>
      <li>{t("PasswordRules.numbers")}</li>
      <li>{t("PasswordRules.lowerUpperCase")}</li>
    </ul>
  );
}
