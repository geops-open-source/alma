import localFont from "next/font/local";

import tw from "@/lib/tw";

const inter = localFont({
  src: "../lib/Inter.woff2",
  variable: "--font-inter",
});

const blokk = localFont({
  src: "../lib/BLOKK.woff2",
  variable: "--font-blokk",
});

export default tw`${blokk.variable} ${inter.variable} font-sans`;
