import Layout from "@/components/Layout";
import MissingPermission from "@/components/MissingPermission";
import { useI18n } from "@/lib/i18n";
import useCurrentUser from "@/lib/useCurrentUser";

export default function AdminLayout({ children }: React.PropsWithChildren) {
  const currentUser = useCurrentUser();
  const { t } = useI18n();
  return (
    <Layout container title={t("admin.title")}>
      {currentUser.permissions.canEditUser ? (
        <>
          <header>
            <nav>
              <Layout.NavList>
                <Layout.NavItem href="/admin/users">
                  {t("admin.users.title")}
                </Layout.NavItem>
                <Layout.NavItem href="/admin/codelists">
                  {t("admin.codelists.title")}
                </Layout.NavItem>
                <Layout.NavItem href="/admin/system">
                  {t("admin.system.title")}
                </Layout.NavItem>
                <Layout.NavItem href="/admin/fields">
                  {t("admin.fields.title")}
                </Layout.NavItem>
                <Layout.NavItem href="/admin/translations">
                  {t("admin.translations.title")}
                </Layout.NavItem>
              </Layout.NavList>
            </nav>
          </header>
          {children}
        </>
      ) : (
        <MissingPermission />
      )}
    </Layout>
  );
}
