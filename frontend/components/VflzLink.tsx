import Link, { type LinkProps } from "next/link";
import { useRouter } from "next/router";
import { type PropsWithChildren, useEffect, useState } from "react";

import getVflzUrl from "@/lib/getVflzUrl";

import type { GetVflzUrlOptions } from "@/lib/getVflzUrl";

export default function VflzLink({
  children,
  options,
  vflzId,
  ...props
}: Omit<LinkProps, "href"> &
  PropsWithChildren<{
    className?: string;
    options?: GetVflzUrlOptions;
    vflzId: string;
  }>) {
  const router = useRouter();
  const [href, setHref] = useState<string>(() => {
    return getVflzUrl(vflzId, options);
  });

  useEffect(() => {
    const onHashchange = () => {
      return setHref(getVflzUrl(vflzId, options));
    };
    window.addEventListener("hashchange", onHashchange);
    return () => {
      return window.removeEventListener("hashchange", onHashchange);
    };
  }, [options, vflzId]);

  return (
    <Link
      {...props}
      href={href}
      onClick={(event) => {
        event.preventDefault();
        void router.push(getVflzUrl(vflzId, options));
      }}
    >
      {children}
    </Link>
  );
}
