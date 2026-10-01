import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { motion, useScroll, useSpring, useTransform } from "motion/react";
import { school } from "../data/site";
import { useMediaQuery } from "../hooks/useMediaQuery";
import { CTA, LazyVideo, Reveal, Scribble, SectionLabel } from "./ui/primitives";
import { ArrowUpRight } from "./ui/Icons";

type Stage = {
  n: string;
  stage: string;
  classes: string;
  body: string;
  tags: string[];
  media: ReactNode;
};

const stages: Stage[] = [
  {
    n: "01",
    stage: "Early Years",
    classes: "Play Group · Nursery · Prep",
    body: "Colour, play and hands-on activity in bright classrooms. Children learn to share a table, hold a pencil and look forward to school.",
    tags: ["Activity-based", "Colourful rooms", "Gentle routines"],
    media: (
      <LazyVideo
        src="./media/early-years.mp4"
        poster="./media/early-years-poster.jpg"
        label="Young children colouring at red and yellow tables"
        className="size-full object-cover"
      />
    ),
  },
  {
    n: "02",
    stage: "Primary",
    classes: "Class 1 – 5",
    body: "Reading, writing and numbers built on solid foundations, in a lively room where curiosity is encouraged, not hushed.",
    tags: ["Strong basics", "Uniform & routine", "Pre-class activities"],
    media: (
      <LazyVideo
        src="./media/classroom.mp4"
        poster="./media/classroom-poster.jpg"
        label="Primary students in uniform colouring at green desks"
        className="size-full object-cover"
      />
    ),
  },
  {
    n: "03",
    stage: "Middle",
    classes: "Class 6 – 8",
    body: "The gear shifts. Lessons move to concept-based learning on the Single National Curriculum, so students understand the why, not just the answer.",
    tags: ["Single National Curriculum", "No rote learning"],
    media: (
      <div className="ruled relative flex size-full flex-col justify-between bg-chalk p-7 text-ink sm:p-9">
        <span className="eyebrow text-muted">Classroom rule no. 1</span>
        <p className="heading text-[clamp(2.3rem,3.7vw,3.9rem)] leading-[0.95]">
          Don’t memorise it.
          <br />
          <span className="relative inline-block text-royal">
            Understand it.
            <Scribble className="absolute -bottom-2 left-0 h-3 w-full" />
          </span>
        </p>
        <span className="text-sm text-muted">Concept first. The marks follow.</span>
      </div>
    ),
  },
  {
    n: "04",
    stage: "Matric",
    classes: "Class 9 – 10",
    body: "Focused, disciplined preparation for the board examinations, and a proud record of toppers to show for it.",
    tags: ["Board-exam focus", "Toppers 2026"],
    media: (
      <div className="relative flex size-full flex-col justify-between overflow-hidden bg-sun p-7 text-ink sm:p-9">
        <span className="eyebrow text-ink/70">Results</span>
        <div>
          <p className="display text-[clamp(5.5rem,11vw,10rem)] leading-[0.8]">100%</p>
          <p className="mt-3 max-w-xs text-[1.05rem] font-medium">
            The result we work towards every year, with top positions on the board.
          </p>
        </div>
        <a
          href={school.videos.toppers}
          target="_blank"
          rel="noopener noreferrer"
          className="group inline-flex items-center gap-2 self-start rounded-full bg-ink px-4 py-2.5 text-sm font-semibold text-chalk"
        >
          Watch: 9th Class toppers 2026
          <ArrowUpRight size={16} className="transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </a>
      </div>
    ),
  },
];

export function Journey() {
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  return (
    <section id="journey" data-nav-dark aria-labelledby="journey-title" className="relative bg-ink text-chalk">
      {isDesktop ? <HorizontalJourney /> : <StackedJourney />}
    </section>
  );
}

function JourneyIntro() {
  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <SectionLabel n="02" tone="light">
          Classes
        </SectionLabel>
        <h2 id="journey-title" className="heading mt-5 text-[clamp(2.6rem,min(6vw,9svh),5.6rem)]">
          From Play Group
          <br />
          <span className="text-sun">to Matric.</span>
        </h2>
      </div>
      <p className="max-w-sm text-white/70">
        One school for every step. Our youngest learn through colour and activity; our seniors through concepts and
        focused board preparation.
      </p>
    </div>
  );
}

