import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { ArrowRight } from "./Icons";

const EASE = [0.16, 1, 0.3, 1] as const;

/* ---------- CTA button ----------
   Pill with a separate arrow "coin". On hover the arrow slides through the
   coin and the pill nudges; colours shift with a CSS transition. */
type CTAProps = {
  href: string;
  children: ReactNode;
  variant?: "sun" | "ink" | "ghost" | "ghost-dark";
  icon?: ReactNode;
  className?: string;
  external?: boolean;
  onClick?: () => void;
};

const variants: Record<NonNullable<CTAProps["variant"]>, { pill: string; coin: string }> = {
  sun: { pill: "bg-sun text-ink hover:bg-[#ffd24d]", coin: "bg-ink text-sun" },
  ink: { pill: "bg-ink text-chalk hover:bg-ink-2", coin: "bg-sun text-ink" },
  ghost: {
    pill: "bg-white/10 text-white ring-1 ring-inset ring-white/35 backdrop-blur-md hover:bg-white/20",
    coin: "bg-white text-ink",
  },
  "ghost-dark": {
    pill: "bg-transparent text-ink ring-1 ring-inset ring-ink/20 hover:bg-ink/5",
    coin: "bg-ink text-chalk",
  },
};

export function CTA({ href, children, variant = "sun", icon, className = "", external, onClick }: CTAProps) {
  const v = variants[variant];
  return (
    <motion.a
      href={href}
      onClick={onClick}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      whileTap={{ scale: 0.97 }}
      className={`group inline-flex min-h-12 items-center gap-3 rounded-full py-1.5 pl-5 pr-1.5 text-[0.95rem] font-semibold tracking-[-0.01em] transition-[background-color,transform,box-shadow] duration-300 ease-[var(--ease-out-quart)] hover:-translate-y-0.5 ${v.pill} ${className}`}
    >
      <span>{children}</span>
      <span
        className={`relative grid size-9 shrink-0 place-items-center overflow-hidden rounded-full ${v.coin}`}
        aria-hidden
      >
        {icon ?? (
          <>
            <ArrowRight
              size={17}
              className="transition-transform duration-300 ease-[var(--ease-out-quart)] group-hover:translate-x-7"
            />
            <ArrowRight
              size={17}
              className="absolute -translate-x-7 transition-transform duration-300 ease-[var(--ease-out-quart)] group-hover:translate-x-0"
            />
          </>
        )}
      </span>
    </motion.a>
  );
}

/* ---------- Reveal on enter ---------- */
type RevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  x?: number;
  as?: "div" | "li" | "section" | "p" | "figure";
};

export function Reveal({ children, className, delay = 0, y = 28, x = 0, as = "div" }: RevealProps) {
  const M = motion[as];
  return (
    <M
      className={className}
      initial={{ opacity: 0, y, x }}
      whileInView={{ opacity: 1, y: 0, x: 0 }}
      viewport={{ once: true, margin: "0px 0px -12% 0px" }}
      transition={{ duration: 0.9, ease: EASE, delay }}
    >
      {children}
    </M>
  );
}

/* ---------- Masked line reveal: each line slides up out of its own clip ---------- */
export function MaskLines({
  lines,
  className = "",
  lineClassName = "",
  delay = 0,
  stagger = 0.09,
  animateOnMount = false,
}: {
  lines: ReactNode[];
  className?: string;
  lineClassName?: string;
  delay?: number;
  stagger?: number;
  animateOnMount?: boolean;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -10% 0px" });
  const show = animateOnMount || inView;
  return (
    <span ref={ref} className={className}>
      {lines.map((line, i) => (
        <span key={i} className="block overflow-hidden pb-[0.08em] -mb-[0.08em]">
          <motion.span
            className={`block ${lineClassName}`}
            initial={{ y: "105%" }}
            animate={show ? { y: "0%" } : { y: "105%" }}
            transition={{ duration: 1.05, ease: EASE, delay: delay + i * stagger }}
          >
            {line}
          </motion.span>
        </span>
      ))}
    </span>
  );
}

/* ---------- Crayon scribble underline that draws itself ---------- */
export function Scribble({
  className = "",
  color = "var(--color-sun)",
  delay = 0.2,
  animateOnMount = false,
}: {
  className?: string;
  color?: string;
  delay?: number;
  animateOnMount?: boolean;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const inView = useInView(ref, { once: true });
  const show = animateOnMount || inView;
  return (
    <svg
      ref={ref}
      viewBox="0 0 300 24"
      preserveAspectRatio="none"
      className={`pointer-events-none ${className}`}
      aria-hidden
    >
      <motion.path
        d="M4 15.5C52 8 104 6.5 160 9.2c43 2 85 4.6 136-1.7M18 19.5c64-5.6 140-6.5 236-3"
        fill="none"
        stroke={color}
        strokeWidth="5.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={show ? { pathLength: 1, opacity: 1 } : {}}
        transition={{ duration: 1.1, ease: [0.65, 0, 0.35, 1], delay }}
      />
    </svg>
  );
}

/* ---------- Video that only loads and plays while on screen ---------- */
export function LazyVideo({
  src,
  poster,
  className = "",
  label,
}: {
  src: string;
  poster: string;
  className?: string;
  label: string;
}) {
  const ref = useRef<HTMLVideoElement>(null);
  const reduce = useReducedMotion();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          if (!loaded) setLoaded(true);
          if (!reduce) el.play().catch(() => {});
        } else {
          el.pause();
        }
      },
      { rootMargin: "200px 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [loaded, reduce]);

  return (
    <video
      ref={ref}
      className={className}
      poster={poster}
      src={loaded ? src : undefined}
      muted
      loop
      playsInline
      preload="none"
      aria-label={label}
    />
  );
}

/* ---------- School crest (cut from the school's own badge artwork) ---------- */
export function Crest({ className = "" }: { className?: string }) {
  return (
    <img
      src="./brand/logo.webp"
      alt="AIMS Grammar High School crest"
      width={186}
      height={186}
      decoding="async"
      className={`rounded-full ${className}`}
    />
  );
}

/* ---------- Section label: number + rule + name ---------- */
export function SectionLabel({ n, children, tone = "ink" }: { n: string; children: ReactNode; tone?: "ink" | "light" }) {
  const c = tone === "ink" ? "text-ink/60 before:bg-ink/25" : "text-white/60 before:bg-white/30";
  return (
    <p className={`eyebrow flex items-center gap-3 ${c} before:h-px before:w-8 before:content-['']`}>
      <span className="tabular-nums">{n}</span>
      <span>{children}</span>
    </p>
  );
}
