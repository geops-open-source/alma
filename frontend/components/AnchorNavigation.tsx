import throttle from "lodash/throttle";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useFormContext } from "react-hook-form";

import XCircleIcon from "@/components/icons/XCircleIcon";

const eventListenerOptions = { capture: true, passive: true };

export interface AnchorNavItem {
  fields: string[];
  id: string;
  legend: string;
}

export default function AnchorNavigation({
  items,
}: {
  items: AnchorNavItem[];
}) {
  const { formState } = useFormContext();
  const [activeItemId, setActiveItemId] = useState(items.at(0)?.id);
  const router = useRouter();

  useEffect(() => {
    let skipScrollEvent = false;

    function onScroll() {
      if (skipScrollEvent) {
        skipScrollEvent = false;
        return;
      }
      let newActiveItemId: null | string | undefined;
      if (window.scrollY <= 0) {
        newActiveItemId = null;
      } else if (
        window.scrollY + window.innerHeight >=
        document.body.scrollHeight
      ) {
        newActiveItemId = items.at(-1)?.id;
      } else {
        newActiveItemId = items.find((item) => {
          const anchor = document.getElementById(item.id);
          return anchor ? anchor.getBoundingClientRect().top >= 0 : false;
        })?.id;
      }

      if (newActiveItemId) {
        setActiveItemId(newActiveItemId);
        const url = `#${newActiveItemId}`;
        window.history.replaceState(window.history.state, "", url);
      } else if (newActiveItemId === null) {
        setActiveItemId(items.at(0)?.id);
        const url = window.location.pathname;
        window.history.replaceState(window.history.state, "", url);
      }
    }

    const throttledOnScroll = throttle(onScroll, 500, { leading: false });
    window.addEventListener("scroll", throttledOnScroll, eventListenerOptions);

    function onHashchange() {
      skipScrollEvent = true;
      const hash = window.location.hash.substring(1);
      const activeItem = items.find((item) => {
        return item.id === hash;
      });
      if (activeItem) {
        setActiveItemId(activeItem.id);
      }
    }

    window.addEventListener("hashchange", onHashchange, eventListenerOptions);

    return () => {
      window.removeEventListener("scroll", throttledOnScroll, true);
      window.removeEventListener("hashchange", onHashchange, true);
    };
  }, [items]);

  useEffect(() => {
    const scrollAnchorIntoView = () => {
      setTimeout(() => {
        const anchor = document.getElementById(window.location.hash.slice(1));
        anchor?.scrollIntoView();
      }, 500); // wait for the page to render
    };
    scrollAnchorIntoView();
    router.events.on("routeChangeComplete", scrollAnchorIntoView);
    return () => {
      return router.events.off("routeChangeComplete", scrollAnchorIntoView);
    };
  }, [router]);

  return (
    <div>
      <nav className="sticky top-38 mt-4 w-40 xl:w-48">
        <ul className="space-y-1">
          {items.map((item, index) => {
            return (
              <li key={index}>
                <a
                  className={`hover:bg-gray-3 hover:text-gray-7 flex space-x-2 rounded-md p-2 px-3 py-2 text-sm ${activeItemId === item.id ? "bg-gray-3 text-gray-7 font-bold" : "text-gray-6 font-medium"}`}
                  href={`#${item.id}`}
                >
                  <span>{item.legend}</span>
                  {item.fields.some((f) => {
                    return f in formState.errors;
                  }) ? (
                    <XCircleIcon className="text-red-5" />
                  ) : null}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
