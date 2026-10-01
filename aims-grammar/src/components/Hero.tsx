import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, useReducedMotion, useScroll, useSpring, useTransform, type MotionValue } from "motion/react";
import { school } from "../data/site";
import { useMediaQuery } from "../hooks/useMediaQuery";
import { CTA, MaskLines, Scribble } from "./ui/primitives";
import { Pause, Phone, Play } from "./ui/Icons";

const EASE = [0.16, 1, 0.3, 1] as const;

/**
 * The hero stays pinned while the next section (passed as children) slides
 * up over it like a sheet of paper. As it's covered, the film recedes into
 * a rounded card and dims, the same hand-off as the reference site.
 */
export function HeroStack({ children }: { children: ReactNode }) {
  const coverRef = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: coverRef, offset: ["start end", "start start"] });
  const p = useSpring(scrollYProgress, { stiffness: 140, damping: 30, restDelta: 0.0005 });

  const scale = useTransform(p, [0, 1], [1, reduce ? 1 : 0.9]);
  const radius = useTransform(p, [0, 1], [0, reduce ? 0 : 40]);
  const dim = useTransform(p, [0, 1], [0, 0.65]);
  const contentY = useTransform(p, [0, 0.7], [0, reduce ? 0 : -110]);
  const contentOpacity = useTransform(p, [0, 0.55], [1, 0]);

  return (
    <div className="relative">
      <Hero scale={scale} radius={radius} dim={dim} contentY={contentY} contentOpacity={contentOpacity} />
      <div ref={coverRef} className="relative z-10">
        {children}
      </div>
    </div>
  );
}

type MV = MotionValue<number>;

function Hero({
  scale,
  radius,
  dim,
  contentY,
  contentOpacity,
}: {
  scale: MV;
  radius: MV;
  dim: MV;
  contentY: MV;
  contentOpacity: MV;
}) {
  const isMobile = useMediaQuery("(max-width: 767px)");
  const reduce = useReducedMotion();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(!reduce);

  const src = isMobile ? "./media/hero-mobile.mp4" : "./media/hero-desktop.mp4";
  const poster = isMobile ? "./media/hero-mobile-poster.jpg" : "./media/hero-desktop-poster.jpg";

  // useReducedMotion can resolve after first render; stop the film once it does.
  useEffect(() => {
    if (reduce) setPlaying(false);
  }, [reduce]);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    if (playing) v.play().catch(() => setPlaying(false));
    else v.pause();
  }, [playing, src]);

  return (
    <section id="top" aria-label="Welcome" className="sticky top-0 h-svh min-h-[36rem] overflow-hidden bg-ink">
      {/* ---- Film ---- */}
      <motion.div
        className="absolute inset-0 origin-top overflow-hidden"
        style={{ scale, borderRadius: radius }}
      >
        <motion.div
          className="absolute inset-0"
          initial={{ scale: 1.14, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 2.2, ease: EASE }}
        >
          <video
            key={src}
            ref={videoRef}
            className="size-full object-cover"
            src={src}
            poster={poster}
            autoPlay={!reduce}
            muted
            loop
            playsInline
            preload="auto"
            aria-label="Children at AIMS Grammar High School colouring and drawing in class"
          />
        </motion.div>
        {/* Legibility: navy wash from the left and bottom, soft shade under the nav. */}
        <div className="absolute inset-0 bg-[linear-gradient(100deg,rgb(14_24_56/0.88)_0%,rgb(14_24_56/0.55)_42%,rgb(14_24_56/0.08)_75%)] max-md:bg-[linear-gradient(180deg,rgb(14_24_56/0.55)_0%,rgb(14_24_56/0.15)_30%,rgb(14_24_56/0.7)_58%,rgb(14_24_56/0.96)_100%)]" />
        <div className="absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-ink/80 to-transparent md:h-1/2" />
        <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-ink/60 to-transparent" />
        <div className="grain absolute inset-0" />
        <motion.div className="absolute inset-0 bg-ink" style={{ opacity: dim }} />
      </motion.div>

      {/* ---- Copy ---- */}
      <motion.div
        style={{ y: contentY, opacity: contentOpacity }}
        className="container-x relative z-10 flex h-full flex-col justify-end pb-8 pt-28 text-white sm:pb-12 lg:pb-14"
      >
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: EASE, delay: 1.0 }}
          className="absolute right-4 top-28 hidden max-w-[19rem] text-right text-[0.95rem] leading-relaxed text-white/80 sm:right-8 md:block lg:right-12 lg:top-32"
        >
          A Play Group to Matric school on Jinnah Road, Khiali. Concept-based teaching, a caring campus, and
          a lot of colouring pencils.
        </motion.p>

        <motion.p
          lang="ur"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: EASE, delay: 0.2 }}
          className="urdu mb-1 self-start text-[1.35rem] text-sun sm:text-[1.7rem]"
        >
          {school.sloganUr}
        </motion.p>

        <h1 className="display text-[clamp(3.7rem,16vw,12.5rem)] uppercase">
          <span className="sr-only">AIMS Grammar High School. </span>
          <MaskLines
            animateOnMount
            delay={0.3}
            stagger={0.12}
            lines={[
              "Small steps.",
              <span key="b" className="relative inline-block">
                Big flight.
                <Scribble
                  animateOnMount
                  delay={1.25}
                  className="absolute -bottom-[0.06em] left-[0.02em] h-[0.16em] w-[96%]"
                />
              </span>,
            ]}
          />
        </h1>

        <div className="mt-7 flex flex-col gap-7 md:mt-9 md:flex-row md:items-end md:justify-between">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: EASE, delay: 0.85 }}
            className="max-w-xl"
          >
            <p className="text-[1.05rem] leading-relaxed text-white/85 sm:text-[1.15rem]">
              At {school.name}, we raise children who are{" "}
              <strong className="font-semibold text-white">happy, confident and competent</strong>, from their
              first crayon in Play Group to their Matric board exams.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <CTA href="#admissions">Apply for {school.session}</CTA>
              <CTA href={school.phones[0].href} variant="ghost" icon={<Phone size={17} />}>
                Call {school.phones[0].label}
              </CTA>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: EASE, delay: 1.1 }}
            className="flex items-center gap-3"
          >
            <a
              href="#admissions"
              className="flex items-center gap-3 rounded-full bg-white/10 py-2 pl-3 pr-5 text-[0.88rem] ring-1 ring-inset ring-white/25 backdrop-blur-md transition-colors hover:bg-white/20"
            >
              <span className="relative flex size-2.5">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-sun opacity-70" />
                <span className="relative inline-flex size-2.5 rounded-full bg-sun" />
              </span>
              <span>
                <span className="font-semibold">Admissions open</span>
                <span className="text-white/70 sm:hidden"> · {school.session}</span>
                <span className="hidden text-white/70 sm:inline"> · {school.admissionClasses}</span>
              </span>
            </a>
            <button
              type="button"
              onClick={() => setPlaying((v) => !v)}
              aria-label={playing ? "Pause background video" : "Play background video"}
              className="grid size-11 shrink-0 place-items-center rounded-full bg-white/10 ring-1 ring-inset ring-white/25 backdrop-blur-md transition-colors hover:bg-white/20"
            >
              {playing ? <Pause size={16} /> : <Play size={16} />}
            </button>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}
