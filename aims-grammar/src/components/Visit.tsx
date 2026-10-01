import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from "motion/react";
import { nav, school, whatsappLink } from "../data/site";
import { CTA, Crest, MaskLines, Reveal, SectionLabel } from "./ui/primitives";
import { ArrowRight, ArrowUpRight, Facebook, Instagram, Mail, MapPin, Phone, WhatsApp, YouTube } from "./ui/Icons";

export function Visit() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [showMap, setShowMap] = useState(false);

  // The Google Maps iframe is heavy; only mount it when the section is close.
  useEffect(() => {
    const el = mapRef.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => e.isIntersecting && setShowMap(true), { rootMargin: "400px 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <section id="visit" aria-labelledby="visit-title" className="ruled relative bg-paper py-24 sm:py-32">
      <div className="container-x grid gap-12 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-5">
          <SectionLabel n="06">Visit us</SectionLabel>
          <h2 id="visit-title" className="heading mt-5 text-[clamp(2.6rem,4.6vw,4.6rem)]">
            <MaskLines lines={["Come and see", "our classrooms."]} />
          </h2>

          <Reveal delay={0.1} className="mt-10 space-y-7">
            <div className="flex gap-4">
              <IconDot><MapPin size={20} /></IconDot>
              <address className="not-italic">
                <span className="block text-[1.15rem] font-semibold">{school.address.line1}</span>
                <span className="block text-muted">
                  {school.address.line2}, {school.address.region}
                </span>
                <a
                  href={school.address.mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1.5 font-semibold underline decoration-sun decoration-2 underline-offset-4"
                >
                  Get directions <ArrowUpRight size={15} />
                </a>
              </address>
            </div>

            <div className="flex gap-4">
              <IconDot><Phone size={20} /></IconDot>
              <ul className="space-y-1">
                {school.phones.map((p) => (
                  <li key={p.href}>
                    <a href={p.href} className="text-[1.15rem] font-semibold tabular-nums hover:text-royal">
                      {p.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex gap-4">
              <IconDot><Mail size={20} /></IconDot>
              <a href={`mailto:${school.email}`} className="self-center text-[1.15rem] font-semibold hover:text-royal">
                {school.email}
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.2} className="mt-10 flex flex-wrap gap-3">
            <CTA href="#admissions" variant="ink">
              Apply for {school.session}
            </CTA>
            <CTA
              href={whatsappLink("Assalam o Alaikum, I'd like to visit AIMS Grammar High School.")}
              variant="ghost-dark"
              external
              icon={<WhatsApp size={17} />}
            >
              WhatsApp us
            </CTA>
          </Reveal>
        </div>

        <Reveal className="lg:col-span-7" y={40}>
          <div
            ref={mapRef}
            className="relative aspect-[4/3] overflow-hidden rounded-[var(--radius-card)] bg-paper-2 ring-1 ring-inset ring-line lg:aspect-auto lg:h-full lg:min-h-[32rem]"
          >
            {showMap ? (
              <iframe
                title="Map showing AIMS Grammar High School on Jinnah Road, Khiali, Gujranwala"
                src={school.address.embedUrl}
                className="absolute inset-0 size-full [filter:saturate(0.85)_contrast(1.02)]"
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            ) : (
              <div className="absolute inset-0 grid place-items-center text-muted">Loading map…</div>
            )}
            <a
              href={school.address.mapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="absolute bottom-4 left-4 inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2.5 text-sm font-semibold text-chalk shadow-lg"
            >
              <MapPin size={16} className="text-sun" /> Open in Google Maps
            </a>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function IconDot({ children }: { children: React.ReactNode }) {
  return (
    <span className="grid size-11 shrink-0 place-items-center rounded-full bg-sun text-ink" aria-hidden>
      {children}
    </span>
  );
}

export function Footer() {
  return (
    <footer id="site-footer" data-nav-dark className="relative overflow-hidden bg-ink pt-20 text-chalk">
      <div className="container-x">
        <div className="grid gap-12 border-b border-white/10 pb-14 md:grid-cols-2 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <div className="flex items-center gap-3">
              <Crest className="size-12" />
              <span className="leading-tight">
                <span className="heading block text-xl">{school.name}</span>
                <span className="text-sm text-white/60">{school.taglines.join(" · ")}</span>
              </span>
            </div>
            <p className="mt-6 max-w-sm text-white/65">
              Play Group to Matric in Khiali, Gujranwala. Raising a happy, confident and competent generation, one small
              step at a time.
            </p>
          </div>

          <nav aria-label="Footer" className="lg:col-span-2 lg:col-start-6">
            <p className="eyebrow text-white/45">Explore</p>
            <ul className="mt-4 space-y-2.5">
              {nav.map((n) => (
                <li key={n.id}>
                  <a href={`#${n.id}`} className="text-white/80 transition-colors hover:text-sun">
                    {n.label}
                  </a>
                </li>
              ))}
              <li>
                <a href="#admissions" className="text-white/80 transition-colors hover:text-sun">
                  Admissions
                </a>
              </li>
            </ul>
          </nav>

          <div className="lg:col-span-3">
            <p className="eyebrow text-white/45">Contact</p>
            <address className="mt-4 space-y-2.5 not-italic text-white/80">
              <p>
                {school.address.line1}
                <br />
                {school.address.line2}
              </p>
              {school.phones.map((p) => (
                <a key={p.href} href={p.href} className="block tabular-nums hover:text-sun">
                  {p.label}
                </a>
              ))}
              <a href={`mailto:${school.email}`} className="block hover:text-sun">
                {school.email}
              </a>
            </address>
          </div>

          <div className="lg:col-span-2">
            <p className="eyebrow text-white/45">Follow</p>
            <ul className="mt-4 space-y-2.5">
              {[
                { href: school.social.youtube, label: "YouTube", icon: <YouTube size={18} /> },
                { href: school.social.instagram, label: "Instagram", icon: <Instagram size={18} /> },
                { href: school.social.facebook, label: "Facebook", icon: <Facebook size={18} /> },
              ].map((s) => (
                <li key={s.label}>
                  <a
                    href={s.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2.5 text-white/80 transition-colors hover:text-sun"
                  >
                    {s.icon} {s.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex flex-col gap-2 py-6 text-sm text-white/45 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} {school.name}. All rights reserved.</p>
          <a href="#top" className="inline-flex items-center gap-1.5 hover:text-white">
            Back to top <ArrowRight size={14} className="-rotate-90" />
          </a>
        </div>
      </div>

      {/* Oversized sign-off */}
      <div aria-hidden className="pointer-events-none select-none overflow-hidden">
        <p className="display translate-y-[18%] whitespace-nowrap text-center text-[19vw] uppercase leading-[0.8] text-white/[0.06]">
          Big flight.
        </p>
      </div>
    </footer>
  );
}

/* Mobile: thumb-reach Call / Apply bar once the visitor is past the hero. */
export function MobileActionBar() {
  const { scrollY } = useScroll();
  const [pastHero, setPastHero] = useState(false);
  const [covered, setCovered] = useState(false);

  useMotionValueEvent(scrollY, "change", (y) => setPastHero(y > window.innerHeight * 0.9));

  // Step aside while the admissions form or footer is on screen (they have their own buttons).
  useEffect(() => {
    const targets = [document.getElementById("admissions"), document.getElementById("site-footer")].filter(
      (el): el is HTMLElement => !!el,
    );
    const visible = new Set<Element>();
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) e.isIntersecting ? visible.add(e.target) : visible.delete(e.target);
      setCovered(visible.size > 0);
    });
    for (const el of targets) io.observe(el);
    return () => io.disconnect();
  }, []);

  const show = pastHero && !covered;

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ y: "120%" }}
          animate={{ y: 0 }}
          exit={{ y: "120%" }}
          transition={{ type: "spring", bounce: 0.15, visualDuration: 0.45 }}
          className="fixed inset-x-3 bottom-[max(0.75rem,env(safe-area-inset-bottom))] z-40 grid grid-cols-[auto_1fr] gap-2 rounded-full bg-ink/95 p-1.5 shadow-[0_20px_40px_-12px_rgb(0_0_0/0.5)] backdrop-blur-lg lg:hidden"
        >
          <a
            href={school.phones[0].href}
            className="flex min-h-12 items-center gap-2 rounded-full px-5 font-semibold text-chalk"
            aria-label={`Call the school on ${school.phones[0].label}`}
          >
            <Phone size={18} className="text-sun" /> Call
          </a>
          <a
            href="#admissions"
            className="flex min-h-12 items-center justify-center gap-2 rounded-full bg-sun font-semibold text-ink"
          >
            Apply for {school.session} <ArrowRight size={17} />
          </a>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
