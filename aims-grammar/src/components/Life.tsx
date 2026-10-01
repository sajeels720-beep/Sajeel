import { useRef, useState } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { school } from "../data/site";
import { Reveal, SectionLabel, MaskLines } from "./ui/primitives";
import { ArrowUpRight, Facebook, Instagram, Play, YouTube } from "./ui/Icons";

type Photo = { src: string; alt: string; title: string; note: string; w: number; h: number; pos?: string };

const photos: Record<string, Photo> = {
  splash: {
    src: "./media/pool-party-splash.webp",
    alt: "Children splashing water at each other in a paddling pool in the school courtyard",
    title: "Summer Pool Party",
    note: "Splash day in the school courtyard.",
    w: 654,
    h: 888,
  },
  fruit: {
    src: "./media/fruit-day-2026.webp",
    alt: "A smiling young boy dressed as an apple, holding a plate of cherries",
    title: "Fruit Day 2026",
    note: "Play Group and Nursery came dressed as their favourite fruit.",
    w: 623,
    h: 971,
  },
  prize: {
    src: "./media/prize-distribution.webp",
    alt: "A young student in a yellow T-shirt holding his AIMS Grammar High School award shield",
    title: "Prize Distribution",
    note: "Every effort recognised on stage.",
    w: 616,
    h: 903,
    pos: "50% 20%",
  },
  welcome: {
    src: "./media/summer-pool-party-welcome.webp",
    alt: "A colourful board reading Welcome to Summer Pool Party, with a child walking past",
    title: "Welcome board",
    note: "The sign that greeted everyone at the pool party.",
    w: 618,
    h: 794,
  },
};

const moments = [
  "Fruit Day",
  "Father’s Day activities",
  "Paper-plate wall hangings",
  "Welcome Back week",
  "14 August celebrations",
  "Defence Day tribute",
  "Annual functions",
  "Debates",
  "Science & art exhibitions",
];

export function Life() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const yB = useTransform(scrollYProgress, [0, 1], [110, -110]);
  const yC = useTransform(scrollYProgress, [0, 1], [50, -50]);

  return (
    <section id="life" aria-labelledby="life-title" className="relative overflow-hidden bg-chalk pb-16 pt-24 sm:pb-20 sm:pt-32">
      <div className="container-x">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <SectionLabel n="04">School life</SectionLabel>
            <h2 id="life-title" className="heading mt-5 text-[clamp(2.6rem,6vw,5.4rem)]">
              <MaskLines lines={["More than", "a classroom."]} />
            </h2>
          </div>
          <Reveal className="max-w-sm text-muted">
            Annual functions, debates, exhibitions and a lot of dressing up. This is where shy children find their
            voice, and where the “confident” part of our promise is built.
          </Reveal>
        </div>

        {/* Desktop: three columns drifting at different speeds */}
        <div ref={ref} className="mt-16 hidden gap-6 lg:grid lg:grid-cols-12">
          <div className="col-span-5 space-y-6">
            <PhotoCard p={photos.splash} className="aspect-[654/800]" eager />
            <VideoFeature />
          </div>
          <motion.div style={{ y: yB }} className="col-span-4 mt-28 space-y-6">
            <PhotoCard p={photos.fruit} className="aspect-[3/4]" />
            <PhotoCard p={photos.welcome} className="aspect-[618/700]" />
          </motion.div>
          <motion.div style={{ y: yC }} className="col-span-3 mt-8 space-y-6">
            <PhotoCard p={photos.prize} className="aspect-[616/860]" />
            <Moments />
          </motion.div>
        </div>

        {/* Mobile / tablet: swipeable strip */}
        <div className="lg:hidden">
          <ul
            className="-mx-4 mt-12 flex snap-x snap-mandatory gap-4 overflow-x-auto px-4 pb-4 [scrollbar-width:none] sm:-mx-8 sm:px-8 [&::-webkit-scrollbar]:hidden"
            aria-label="Photos from school life"
          >
            {Object.values(photos).map((p) => (
              <li key={p.src} className="w-[78vw] max-w-[22rem] shrink-0 snap-start">
                <PhotoCard p={p} className="aspect-[3/4]" />
              </li>
            ))}
          </ul>
          <p className="mt-2 text-sm text-muted" aria-hidden>
            Swipe for more →
          </p>
          <div className="mt-10 grid gap-8 sm:grid-cols-2">
            <VideoFeature />
            <Moments />
          </div>
        </div>
      </div>
    </section>
  );
}

