import { useEffect, useRef } from "react";
import type { Segment } from "../types/article";

type SubtitleViewProps = {
  segments: Segment[];
  activeSegmentId: string | null;
};

export function SubtitleView({ segments, activeSegmentId }: SubtitleViewProps) {
  const activeElementRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    activeElementRef.current?.scrollIntoView({
      block: "nearest",
      behavior: "smooth",
    });
  }, [activeSegmentId]);

  return (
    <section className="subtitle-panel">
      <div className="subtitle-list">
        {segments.map((segment) => {
          const isActive = segment.id === activeSegmentId;

          return (
            <article
              className={isActive ? "subtitle-card active" : "subtitle-card"}
              key={segment.id}
            >
              <div
                ref={isActive ? activeElementRef : null}
                className="subtitle-card-inner"
              >
                <p className="subtitle-source">{segment.sourceText}</p>
                <p className="subtitle-translation">
                  {segment.translatedText ?? "Translation unavailable"}
                </p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
