import type { Meta, StoryObj } from "@storybook/react";
import { createKcPageStory } from "../KcPageStory";

const { KcPageStory } = createKcPageStory({ pageId: "login-otp.ftl" });

const meta = {
  title: "login/login-otp.ftl",
  component: KcPageStory,
} satisfies Meta<typeof KcPageStory>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        auth: {
          attemptedUsername: "foo@bar.com",
          showResetCredentials: false,
          showUsername: true,
        },
        otpLogin: {
          userOtpCredentials: [],
        },
      }}
    />
  ),
};