function PhotoCard({ p, className = "", eager }: { p: Photo; className?: string; eager?: boolean }) {
  return (
    <motion.figure
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -10% 0px" }}
      transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
      className={`group relative overflow-hidden rounded-[var(--radius-card)] bg-paper-2 ${className}`}
    >
      <img
        src={p.src}
        alt={p.alt}
        width={p.w}
        height={p.h}
        loading={eager ? "eager" : "lazy"}
        decoding="async"
        style={p.pos ? { objectPosition: p.pos } : undefined}
        className="absolute inset-0 size-full object-cover transition-transform duration-[1.2s] ease-[var(--ease-out-expo)] group-hover:scale-[1.05]"
      />
      <div className="absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-ink/75 to-transparent" />
      <figcaption className="absolute inset-x-0 bottom-0 p-5 text-white">
        <span className="heading block text-[1.45rem]">{p.title}</span>
        <span className="mt-1 block max-w-[26ch] text-[0.9rem] leading-snug text-white/85 transition-[opacity,transform] duration-500 lg:translate-y-2 lg:opacity-0 lg:group-hover:translate-y-0 lg:group-hover:opacity-100">
          {p.note}
        </span>
      </figcaption>
    </motion.figure>
  );
}

/* Click-to-load YouTube: nothing from YouTube loads until the visitor asks for it. */
function VideoFeature() {
  const [play, setPlay] = useState(false);
  const { id, title } = school.videos.feature;
  return (
    <Reveal>
      <div className="overflow-hidden rounded-[var(--radius-card)] bg-ink text-chalk">
        <div className="relative aspect-video">
          {play ? (
            <iframe
              className="absolute inset-0 size-full"
              src={`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`}
              title={title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <button
              type="button"
              onClick={() => setPlay(true)}
              className="group absolute inset-0 size-full"
              aria-label={`Play video: ${title}`}
            >
              <img
                src="./media/video-balanced-generation.webp"
                alt=""
                loading="lazy"
                className="absolute inset-0 size-full object-cover opacity-80 transition-[opacity,transform] duration-700 group-hover:scale-[1.03] group-hover:opacity-100"
              />
              <span className="absolute inset-0 bg-ink/30" />
              <span className="absolute left-1/2 top-1/2 grid size-16 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full bg-sun text-ink shadow-xl transition-transform duration-500 group-hover:scale-110">
                <Play size={24} className="translate-x-0.5" />
              </span>
            </button>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-4 p-5 sm:p-6">
          <div>
            <p className="eyebrow text-sun">Watch</p>
            <p className="heading mt-1 text-[1.4rem]">Building a Balanced Generation</p>
          </div>
          <a
            href={school.social.youtube}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-white/20"
          >
            <YouTube size={18} /> More on YouTube
          </a>
        </div>
      </div>
    </Reveal>
  );
}

function Moments() {
  return (
    <Reveal className="rounded-[var(--radius-card)] bg-paper p-6 ring-1 ring-inset ring-line">
      <p className="eyebrow text-muted">Also on the calendar</p>
      <ul className="mt-4 flex flex-wrap gap-2">
        {moments.map((m) => (
          <li key={m} className="rounded-full bg-chalk px-3 py-1.5 text-[0.85rem] ring-1 ring-inset ring-line">
            {m}
          </li>
        ))}
      </ul>
      <div className="mt-6 flex flex-wrap gap-2 border-t border-line pt-5">
        <FollowLink href={school.social.instagram} label="Instagram" icon={<Instagram size={18} />} />
        <FollowLink href={school.social.facebook} label="Facebook" icon={<Facebook size={18} />} />
      </div>
    </Reveal>
  );
}

function FollowLink({ href, label, icon }: { href: string; label: string; icon: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="group inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2.5 text-sm font-semibold text-chalk"
    >
      {icon} {label}
      <ArrowUpRight size={15} className="transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
    </a>
  );
}
