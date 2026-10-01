import { useRef } from "react";
import { motion, useScroll, useTransform, type MotionValue } from "motion/react";
import { school } from "../data/site";
import { Reveal, SectionLabel } from "./ui/primitives";

const EASE = [0.16, 1, 0.3, 1] as const;

const statement =
  "Report cards matter. But our real job is bigger: raising a balanced generation of children who are happy, confident and competent.";
const highlight = new Set(["happy,", "confident", "competent."]);

export function Vision() {
  return (
    <section
      id="vision"
      className="ruled relative rounded-t-[2rem] bg-paper pb-24 pt-20 shadow-[0_-30px_60px_-20px_rgb(14_24_56/0.45)] sm:rounded-t-[2.75rem] sm:pb-32 sm:pt-28"
    >
      <div className="container-x">
        <SectionLabel n="01">Our vision</SectionLabel>
        <ScrollStatement />

        <div className="mt-20 grid gap-14 lg:mt-28 lg:grid-cols-12 lg:gap-10">
          <StagePhoto />
          <div className="lg:col-span-6 lg:col-start-7">
            <Reveal>
              <h2 className="heading text-[clamp(2.1rem,4.2vw,3.6rem)]">
                Three promises,
                <br />
                one balanced child.
              </h2>
              <p className="mt-5 max-w-lg text-muted">
                We call it <em className="not-italic font-semibold text-ink">mutawazin nasal</em>, a balanced
                generation. Good teaching alone isn't enough. Children also need a place where they feel safe and
                a stage where they learn to stand tall.
              </p>
            </Reveal>
            <Venn />
          </div>
        </div>
      </div>
    </section>
  );
}

/* Statement whose words ink in one by one as you scroll past. */
function ScrollStatement() {
  const ref = useRef<HTMLParagraphElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 0.85", "end 0.45"] });
  const words = statement.split(" ");
  return (
    <p
      ref={ref}
      className="heading mt-8 max-w-[22ch] text-[clamp(2.2rem,5.6vw,5.4rem)] leading-[1] sm:max-w-[20ch]"
      aria-label={statement}
    >
      {words.map((w, i) => (
        <Word key={i} progress={scrollYProgress} range={[i / words.length, (i + 1) / words.length]} hl={highlight.has(w)}>
          {w}
        </Word>
      ))}
    </p>
  );
}

function Word({
  children,
  progress,
  range,
  hl,
}: {
  children: string;
  progress: MotionValue<number>;
  range: [number, number];
  hl: boolean;
}) {
  const opacity = useTransform(progress, range, [0.16, 1]);
  return (
    <span aria-hidden className="relative mr-[0.22em] inline-block">
      <motion.span style={{ opacity }} className={hl ? "text-royal" : undefined}>
        {children}
      </motion.span>
    </span>
  );
}

function StagePhoto() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["-8%", "8%"]);
  return (
    <figure ref={ref} className="lg:col-span-5">
      <motion.div
        initial={{ clipPath: "inset(18% 12% 18% 12% round 2rem)" }}
        whileInView={{ clipPath: "inset(0% 0% 0% 0% round 1.75rem)" }}
        viewport={{ once: true, margin: "0px 0px -15% 0px" }}
        transition={{ duration: 1.4, ease: EASE }}
        className="relative aspect-[4/5] overflow-hidden rounded-[var(--radius-card)] bg-paper-2"
      >
        <motion.img
          src="./media/stage-nanhay-qadam.webp"
          alt="Six AIMS students in uniform kneel and stand on stage with arms forming the letter A, in front of the Nanhay Qadam Bari Urhan banner"
          loading="lazy"
          decoding="async"
          width={629}
          height={836}
          style={{ y }}
          className="absolute inset-x-0 top-[-10%] h-[120%] w-full object-cover"
        />
      </motion.div>
      <figcaption className="mt-4 flex items-start justify-between gap-4 text-[0.92rem] text-muted">
        <span>Our students on stage, making the “A” of AIMS under the school motto.</span>
        <span lang="ur" className="urdu shrink-0 text-[1.05rem] leading-[1.6] text-ink">
          {school.sloganUr}
        </span>
      </figcaption>
    </figure>
  );
}

const circles = [
  { label: "Happy", cx: 190, cy: 178, fill: "#F6C432", from: { x: -70, y: -50 }, note: "A safe, caring campus" },
  { label: "Confident", cx: 330, cy: 178, fill: "#3A8BDA", from: { x: 70, y: -50 }, note: "Stage, debates and activities" },
  { label: "Competent", cx: 260, cy: 298, fill: "#E2492F", from: { x: 0, y: 80 }, note: "Concepts, not rote learning" },
] as const;

const labelPos = [
  { x: 150, y: 150 },
  { x: 372, y: 150 },
  { x: 260, y: 372 },
];

function Venn() {
  return (
    <div className="mt-10">
      <motion.svg
        viewBox="0 0 520 470"
        className="mx-auto w-full max-w-[34rem] overflow-visible"
        role="img"
        aria-label="Venn diagram: Happy, Confident and Competent overlap to form a balanced generation"
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "0px 0px -20% 0px" }}
      >
        {circles.map((c, i) => (
          <motion.g
            key={c.label}
            variants={{
              hidden: { x: c.from.x, y: c.from.y, opacity: 0 },
              show: { x: 0, y: 0, opacity: 1 },
            }}
            transition={{ type: "spring", bounce: 0.18, visualDuration: 1.1, delay: i * 0.12 }}
          >
            <circle cx={c.cx} cy={c.cy} r={150} fill={c.fill} fillOpacity={0.28} style={{ mixBlendMode: "multiply" }} />
            <circle cx={c.cx} cy={c.cy} r={150} fill="none" stroke="#0E1838" strokeOpacity={0.35} strokeWidth={1.2} />
            <text
              x={labelPos[i].x}
              y={labelPos[i].y}
              textAnchor="middle"
              className="heading"
              fontSize={30}
              fill="#0E1838"
            >
              {c.label}
            </text>
          </motion.g>
        ))}
        <motion.g
          variants={{ hidden: { opacity: 0, scale: 0.6 }, show: { opacity: 1, scale: 1 } }}
          transition={{ type: "spring", bounce: 0.35, visualDuration: 0.6, delay: 1.05 }}
          style={{ transformOrigin: "260px 222px" }}
        >
          <rect x={186} y={202} width={148} height={42} rx={21} fill="#0E1838" />
          <text x={260} y={229} textAnchor="middle" fontSize={17} fontWeight={600} fill="#F6C432">
            Balanced
          </text>
        </motion.g>
      </motion.svg>

      <ul className="mt-8 grid gap-3 sm:grid-cols-3">
        {circles.map((c, i) => (
          <Reveal as="li" key={c.label} delay={0.1 * i} y={16} className="flex gap-3 border-t border-line pt-3">
            <span className="mt-1.5 size-3 shrink-0 rounded-full" style={{ background: c.fill }} />
            <span className="text-[0.95rem] leading-snug">
              <strong className="block font-semibold">{c.label}</strong>
              <span className="text-muted">{c.note}</span>
            </span>
          </Reveal>
        ))}
      </ul>
    </div>
  );
}
