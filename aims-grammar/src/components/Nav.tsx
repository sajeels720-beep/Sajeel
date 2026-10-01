import { useEffect, useState } from "react";
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from "motion/react";
import { nav, school, whatsappLink } from "../data/site";
import { Crest } from "./ui/primitives";
import { ArrowRight, Close, Facebook, Instagram, Menu, Phone, WhatsApp, YouTube } from "./ui/Icons";

const EASE = [0.16, 1, 0.3, 1] as const;

export function Nav() {
  const { scrollY } = useScroll();
  const [solid, setSolid] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string>("");
  const [onDark, setOnDark] = useState(false);

  useMotionValueEvent(scrollY, "change", (y) => {
    const prev = scrollY.getPrevious() ?? 0;
    const vh = window.innerHeight;
    setSolid(y > vh * 0.85);
    // Tuck the bar away while reading downward; bring it back on any upward scroll.
    setHidden(y > vh * 1.2 && y > prev + 4);
    if (y < prev - 4) setHidden(false);
  });

  useEffect(() => {
    const ids = nav.map((n) => n.id);
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) io.observe(el);
    }
    return () => io.disconnect();
  }, []);

  // Track whether a dark section sits under the bar, so it can switch to a navy finish.
  useEffect(() => {
    const dark = document.querySelectorAll("[data-nav-dark]");
    const under = new Set<Element>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) e.isIntersecting ? under.add(e.target) : under.delete(e.target);
        setOnDark(under.size > 0);
      },
      { rootMargin: "0px 0px -94% 0px" },
    );
    dark.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    document.documentElement.style.overflow = open ? "hidden" : "";
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const light = open || !solid || onDark;

  return (
    <>
      <a
        href="#main"
        className="fixed left-4 top-3 z-[60] -translate-y-20 rounded-full bg-sun px-4 py-2 font-semibold text-ink focus:translate-y-0"
      >
        Skip to content
      </a>

      <motion.header
        initial={{ y: -24, opacity: 0 }}
        animate={{ y: hidden && !open ? "-110%" : 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: EASE }}
        className="fixed inset-x-0 top-0 z-50"
      >
        <div
          className={`transition-[background-color,box-shadow,padding] duration-500 ease-[var(--ease-out-quart)] ${
            solid && !open
              ? onDark
                ? "bg-ink/80 py-2.5 shadow-[0_1px_0_rgb(255_255_255/0.08)] backdrop-blur-xl"
                : "bg-paper/85 py-2.5 shadow-[0_1px_0_var(--color-line)] backdrop-blur-xl"
              : "bg-transparent py-4 sm:py-5"
          }`}
        >
          <nav className="container-x flex items-center justify-between gap-6" aria-label="Main">
            <a href="#top" className="group flex items-center gap-3" aria-label="AIMS Grammar High School, home">
              <Crest className="size-10 shrink-0 drop-shadow-sm transition-transform duration-500 group-hover:rotate-[-8deg] sm:size-11" />
              <span
                className={`leading-[1.05] transition-colors duration-500 ${light ? "text-white" : "text-ink"}`}
              >
                <span className="heading block text-[1.12rem]">AIMS Grammar</span>
                <span className={`block text-[0.72rem] font-medium tracking-[0.12em] uppercase ${light ? "text-white/70" : "text-muted"}`}>
                  High School · Gujranwala
                </span>
              </span>
            </a>

            <ul className="hidden items-center gap-1 xl:flex">
              {nav.map((item) => {
                const isActive = active === item.id;
                return (
                  <li key={item.id}>
                    <a
                      href={`#${item.id}`}
                      aria-current={isActive ? "true" : undefined}
                      className={`relative whitespace-nowrap rounded-full px-4 py-2 text-[0.93rem] font-medium transition-colors duration-300 ${
                        light ? "text-white/85 hover:text-white" : "text-ink/75 hover:text-ink"
                      }`}
                    >
                      {item.label}
                      {isActive && (
                        <motion.span
                          layoutId="nav-dot"
                          className="absolute bottom-0.5 left-1/2 size-1.5 -translate-x-1/2 rounded-full bg-sun"
                          transition={{ type: "spring", bounce: 0.25, visualDuration: 0.4 }}
                        />
                      )}
                    </a>
                  </li>
                );
              })}
            </ul>

            <div className="flex items-center gap-2">
              <a
                href="#admissions"
                className="hidden items-center gap-2 whitespace-nowrap rounded-full bg-sun px-5 py-2.5 text-[0.92rem] font-semibold text-ink transition-[transform,background-color] duration-300 hover:-translate-y-0.5 hover:bg-[#ffd24d] sm:inline-flex"
              >
                Admissions {school.session}
                <ArrowRight size={16} />
              </a>
              <button
                type="button"
                onClick={() => setOpen((o) => !o)}
                aria-expanded={open}
                aria-controls="mobile-menu"
                aria-label={open ? "Close menu" : "Open menu"}
                className={`grid size-12 place-items-center rounded-full transition-colors duration-300 xl:hidden ${
                  open
                    ? "bg-white/10 text-white"
                    : light
                      ? "bg-white/15 text-white ring-1 ring-inset ring-white/30 backdrop-blur-md"
                      : "bg-ink text-chalk"
                }`}
              >
                {open ? <Close size={22} /> : <Menu size={22} />}
              </button>
            </div>
          </nav>
        </div>
      </motion.header>

      <AnimatePresence>
        {open && (
          <motion.div
            id="mobile-menu"
            role="dialog"
            aria-modal="true"
            aria-label="Menu"
            className="fixed inset-0 z-40 flex flex-col overflow-y-auto bg-ink px-4 pb-8 pt-28 text-white sm:px-8 xl:hidden"
            initial={{ clipPath: "inset(0 0 100% 0)" }}
            animate={{ clipPath: "inset(0 0 0% 0)" }}
            exit={{ clipPath: "inset(0 0 100% 0)" }}
            transition={{ duration: 0.6, ease: [0.76, 0, 0.24, 1] }}
          >
            <ul className="flex flex-col">
              {nav.map((item, i) => (
                <li key={item.id} className="overflow-hidden border-b border-white/10">
                  <motion.a
                    href={`#${item.id}`}
                    onClick={() => setOpen(false)}
                    initial={{ y: "100%" }}
                    animate={{ y: 0 }}
                    transition={{ duration: 0.7, ease: EASE, delay: 0.15 + i * 0.05 }}
                    className="heading flex items-center justify-between py-4 text-[2.4rem]"
                  >
                    {item.label}
                    <ArrowRight size={26} className="text-sun" />
                  </motion.a>
                </li>
              ))}
            </ul>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: EASE, delay: 0.45 }}
              className="mt-auto grid gap-3"
            >
              <a
                href="#admissions"
                onClick={() => setOpen(false)}
                className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-sun text-lg font-semibold text-ink"
              >
                Apply for {school.session} <ArrowRight size={18} />
              </a>
              <div className="grid grid-cols-2 gap-3">
                <a
                  href={school.phones[0].href}
                  className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-white/10 font-semibold"
                >
                  <Phone size={18} /> Call
                </a>
                <a
                  href={whatsappLink("Assalam o Alaikum, I'd like to ask about admissions at AIMS Grammar High School.")}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-white/10 font-semibold"
                >
                  <WhatsApp size={18} /> WhatsApp
                </a>
              </div>
              <div className="mt-2 flex items-center justify-center gap-2 text-white/80">
                <SocialLink href={school.social.youtube} label="YouTube"><YouTube size={22} /></SocialLink>
                <SocialLink href={school.social.instagram} label="Instagram"><Instagram size={22} /></SocialLink>
                <SocialLink href={school.social.facebook} label="Facebook"><Facebook size={22} /></SocialLink>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function SocialLink({ href, label, children }: { href: string; label: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`AIMS Grammar High School on ${label}`}
      className="grid size-12 place-items-center rounded-full transition-colors hover:bg-white/10 hover:text-white"
    >
      {children}
    </a>
  );
}