/* ---------- Desktop: pinned, scroll moves the track sideways ---------- */
function HorizontalJourney() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [distance, setDistance] = useState(0);

  useLayoutEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    const measure = () => setDistance(Math.max(0, track.scrollWidth - window.innerWidth));
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(track);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  const { scrollYProgress } = useScroll({ target: sectionRef, offset: ["start start", "end end"] });
  const smooth = useSpring(scrollYProgress, { stiffness: 160, damping: 32, restDelta: 0.0005 });
  const x = useTransform(smooth, [0, 1], [0, -distance]);
  const planeX = useTransform(smooth, [0, 1], ["0%", "100%"]);
  const trail = useTransform(smooth, [0, 1], [0, 1]);

  return (
    <div ref={sectionRef} style={{ height: `calc(100svh + ${distance}px)` }} className="relative">
      <div className="sticky top-0 flex h-svh flex-col overflow-hidden pb-10 pt-28">
        <div className="container-x">
          <JourneyIntro />
        </div>

        <motion.div ref={trackRef} style={{ x }} className="mt-10 flex min-h-0 flex-1 gap-6 pl-12 pr-[12vw]">
          {stages.map((s) => (
            <StagePanel key={s.n} s={s} className="w-[min(78vw,64rem)] shrink-0" />
          ))}
          <FinalPanel className="w-[min(46vw,34rem)] shrink-0" />
        </motion.div>

        {/* Flight path: the paper plane travels from Play Group to Matric as you scroll. */}
        <div className="container-x mt-8">
          <div className="relative h-8">
            <div className="absolute inset-x-0 top-1/2 border-t-2 border-dashed border-white/20" />
            <motion.div
              className="absolute left-0 top-1/2 h-0.5 w-full origin-left -translate-y-[1px] bg-sun"
              style={{ scaleX: trail }}
            />
            <div className="absolute inset-x-0 top-1/2 flex -translate-y-1/2 justify-between">
              {["Play Group", "Primary", "Middle", "Matric"].map((l) => (
                <span key={l} className="relative flex flex-col items-center">
                  <span className="size-2.5 rounded-full bg-white/40" />
                  <span className="absolute top-4 whitespace-nowrap text-xs text-white/50">{l}</span>
                </span>
              ))}
            </div>
            <motion.div className="absolute inset-y-0 left-0 right-0" style={{ x: planeX }}>
              <PaperPlane className="absolute -left-4 top-1/2 size-8 -translate-y-1/2 text-sun" />
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Mobile / tablet: stacked cards ---------- */
function StackedJourney() {
  return (
    <div className="container-x py-24 sm:py-28">
      <JourneyIntro />
      <ol className="relative mt-14 grid gap-8 border-l-2 border-dashed border-white/20 pl-5 sm:pl-8">
        {stages.map((s) => (
          <Reveal as="li" key={s.n} className="relative">
            <span className="absolute -left-[1.72rem] top-6 size-3 rounded-full bg-sun ring-4 ring-ink sm:-left-[2.47rem]" />
            <StagePanel s={s} />
          </Reveal>
        ))}
        <Reveal as="li" className="relative">
          <PaperPlane className="absolute -left-[2.15rem] top-4 size-7 rotate-90 text-sun sm:-left-[2.9rem]" />
          <FinalPanel />
        </Reveal>
      </ol>
    </div>
  );
}

function StagePanel({ s, className = "" }: { s: Stage; className?: string }) {
  return (
    <article
      className={`grid overflow-hidden rounded-[var(--radius-card)] bg-ink-2 ring-1 ring-inset ring-white/10 lg:h-full lg:grid-cols-[1fr_1.15fr] ${className}`}
    >
      <div className="flex flex-col p-6 sm:p-9">
        <div className="flex items-baseline justify-between">
          <span className="display text-[3.4rem] text-white/15 sm:text-[4.5rem]">{s.n}</span>
          <span className="eyebrow text-sun">{s.classes}</span>
        </div>
        <h3 className="heading mt-4 text-[2.3rem] sm:text-[3rem] lg:mt-auto">{s.stage}</h3>
        <p className="mt-3 max-w-md text-white/75">{s.body}</p>
        <ul className="mt-6 flex flex-wrap gap-2">
          {s.tags.map((t) => (
            <li key={t} className="rounded-full bg-white/[0.07] px-3 py-1.5 text-[0.8rem] text-white/80 ring-1 ring-inset ring-white/10">
              {t}
            </li>
          ))}
        </ul>
      </div>
      <div className="relative aspect-[4/3] overflow-hidden lg:aspect-auto">{s.media}</div>
    </article>
  );
}

function FinalPanel({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col justify-center rounded-[var(--radius-card)] p-6 sm:p-9 lg:h-full ${className}`}>
      <p lang="ur" className="urdu text-[1.6rem] text-sun">
        {school.sloganUr}
      </p>
      <p className="display mt-1 text-[clamp(3.6rem,7vw,7rem)] uppercase">
        Big
        <br />
        flight.
      </p>
      <p className="mt-4 max-w-xs text-white/70">Every Matric student here once took a first small step in Play Group.</p>
      <CTA href="#admissions" className="mt-7 self-start">
        Start in {school.session}
      </CTA>
    </div>
  );
}

function PaperPlane({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <path d="M3 15.2 28.5 4.5 22.4 27.3l-6.6-6.1-4.6 4.4.4-6.6L3 15.2Z" fill="currentColor" />
      <path d="m11.6 19 16.9-14.5" stroke="#0E1838" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  );
}
