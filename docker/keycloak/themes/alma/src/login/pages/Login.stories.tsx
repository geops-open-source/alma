import type { Meta, StoryObj } from "@storybook/react";
import { createKcPageStory } from "../KcPageStory";

const { KcPageStory } = createKcPageStory({ pageId: "login.ftl" });

const meta = {
  title: "login/login.ftl",
  component: KcPageStory,
} satisfies Meta<typeof KcPageStory>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        realm: {
          registrationAllowed: false,
          rememberMe: false,
        },
      }}
    />
  ),
};

export const WithResetCredentials: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        realm: {
          registrationAllowed: false,
          rememberMe: false,
        },
        auth: {
          showResetCredentials: false,
          showUsername: true,
        },
      }}
    />
  ),
};

export const WithSSO: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        realm: {
          registrationAllowed: false,
          rememberMe: false,
        },
        social: {
          displayInfo: true,
          providers: [
            {
              loginUrl: "sso1",
              alias: "sso1",
              providerId: "sso1",
              displayName: "Mit SSO 1 anmelden",
            },
            {
              loginUrl: "sso2",
              alias: "sso2",
              providerId: "sso2",
              displayName: "Mit SSO 2 anmelden",
            },
          ],
        },
      }}
    />
  ),
};