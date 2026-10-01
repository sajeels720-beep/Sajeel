import { motion } from "motion/react";
import { Reveal, SectionLabel, MaskLines } from "./ui/primitives";
import { ArrowRight } from "./ui/Icons";

const values = [
  {
    title: "Islamiat & Qirat",
    body: "Faith and Quran recitation are part of the school day, not an afterthought.",
  },
  {
    title: "Respect",
    body: "For teachers, classmates and elders. Taught every day, and expected.",
  },
  {
    title: "Love for Pakistan",
    body: "From 14 August to Defence Day, students celebrate and honour their country.",
  },
  {
    title: "Punctuality & uniform",
    body: "On time, in uniform, ready to learn. Discipline is a habit we start early.",
  },
];

export function Values() {
  return (
    <section id="values" aria-labelledby="values-title" className="relative bg-paper py-24 sm:py-32">
      <div className="container-x grid gap-14 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-32">
            <SectionLabel n="03">Character</SectionLabel>
            <h2 id="values-title" className="heading mt-5 text-[clamp(2.6rem,6vw,5.4rem)]">
              <MaskLines lines={["Character", "comes first."]} />
            </h2>
            <Reveal delay={0.2}>
              <blockquote className="relative mt-10 max-w-md border-l-4 border-sun pl-6">
                <p className="text-[1.3rem] font-medium leading-snug tracking-[-0.01em] sm:text-[1.45rem]">
                  “Alongside excellent education, building strong character is our first priority.”
                </p>
                <footer className="mt-4 text-[0.9rem] text-muted">The Director, AIMS Grammar High School</footer>
              </blockquote>
            </Reveal>
          </div>
        </div>

        <ol className="border-t border-line lg:col-span-7">
          {values.map((v, i) => (
            <Reveal as="li" key={v.title} delay={i * 0.06} y={20}>
              <div className="group relative isolate overflow-hidden border-b border-line">
                <span
                  aria-hidden
                  className="absolute inset-0 -z-10 origin-bottom scale-y-0 bg-ink transition-transform duration-500 ease-[var(--ease-out-expo)] group-hover:scale-y-100"
                />
                <div className="grid grid-cols-[auto_1fr_auto] items-start gap-x-5 px-1 py-7 transition-colors duration-500 group-hover:text-chalk sm:gap-x-8 sm:px-4 sm:py-9">
                  <span className="display pt-1 text-[1.6rem] text-sun-deep tabular-nums sm:text-[2rem]">
                    0{i + 1}
                  </span>
                  <div>
                    <h3 className="heading text-[1.9rem] sm:text-[2.6rem]">{v.title}</h3>
                    <p className="mt-2 max-w-md text-muted transition-colors duration-500 group-hover:text-white/70">
                      {v.body}
                    </p>
                  </div>
                  <ArrowRight
                    size={26}
                    className="mt-2 -rotate-45 text-ink/30 transition-[transform,color] duration-500 group-hover:rotate-0 group-hover:text-sun"
                  />
                </div>
              </div>
            </Reveal>
          ))}
        </ol>
      </div>

      <Parents />
    </section>
  );
}

/* Parents ↔ teachers as one continuous loop, the way the school describes it. */
function Parents() {
  const loop =
    "M290 100C320 60 340 38 366 38a62 62 0 0 1 0 124c-26 0-46-22-76-62-30-40-50-62-76-62a62 62 0 0 0 0 124c26 0 46-22 76-62Z";
  return (
    <div className="container-x mt-24 sm:mt-32">
      <div className="grid items-center gap-10 overflow-hidden rounded-[var(--radius-card)] bg-paper-2 p-6 sm:p-10 lg:grid-cols-2 lg:p-14">
        <div className="relative">
          <svg viewBox="100 0 380 200" className="w-full" role="img" aria-label="A loop joining home and school">
            <path d={loop} fill="none" stroke="#0E1838" strokeOpacity={0.12} strokeWidth={14} strokeLinecap="round" />
            <motion.path
              d={loop}
              fill="none"
              stroke="#F6C432"
              strokeWidth={14}
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true, margin: "0px 0px -20% 0px" }}
              transition={{ duration: 2.2, ease: [0.65, 0, 0.35, 1] }}
            />
            <text x={214} y={108} textAnchor="middle" className="heading" fontSize={24} fill="#0E1838">
              Home
            </text>
            <text x={366} y={108} textAnchor="middle" className="heading" fontSize={24} fill="#0E1838">
              School
            </text>
          </svg>
        </div>
        <div>
          <p className="eyebrow text-muted">Parents</p>
          <h3 className="heading mt-3 text-[clamp(2rem,4vw,3.2rem)]">Parents are part of the AIMS family.</h3>
          <p className="mt-4 max-w-lg text-muted">
            Regular parent–teacher meetings and school events keep home and classroom pulling in the same direction.
            When you know what’s happening in class, your child feels it.
          </p>
          <p className="mt-6 text-[1.15rem] font-semibold">Better communication, brighter progress.</p>
        </div>
      </div>
    </div>
  );
}
